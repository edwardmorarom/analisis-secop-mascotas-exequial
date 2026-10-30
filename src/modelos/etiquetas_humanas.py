import pandas as pd

from src.etl.comun import RAIZ, cargar_config, ruta
from src.modelos.datos_clasificacion import CLASES

ORDEN_PRECEDENCIA = ["top_valor", "adicionales_d81", "secop1_nuevos", "humanitarios_40", "estrato_d_150", "validacion_60_revisada", "muestra_400"]
RUTA_LOTES = {"humanitarios_40": ("humanitarios_40.xlsx", "humanitarios_40_maestra.parquet"),
              "estrato_d_150": ("estrato_d_150.xlsx", "estrato_d_150_maestra.parquet")}
# D92: servicios profesionales o de apoyo a la gestión que apoyan asistencia funeraria son no_funerario (el Excel de Edward los trae como mixto).
CORRECCION_D92 = {"humanitarios_40": {"H005", "H009", "H028", "H030", "H031"}}
# D92: V046 (SSF-013, personal de la Subdirección de Servicios Funerarios) pasa de funerario a no_funerario por decisión de Edward.
CORRECCION_D92_VALIDACION = {"V046": "no_funerario"}


def muestra_400(procesado):
    e = pd.read_parquet(procesado / "etiquetas_finales.parquet")[["id_muestra", "etiqueta", "forense"]]
    m = pd.read_parquet(procesado / "muestra_secop_maestra.parquet")[["id_muestra", "fuente", "llave"]]
    return e.merge(m, on="id_muestra").assign(origen="muestra_400")


def validacion_60(procesado):
    from src.modelos.evaluar_validacion import LIBRO
    from src.modelos.revision_etiquetas import DESTINO
    e = pd.read_excel(LIBRO, sheet_name="Etiquetado", dtype=str)[["id_muestra", "etiqueta", "forense"]]
    r = pd.read_excel(DESTINO, sheet_name="Revision", dtype=str)
    r = r[r["etiqueta_revisada"].notna()].set_index("id_muestra")
    e = e.set_index("id_muestra")
    e.loc[r.index, "etiqueta"] = r["etiqueta_revisada"]
    e.loc[r.index, "forense"] = r["forense_revisado"].fillna(e.loc[r.index, "forense"])
    for i, etiqueta in CORRECCION_D92_VALIDACION.items():
        e.loc[i, "etiqueta"] = etiqueta
    m =pd.read_parquet(procesado / "validacion_externa_maestra.parquet")[["id_muestra", "fuente", "llave"]]
    return e.reset_index().merge(m, on="id_muestra").assign(origen="validacion_60_revisada")


def desde_excel(procesado, libro, maestra, origen):
    if not libro.exists():
        return None
    e = pd.read_excel(libro, sheet_name="Etiquetado", dtype=str)[["id_muestra", "etiqueta", "forense"]]
    if e["etiqueta"].isna().any():
        return None
    m = pd.read_parquet(procesado / maestra)[["id_muestra", "fuente", "llave"]]
    return e.merge(m, on="id_muestra").assign(origen=origen)


def lote(procesado, nombre):
    libro, maestra = RUTA_LOTES[nombre]
    e = desde_excel(procesado, RAIZ / "docs" / "revision_f4" / libro, maestra, nombre)
    if e is not None and nombre in CORRECCION_D92:
        e["etiqueta_excel"] = e["etiqueta"]
        e.loc[e["id_muestra"].isin(CORRECCION_D92[nombre]), "etiqueta"] = "no_funerario"
    return e


def adicionales(procesado):
    archivo = procesado / "etiquetas_humanas_adicionales.csv"
    if not archivo.exists():
        return None
    h = pd.read_csv(archivo, dtype=str)
    return h.assign(id_muestra=None, origen="adicionales_d81")[["id_muestra", "etiqueta", "forense", "fuente", "llave", "origen"]]


def construir(config=None, incluir_top_valor=True):
    """Tabla de etiquetas humanas por (fuente, llave); si un contrato está en varias fuentes manda la de mayor precedencia."""
    from src.modelos.secop1_nuevos import DESTINO as SECOP1
    from src.modelos.top_valor import DESTINO as TOP
    config = config or cargar_config()
    procesado = ruta(config, "processed")
    partes = [muestra_400(procesado), validacion_60(procesado), desde_excel(procesado, SECOP1, "secop1_nuevos_maestra.parquet", "secop1_nuevos"),
              adicionales(procesado), lote(procesado, "humanitarios_40"), lote(procesado, "estrato_d_150")]
    if incluir_top_valor:
        partes.append(desde_excel(procesado, TOP, "top_valor_maestra.parquet", "top_valor"))
    todo = pd.concat([p for p in partes if p is not None], ignore_index=True)
    todo["etiqueta"] = todo["etiqueta"].str.strip().str.lower()
    assert todo["etiqueta"].isin(CLASES).all(), "etiqueta humana inválida"
    todo["prioridad"] = todo["origen"].map({o: i for i, o in enumerate(ORDEN_PRECEDENCIA)})
    todo = todo.sort_values("prioridad")
    conflictos = todo[todo.duplicated(["fuente", "llave"], keep=False)].groupby(["fuente", "llave"])["etiqueta"].nunique()
    todo = todo.drop_duplicates(["fuente", "llave"], keep="first").drop(columns="prioridad").reset_index(drop=True)
    todo.attrs["conflictos"] = int((conflictos > 1).sum())
    return todo
