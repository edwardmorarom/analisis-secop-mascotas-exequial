import numpy as np
import pandas as pd

from src.etl.comun import cargar_config, ruta
from src.modelos import estimador_diferencia as ed
from src.modelos.etiquetas_humanas import construir

ESCENARIOS = [("tfidf", False), ("tfidf", True), ("e5", False), ("e5", True)]


def confirmado(config, u):
    h = construir(config)
    x = u.merge(h[["fuente", "llave", "etiqueta", "origen"]], on=["fuente", "llave"], how="inner")
    sin = x.loc[x["etiqueta"] == "funerario", "valor_constante_2025"].sum() / 1e9
    con = x.loc[x["etiqueta"].isin(["funerario", "mixto"]), "valor_constante_2025"].sum() / 1e9
    por_origen = x.assign(v=x["valor_constante_2025"] / 1e9).groupby(["origen", "etiqueta"])["v"].sum().unstack(fill_value=0)
    return sin, con, por_origen, len(x)


def contribuciones(d, modelo, con_mixto, rng, repeticiones=2000):
    """Aporte de cada estrato a la varianza del estimador: varianza bootstrap de su término Σ w (y − ŷ) v."""
    y = ed.indicador(d["etiqueta"], con_mixto).values
    yhat = ed.indicador(d[f"pred_{modelo}_modelo"], con_mixto).values
    z = d["peso"].values * (y - yhat) * d["valor_constante_2025"].values
    filas = []
    for e in d["estrato"].unique():
        idx = np.flatnonzero((d["estrato"] == e).values)
        sim = np.array([z[rng.choice(idx, len(idx))].sum() for _ in range(repeticiones)])
        filas.append({"estrato": e, "n_muestra": len(idx), "N_ajustado": float(d["peso"].values[idx].sum()), "correccion_mm": z[idx].sum() / 1e9,
                      "varianza_mm2": sim.var(ddof=1) / 1e18, "errores_en_muestra": int(((y - yhat)[idx] != 0).sum())})
    t = pd.DataFrame(filas)
    t["pct_varianza"] = t["varianza_mm2"] / t["varianza_mm2"].sum() * 100
    t["desv_est_mm"] = np.sqrt(t["varianza_mm2"])
    return t.sort_values("pct_varianza", ascending=False)


def main():
    config = cargar_config()
    u, d400, d30 = ed.bloques(config)
    u = ed.subestratos(config, u)
    nuevo = (u["fuente"] == "secop1") & (u["anio"] >= 2023)
    h = construir(config)
    llaves_censo = set(zip(ed.censo(h)["fuente"], ed.censo(h)["llave"]))
    print("contratos del censo:", len(llaves_censo))
    en_muestra = d400.merge(pd.DataFrame(list(llaves_censo), columns=["fuente", "llave"]), on=["fuente", "llave"])
    print("censados que están en la muestra de 400:", len(en_muestra))
    d400 = d400.assign(peso=ed.ajustar_pesos(d400, u, llaves_censo, nuevo, "400"))
    d30 = d30.assign(peso=ed.ajustar_pesos(d30, u, llaves_censo, nuevo, "30"))
    marco = u[~nuevo]
    print("N del marco por estrato (todos / sin censo) y n de la muestra, tamaño ajustado = N ajustado:")
    n_marco = marco.groupby("subestrato").size()
    n_censo = marco[[(f, l) in llaves_censo for f, l in zip(marco["fuente"], marco["llave"])]].groupby("subestrato").size()
    n_muestra = d400.groupby("estrato").size()
    ajustado = d400.groupby("estrato")["peso"].sum()
    print(pd.DataFrame({"N": n_marco, "censo": n_censo, "n": n_muestra, "N_ajustado_por_pesos": ajustado}).fillna(0).round(1).to_string())
    sin, con, por_origen, n_etiquetados = confirmado(config, u)
    print(f"\nValor confirmado por etiquetas humanas ({n_etiquetados} contratos): funerario {sin:.1f}; funerario o mixto {con:.1f} (miles de millones de 2025)")
    print(por_origen.round(1).to_string())
    est = ed.estimar(config, con_censo=True)
    print(est[["modelo", "mixto", "estimador_diferencia", "ic95_bajo", "ic95_alto"]].assign(
        estimador_diferencia=lambda t: t["estimador_diferencia"] / 1e9, ic95_bajo=lambda t: t["ic95_bajo"] / 1e9, ic95_alto=lambda t: t["ic95_alto"] / 1e9).round(1).to_string(index=False))
    rng = np.random.default_rng(2026)
    pd.set_option("display.width", 220)
    for modelo, mixto in ESCENARIOS:
        t = contribuciones(d400, modelo, mixto, rng)
        t30 = contribuciones(d30, modelo, mixto, rng)
        t30["estrato"] = "SECOP I nuevo: " + t30["estrato"].astype(str)
        todo = pd.concat([t, t30])
        todo["pct_varianza"] = todo["varianza_mm2"] / todo["varianza_mm2"].sum() * 100
        print(f"\nAporte a la varianza: {modelo}, {'con' if mixto else 'sin'} mixto (desviación total {np.sqrt(todo['varianza_mm2'].sum()):.1f} mm)")
        print(todo[["estrato", "n_muestra", "N_ajustado", "errores_en_muestra", "correccion_mm", "desv_est_mm", "pct_varianza"]].round(2).to_string(index=False))
        todo.assign(modelo=modelo, mixto=int(mixto)).to_csv(ruta(config, "processed") / "resultados_secop" / f"varianza_por_estrato_{modelo}_{'con' if mixto else 'sin'}_mixto.csv", index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
