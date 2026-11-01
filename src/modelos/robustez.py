import os

os.environ["OMP_NUM_THREADS"] = "1"

import warnings

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.svm import LinearSVC
from xgboost import XGBClassifier

from src.etl.comun import cargar_config, ruta
from src.evaluacion.metricas_ponderadas import fila_resumen
from src.modelos.comparar import guardar
from src.modelos.datos_clasificacion import CLASES, SENALES_NUCLEO, asignar_pliegues, cargar
from src.modelos.deepseek_clasificador import elegir_ejemplos
from src.modelos.evaluar_validacion import cargar_validacion
from src.modelos.tfidf_logistica import vectorizador

warnings.filterwarnings("ignore")
SEMILLA = 2026
NOMBRES = {"reglas": "Reglas", "tfidf_logistica": "TF-IDF + regresión logística", "e5_logistica": "e5 + regresión logística",
           "deepseek_flash": "DeepSeek flash (8 ejemplos)", "svm_lineal": "SVM lineal (TF-IDF)", "xgboost": "XGBoost (TF-IDF)"}


def svm():
    cuadricula = GridSearchCV(LinearSVC(max_iter=20000), {"C": np.logspace(-1, 2, 7)}, scoring="f1_macro",
                              cv=StratifiedKFold(3, shuffle=True, random_state=SEMILLA))
    return cuadricula


def xgb():
    return XGBClassifier(objective="multi:softprob", n_estimators=300, max_depth=4, learning_rate=0.1, subsample=0.8,
                         colsample_bytree=0.5, random_state=SEMILLA, n_jobs=1, eval_metric="mlogloss", verbosity=0)


def puntajes(nombre, modelo, x_entrenamiento, y, x_prueba):
    y = np.array([str(c) for c in y])
    codigos = np.array([CLASES.index(c) for c in y])
    modelo.fit(x_entrenamiento, y if nombre == "svm_lineal" else codigos)
    if nombre == "svm_lineal":
        s = modelo.decision_function(x_prueba)
        orden = [list(modelo.classes_).index(c) for c in CLASES]
        s = s[:, orden]
        e = np.exp(s - s.max(axis=1, keepdims=True))
        return e / e.sum(axis=1, keepdims=True)
    return modelo.predict_proba(x_prueba)


def validar_cruzada(nombre, fabrica, d, pliegue):
    prob = np.zeros((len(d), len(CLASES)))
    for k in range(pliegue.max() + 1):
        prueba = pliegue == k
        v = vectorizador()
        x_e = v.fit_transform(d.loc[~prueba, "texto"])
        prob[prueba] = puntajes(nombre, fabrica(), x_e, d.loc[~prueba, "etiqueta"].values, v.transform(d.loc[prueba, "texto"]))
    return prob


def predecir_validacion(nombre, fabrica, d, val):
    v = vectorizador()
    x = v.fit_transform(d["texto"])
    prob = puntajes(nombre, fabrica(), x, d["etiqueta"].values, v.transform(val["texto"]))
    return [CLASES[i] for i in prob.argmax(axis=1)]


def resumen(nombre, y, p, w, e, escala):
    f = fila_resumen(nombre, y, p, w, e)
    f.pop("modelo")
    return {"modelo": NOMBRES[nombre], **{f"{escala}_{k}": v for k, v in f.items()}}


def main():
    config = cargar_config()
    procesado = ruta(config, "processed")
    d = cargar(config)
    pliegue = asignar_pliegues(d)
    ejemplos = elegir_ejemplos(d)["id_muestra"]
    comun = ~d["id_muestra"].isin(ejemplos)
    val = cargar_validacion(config)
    guardadas = pd.read_parquet(procesado / "predicciones_validacion_60.parquet")
    interim = ruta(config, "interim")
    senales = pd.concat([pd.read_parquet(interim / f"{f}_senales.parquet", columns=["llave", *SENALES_NUCLEO]).assign(fuente=f)
                         for f in ("secop1", "secop2")])
    reglas_val = val.merge(senales, on=["fuente", "llave"])[SENALES_NUCLEO].any(axis=1).map({True: "funerario", False: "no_funerario"}).values
    cv, ext = {}, {}
    cv["reglas"] = pd.read_parquet(procesado / "predicciones_reglas.parquet")["pred_reglas"].values
    ext["reglas"] = reglas_val
    for nombre, archivo in (("tfidf_logistica", "tfidf_logistica"), ("e5_logistica", "e5_logistica")):
        cv[nombre] = pd.read_parquet(procesado / f"predicciones_cv_{archivo}.parquet")["pred"].values
        ext[nombre] = guardadas["pred_" + nombre].values
    cv_ds = pd.read_parquet(procesado / "predicciones_deepseek.parquet").set_index("id_muestra")["pred"]
    cv["deepseek_flash"] = d["id_muestra"].map(cv_ds).values
    ext["deepseek_flash"] = guardadas["pred_deepseek_flash"].values
    for nombre, fabrica in (("svm_lineal", svm), ("xgboost", xgb)):
        prob = validar_cruzada(nombre, fabrica, d, pliegue)
        cv[nombre] = guardar(f"{nombre}", d, prob)
        ext[nombre] = predecir_validacion(nombre, fabrica, d, val)
    assert (guardadas["id_muestra"].values == val["id_muestra"].values).all()
    filas = []
    for nombre in NOMBRES:
        p_cv = pd.Series(cv[nombre], index=d.index)
        ok = comun & p_cv.notna()
        fila = {**resumen(nombre, d.loc[ok, "etiqueta"], p_cv[ok], d.loc[ok, "peso"], d.loc[ok, "subestrato"], "cv392")}
        fila.update({k: v for k, v in resumen(nombre, val["etiqueta"], ext[nombre], val["peso"], val["subestrato"], "val60_pond").items() if k != "modelo"})
        fila.update({k: v for k, v in resumen(nombre, val["etiqueta"], ext[nombre], np.ones(len(val)), val["subestrato"], "val60_sin").items() if k != "modelo"})
        filas.append(fila)
    t = pd.DataFrame(filas)
    t.to_csv(procesado / "tabla_robustez.csv", index=False, encoding="utf-8-sig")
    pd.set_option("display.width", 250)
    cols = ["modelo", "cv392_precision", "cv392_sensibilidad", "cv392_f1", "cv392_f1_ic_bajo", "cv392_f1_ic_alto",
            "val60_pond_f1", "val60_pond_f1_ic_bajo", "val60_pond_f1_ic_alto", "val60_sin_f1", "val60_sin_f1_ic_bajo", "val60_sin_f1_ic_alto"]
    print(t[cols].round(3).to_string(index=False))
    print(t[["modelo", "val60_pond_precision", "val60_pond_sensibilidad", "val60_sin_precision", "val60_sin_sensibilidad"]].round(3).to_string(index=False))
    for nombre in ("svm_lineal", "xgboost"):
        print(nombre, pd.crosstab(val["etiqueta"], pd.Series(ext[nombre], name="m")).reindex(index=CLASES, columns=CLASES, fill_value=0).values.tolist())


if __name__ == "__main__":
    main()
