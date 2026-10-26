import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

from src.etl.comun import cargar_config, ruta

CLASES = ["funerario", "mixto", "no_funerario"]
SENALES_NUCLEO = ["funera", "exequ", "inhuma", "cremaci", "sepelio", "sepult",
                  "unspsc_851715", "unspsc_4813", "unspsc_422621"]
MIN_POR_CELDA = 5


def texto_contrato(objeto, descripcion, codigo):
    objeto, descripcion = (objeto or "").strip(), (descripcion or "").strip()
    texto = objeto if descripcion in ("", objeto) else f"{objeto} | {descripcion}"
    return f"{texto} | UNSPSC {codigo}" if codigo else texto


def cargar(config=None):
    config = config or cargar_config()
    procesado, interim = ruta(config, "processed"), ruta(config, "interim")
    etiquetas = pd.read_parquet(procesado / "etiquetas_finales.parquet")
    maestra = pd.read_parquet(procesado / "muestra_secop_maestra.parquet").drop(columns=["subestrato", "peso", "anio"])
    textos = pd.concat([
        pd.read_parquet(interim / f"{f}_senales.parquet", columns=["llave", "objeto", "descripcion", "codigo"]).assign(fuente=f)
        for f in ("secop1", "secop2")])
    d = etiquetas.merge(maestra, on="id_muestra", validate="one_to_one").merge(
        textos, on=["fuente", "llave"], how="left", validate="one_to_one")
    d["texto"] = [texto_contrato(o, s, c) for o, s, c in zip(d["objeto"], d["descripcion"], d["codigo"])]
    return d.sort_values("n").reset_index(drop=True)


def asignar_pliegues(d, n_pliegues=5, semilla=2026):
    clave = d["subestrato"] + "|" + d["etiqueta"]
    clave = clave.where(clave.map(clave.value_counts()) >= MIN_POR_CELDA, "otras")
    pliegue = np.zeros(len(d), dtype=int)
    for k, (_, prueba) in enumerate(StratifiedKFold(n_pliegues, shuffle=True, random_state=semilla).split(d, clave)):
        pliegue[prueba] = k
    return pliegue
