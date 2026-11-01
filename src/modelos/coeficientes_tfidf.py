import numpy as np
import pandas as pd

from src.etl.anonimizar import anonimizar
from src.etl.comun import RAIZ, cargar_config
from src.modelos.clasificar_todos import universo
from src.modelos.comparar import regresion_logistica
from src.modelos.datos_clasificacion import CLASES
from src.modelos.etiquetas_humanas import construir
from src.modelos.tfidf_logistica import vectorizador

DESTINO = RAIZ / "docs" / "resultados" / "coeficientes_tfidf.md"


def tabla(df, cols):
    return "\n".join(["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)] +
                     ["| " + " | ".join(str(r[c]) for c in cols) + " |" for _, r in df.iterrows()])


def coma(v, d=3):
    return f"{v:.{d}f}".replace(".", ",")


def main():
    config = cargar_config()
    u = universo(config)
    h = construir(config)
    entrenamiento = h[["fuente", "llave", "etiqueta"]].merge(u[["fuente", "llave", "texto"]], on=["fuente", "llave"], validate="one_to_one")
    v = vectorizador()
    x = v.fit_transform(entrenamiento["texto"])
    modelo = regresion_logistica().fit(x, entrenamiento["etiqueta"])
    i = list(modelo.classes_).index("funerario")
    nombres = np.array(v.get_feature_names_out())
    coef = modelo.coef_[i]
    orden = np.argsort(coef)
    favor = pd.DataFrame({"término": nombres[orden[::-1][:20]], "coeficiente": [coma(c) for c in coef[orden[::-1][:20]]]})
    contra = pd.DataFrame({"término": nombres[orden[:20]], "coeficiente": [coma(c) for c in coef[orden[:20]]]})
    resto = u.merge(h[["fuente", "llave"]], on=["fuente", "llave"], how="left", indicator=True)
    resto = resto[resto["_merge"] == "left_only"].drop(columns="_merge").reset_index(drop=True)
    xr = v.transform(resto["texto"])
    p = modelo.predict_proba(xr)[:, i]
    resto["p"] = p
    elegidos = [("probabilidad alta de funerario", resto.index[np.argsort(np.abs(p - 0.97))[0]]),
                ("probabilidad baja", resto.index[np.argsort(np.abs(p - 0.03))[0]]),
                ("caso intermedio", resto.index[np.argsort(np.abs(p - 0.5))[0]])]
    L = ["# Coeficientes del modelo TF-IDF (auditabilidad)", "",
         "Solo reporte. Generado por `python -m src.modelos.coeficientes_tfidf`. Modelo: TF-IDF (unigramas y bigramas, `min_df` 2, tf sublineal) con regresión logística multinomial (D56), ajustado con **todas las etiquetas humanas vigentes** "
         f"({len(entrenamiento)} contratos: {', '.join(f'{k} {n}' for k, n in entrenamiento['etiqueta'].value_counts().items())}); C elegido por validación cruzada de 3 pliegues: {coma(float(modelo.C_[i]), 2)}. "
         f"Vocabulario: {len(nombres):} términos. Los coeficientes son los de la clase `funerario` frente a las otras dos clases; un coeficiente positivo sube la probabilidad de `funerario`. Los textos incluyen el código UNSPSC como palabra (`UNSPSC`).", "",
         "## 20 términos con mayor coeficiente a favor de `funerario`", "", tabla(favor, ["término", "coeficiente"]), "",
         "## 20 términos con mayor coeficiente en contra", "", tabla(contra, ["término", "coeficiente"]), "",
         "## Tres contratos de ejemplo", "",
         "Contratos sin etiqueta humana (el modelo no los vio al ajustarse). Se eligen los más cercanos a probabilidad 0,97, 0,03 y 0,50. La contribución de un término es su valor TF-IDF por su coeficiente; se listan las cinco mayores a favor y las cinco mayores en contra. Objeto anonimizado y recortado a 300 caracteres.", ""]
    for titulo, k in elegidos:
        fila = xr[k]
        contribucion = fila.multiply(coef).toarray().ravel()
        top = np.argsort(contribucion)
        pos = [f"{nombres[j]} ({coma(contribucion[j])})" for j in top[::-1][:5] if contribucion[j] > 0]
        neg = [f"{nombres[j]} ({coma(contribucion[j])})" for j in top[:5] if contribucion[j] < 0]
        r = resto.loc[k]
        L += [f"### {titulo}: probabilidad de `funerario` {coma(r['p'])}", "",
              f"- Fuente y año: {r['fuente']}, {int(r['anio'])}.", f"- Texto: {' '.join(anonimizar(r['texto']).split())[:300]}",
              f"- Términos que más aportaron a favor: {', '.join(pos) or 'ninguno'}.", f"- Términos que más aportaron en contra: {', '.join(neg) or 'ninguno'}.", ""]
    DESTINO.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:12])[:1500])


if __name__ == "__main__":
    main()
