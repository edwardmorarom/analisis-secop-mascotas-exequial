import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from src.etl.comun import cargar_config, ruta
from src.modelos.comparar import regresion_logistica
from src.modelos.datos_clasificacion import CLASES, cargar, texto_contrato
from src.modelos.embeddings_logistica import incrustar
from src.modelos.tfidf_logistica import vectorizador

COLUMNAS_VALOR = {"secop1": "cuantia_contrato", "secop2": "valor_del_contrato"}


def universo(config):
    interim = ruta(config, "interim")
    partes = []
    for f, col in COLUMNAS_VALOR.items():
        d = pd.read_parquet(interim / f"{f}_senales.parquet")
        anio = d["anio"] if "anio" in d else pd.to_datetime(d["fecha_de_firma_del_contrato"]).dt.year
        partes.append(pd.DataFrame({
            "fuente": f, "llave": d["llave"], "anio": anio.values, "valor": pd.to_numeric(d[col], errors="coerce").values,
            "estrato": d["estrato"].values,
            "texto": [texto_contrato(o, s, c) for o, s, c in zip(d["objeto"], d["descripcion"], d["codigo"])]}))
    return pd.concat(partes, ignore_index=True)


def predecir(modelo, x):
    prob = modelo.predict_proba(x)
    return prob[:, [list(modelo.classes_).index(c) for c in CLASES]]


def main():
    config = cargar_config()
    procesado = ruta(config, "processed")
    muestra = cargar(config)
    u = universo(config)
    assert not u.duplicated(["fuente", "llave"]).any()
    v = vectorizador()
    prob_tfidf = predecir(regresion_logistica().fit(v.fit_transform(muestra["texto"]), muestra["etiqueta"]), v.transform(u["texto"]))
    destino = procesado / "embeddings_e5_universo.npy"
    if destino.exists():
        x = np.load(destino)
    else:
        x = incrustar(u["texto"].tolist())
        np.save(destino, x)
    x_muestra = np.load(procesado / "embeddings_e5_muestra.npy")
    prob_e5 = predecir(regresion_logistica().fit(x_muestra, muestra["etiqueta"]), x)
    out = u.drop(columns="texto").copy()
    for nombre, p in (("tfidf", prob_tfidf), ("e5", prob_e5)):
        out[f"pred_{nombre}"] = [CLASES[i] for i in p.argmax(axis=1)]
        for k, c in enumerate(CLASES):
            out[f"p_{nombre}_{c}"] = p[:, k]
    # en los 400 casos de la muestra se usa la predicción fuera de pliegue (sin fuga) y se guarda la etiqueta humana
    clave = muestra.set_index(["fuente", "llave"])
    out = out.merge(muestra[["fuente", "llave", "id_muestra", "etiqueta", "forense"]].rename(
        columns={"etiqueta": "etiqueta_humana", "forense": "forense_humano"}), on=["fuente", "llave"], how="left")
    for nombre in ("tfidf_logistica", "e5_logistica"):
        oof = pd.read_parquet(procesado / f"predicciones_cv_{nombre}.parquet").set_index("id_muestra")
        corto = nombre.split("_")[0]
        en = out["id_muestra"].notna()
        ids = out.loc[en, "id_muestra"]
        out.loc[en, f"pred_{corto}"] = ids.map(oof["pred"]).values
        for c in CLASES:
            out.loc[en, f"p_{corto}_{c}"] = ids.map(oof[f"p_{c}"]).values
    out.to_parquet(procesado / "clasificacion_universo.parquet", index=False)
    print(len(out), out["pred_tfidf"].value_counts().to_dict(), out["pred_e5"].value_counts().to_dict())


if __name__ == "__main__":
    main()
