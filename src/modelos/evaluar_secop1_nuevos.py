import numpy as np
import pandas as pd

from src.etl.comun import cargar_config, ruta
from src.evaluacion.metricas_ponderadas import fila_resumen
from src.modelos.datos_clasificacion import CLASES
from src.modelos.secop1_nuevos import DESTINO


def cargar_etiquetadas(config):
    m = pd.read_parquet(ruta(config, "processed") / "secop1_nuevos_maestra.parquet")
    e = pd.read_excel(DESTINO, sheet_name="Etiquetado", dtype=str)[["id_muestra", "etiqueta", "forense", "notas"]]
    e["etiqueta"] = e["etiqueta"].str.strip().str.lower()
    assert e["etiqueta"].isin(CLASES).all(), "el libro no está completo"
    return m.merge(e, on="id_muestra", validate="one_to_one")


def main():
    d = cargar_etiquetadas(cargar_config())
    pd.set_option("display.width", 220)
    filas = []
    for modelo in ("pred_tfidf", "pred_e5"):
        for escala, w in (("ponderado", d["peso"]), ("sin_ponderar", np.ones(len(d)))):
            f = fila_resumen(modelo.replace("pred_", ""), d["etiqueta"], d[modelo], w, d["grupo_pred"])
            filas.append({"escala": escala, **f})
        print(f"\n{modelo}: matriz de confusión (filas = humano, columnas = modelo)")
        print(pd.crosstab(d["etiqueta"], d[modelo]).reindex(index=CLASES, columns=CLASES, fill_value=0).to_string())
    t = pd.DataFrame(filas)
    print(t[["escala", "modelo", "precision", "precision_ic_bajo", "precision_ic_alto", "sensibilidad", "sensibilidad_ic_bajo",
             "sensibilidad_ic_alto", "f1"]].round(3).to_string(index=False))
    t.to_csv(ruta(cargar_config(), "processed") / "evaluacion_secop1_nuevos.csv", index=False, encoding="utf-8-sig")
    print("\nPor grupo de muestreo (clasificado por TF-IDF):")
    print(pd.crosstab(d["grupo_pred"], d["etiqueta"]).to_string())
    errores = d[(d["pred_tfidf"] != d["etiqueta"]) | (d["pred_e5"] != d["etiqueta"])]
    print(errores[["id_muestra", "anio", "grupo_pred", "etiqueta", "pred_tfidf", "pred_e5", "notas"]].to_string(index=False))


if __name__ == "__main__":
    main()
