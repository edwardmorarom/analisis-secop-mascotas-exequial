import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from src.etl.comun import RAIZ, cargar_config, guardar_libro
from src.modelos import mercado_patrones as mp
from src.modelos.perfil_variables import SEMILLA, cargar, homologar

DESTINO = RAIZ / "docs" / "revision_f4" / "derivadas_entidad_2.xlsx"
SEMILLA_2 = 2031
POR_CATEGORIA = 5
COLUMNAS = ["id", "fuente", "anio", "entidad", "orden", "tipo_entidad_derivado", "correcto", "tipo_correcto", "nota"]


def seleccion(f):
    """5 al azar por categoría derivada y 5 con «salud» y «alcaldía» o «municipio»; sin repetir los 20 de derivadas.xlsx."""
    previos = set(np.sort(np.random.default_rng(SEMILLA).choice(len(f), 20, replace=False)))
    rng = np.random.default_rng(SEMILLA_2)
    nombre = f["entidad"].map(mp.normalizar_texto)
    mixto = nombre.str.contains("SALUD") & nombre.str.contains("ALCALDIA|MUNICIPIO")
    libre = ~f.index.isin(previos)
    partes = []
    for categoria in sorted(f["tipo_entidad"].unique()):
        cand = f.index[(f["tipo_entidad"] == categoria) & libre & ~mixto]
        partes.append(rng.choice(cand, min(POR_CATEGORIA, len(cand)), replace=False))
    cand = f.index[mixto & libre]
    partes.append(rng.choice(cand, min(POR_CATEGORIA, len(cand)), replace=False))
    return f.loc[np.concatenate(partes)], int(mixto.sum())


def main():
    f = homologar(cargar(cargar_config()))
    muestra, n_mixto = seleccion(f)
    wb = Workbook()
    ws = wb.active
    ws.title = "tipo_entidad"
    ws.append(COLUMNAS)
    for c in ws[1]:
        c.font = Font(bold=True)
    for i, r in enumerate(muestra.itertuples(), 1):
        ws.append([f"TE{i:02d}", r.fuente, int(r.anio), r.entidad, r.orden, r.tipo_entidad] + [None] * 3)
    n = len(muestra)
    col_ok = COLUMNAS.index("correcto") + 1
    dv = DataValidation(type="list", formula1='"sí,no"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"{ws.cell(2, col_ok).coordinate}:{ws.cell(n + 1, col_ok).coordinate}")
    estilo = PatternFill("solid", fgColor="FFF2CC")
    for fila in range(2, n + 2):
        for k in range(1, len(COLUMNAS) + 1):
            ws.cell(fila, k).alignment = Alignment(wrap_text=True, vertical="top")
            if k >= col_ok:
                ws.cell(fila, k).fill = estilo
    for letra, ancho in zip("ABCDEFGHI", (8, 9, 7, 40, 40, 32, 14, 28, 30)):
        ws.column_dimensions[letra].width = ancho
    if not guardar_libro(wb, DESTINO):
        return
    print("escrito", DESTINO, n, "filas | contratos con «salud» y «alcaldía» o «municipio»:", n_mixto)
    print(muestra["tipo_entidad"].value_counts().to_dict())


if __name__ == "__main__":
    main()
