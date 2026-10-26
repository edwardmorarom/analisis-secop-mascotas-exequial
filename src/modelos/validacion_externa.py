import numpy as np
import pandas as pd
from openpyxl.styles import Alignment, Font

from src.etl.anonimizar import anonimizar
from src.etl.comun import RAIZ, cargar_config, ruta
from src.evaluacion.plantillas_etiquetado import libro
from src.evaluacion.reglas_etiquetado import D20, D21
from src.modelos.muestra_secop import ASIGNACION, reparto, subestrato

N_VALIDACION = 60
SEMILLA = 2027
REGLAS_NUEVAS = [
    "Póliza de vida grupo con auxilio funerario → no_funerario (es una indemnización).",
    "Custodia y conservación de cuerpos NN o no reclamados → funerario; la custodia del cementerio como lugar es no_funerario.",
    "Infraestructura de salas de necropsia o de Medicina Legal → forense 1; una morgue sin necropsia → forense 0.",
    "Todo trabajo de búsqueda, identificación o información sobre personas desaparecidas, fosas o SIRDEC → forense 1.",
]


def seleccionar(config):
    interim, procesado = ruta(config, "interim"), ruta(config, "processed")
    a = pd.concat([pd.read_parquet(interim / f"{n}_senales.parquet") for n in ("secop1", "secop2")], ignore_index=True)
    a["subestrato"] = a.apply(subestrato, axis=1)
    en_muestra = pd.read_parquet(procesado / "muestra_secop_maestra.parquet")[["fuente", "llave"]].assign(en400=True)
    a = a.merge(en_muestra, on=["fuente", "llave"], how="left")
    a["en400"] = a["en400"].fillna(False).astype(bool)
    resto = a[~a["en400"]]
    disponibles = resto["subestrato"].value_counts()
    base = pd.Series({k: v for k, v in ASIGNACION.items() if disponibles.get(k, 0) > 0}, dtype=float)
    cuotas = reparto(base, N_VALIDACION)
    rng = np.random.default_rng(SEMILLA)
    partes = []
    for nombre, n in cuotas.items():
        est = resto[resto["subestrato"] == nombre]
        n = min(n, len(est))
        if n:
            partes.append(est.sample(n=n, random_state=int(rng.integers(2**31))).assign(n_estrato=n, N_estrato=len(est)))
    m = pd.concat(partes)
    m["peso"] = m["N_estrato"] / m["n_estrato"]
    m = m.sample(frac=1, random_state=SEMILLA).reset_index(drop=True)
    m.insert(0, "id_muestra", [f"V{i:03d}" for i in range(1, len(m) + 1)])
    assert len(m) == N_VALIDACION and not m.duplicated(["fuente", "llave"]).any() and not m["en400"].any()
    assert abs(m["peso"].sum() - len(resto)) < 1e-6
    return m, len(a), len(resto)


def main():
    config = cargar_config()
    m, total, resto = seleccionar(config)
    procesado = ruta(config, "processed")
    m[["id_muestra", "fuente", "llave", "anio", "subestrato", "N_estrato", "n_estrato", "peso"]].to_parquet(
        procesado / "validacion_externa_maestra.parquet", index=False)
    texto = m[["id_muestra", "fuente", "anio", "nombre_entidad", "objeto", "descripcion", "codigo"]].copy()
    for col in ("objeto", "descripcion"):
        texto[col] = texto[col].map(anonimizar)
    wb = libro(texto, "edward", calibracion=0)
    ws = wb["Instrucciones"]
    ws["A1"] = "Validación externa SECOP — revisor: Edward (60 contratos fuera de los 400)"
    fila = ws.max_row + 2
    ws.cell(fila, 1, "CRITERIO COMPLETO (D20, D21 y reglas 10 a 13)").font = Font(bold=True)
    for t in D20 + D21 + REGLAS_NUEVAS:
        fila += 1
        c = ws.cell(fila, 1, t)
        c.alignment = Alignment(wrap_text=True, vertical="top")
    destino = RAIZ / "docs" / "etiquetado" / "validacion_edward.xlsx"
    wb.save(destino)
    print(f"{N_VALIDACION} contratos de {resto:,} disponibles (universo {total:,}); estratos:")
    print(m.groupby("subestrato").agg(n=("peso", "size"), N_disponible=("N_estrato", "first"), peso=("peso", "first")).round(1).to_string())
    print(m.groupby("fuente").size().to_dict(), "→", destino)


if __name__ == "__main__":
    main()
