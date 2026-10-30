import numpy as np
import pandas as pd

from src.etl.comun import cargar_config, ruta
from src.evaluacion.metricas_ponderadas import fila_resumen
from src.modelos.datos_clasificacion import CLASES
from src.modelos.revision_etiquetas import DESTINO

MODELOS = ["tfidf_logistica", "e5_logistica", "deepseek_flash"]


def etiquetas_revisadas(d):
    r = pd.read_excel(DESTINO, sheet_name="Revision", dtype=str)
    r = r[r["etiqueta_revisada"].notna()]
    assert r["etiqueta_revisada"].isin(CLASES).all(), "etiqueta revisada inválida"
    out = d.copy()
    for fila in r.itertuples():
        i = out.index[out["id_muestra"] == fila.id_muestra][0]
        out.at[i, "etiqueta"] = fila.etiqueta_revisada
        if isinstance(fila.forense_revisado, str):
            out.at[i, "forense"] = int(fila.forense_revisado)
    return out, r


def etiquetas_d92(d):
    from src.modelos.etiquetas_humanas import CORRECCION_D92_VALIDACION
    out = d.copy()
    for i, etiqueta in CORRECCION_D92_VALIDACION.items():
        out.loc[out["id_muestra"] == i, "etiqueta"] = etiqueta
    return out


def tabla(d, version):
    filas = []
    for m in MODELOS:
        p = d["pred_" + m]
        pond = fila_resumen(m, d["etiqueta"], p, d["peso"], d["subestrato"])
        sin = fila_resumen(m, d["etiqueta"], p, np.ones(len(d)), d["subestrato"])
        filas.append({"version": version, "modelo": m, **{f"pond_{k}": v for k, v in pond.items() if k != "modelo"},
                      **{f"sin_{k}": v for k, v in sin.items() if k != "modelo"}})
    return pd.DataFrame(filas)


def main():
    config = cargar_config()
    d = pd.read_parquet(ruta(config, "processed") / "predicciones_validacion_60.parquet")
    revisado, cambios = etiquetas_revisadas(d)
    pd.set_option("display.width", 220)
    print("filas revisadas:", len(cambios), "| cambian de etiqueta:", int((revisado["etiqueta"] != d["etiqueta"]).sum()))
    d92 = etiquetas_d92(revisado)
    print("cambian por D92:", int((d92["etiqueta"] != revisado["etiqueta"]).sum()))
    t = pd.concat([tabla(d, "original"), tabla(revisado, "revisada"), tabla(d92, "revisada_d92")])
    cols = ["version", "modelo", "pond_precision", "pond_sensibilidad", "pond_f1", "pond_f1_ic_bajo", "pond_f1_ic_alto",
            "sin_precision", "sin_sensibilidad", "sin_f1", "sin_f1_ic_bajo", "sin_f1_ic_alto"]
    print(t[cols].round(3).to_string(index=False))
    for version, x in (("original", d), ("revisada", revisado), ("revisada_d92", d92)):
        mejor = t[t["version"] == version].sort_values("pond_f1", ascending=False).iloc[0]["modelo"]
        print(f"{version}: el F1 ponderado más alto es el de {mejor}; DeepSeek {'sí' if mejor == 'deepseek_flash' else 'no'} lo tiene (regla D62)")
        for m in MODELOS:
            print(m, pd.crosstab(x["etiqueta"], x["pred_" + m]).reindex(index=CLASES, columns=CLASES, fill_value=0).values.tolist())
    t.to_csv(ruta(config, "processed") / "tabla_validacion_60_revisada.csv", index=False)


if __name__ == "__main__":
    main()
