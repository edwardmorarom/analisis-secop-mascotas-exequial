import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from src.etl.comun import RAIZ, cargar_config, ruta
from src.evaluacion.metricas_ponderadas import fila_resumen
from src.modelos import deepseek_clasificador as ds
from src.modelos.clasificar_todos import predecir, universo
from src.modelos.datos_clasificacion import CLASES, cargar
from src.modelos.embeddings_logistica import incrustar
from src.modelos.comparar import regresion_logistica
from src.modelos.tfidf_logistica import vectorizador

LIBRO = RAIZ / "docs" / "etiquetado" / "validacion_edward.xlsx"
REGISTRO = RAIZ / "logs" / "deepseek_validacion.jsonl"


def cargar_validacion(config):
    maestra = pd.read_parquet(ruta(config, "processed") / "validacion_externa_maestra.parquet")
    u = universo(config)
    d = maestra.merge(u[["fuente", "llave", "texto"]], on=["fuente", "llave"], validate="one_to_one")
    etiquetas = pd.read_excel(LIBRO, sheet_name="Etiquetado", dtype=str)[["id_muestra", "etiqueta", "forense"]]
    etiquetas["etiqueta"] = etiquetas["etiqueta"].str.strip().str.lower()
    d = d.merge(etiquetas, on="id_muestra", validate="one_to_one")
    assert d["etiqueta"].isin(CLASES).all() and d["forense"].isin(["0", "1"]).all(), "el libro no está completo"
    d["forense"] = d["forense"].astype(int)
    return d


def predicciones_locales(config, d):
    muestra = cargar(config)
    v = vectorizador()
    tfidf = regresion_logistica().fit(v.fit_transform(muestra["texto"]), muestra["etiqueta"])
    e5 = regresion_logistica().fit(np.load(ruta(config, "processed") / "embeddings_e5_muestra.npy"), muestra["etiqueta"])
    p1 = predecir(tfidf, v.transform(d["texto"]))
    p2 = predecir(e5, incrustar(d["texto"].tolist()))
    return {"tfidf_logistica": [CLASES[i] for i in p1.argmax(axis=1)], "e5_logistica": [CLASES[i] for i in p2.argmax(axis=1)]}


def predicciones_deepseek(config, d):
    if ds.en_hora_pico() and "--forzar-pico" not in sys.argv:
        raise SystemExit("Hora pico de DeepSeek (01-04 y 06-10 UTC entre semana): se pospone la corrida.")
    modelo = config["llm"]["modelo"]
    ejemplos = ds.elegir_ejemplos(cargar(config))
    c = ds.cliente()

    def una(r):
        try:
            return {"id_muestra": r.id_muestra, **ds.llamar(c, modelo, ejemplos, r.texto),
                    "momento_utc": datetime.now(timezone.utc).isoformat()}
        except Exception as e:
            return {"id_muestra": r.id_muestra, "error": str(e)[:200], "tokens_entrada": 0, "tokens_salida": 0}

    with ThreadPoolExecutor(6) as pool:
        resultados = list(pool.map(una, d.itertuples()))
    REGISTRO.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in resultados) + "\n", encoding="utf-8")
    pred = {r["id_muestra"]: ds.interpretar(r["respuesta"]) if "respuesta" in r else (None, None) for r in resultados}
    return [pred[i][0] or "no_funerario" for i in d["id_muestra"]], ds.costo_real([r for r in resultados if "error" not in r])


def main():
    config = cargar_config()
    d = cargar_validacion(config)
    pred = predicciones_locales(config, d)
    pred["deepseek_flash"], costo = predicciones_deepseek(config, d)
    uno = np.ones(len(d))
    filas = []
    for nombre, p in pred.items():
        pond = fila_resumen(nombre, d["etiqueta"], p, d["peso"], d["subestrato"])
        sinpond = fila_resumen(nombre, d["etiqueta"], p, uno, d["subestrato"])
        filas.append({**{f"pond_{k}": v for k, v in pond.items() if k != "modelo"},
                      **{f"sin_{k}": v for k, v in sinpond.items() if k != "modelo"}, "modelo": nombre})
        print(f"\n{nombre}: matriz de confusión (filas = humano, columnas = modelo)")
        print(pd.crosstab(d["etiqueta"], pd.Series(p, name="modelo"), dropna=False).reindex(index=CLASES, columns=CLASES, fill_value=0).to_string())
    tabla = pd.DataFrame(filas).set_index("modelo")
    pd.set_option("display.width", 220)
    print("\nPonderado:\n", tabla.filter(like="pond_").round(3).T.to_string())
    print("\nSin ponderar:\n", tabla.filter(like="sin_").round(3).T.to_string())
    print("\nCosto real DeepSeek:", costo)
    tabla.to_csv(ruta(config, "processed") / "tabla_validacion_60.csv")
    d.assign(**{f"pred_{k}": v for k, v in pred.items()}).drop(columns="texto").to_parquet(
        ruta(config, "processed") / "predicciones_validacion_60.parquet", index=False)


if __name__ == "__main__":
    main()
