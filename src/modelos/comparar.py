import warnings

warnings.filterwarnings("ignore", category=FutureWarning, module="sklearn")
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegressionCV
from sklearn.model_selection import StratifiedKFold

from src.etl.comun import cargar_config, ruta
from src.evaluacion.metricas_ponderadas import fila_resumen
from src.modelos.datos_clasificacion import CLASES, asignar_pliegues, cargar

GRILLA_C = np.logspace(-1, 3, 9)


def regresion_logistica(class_weight=None, semilla=2026):
    return LogisticRegressionCV(Cs=GRILLA_C, cv=StratifiedKFold(3, shuffle=True, random_state=semilla),
                                scoring="f1_macro", max_iter=5000, class_weight=class_weight)


def validar(d, pliegue, ajustar_predecir):
    """`ajustar_predecir(entrenamiento, prueba)` devuelve una matriz de probabilidades con columnas en CLASES."""
    prob = np.zeros((len(d), len(CLASES)))
    for k in range(pliegue.max() + 1):
        prueba = pliegue == k
        prob[prueba] = ajustar_predecir(d[~prueba], d[prueba])
    return prob


def guardar(nombre, d, prob):
    salida = pd.DataFrame(prob, columns=[f"p_{c}" for c in CLASES]).assign(id_muestra=d["id_muestra"].values)
    salida["pred"] = [CLASES[i] for i in prob.argmax(axis=1)]
    salida.to_parquet(ruta(cargar_config(), "processed") / f"predicciones_cv_{nombre}.parquet", index=False)
    return salida["pred"].values


def resumen(nombre, d, pred):
    return fila_resumen(nombre, d["etiqueta"], pred, d["peso"], d["subestrato"])


def mixto_aparte(d, pred):
    m = d["etiqueta"] == "mixto"
    return {"mixto_total": int(m.sum()), "mixto_predicho_mixto": int((pred[m] == "mixto").sum()),
            "mixto_predicho_funerario": int((pred[m] == "funerario").sum())}
