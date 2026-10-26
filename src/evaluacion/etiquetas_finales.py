import pandas as pd

from src.etl.comun import RAIZ, cargar_config, ruta
from src.evaluacion.kappa import CLASES, leer

CARPETA = RAIZ / "docs" / "etiquetado"
FORENSE_POR_REGLA_FOSAS = {"M112"}


def cargar():
    final = CARPETA / "etiquetado_final.xlsx"
    revisar = pd.read_excel(final, sheet_name="Revisar", dtype=str)
    finales = pd.read_excel(final, sheet_name="Etiquetas finales", dtype=str)
    harold = pd.read_excel(CARPETA / "etiquetado_harold.xlsx", sheet_name="Etiquetado", dtype=str)
    return revisar, finales, harold


def verificar(revisar, finales, harold):
    assert finales["id_muestra"].tolist() == harold["id_muestra"].tolist(), "orden distinto entre los libros"
    assert (finales["decision_harold"].values == harold["decision_harold"].values).all()
    assert (revisar["revisado"].str.strip().str.lower() == "sí").all(), "hay filas de Revisar sin revisado = sí"
    assert revisar["id_muestra"].is_unique and revisar["id_muestra"].isin(finales["id_muestra"]).all()
    fuera = finales[~finales["id_muestra"].isin(revisar["id_muestra"])]
    assert (fuera["etiqueta_final"] == fuera["decision_harold"]).all(), "propuesta distinta de la decisión de Harold"
    explicito = fuera["forense_harold"].notna()
    assert (fuera.loc[explicito, "forense_final"] == fuera.loc[explicito, "forense_harold"]).all()
    return {"fuera_de_revisar": len(fuera), "forense_sin_dato_de_harold_fuera": int((~explicito).sum())}


def construir(revisar, finales, harold, e, n):
    base = finales[["n", "id_muestra"]].copy()
    base["n"] = base["n"].astype(int)
    base["decision_harold"] = finales["decision_harold"].values
    base["forense_harold"] = pd.to_numeric(finales["forense_harold"]).values
    base = base.merge(revisar[["id_muestra", "tu_etiqueta", "tu_forense"]], on="id_muestra", how="left")
    en_revisar = base["tu_etiqueta"].notna()
    base["etiqueta"] = base["tu_etiqueta"].where(en_revisar, base["decision_harold"]).str.strip().str.lower()
    base["forense"] = pd.to_numeric(base["tu_forense"]).where(en_revisar, base["forense_harold"].fillna(0)).astype(int)
    base["origen"] = en_revisar.map({True: "revision_edward", False: "propuesta_harold"})
    base["forense_deducido"] = (base["forense_harold"].isna() & ~en_revisar).astype(int)
    regla = base["id_muestra"].isin(FORENSE_POR_REGLA_FOSAS)
    base["forense_por_regla_fosas"] = regla.astype(int)
    base.loc[regla, "forense"] = 1
    base = base.merge(e[["id_muestra", "etiqueta", "forense"]].rename(
        columns={"etiqueta": "etiqueta_edward", "forense": "forense_edward"}), on="id_muestra")
    base = base.merge(n[["id_muestra", "etiqueta", "forense"]].rename(
        columns={"etiqueta": "etiqueta_natalia", "forense": "forense_natalia"}), on="id_muestra")
    return base.drop(columns=["tu_etiqueta", "tu_forense"])


def main():
    config = cargar_config()
    revisar, finales, harold = cargar()
    resumen = verificar(revisar, finales, harold)
    e, n = leer(CARPETA / "etiquetado_edward.xlsx", "edward"), leer(CARPETA / "etiquetado_natalia.xlsx", "natalia")
    base = construir(revisar, finales, harold, e, n)
    assert base["etiqueta"].isin(CLASES).all() and base["forense"].isin([0, 1]).all()
    incoherentes = base[(base["forense"] == 1) & (base["etiqueta"] == "funerario")]
    assert incoherentes.empty, f"funerario con forense = 1: {incoherentes['id_muestra'].tolist()}"
    maestra = pd.read_parquet(ruta(config, "processed") / "muestra_secop_maestra.parquet")
    base = base.merge(maestra[["id_muestra", "subestrato", "peso"]], on="id_muestra", validate="one_to_one")
    base.to_parquet(ruta(config, "processed") / "etiquetas_finales.parquet", index=False)
    print(resumen, "| filas:", len(base), "| origen:", base["origen"].value_counts().to_dict())
    print("regla fosas aplicada a:", base.loc[base["forense_por_regla_fosas"] == 1, "id_muestra"].tolist())
    print(pd.crosstab(base["etiqueta"], base["forense"], margins=True).to_string())
    print("incoherencias (funerario con forense = 1):", len(incoherentes))


if __name__ == "__main__":
    main()
