import argparse

import numpy as np
import pandas as pd

from src.etl.comun import cargar_config, ruta
from src.etl.extraer_minsalud import RAZON_MAXIMA, cargar_pob_dane, razon_reproducible

ANIOS_BASE = (2018, 2019, 2022)
TOLERANCIA_PICO = 0.05


def resumen(poblacion, animales, maximo):
    razon = poblacion / animales.replace(0, np.nan)
    cercano = np.rint(razon)
    casi_entera = ((razon - cercano).abs() < TOLERANCIA_PICO) & (cercano >= 1) & (cercano <= maximo)
    reproducible = ~np.isnan(razon_reproducible(poblacion, animales, maximo))
    en_tope = reproducible & (np.rint(poblacion / animales.replace(0, np.nan)) == maximo)
    valido = razon.notna()
    return {"n": int(valido.sum()), "casi_entera_%": 100 * casi_entera[valido].mean(),
            "reproducible_%": 100 * reproducible[valido].mean(), "reproducible_en_tope_%": 100 * en_tope[valido].mean()}


def tabla(config, df, anio_informe, base_pdf=None):
    filas = []
    es_muni = df["tipo"].isin(["municipio", "distrito"]) & df["cod_divipola"].notna()
    m = df[es_muni]
    bases = [("pob_pdf (cifra impresa)", m[base_pdf].astype(float))] if base_pdf else []
    for anio in sorted({*ANIOS_BASE, anio_informe}):
        bases.append((f"DANE {anio}", m["cod_divipola"].map(cargar_pob_dane(config, anio)).astype(float)))
    for nombre, pob in bases:
        for especie, columna in (("perro", "poblacion_perros"), ("gato", "poblacion_gatos")):
            filas.append({"informe": anio_informe, "base": nombre, "especie": especie,
                          **resumen(pob.reset_index(drop=True), m[columna].astype(float).reset_index(drop=True),
                                    RAZON_MAXIMA[especie])})
    return pd.DataFrame(filas)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--anios", type=int, nargs="+", default=[2019, 2023, 2024])
    a = p.parse_args()
    config = cargar_config()
    pd.set_option("display.width", 220)
    for anio in a.anios:
        df = pd.read_parquet(ruta(config, "interim") / f"minsalud_{anio}.parquet")
        t = tabla(config, df, anio, "pob_pdf" if anio == 2019 else None)
        print(f"\nInforme {anio}: % de municipios cuya población de animales se reproduce con DANE / R (R entero, ±1 animal)")
        print(t.drop(columns="informe").round(1).to_string(index=False))


if __name__ == "__main__":
    main()
