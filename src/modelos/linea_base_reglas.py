import pandas as pd

from src.evaluacion.metricas_ponderadas import fila_resumen
from src.modelos.datos_clasificacion import SENALES_NUCLEO, cargar


def predecir(d):
    return pd.Series(["funerario" if v else "no_funerario" for v in d[SENALES_NUCLEO].any(axis=1)], index=d.index)


def main():
    d = cargar()
    pred = predecir(d)
    pd.set_option("display.width", 200)
    print(pd.DataFrame([fila_resumen("reglas", d["etiqueta"], pred, d["peso"], d["subestrato"])]).round(3).T)
    print(pd.crosstab(d["etiqueta"], pred))
    d.assign(pred_reglas=pred)[["id_muestra", "pred_reglas"]].to_parquet(
        "data/processed/predicciones_reglas.parquet", index=False)


if __name__ == "__main__":
    main()
