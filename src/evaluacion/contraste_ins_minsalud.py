import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from src.etl.comun import cargar_config, ruta
from src.etl.extraer_minsalud import cargar_pob_dane

ANIOS = (2023, 2024)
REPETICIONES = 2000
SEMILLA = 2026


def base(config, anio):
    p = ruta(config, "processed")
    ins = pd.read_parquet(ruta(config, "interim") / "ins_agresiones_municipal.parquet")
    ins = ins[(ins["anio"] == anio) & ins["cod_divipola"].notna()][["cod_divipola", "municipio_pdf", "departamento_pdf", "casos", "poblacion"]]
    ms = pd.read_parquet(p / "panel_minsalud_municipal.parquet")
    ms = ms[(ms["anio"] == anio) & ms["tipo"].isin(["municipio", "distrito"])][["cod_divipola", "poblacion_perros", "pob_dane", "metodo_estimacion"]]
    pob = cargar_pob_dane(config, anio).rename_axis("cod_divipola").reset_index()
    d = ins.merge(ms[["cod_divipola", "poblacion_perros", "metodo_estimacion"]], on="cod_divipola", how="left").merge(pob, on="cod_divipola", how="left")
    d["anio"] = anio
    d["agresiones_x100k"] = d["casos"] / d["pob_dane"] * 1e5
    d["perros_x1000hab"] = d["poblacion_perros"] / d["pob_dane"] * 1e3
    inc = pd.read_csv(p / "incidencias.csv", dtype={"cod_divipola": str})
    marc = inc[inc["anio"] == anio].groupby("cod_divipola")["regla"].agg(lambda s: ",".join(sorted(set(s)))).rename("reglas")
    d = d.merge(marc, on="cod_divipola", how="left")
    d["marcada"] = d["reglas"].notna()
    return d


def spearman_boot(x, y, rng):
    rho = spearmanr(x, y)[0]
    n = len(x)
    sim = np.empty(REPETICIONES)
    for b in range(REPETICIONES):
        i = rng.integers(0, n, n)
        sim[b] = spearmanr(x[i], y[i])[0]
    return rho, np.percentile(sim, 2.5), np.percentile(sim, 97.5)


def residuos(d):
    """Residuo de percentiles: percentil de agresiones menos el percentil esperado por una recta sobre el de perros."""
    pa = d["agresiones_x100k"].rank(pct=True)
    pp = d["perros_x1000hab"].rank(pct=True)
    b, a = np.polyfit(pp, pa, 1)
    return pa - (a + b * pp)


def main():
    config = cargar_config()
    rng = np.random.default_rng(SEMILLA)
    filas, tops = [], []
    for anio in ANIOS:
        d = base(config, anio)
        v = d.dropna(subset=["agresiones_x100k", "perros_x1000hab"])
        v = v[(v["poblacion_perros"] > 0) & (v["casos"] > 0)]
        for nombre, x in (("todos", v), ("sin filas marcadas", v[~v["marcada"]])):
            rho, lo, hi = spearman_boot(x["agresiones_x100k"].values, x["perros_x1000hab"].values, rng)
            filas.append({"anio": anio, "conjunto": nombre, "municipios": len(x), "spearman": rho, "ic95_bajo": lo, "ic95_alto": hi,
                          "marcados": int(x["marcada"].sum())})
        v = v.assign(residuo=residuos(v))
        t = v.reindex(v["residuo"].abs().sort_values(ascending=False).index).head(20)
        tops.append(t[["anio", "cod_divipola", "municipio_pdf", "departamento_pdf", "casos", "pob_dane", "poblacion_perros", "agresiones_x100k", "perros_x1000hab", "residuo", "marcada", "reglas"]])
        filas[-2]["excluidos_sin_dato_o_cero"] = len(d) - len(v)
        filas[-1]["excluidos_sin_dato_o_cero"] = len(d) - len(v)
        d.to_parquet(ruta(config, "processed") / f"contraste_ins_minsalud_{anio}.parquet", index=False)
    r = pd.DataFrame(filas)
    t = pd.concat(tops, ignore_index=True)
    out = ruta(config, "processed") / "resultados_ins"
    out.mkdir(exist_ok=True)
    r.to_csv(out / "spearman.csv", index=False, encoding="utf-8-sig")
    t.to_csv(out / "mayor_residuo.csv", index=False, encoding="utf-8-sig")
    pd.set_option("display.width", 250)
    print(r.round(3).to_string(index=False))
    print(t.round(2).to_string(index=False))
    print(t.groupby("anio")["marcada"].sum())


if __name__ == "__main__":
    main()
