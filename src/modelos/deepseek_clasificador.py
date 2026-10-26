import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

from src.etl.comun import RAIZ, cargar_config
from src.evaluacion.reglas_etiquetado import D20, D21
from src.modelos.datos_clasificacion import cargar, texto_contrato

N_EJEMPLOS = 8
MAX_CARACTERES_EJEMPLO = 260
CARACTERES_POR_TOKEN = (3.0, 3.5, 4.0)
TOKENS_SALIDA = 20
PRECIOS_USD_POR_MILLON = {"entrada_sin_cache": 0.30, "entrada_con_cache": 0.006, "salida": 1.20}
REGLAS_NUEVAS = [
    "Póliza de vida grupo con auxilio funerario → no_funerario (es una indemnización).",
    "Custodia y conservación de cuerpos NN o no reclamados → funerario; la custodia del cementerio como lugar es no_funerario.",
    "Infraestructura de salas de necropsia o de Medicina Legal → forense 1; una morgue sin necropsia → forense 0.",
    "Todo trabajo de búsqueda, identificación o información sobre personas desaparecidas, fosas o SIRDEC → forense 1.",
]
INSTRUCCION = (
    "Clasificas objetos de contratos públicos colombianos en tres clases: funerario, no_funerario o mixto, y marcas "
    "aparte forense (0 o 1). Responde solo un JSON con las claves \"etiqueta\" y \"forense\".\n\nCriterio:\n"
    + "\n".join(f"- {r}" for r in D20 + D21 + REGLAS_NUEVAS))


def elegir_ejemplos(d, semilla=2026):
    """Dos o tres casos cortos y claros por clase, más uno forense; se excluyen de la evaluación."""
    corto = d[d["texto"].str.len() <= MAX_CARACTERES_EJEMPLO]
    rng = np.random.default_rng(semilla)
    cupos = [("funerario", 0, 3), ("no_funerario", 0, 2), ("mixto", 0, 2), ("no_funerario", 1, 1)]
    ids = []
    for clase, forense, n in cupos:
        candidatos = corto[(corto["etiqueta"] == clase) & (corto["forense"] == forense) & ~corto["id_muestra"].isin(ids)]
        ids += list(rng.choice(candidatos["id_muestra"].values, min(n, len(candidatos)), replace=False))
    return d[d["id_muestra"].isin(ids)].sort_values("n")


def mensajes(ejemplos, texto):
    m = [{"role": "system", "content": INSTRUCCION}]
    for e in ejemplos.itertuples():
        m.append({"role": "user", "content": e.texto})
        m.append({"role": "assistant", "content": json.dumps({"etiqueta": e.etiqueta, "forense": int(e.forense)})})
    m.append({"role": "user", "content": texto})
    return m


def estimar(n_llamadas, caracteres_prefijo, caracteres_texto_total):
    """Costo en USD: el prefijo (instrucción y ejemplos) se factura sin caché una vez y con caché las demás."""
    p = PRECIOS_USD_POR_MILLON
    filas = []
    for cpt in CARACTERES_POR_TOKEN:
        prefijo, texto = caracteres_prefijo / cpt, caracteres_texto_total / cpt
        salida = n_llamadas * TOKENS_SALIDA * p["salida"] / 1e6
        con_cache = (prefijo + texto) * p["entrada_sin_cache"] / 1e6 + prefijo * (n_llamadas - 1) * p["entrada_con_cache"] / 1e6 + salida
        sin_cache = (prefijo * n_llamadas + texto) * p["entrada_sin_cache"] / 1e6 + salida
        filas.append({"caracteres_por_token": cpt, "tokens_prefijo": round(prefijo),
                      "tokens_entrada_totales": round(prefijo * n_llamadas + texto),
                      "costo_usd_con_cache": round(con_cache, 2), "costo_usd_sin_cache": round(sin_cache, 2)})
    return pd.DataFrame(filas)
