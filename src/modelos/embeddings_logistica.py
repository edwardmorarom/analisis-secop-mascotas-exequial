import numpy as np
import pandas as pd

from src.etl.comun import cargar_config, ruta
from src.modelos.comparar import guardar, mixto_aparte, regresion_logistica, resumen, validar
from src.modelos.datos_clasificacion import CLASES, asignar_pliegues, cargar

MODELO = "intfloat/multilingual-e5-base"
MAX_TOKENS = 256


def incrustar(textos, lote=32):
    from sentence_transformers import SentenceTransformer
    modelo = SentenceTransformer(MODELO)
    modelo.max_seq_length = MAX_TOKENS
    return modelo.encode([f"query: {t}" for t in textos], batch_size=lote, normalize_embeddings=True,
                         show_progress_bar=False)


def ajustar_predecir(x):
    def f(entrenamiento, prueba):
        modelo = regresion_logistica().fit(x[entrenamiento.index], entrenamiento["etiqueta"])
        prob = modelo.predict_proba(x[prueba.index])
        return prob[:, [list(modelo.classes_).index(c) for c in CLASES]]
    return f


def main():
    d = cargar()
    destino = ruta(cargar_config(), "processed") / "embeddings_e5_muestra.npy"
    if destino.exists():
        x = np.load(destino)
    else:
        x = incrustar(d["texto"].tolist())
        np.save(destino, x)
    pred = guardar("e5_logistica", d, validar(d, asignar_pliegues(d), ajustar_predecir(x)))
    pd.set_option("display.width", 200)
    print(pd.DataFrame([{**resumen("e5_logistica", d, pred), **mixto_aparte(d, pred)}]).round(3).T)


if __name__ == "__main__":
    main()
