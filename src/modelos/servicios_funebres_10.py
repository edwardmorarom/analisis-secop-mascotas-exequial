import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from src.etl.anonimizar import anonimizar
from src.etl.comun import RAIZ, cargar_config, guardar_libro
from src.modelos import mercado_patrones as mp
from src.modelos.perfil_variables import cargar

DESTINO = RAIZ / "docs" / "revision_f4" / "servicios_funebres_10.xlsx"
SEMILLA = 2032
N = 10
SERVICIOS_FUNEBRES = r"SERVICIOS? FUNEBRES?"
COLUMNAS = ["id", "anio", "entidad", "objeto", "incluye_inhumacion_cremacion"]


def candidatos(f):
    """Contratos que la regla A activaría: «servicios fúnebres» y ninguna otra expresión de inhumación o cremación."""
    t = f["objeto"].map(mp.normalizar_texto)
    return f[t.str.contains(SERVICIOS_FUNEBRES, regex=True) & ~f["incluye_inhumacion_cremacion"]]


def main():
    c = candidatos(cargar(cargar_config()))
    muestra = c.iloc[np.sort(np.random.default_rng(SEMILLA).choice(len(c), N, replace=False))]
    wb = Workbook()
    ws = wb.active
    ws.title = "Revision"
    ws.append(COLUMNAS)
    for k in ws[1]:
        k.font = Font(bold=True)
    for i, r in enumerate(muestra.itertuples(), 1):
        ws.append([f"SF{i:02d}", int(r.anio), r.entidad, " ".join(anonimizar(r.objeto).split())])
    dv = DataValidation(type="list", formula1='"sí,no"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"E2:E{N + 1}")
    amarillo = PatternFill("solid", fgColor="FFF2CC")
    for fila in range(2, N + 2):
        for k in range(1, len(COLUMNAS) + 1):
            ws.cell(fila, k).alignment = Alignment(wrap_text=True, vertical="top")
        ws.cell(fila, 5).fill = amarillo
    for letra, ancho in zip("ABCDE", (8, 7, 45, 90, 28)):
        ws.column_dimensions[letra].width = ancho
    if guardar_libro(wb, DESTINO):
        print("escrito", DESTINO, len(muestra), "filas de", len(c), "candidatos")


if __name__ == "__main__":
    main()
