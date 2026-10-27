import numpy as np
import pandas as pd

from src.etl.comun import cargar_config, ruta
from src.modelos.etiquetas_humanas import construir
from src.modelos.muestra_secop import subestrato

REPETICIONES = 2000
SEMILLA = 2026
ESCENARIOS = [("tfidf", False), ("tfidf", True), ("e5", False), ("e5", True)]


def indicador(serie, con_mixto):
    return serie.isin(["funerario", "mixto"] if con_mixto else ["funerario"]).astype(float)


def bloques(config):
    procesado = ruta(config, "processed")
    u = pd.read_parquet(procesado / "resultados_secop" / "universo_mercado.parquet")
    valores = u[["fuente", "llave", "valor_constante_2025"]]
    e = pd.read_parquet(procesado / "etiquetas_finales.parquet")[["id_muestra", "etiqueta", "peso", "subestrato"]]
    m = pd.read_parquet(procesado / "muestra_secop_maestra.parquet")[["id_muestra", "fuente", "llave"]]
    pred = u[["fuente", "llave", "pred_tfidf_modelo", "pred_e5_modelo"]]
    d400 = e.merge(m, on="id_muestra").merge(valores, on=["fuente", "llave"]).merge(pred, on=["fuente", "llave"])
    d400["estrato"] = d400["subestrato"]
    n = pd.read_parquet(procesado / "secop1_nuevos_maestra.parquet")
    from src.modelos.evaluar_secop1_nuevos import cargar_etiquetadas
    n = cargar_etiquetadas(config)[["id_muestra", "fuente", "llave", "etiqueta", "peso", "grupo_pred"]]
    d30 = n.merge(valores, on=["fuente", "llave"]).merge(pred, on=["fuente", "llave"])
    d30["estrato"] = d30["grupo_pred"]
    return u, d400, d30


def correccion(d, modelo, con_mixto):
    y = indicador(d["etiqueta"], con_mixto)
    yhat = indicador(d[f"pred_{modelo}_modelo"], con_mixto)
    return (d["peso"] * (y - yhat) * d["valor_constante_2025"]).sum()


def bootstrap(d, modelo, con_mixto, rng):
    grupos = [np.flatnonzero((d["estrato"] == e).values) for e in d["estrato"].unique()]
    y = indicador(d["etiqueta"], con_mixto).values
    yhat = indicador(d[f"pred_{modelo}_modelo"], con_mixto).values
    terminos = (d["peso"].values * (y - yhat) * d["valor_constante_2025"].values)
    salida = np.empty(REPETICIONES)
    for b in range(REPETICIONES):
        salida[b] = sum(terminos[rng.choice(g, len(g))].sum() for g in grupos)
    return salida


def subestratos(config, u):
    interim = ruta(config, "interim")
    a = pd.concat([pd.read_parquet(interim / f"{n}_senales.parquet") for n in ("secop1", "secop2")], ignore_index=True)
    a["subestrato"] = a.apply(subestrato, axis=1)
    return u.merge(a[["fuente", "llave", "subestrato"]], on=["fuente", "llave"], how="left")


def censo(h):
    """Contratos revisados en forma censal por valor: la revisión de los 50 mayores (D83) y las dos etiquetas de D81."""
    return h[h["origen"].isin(["top_valor", "adicionales_d81"])]


def ajustar_pesos(d, u, llaves_censo, nuevo, por):
    """Descuenta del tamaño del estrato los contratos del censo para que el peso N/n represente solo al resto."""
    u = u.assign(censo=[(f, l) in llaves_censo for f, l in zip(u["fuente"], u["llave"])])
    if por == "400":
        marco = u[~nuevo]
        n_h = marco.groupby("subestrato").size() - marco[marco["censo"]].groupby("subestrato").size().reindex(marco["subestrato"].unique(), fill_value=0)
        n_muestra = d.groupby("estrato").size()
        return d["estrato"].map(n_h / n_muestra)
    nuevos = u[nuevo]
    grupo = np.where(nuevos["pred_tfidf_modelo"] == "funerario", "funerario", "otras")
    n_h = pd.Series(1, index=nuevos.index).groupby(grupo).sum() - nuevos[nuevos["censo"]].assign(g=lambda x: np.where(x["pred_tfidf_modelo"] == "funerario", "funerario", "otras")).groupby("g").size().reindex(["funerario", "otras"], fill_value=0)
    n_muestra = d.groupby("estrato").size()
    return d["estrato"].map(n_h / n_muestra)


def estimar(config, con_censo=True):
    u, d400, d30 = bloques(config)
    u = subestratos(config, u)
    nuevo = (u["fuente"] == "secop1") & (u["anio"] >= 2023)
    h = construir(config)
    llaves_censo = set(zip(censo(h)["fuente"], censo(h)["llave"])) if con_censo else set()
    if con_censo:
        d400 = d400.assign(peso=ajustar_pesos(d400, u, llaves_censo, nuevo, "400"))
        d30 = d30.assign(peso=ajustar_pesos(d30, u, llaves_censo, nuevo, "30"))
    ya = u.merge(h[["fuente", "llave", "etiqueta"]], on=["fuente", "llave"], how="left")
    rng = np.random.default_rng(SEMILLA)
    filas = []
    for modelo, con_mixto in ESCENARIOS:
        yhat_u = indicador(u[f"pred_{modelo}_modelo"], con_mixto)
        total_modelo = (yhat_u * u["valor_constante_2025"]).sum()
        humana_u = ya["etiqueta"].notna()
        en_censo = pd.Series([(f, l) in llaves_censo for f, l in zip(u["fuente"], u["llave"])], index=u.index)
        # parte censal: se sustituye la predicción por la etiqueta humana (error exacto)
        y_censo = indicador(ya.loc[en_censo, "etiqueta"], con_mixto)
        correccion_censo = ((y_censo - yhat_u[en_censo]) * u.loc[en_censo, "valor_constante_2025"]).sum()
        humana = ya["etiqueta"].notna()
        clase = ya[f"pred_{modelo}_modelo"].where(~humana, ya["etiqueta"])
        total_con_etiquetas = (indicador(clase, con_mixto) * ya["valor_constante_2025"]).sum()
        c400, c30 = correccion(d400, modelo, con_mixto), correccion(d30, modelo, con_mixto)
        b400 = bootstrap(d400, modelo, con_mixto, rng)
        b30 = bootstrap(d30, modelo, con_mixto, rng)
        estimador = total_modelo + correccion_censo + c400 + c30
        simulados = total_modelo + correccion_censo + b400 + b30
        filas.append({"modelo": modelo, "mixto": "con mixto" if con_mixto else "sin mixto",
                      "con_censo": con_censo, "total_sin_corregir": total_modelo, "total_con_etiquetas_humanas": total_con_etiquetas,
                      "correccion_censo": correccion_censo, "correccion_muestra_400": c400, "correccion_secop1_nuevos": c30, "estimador_diferencia": estimador,
                      "ic95_bajo": np.percentile(simulados, 2.5), "ic95_alto": np.percentile(simulados, 97.5),
                      "error_estandar_bootstrap": simulados.std(ddof=1), "total_bloque_secop1_nuevo": (yhat_u[nuevo] * u.loc[nuevo, "valor_constante_2025"]).sum()})
    return pd.DataFrame(filas)


def main():
    config = cargar_config()
    t = pd.concat([estimar(config, con_censo=False), estimar(config, con_censo=True)], ignore_index=True)
    t.to_csv(ruta(config, "processed") / "resultados_secop" / "estimador_diferencia.csv", index=False, encoding="utf-8-sig")
    pd.set_option("display.width", 250)
    mm = t.copy()
    for c in t.columns[3:]:
        mm[c] = t[c] / 1e9
    print(mm.round(2).to_string(index=False))




def estados_de_revision(config):
    """Mercado con la clase del modelo, con la jerarquía sin la revisión por valor y con la jerarquía completa."""
    u = pd.read_parquet(ruta(config, "processed") / "resultados_secop" / "universo_mercado.parquet")
    h_all = construir(config)
    estados = {"A: sin revisión (modelo y las 2 etiquetas de D81)": h_all[h_all["origen"] == "adicionales_d81"],
               "B: jerarquía sin la revisión por valor (400, 60, 30 y D81)": h_all[h_all["origen"] != "top_valor"],
               "C: jerarquía completa (con los 50 por valor)": h_all}
    filas = []
    for nombre, h in estados.items():
        x = u.merge(h[["fuente", "llave", "etiqueta"]], on=["fuente", "llave"], how="left")
        for modelo in ("tfidf", "e5"):
            clase = x[f"pred_{modelo}_modelo"].where(x["etiqueta"].isna(), x["etiqueta"])
            for con_mixto in (False, True):
                m = clase.isin(["funerario", "mixto"] if con_mixto else ["funerario"])
                g = x[m].groupby("anio")["valor_constante_2025"].sum()
                filas.append({"estado": nombre, "modelo": modelo, "mixto": "con" if con_mixto else "sin", "contratos": int(m.sum()),
                              "valor_mm": x.loc[m, "valor_constante_2025"].sum() / 1e9, **{f"v{a}": g.get(a, 0) / 1e9 for a in range(2020, 2026)}})
    t = pd.DataFrame(filas)
    t.to_csv(ruta(config, "processed") / "resultados_secop" / "mercado_con_y_sin_revision.csv", index=False, encoding="utf-8-sig")
    return t


if __name__ == "__main__":
    main()
    estados_de_revision(cargar_config())
