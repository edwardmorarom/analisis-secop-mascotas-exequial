import glob

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from src.etl.comun import RAIZ, cargar_config, ruta
from src.etl.extraer_minsalud import cargar_pob_dane, normalizar

MICRODATOS = "data/raw/dane/em2021/microdatos/"
SOLO_CABECERA = {"25269", "25899", "25290", "25430", "25126", "25740", "25260", "25817", "25785", "25799", "25099",
                 "25295", "25769", "25898"}
VIVIENDAS_POR_SEGMENTO = 10
SALIDA = "em2021"


def leer(patron):
    f = glob.glob(str(RAIZ / MICRODATOS / patron))[0]
    d = pd.read_csv(f, sep=";", encoding="latin-1", decimal=",", low_memory=False)
    return d


def cargar_hogares():
    a = leer("Identifica*.csv")[["DIRECTORIO", "DPTO", "MPIO", "CLASE", "COD_LOCALIDAD", "NOMBRE_LOCALIDAD", "ESTRATO2021", "FEX_C"]]
    c = leer("Condiciones*.csv")[["DIRECTORIO", "DIRECTORIO_HOG", "NHCCP47A", "NHCCP47A1", "NHCCP47B", "NHCCP47B1", "NHCCP47C"]]
    h = c.merge(a, on="DIRECTORIO", how="left", validate="many_to_one")
    assert h["FEX_C"].notna().all(), "hogares sin factor de expansión"
    h["perro"] = (h["NHCCP47A"] == 1).astype(int)
    h["gato"] = (h["NHCCP47B"] == 1).astype(int)
    h["otro"] = (h["NHCCP47C"] == 1).astype(int)
    h["mascota"] = ((h["perro"] + h["gato"] + h["otro"]) > 0).astype(int)
    h["n_perros"] = np.where(h["perro"] == 1, h["NHCCP47A1"].fillna(0), 0.0)
    h["n_gatos"] = np.where(h["gato"] == 1, h["NHCCP47B1"].fillna(0), 0.0)
    h["unidad_municipio"] = h["MPIO"].astype(int).astype(str).str.zfill(5)
    h["hogar"] = 1
    h["segmento"] = (h.sort_values(["ESTRATO2021", "DIRECTORIO"]).groupby("ESTRATO2021").cumcount() // VIVIENDAS_POR_SEGMENTO)
    return h


def total_y_cv(d, variable, psu):
    """Total expandido y su coeficiente de variación por linealización (estratos y conglomerados)."""
    d = d.assign(z=d["FEX_C"] * d[variable])
    por_psu = d.groupby(["ESTRATO2021", psu])["z"].sum()
    total = float(por_psu.sum())
    var = 0.0
    for _, g in por_psu.groupby(level=0):
        n = len(g)
        if n > 1:
            var += n / (n - 1) * ((g - g.mean()) ** 2).sum()
    return total, (np.sqrt(var) / total if total > 0 else np.nan)


def estimar_unidad(d):
    fila = {"hogares_muestra": len(d), "viviendas_muestra": d["DIRECTORIO"].nunique(), "estratos": d["ESTRATO2021"].nunique()}
    for nombre, var in (("hogares", "hogar"), ("hogares_con_perro", "perro"), ("hogares_con_gato", "gato"),
                        ("hogares_con_mascota", "mascota"), ("perros", "n_perros"), ("gatos", "n_gatos")):
        t, cv_seg = total_y_cv(d, var, "segmento")
        _, cv_viv = total_y_cv(d, var, "DIRECTORIO")
        fila[nombre], fila[f"cv_{nombre}"], fila[f"cv_viv_{nombre}"] = t, cv_seg, cv_viv
    fila["pct_hogares_con_perro"] = fila["hogares_con_perro"] / fila["hogares"] * 100
    fila["perros_por_hogar_con_perro"] = fila["perros"] / fila["hogares_con_perro"] if fila["hogares_con_perro"] else np.nan
    return fila


def unidades(h):
    filas = []
    for cod, g in h.groupby("unidad_municipio"):
        filas.append({"tipo": "municipio", "codigo": cod, "nombre": cod, "cobertura": "solo cabecera" if cod in SOLO_CABECERA else "cabecera y resto",
                      **estimar_unidad(g)})
    bogota = h[h["unidad_municipio"] == "11001"]
    for loc, g in bogota.groupby("NOMBRE_LOCALIDAD"):
        filas.append({"tipo": "localidad", "codigo": str(int(g["COD_LOCALIDAD"].iloc[0])), "nombre": loc, "cobertura": "cabecera y rural", **estimar_unidad(g)})
    return pd.DataFrame(filas)


def minsalud(config):
    procesado = ruta(config, "processed")
    panel = pd.read_parquet(procesado / "panel_minsalud_municipal.parquet")
    panel = panel[panel["anio"].isin([2019, 2023, 2024]) & panel["cod_divipola"].notna()]
    muni = panel.pivot_table(index="cod_divipola", columns="anio", values="poblacion_perros", aggfunc="first")
    muni.columns = [f"minsalud_perros_{a}" for a in muni.columns]
    metodo = panel[panel["anio"] == 2019].set_index("cod_divipola")["metodo_estimacion"].rename("metodo_2019")
    muni = muni.join(metodo)
    loc = pd.read_parquet(procesado / "minsalud_localidades_bogota.parquet")
    loc = loc.assign(clave=loc["municipio_pdf"].map(normalizar)).pivot_table(index="clave", columns="anio", values="poblacion_perros", aggfunc="first")
    loc.columns = [f"minsalud_perros_{a}" for a in loc.columns]
    return muni, loc


def comparar(u, config):
    muni, loc = minsalud(config)
    pob = cargar_pob_dane(config, 2021)
    llaves = u.apply(lambda r: r["codigo"] if r["tipo"] == "municipio" else normalizar(r["nombre"]), axis=1)
    ms = pd.concat([muni.reindex(llaves[u["tipo"] == "municipio"]).set_index(u.index[u["tipo"] == "municipio"]),
                    loc.reindex(llaves[u["tipo"] == "localidad"]).set_index(u.index[u["tipo"] == "localidad"])])
    out = u.join(ms)
    out["minsalud_perros_2021_interp"] = np.sqrt(out["minsalud_perros_2019"] * out["minsalud_perros_2023"])
    for a in ("2019", "2021_interp", "2023", "2024"):
        out[f"razon_minsalud_em_{a}"] = out[f"minsalud_perros_{a}"] / out["perros"]
        out[f"razon_minsalud_hogares_con_perro_{a}"] = out[f"minsalud_perros_{a}"] / out["hogares_con_perro"]
    out["poblacion_dane_2021"] = out.apply(lambda r: pob.get(r["codigo"]) if r["tipo"] == "municipio" else np.nan, axis=1)
    out["habitantes_por_perro_em"] = out["poblacion_dane_2021"] / out["perros"]
    for a in ("2019", "2023", "2024"):
        out[f"habitantes_por_perro_minsalud_{a}"] = out["poblacion_dane_2021"] / out[f"minsalud_perros_{a}"]
    return out


def correlaciones(c, filtro, etiqueta):
    filas = []
    x = c[filtro]
    for a in ("2019", "2021_interp", "2023", "2024"):
        v = x[["perros", f"minsalud_perros_{a}"]].dropna()
        if len(v) >= 5:
            rho, p = spearmanr(v["perros"], v[f"minsalud_perros_{a}"])
            filas.append({"grupo": etiqueta, "anio_minsalud": a, "unidades": len(v), "spearman": rho, "p": p})
    return pd.DataFrame(filas)


def gasto_mascotas(h):
    m = leer("Gastos*/*.csv")[["DIRECTORIO", "DIRECTORIO_HOG", "NHCMP11P", "NHCMP11PA", "NHCMP11PB"]]
    d = h.merge(m, on=["DIRECTORIO", "DIRECTORIO_HOG"], how="left", validate="one_to_one")
    d["gasto_si"] = (d["NHCMP11P"] == 1).astype(int)
    d["gasto_anual"] = np.where(d["gasto_si"] == 1, d["NHCMP11PA"].fillna(0) + d["NHCMP11PB"].fillna(0), 0.0)
    d["gasto_mensual"] = d["gasto_anual"] / 12
    d["tenencia"] = np.select([(d["perro"] == 1) & (d["gato"] == 1), d["perro"] == 1, d["gato"] == 1, d["otro"] == 1],
                              ["perro y gato", "solo perro", "solo gato", "solo otras mascotas"], "sin mascotas")
    d["bogota"] = np.where(d["unidad_municipio"] == "11001", "Bogotá", "Municipios de Cundinamarca")
    return d


def media_ponderada(d, var="gasto_mensual"):
    w = d["FEX_C"]
    media = (w * d[var]).sum() / w.sum()
    # linealización de la razón sobre segmentos
    z = (d["FEX_C"] * (d[var] - media)).groupby([d["ESTRATO2021"], d["segmento"]]).sum()
    v = 0.0
    for _, g in z.groupby(level=0):
        n = len(g)
        if n > 1:
            v += n / (n - 1) * ((g - g.mean()) ** 2).sum()
    return media, np.sqrt(v) / w.sum() / media if media else np.nan


def mediana_ponderada(x, w):
    o = np.argsort(x.values)
    xs, ws = x.values[o], w.values[o]
    c = np.cumsum(ws) / ws.sum()
    return float(xs[np.searchsorted(c, 0.5)])


def resumen_gasto(d):
    filas = []
    grupos = [("Todos los hogares", d)] + [(f"Hogares {t}", g) for t, g in d.groupby("tenencia")] + [
        (f"Hogares con mascota, {b}", g[g["mascota"] == 1]) for b, g in d.groupby("bogota")]
    grupos.append(("Hogares con mascota", d[d["mascota"] == 1]))
    for nombre, g in grupos:
        media, cv = media_ponderada(g)
        con = g[g["gasto_si"] == 1]
        media_con, cv_con = media_ponderada(con) if len(con) > 1 else (np.nan, np.nan)
        filas.append({"grupo": nombre, "hogares_muestra": len(g), "hogares_expandidos": g["FEX_C"].sum(),
                      "pct_con_gasto": (g["FEX_C"] * g["gasto_si"]).sum() / g["FEX_C"].sum() * 100,
                      "gasto_mensual_medio": media, "cv_gasto_mensual_medio": cv,
                      "gasto_mensual_medio_si_gasta": media_con, "cv_si_gasta": cv_con,
                      "mediana_gasto_mensual_si_gasta": mediana_ponderada(con["gasto_mensual"], con["FEX_C"]) if len(con) else np.nan})
    return pd.DataFrame(filas)


def main():
    config = cargar_config()
    salida = ruta(config, "processed") / SALIDA
    salida.mkdir(parents=True, exist_ok=True)
    h = cargar_hogares()
    u = unidades(h)
    c = comparar(u, config)
    c.to_csv(salida / "em2021_vs_minsalud.csv", index=False, encoding="utf-8-sig")
    cor = pd.concat([correlaciones(c, c["tipo"] == "municipio", "municipios (cabecera y resto)"),
                     correlaciones(c, (c["tipo"] == "municipio") & (c["cobertura"] == "cabecera y resto"), "municipios con cabecera y resto"),
                     correlaciones(c, c["tipo"] == "localidad", "localidades de Bogotá")])
    cor.to_csv(salida / "em2021_correlaciones.csv", index=False, encoding="utf-8-sig")
    g = gasto_mascotas(h)
    r = resumen_gasto(g)
    r.to_csv(salida / "em2021_gasto_mascotas.csv", index=False, encoding="utf-8-sig")
    pd.set_option("display.width", 250)
    print("hogares:", len(h), "viviendas:", h["DIRECTORIO"].nunique(), "hogares expandidos:", round(h["FEX_C"].sum()))
    print(c[c["tipo"] == "municipio"][["codigo", "cobertura", "hogares_muestra", "hogares_con_perro", "cv_hogares_con_perro", "perros", "cv_perros", "gatos", "cv_gatos",
                                       "minsalud_perros_2019", "minsalud_perros_2023", "minsalud_perros_2024"]].round(2).to_string(index=False))
    print(cor.round(3).to_string(index=False))
    print(r.round(1).to_string(index=False))


if __name__ == "__main__":
    main()
