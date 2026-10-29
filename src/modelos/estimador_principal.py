import numpy as np
import pandas as pd

from src.etl.comun import cargar_config, ruta
from src.evaluacion.metricas_ponderadas import fila_resumen
from src.modelos import estimador_diferencia as ed
from src.modelos.etiquetas_humanas import construir
from src.modelos.sensibilidad_mixtos import humanitarios, universo

REPETICIONES = 2000
SEMILLA = 2026
ORIGENES_PREVIOS = ("muestra_400", "validacion_60_revisada", "secop1_nuevos", "top_valor", "adicionales_d81")
MODELOS = ("tfidf", "e5")


def _lote(procesado, nombre, uu, h):
    m = pd.read_parquet(procesado / f"{nombre}_maestra.parquet")
    d = m.merge(uu[["fuente", "llave", "valor_constante_2025", "pred_tfidf_modelo", "pred_e5_modelo"]], on=["fuente", "llave"], validate="one_to_one")
    return d.merge(h[["fuente", "llave", "etiqueta"]], on=["fuente", "llave"], validate="one_to_one")


def preparar(config):
    procesado = ruta(config, "processed")
    uu = universo(config)
    _, d400, d30 = ed.bloques(config)
    h = construir(config)
    nuevo = (uu["fuente"] == "secop1") & (uu["anio"] >= 2023)
    S = humanitarios(uu)
    llaves_S = set(zip(S["fuente"], S["llave"]))
    exactos_S = S[S["origen"].isin(ORIGENES_PREVIOS)]
    censo_h = ed.censo(h)
    exactos = set(zip(censo_h["fuente"], censo_h["llave"])) | set(zip(exactos_S["fuente"], exactos_S["llave"]))
    llaves_pesos = exactos | llaves_S
    fuera = lambda d: d[[(f, l) not in llaves_S for f, l in zip(d["fuente"], d["llave"])]]
    dH = _lote(procesado, "humanitarios_40", uu, h).assign(estrato=lambda t: "H_" + t["subestrato"])
    dD = _lote(procesado, "estrato_d_150", uu, h).assign(estrato="D_sin_senal")
    d400 = pd.concat([fuera(d400), dD[d400.columns.intersection(dD.columns)]], ignore_index=True)
    d400 = d400.assign(peso=ed.ajustar_pesos(d400, uu, llaves_pesos, nuevo, "400"))
    d30 = fuera(d30)
    d30 = d30.assign(peso=ed.ajustar_pesos(d30, uu, llaves_pesos, nuevo, "30"))
    return dict(uu=uu, h=h, S=S, nuevo=nuevo, exactos=exactos, d400=d400, d30=d30, dH=dH, dD=dD)


def terminos(d, modelo, con_mixto=False):
    y = ed.indicador(d["etiqueta"], con_mixto).values
    yhat = ed.indicador(d[f"pred_{modelo}_modelo"], con_mixto).values
    return d["peso"].values * (y - yhat) * d["valor_constante_2025"].values


def estimar(p, modelo, rng, con_mixto=False):
    uu, h = p["uu"], p["h"]
    yhat_u = ed.indicador(uu[f"pred_{modelo}_modelo"], con_mixto)
    total_modelo = (yhat_u * uu["valor_constante_2025"]).sum()
    ex = uu.merge(h[["fuente", "llave", "etiqueta"]].rename(columns={"etiqueta": "et"}), on=["fuente", "llave"])
    ex = ex[[(f, l) in p["exactos"] for f, l in zip(ex["fuente"], ex["llave"])]]
    censo = ((ed.indicador(ex["et"], con_mixto) - ed.indicador(ex[f"pred_{modelo}_modelo"], con_mixto)) * ex["valor_constante_2025"]).sum()
    bloques = [(p["d400"], "estrato"), (p["d30"], "estrato"), (p["dH"], "estrato")]
    grupos, puntual = [], {}
    for nombre, (d, col) in zip(("muestra_400_y_D150", "secop1_nuevos", "humanitarios_40"), bloques):
        z = terminos(d, modelo, con_mixto)
        puntual[nombre] = z.sum()
        grupos += [z[(d[col] == e).values] for e in d[col].unique()]
    simulados = np.zeros(REPETICIONES)
    for z in grupos:
        simulados += z[rng.integers(0, len(z), (REPETICIONES, len(z)))].sum(axis=1)
    base = total_modelo + censo
    estimador = base + sum(puntual.values())
    return {"modelo": modelo, "total_sin_corregir": total_modelo, "correccion_censo": censo, **{f"correccion_{k}": v for k, v in puntual.items()},
            "estimador": estimador, "ic95_bajo": np.percentile(base + simulados, 2.5), "ic95_alto": np.percentile(base + simulados, 97.5),
            "error_estandar": (base + simulados).std(ddof=1)}


def cota_estrato_d(p):
    d = p["uu"][(p["uu"]["subestrato"] == "D_sin_senal") & ~p["nuevo"]]
    et = d[d["origen"].isin(("muestra_400", "estrato_d_150", "validacion_60_revisada"))]
    n, positivos = len(et), int((et["etiqueta"] == "funerario").sum())
    N = len(d)
    cota = 3 / n if positivos == 0 else np.nan
    return {"etiquetados": n, "funerarios": positivos, "tamano_D": N, "cota_proporcion_95": cota, "contratos_ocultos_max": cota * N,
            "valor_medio_contrato_D_mm": d["valor_constante_2025"].mean() / 1e9, "valor_ilustrativo_mm": cota * N * d["valor_constante_2025"].mean() / 1e9}


def f1_lotes(p):
    dH, dD = p["dH"], p["dD"]
    filas = []
    for clase, definicion in (("funerario", ("funerario",)), ("funerario o mixto", ("funerario", "mixto"))):
        y = np.where(dH["etiqueta"].isin(definicion), "funerario", "otro")
        for nombre, col in (("TF-IDF", "pred_tfidf_modelo"), ("e5", "pred_e5_modelo")):
            pred = np.where(dH[col].isin(definicion), "funerario", "otro")
            for escala, peso in (("ponderado", dH["peso"]), ("sin ponderar", np.ones(len(dH)))):
                f = fila_resumen(nombre, y, pred, peso, dH["estrato"])
                filas.append({"lote": "humanitarios 40", "definicion": clase, "modelo": nombre, "escala": escala, **{k: v for k, v in f.items() if k != "modelo"}})
    for nombre, col in (("TF-IDF", "pred_tfidf_modelo"), ("e5", "pred_e5_modelo")):
        fp = int((dD[col] == "funerario").sum())
        filas.append({"lote": "estrato D 150", "definicion": "funerario", "modelo": nombre, "escala": "conteos", "precision": 0.0 if fp else np.nan,
                      "sensibilidad": np.nan, "f1": np.nan, "falsos_positivos": fp, "verdaderos_negativos": len(dD) - fp, "positivos_reales": 0})
    return pd.DataFrame(filas)


def mixtos_aparte(p):
    uu = p["uu"]
    m = uu["pred_tfidf"] == "mixto"
    return {"contratos": int(m.sum()), "valor_mm": uu.loc[m, "valor_constante_2025"].sum() / 1e9}


def main():
    config = cargar_config()
    p = preparar(config)
    rng = np.random.default_rng(SEMILLA)
    filas = [estimar(p, m, rng) for m in MODELOS]
    t = pd.DataFrame(filas)
    salida = ruta(config, "processed") / "resultados_secop"
    t.to_csv(salida / "estimador_principal.csv", index=False, encoding="utf-8-sig")
    cota = cota_estrato_d(p)
    pd.Series(cota).to_csv(salida / "cota_estrato_d.csv", encoding="utf-8-sig")
    f = f1_lotes(p)
    f.to_csv(salida / "f1_lotes_nuevos.csv", index=False, encoding="utf-8-sig")
    pd.Series(mixtos_aparte(p)).to_csv(salida / "mixtos_aparte.csv", encoding="utf-8-sig")
    pd.set_option("display.width", 250)
    mm = t.copy()
    for c in t.columns[1:]:
        mm[c] = t[c] / 1e9
    print(mm.round(2).to_string(index=False))
    print(cota)
    print(f.round(3).to_string(index=False))
    print(mixtos_aparte(p))
    print({k: (len(v) if hasattr(v, "__len__") else v) for k, v in p.items() if k in ("S", "d400", "d30", "dH", "dD", "exactos")})
    print(p["d400"].groupby("estrato")["peso"].agg(["size", "first"]).round(2).to_string())
    print(p["dH"].groupby("estrato")["peso"].agg(["size", "first"]).round(2).to_string())


if __name__ == "__main__":
    main()
