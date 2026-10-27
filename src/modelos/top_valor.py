import numpy as np
import pandas as pd
from openpyxl.styles import Alignment, Font

from src.etl.anonimizar import anonimizar
from src.etl.comun import RAIZ, cargar_config, ruta
from src.evaluacion.plantillas_etiquetado import libro
from src.evaluacion.reglas_etiquetado import D20, D21
from src.modelos.validacion_externa import REGLAS_NUEVAS

N_TOP = 50
SEMILLA = 2026
CLASES_CANDIDATAS = ("funerario", "mixto")
DESTINO = RAIZ / "docs" / "revision_f4" / "top_valor.xlsx"


def con_etiqueta_humana(u, procesado):
    """Llaves (fuente, llave) con etiqueta humana distinta de la propia revisión por valor (que no cambia la selección)."""
    from src.modelos.etiquetas_humanas import construir
    h = construir(incluir_top_valor=False)
    return set(zip(h["fuente"], h["llave"]))


def seleccionar(config, n=N_TOP):
    procesado = ruta(config, "processed")
    u = pd.read_parquet(procesado / "resultados_secop" / "universo_mercado.parquet")
    etiquetados = con_etiqueta_humana(u, procesado)
    u["con_etiqueta_humana"] = [(f, l) in etiquetados for f, l in zip(u["fuente"], u["llave"])]
    candidatos = u[u["pred_tfidf_modelo"].isin(CLASES_CANDIDATAS) | u["pred_e5_modelo"].isin(CLASES_CANDIDATAS)]
    elegibles = candidatos[~candidatos["con_etiqueta_humana"]].sort_values("valor_constante_2025", ascending=False)
    top = elegibles.head(n).copy()
    top["rango_valor"] = np.arange(1, len(top) + 1)
    return u, candidatos, elegibles, top


def cobertura(u, candidatos, elegibles, top):
    mercado_sin = u.loc[u["pred_tfidf"] == "funerario", "valor_constante_2025"].sum()
    mercado_con = u.loc[u["pred_tfidf"].isin(CLASES_CANDIDATAS), "valor_constante_2025"].sum()
    union = candidatos["valor_constante_2025"].sum()
    t_sin = top.loc[top["pred_tfidf"] == "funerario", "valor_constante_2025"].sum()
    t_con = top.loc[top["pred_tfidf"].isin(CLASES_CANDIDATAS), "valor_constante_2025"].sum()
    return {"candidatos": len(candidatos), "candidatos_ya_etiquetados": int(candidatos["con_etiqueta_humana"].sum()),
            "elegibles": len(elegibles), "valor_top50": top["valor_constante_2025"].sum(),
            "umbral_valor_constante": top["valor_constante_2025"].min(), "umbral_valor_corriente_50": top["valor"].min(),
            "siguiente_valor_constante": elegibles["valor_constante_2025"].iloc[len(top)],
            "mercado_tfidf_sin_mixto": mercado_sin, "top50_en_mercado_sin_mixto": t_sin, "pct_sin_mixto": t_sin / mercado_sin * 100,
            "mercado_tfidf_con_mixto": mercado_con, "top50_en_mercado_con_mixto": t_con, "pct_con_mixto": t_con / mercado_con * 100,
            "union_modelos": union, "pct_union": top["valor_constante_2025"].sum() / union * 100}


def main():
    config = cargar_config()
    if DESTINO.exists() and pd.read_excel(DESTINO, sheet_name="Etiquetado", dtype=str)["etiqueta"].notna().any():
        raise SystemExit("top_valor.xlsx ya tiene etiquetas: no se regenera (cambiaría la selección).")
    u, candidatos, elegibles, top = seleccionar(config)
    c = cobertura(u, candidatos, elegibles, top)
    procesado = ruta(config, "processed")
    texto = pd.concat([
        pd.read_parquet(ruta(config, "interim") / "secop1_senales.parquet", columns=["llave", "descripcion", "codigo"]).assign(fuente="secop1"),
        pd.read_parquet(ruta(config, "interim") / "secop2_senales.parquet", columns=["llave", "descripcion", "codigo"]).assign(fuente="secop2")])
    top = top.merge(texto, on=["fuente", "llave"], how="left", suffixes=("", "_s"))
    mezcla = top.drop(columns=["id_muestra"]).sample(frac=1, random_state=SEMILLA).reset_index(drop=True)
    mezcla.insert(0, "id_muestra", [f"T{i:03d}" for i in range(1, len(mezcla) + 1)])
    mezcla[["id_muestra", "fuente", "llave", "anio", "rango_valor", "valor", "valor_constante_2025", "pred_tfidf_modelo", "pred_e5_modelo",
            "p_tfidf_funerario", "p_e5_funerario"]].to_parquet(procesado / "top_valor_maestra.parquet", index=False)
    datos = mezcla[["id_muestra", "fuente", "anio", "entidad", "objeto", "descripcion", "codigo"]].rename(columns={"entidad": "nombre_entidad"})
    for col in ("objeto", "descripcion"):
        datos[col] = datos[col].map(anonimizar)
    wb = libro(datos, "edward", calibracion=0)
    ws = wb["Instrucciones"]
    ws["A1"] = "Contratos de mayor valor 2020-2025 — revisor: Edward (50 contratos)"
    fila = ws.max_row + 2
    ws.cell(fila, 1, "CRITERIO COMPLETO (D20, D21 y reglas 10 a 13)").font = Font(bold=True)
    for t in D20 + D21 + REGLAS_NUEVAS:
        fila += 1
        ws.cell(fila, 1, t).alignment = Alignment(wrap_text=True, vertical="top")
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    wb.save(DESTINO)
    pd.set_option("display.width", 200)
    print({k: (round(v / 1e9, 3) if "valor" in k or k in ("mercado_tfidf_sin_mixto", "mercado_tfidf_con_mixto", "union_modelos", "top50_en_mercado_sin_mixto", "top50_en_mercado_con_mixto") else (round(v, 2) if isinstance(v, float) else v)) for k, v in c.items()})
    print(mezcla.groupby(["pred_tfidf_modelo", "pred_e5_modelo"]).size().to_dict())
    print("→", DESTINO)



def evaluar(config=None):
    """Precisión y sensibilidad de TF-IDF y e5 en los 50, ponderadas por valor constante y por número de contratos."""
    config = config or cargar_config()
    procesado = ruta(config, "processed")
    m = pd.read_parquet(procesado / "top_valor_maestra.parquet")
    e = pd.read_excel(DESTINO, sheet_name="Etiquetado", dtype=str)[["id_muestra", "etiqueta"]]
    d = m.merge(e, on="id_muestra", validate="one_to_one")
    d["etiqueta"] = d["etiqueta"].str.strip().str.lower()
    filas = []
    for nombre, clases in (("sin mixto", ["funerario"]), ("con mixto", ["funerario", "mixto"])):
        for modelo, col in (("tfidf", "pred_tfidf_modelo"), ("e5", "pred_e5_modelo")):
            pred, hum = d[col].isin(clases), d["etiqueta"].isin(clases)
            v = d["valor_constante_2025"] / 1e9
            vp = v[pred & hum].sum()
            filas.append({"definicion": nombre, "modelo": modelo, "predichos": int(pred.sum()), "humanos": int(hum.sum()),
                          "aciertos": int((pred & hum).sum()), "precision_por_contratos": (pred & hum).sum() / pred.sum(),
                          "sensibilidad_por_contratos": (pred & hum).sum() / hum.sum(), "valor_predicho": v[pred].sum(),
                          "valor_humano": v[hum].sum(), "valor_acertado": vp, "precision_por_valor": vp / v[pred].sum(),
                          "sensibilidad_por_valor": vp / v[hum].sum(),
                          "valor_clase_exacta": v[d[col] == d["etiqueta"]].sum(), "clase_exacta_contratos": int((d[col] == d["etiqueta"]).sum())})
    t = pd.DataFrame(filas)
    t.to_csv(procesado / "resultados_secop" / "top_valor_evaluacion.csv", index=False, encoding="utf-8-sig")
    resumen = d.groupby("etiqueta").agg(contratos=("valor", "size"), valor_constante=("valor_constante_2025", lambda s: s.sum() / 1e9)).reset_index()
    resumen.to_csv(procesado / "resultados_secop" / "top_valor_etiquetas.csv", index=False, encoding="utf-8-sig")
    return t, resumen


if __name__ == "__main__":
    main()
