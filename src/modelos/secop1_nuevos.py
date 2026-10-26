import numpy as np
import pandas as pd
from openpyxl.styles import Alignment, Font

from src.etl.anonimizar import anonimizar
from src.etl.comun import RAIZ, cargar_config, ruta
from src.evaluacion.plantillas_etiquetado import libro
from src.evaluacion.reglas_etiquetado import D20, D21
from src.modelos.validacion_externa import REGLAS_NUEVAS

N_POR_GRUPO = 15
SEMILLA = 2026
DESTINO = RAIZ / "docs" / "revision_f4" / "secop1_nuevos.xlsx"


def seleccionar(config):
    procesado, interim = ruta(config, "processed"), ruta(config, "interim")
    c = pd.read_parquet(procesado / "clasificacion_universo.parquet")
    c = c[(c["fuente"] == "secop1") & (c["anio"] >= 2023)].drop(columns=["id_muestra", "etiqueta_humana", "forense_humano"])
    rng = np.random.default_rng(SEMILLA)
    partes = []
    for clase, funerario in (("funerario", True), ("otras", False)):
        g = c[(c["pred_tfidf"] == "funerario") == funerario]
        partes.append(g.sample(n=N_POR_GRUPO, random_state=int(rng.integers(2**31))).assign(
            grupo_pred=clase, N_grupo=len(g), peso=len(g) / N_POR_GRUPO))
    m = pd.concat(partes).sample(frac=1, random_state=SEMILLA).reset_index(drop=True)
    m.insert(0, "id_muestra", [f"S{i:03d}" for i in range(1, len(m) + 1)])
    textos = pd.read_parquet(interim / "secop1_senales.parquet", columns=["llave", "nombre_entidad", "objeto", "descripcion", "codigo"])
    m = m.merge(textos, on="llave", validate="one_to_one")
    m = m.assign(fuente="secop1").sort_values("id_muestra").reset_index(drop=True)
    return m


def main():
    config = cargar_config()
    m = seleccionar(config)
    procesado = ruta(config, "processed")
    m[["id_muestra", "fuente", "llave", "anio", "grupo_pred", "N_grupo", "peso", "pred_tfidf", "pred_e5"]].to_parquet(
        procesado / "secop1_nuevos_maestra.parquet", index=False)
    texto = m[["id_muestra", "fuente", "anio", "nombre_entidad", "objeto", "descripcion", "codigo"]].copy()
    for col in ("objeto", "descripcion"):
        texto[col] = texto[col].map(anonimizar)
    wb = libro(texto, "edward", calibracion=0)
    ws = wb["Instrucciones"]
    ws["A1"] = "Contratos nuevos de SECOP I 2023-2025 — revisor: Edward (30 contratos)"
    fila = ws.max_row + 2
    ws.cell(fila, 1, "CRITERIO COMPLETO (D20, D21 y reglas 10 a 13)").font = Font(bold=True)
    for t in D20 + D21 + REGLAS_NUEVAS:
        fila += 1
        ws.cell(fila, 1, t).alignment = Alignment(wrap_text=True, vertical="top")
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    wb.save(DESTINO)
    print(len(m), "contratos;", m.groupby("anio").size().to_dict(), "→", DESTINO)


if __name__ == "__main__":
    main()
