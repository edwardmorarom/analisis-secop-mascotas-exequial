import argparse
import random

import pandas as pd
from openpyxl import Workbook, load_workbook

from src.etl.clasificar_places import LIBROS
from src.evaluacion.kappa_places import CARPETA, comparar, leer

SEMILLA = 2029
N = 25
RONDA = "consistencia"
COLUMNAS = ["id_revision", "ronda", "nombre", "direccion", "municipio", "tipos", "clase", "verificado_en", "nota"]
SEGUNDA = CARPETA / "places_consistencia_edward.xlsx"


def filas_finales(ruta):
    ws = load_workbook(ruta, read_only=True)["revision"]
    filas = list(ws.iter_rows(values_only=True))
    d = pd.DataFrame(filas[1:], columns=filas[0])
    return d[d["ronda"] == "final"]


def preparar(libro=LIBROS["edward"], destino=SEGUNDA):
    """Entrega 25 filas finales elegidas al azar, sin clase, para reclasificarlas; exige la ronda final completa."""
    final = filas_finales(libro)
    sin_clase = final[final["clase"].isna() | (final["clase"].astype("string").str.strip() == "")]
    if len(sin_clase):
        raise ValueError(f"la ronda final no está completa: {len(sin_clase)} filas sin clase")
    ids = random.Random(SEMILLA).sample(sorted(final["id_revision"]), N)
    wb = Workbook()
    ws = wb.active
    ws.title = "revision"
    ws.append(COLUMNAS)
    for _, f in final[final["id_revision"].isin(ids)].sort_values("id_revision").iterrows():
        ws.append([f["id_revision"], RONDA, f["nombre"], f["direccion"], f["municipio"], f["tipos"], None, None, None])
    wb.save(destino)
    return sorted(ids)


def comparar_consistencia(libro=LIBROS["edward"], segunda=SEGUNDA):
    primera = leer(libro, "final")
    repetida = leer(segunda, RONDA)
    return comparar(primera.loc[repetida.index], repetida)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preparar", action="store_true")
    ap.add_argument("--comparar", action="store_true")
    args = ap.parse_args()
    if args.preparar:
        print(preparar())
    if args.comparar:
        r = comparar_consistencia()
        print(f"filas: {r['n']} | acuerdo: {r['acuerdo']:.3f} | κ de Cohen intra-revisor: {r['kappa']:.3f}")
        print(r["confusion"].to_string())
        r["desacuerdos"].to_csv(CARPETA / "desacuerdos_consistencia.csv", index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
