import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from src.modelos.comparar import guardar, mixto_aparte, regresion_logistica, resumen, validar
from src.modelos.datos_clasificacion import CLASES, asignar_pliegues, cargar


def vectorizador():
    return TfidfVectorizer(strip_accents="unicode", lowercase=True, ngram_range=(1, 2), sublinear_tf=True, min_df=2)


def ajustar_predecir_con(class_weight):
    def f(entrenamiento, prueba):
        v = vectorizador()
        x = v.fit_transform(entrenamiento["texto"])
        modelo = regresion_logistica(class_weight).fit(x, entrenamiento["etiqueta"])
        prob = modelo.predict_proba(v.transform(prueba["texto"]))
        return prob[:, [list(modelo.classes_).index(c) for c in CLASES]]
    return f


def palabras_decisivas(d, class_weight, k=12):
    v = vectorizador()
    x = v.fit_transform(d["texto"])
    modelo = regresion_logistica(class_weight).fit(x, d["etiqueta"])
    nombres = np.array(v.get_feature_names_out())
    fila = list(modelo.classes_).index("funerario")
    orden = np.argsort(modelo.coef_[fila])
    return nombres[orden[-k:]][::-1], nombres[orden[:k]], float(modelo.C_[fila])


def main():
    d = cargar()
    pliegue = asignar_pliegues(d)
    pd.set_option("display.width", 220)
    filas = []
    for nombre, cw in (("tfidf_logistica", None), ("tfidf_logistica_balanceada", "balanced")):
        prob = validar(d, pliegue, ajustar_predecir_con(cw))
        pred = guardar(nombre, d, prob)
        filas.append({**resumen(nombre, d, pred), **mixto_aparte(d, pred)})
    print(pd.DataFrame(filas).round(3).T)
    arriba, abajo, c = palabras_decisivas(d, None)
    print("C elegido (ajuste completo):", c)
    print("hacia funerario:", ", ".join(arriba))
    print("hacia no funerario:", ", ".join(abajo))


if __name__ == "__main__":
    main()
