import numpy as np
import pandas as pd

from src.etl.comun import cargar_config, ruta
from src.evaluacion.metricas_ponderadas import fila_resumen
from src.modelos.datos_clasificacion import CLASES, cargar
from src.modelos.evaluar_validacion import cargar_validacion
from src.modelos.reevaluar_validacion import etiquetas_d92, etiquetas_revisadas
from src.modelos.robustez import NOMBRES, predecir_validacion, svm, xgb


def main():
    config = cargar_config()
    procesado = ruta(config, "processed")
    d = cargar(config)
    val = cargar_validacion(config)
    revisada, cambios = etiquetas_revisadas(val)
    guardadas = pd.read_parquet(procesado / "predicciones_validacion_60.parquet")
    pred = {"tfidf_logistica": guardadas["pred_tfidf_logistica"].values}
    for nombre, fabrica in (("svm_lineal", svm), ("xgboost", xgb)):
        pred[nombre] = predecir_validacion(nombre, fabrica, d, val)
    filas = []
    for version, x in (("original", val), ("revisada", revisada), ("revisada_d92", etiquetas_d92(revisada))):
        for nombre, p in pred.items():
            for escala, peso in (("ponderado", x["peso"].values), ("sin ponderar", np.ones(len(x)))):
                f = fila_resumen(nombre, x["etiqueta"], p, peso, x["subestrato"])
                filas.append({"version": version, "modelo": NOMBRES[nombre], "escala": escala, **{k: v for k, v in f.items() if k != "modelo"}})
    t = pd.DataFrame(filas)
    t.to_csv(procesado / "tabla_robustez_validacion_revisada.csv", index=False, encoding="utf-8-sig")
    pd.set_option("display.width", 250)
    print("etiquetas que cambian:", int((revisada["etiqueta"] != val["etiqueta"]).sum()))
    print(t[["version", "modelo", "escala", "precision", "sensibilidad", "f1", "f1_ic_bajo", "f1_ic_alto"]].round(3).to_string(index=False))
    final = etiquetas_d92(revisada)
    for nombre in ("svm_lineal", "xgboost", "tfidf_logistica"):
        print(nombre, pd.crosstab(final["etiqueta"], pd.Series(pred[nombre], index=revisada.index, name="m")).reindex(index=CLASES, columns=CLASES, fill_value=0).values.tolist())


if __name__ == "__main__":
    main()
