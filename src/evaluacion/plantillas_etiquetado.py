import sys
from pathlib import Path

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from src.etl.comun import RAIZ, cargar_config, ruta
from src.evaluacion.reglas_etiquetado import instrucciones

REVISORES = ["edward", "natalia"]
CALIBRACION = 40
ENCABEZADO = ["n", "ronda", "id_muestra", "fuente", "anio", "entidad", "objeto", "descripcion", "codigo_unspsc",
              "etiqueta", "forense", "notas"]
ANCHOS = [6, 13, 11, 9, 7, 34, 70, 55, 12, 14, 9, 40]
CLASES = "funerario,no_funerario,mixto"


def escribir_instrucciones(guia, revisor):
    guia["A1"] = f"Etiquetado SECOP — revisor: {revisor.capitalize()}"
    guia["A1"].font = Font(bold=True, size=13)
    for i, t in enumerate(instrucciones(), 3):
        celda = guia.cell(i, 1, t)
        celda.alignment = Alignment(wrap_text=True, vertical="top")
        celda.font = Font(bold=t.isupper())
    guia.column_dimensions["A"].width = 110


def actualizar_en_sitio(path, datos, revisor):
    """Corrige textos e instrucciones sin tocar etiqueta, forense ni notas."""
    wb = load_workbook(path)
    ws = wb["Etiquetado"]
    cabecera = {c.value: c.column for c in ws[1]}
    previos = [(ws.cell(f, cabecera[k]).value) for f in range(2, ws.max_row + 1) for k in ("etiqueta", "forense", "notas")]
    texto = datos.set_index("id_muestra")
    cambios = 0
    for f in range(2, ws.max_row + 1):
        fila = texto.loc[ws.cell(f, cabecera["id_muestra"]).value]
        for col, campo in (("entidad", "nombre_entidad"), ("objeto", "objeto"), ("descripcion", "descripcion"),
                           ("codigo_unspsc", "codigo")):
            nuevo = fila[campo] if isinstance(fila[campo], str) else ""
            celda = ws.cell(f, cabecera[col])
            if (celda.value or "") != nuevo:
                celda.value = nuevo
                cambios += 1
    if "Instrucciones" in wb.sheetnames:
        del wb["Instrucciones"]
    escribir_instrucciones(wb.create_sheet("Instrucciones"), revisor)
    posteriores = [(ws.cell(f, cabecera[k]).value) for f in range(2, ws.max_row + 1) for k in ("etiqueta", "forense", "notas")]
    assert previos == posteriores, "las etiquetas no deben cambiar"
    wb.save(path)
    return cambios


def libro(datos, revisor):
    wb = Workbook()
    ws = wb.active
    ws.title = "Etiquetado"
    ws.append(ENCABEZADO)
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="1F1F1F")
        c.alignment = Alignment(vertical="center", wrap_text=True)
    amarillo = PatternFill("solid", fgColor="FFF2CC")
    azul = PatternFill("solid", fgColor="DDEBF7")
    for i, r in enumerate(datos.itertuples(index=False), 1):
        ronda = "calibración" if i <= CALIBRACION else "principal"
        ws.append([i, ronda, r.id_muestra, r.fuente, int(r.anio), r.nombre_entidad, r.objeto,
                   r.descripcion if isinstance(r.descripcion, str) else "", r.codigo if isinstance(r.codigo, str) else "",
                   None, None, None])
        fila = i + 1
        for col in (1, 2):
            if i <= CALIBRACION:
                ws.cell(fila, col).fill = azul
        for col in (10, 11, 12):
            ws.cell(fila, col).fill = amarillo
        for col in (6, 7, 8):
            ws.cell(fila, col).alignment = Alignment(wrap_text=True, vertical="top")
    for letra, ancho in zip("ABCDEFGHIJKL", ANCHOS):
        ws.column_dimensions[letra].width = ancho
    n = len(datos) + 1
    etiquetas = DataValidation(type="list", formula1=f'"{CLASES}"', allow_blank=True, showErrorMessage=True,
                               errorTitle="Etiqueta", error="Use funerario, no_funerario o mixto.")
    forense = DataValidation(type="list", formula1='"0,1"', allow_blank=True, showErrorMessage=True,
                             errorTitle="Forense", error="Use 0 o 1.")
    ws.add_data_validation(etiquetas)
    ws.add_data_validation(forense)
    etiquetas.add(f"J2:J{n}")
    forense.add(f"K2:K{n}")
    ws.freeze_panes = "D2"
    ws.auto_filter.ref = f"A1:L{n}"
    escribir_instrucciones(wb.create_sheet("Instrucciones"), revisor)
    return wb


def main(carpeta=None):
    config = cargar_config()
    datos = pd.read_csv(ruta(config, "processed") / "muestra_secop_etiquetado.csv", dtype=str)
    datos["anio"] = datos["anio"].astype(int)
    destino = Path(carpeta) if carpeta else RAIZ / "docs" / "etiquetado"
    destino.mkdir(parents=True, exist_ok=True)
    for revisor in REVISORES:
        path = destino / f"etiquetado_{revisor}.xlsx"
        try:
            if path.exists():
                print(f"{path.name}: {actualizar_en_sitio(path, datos, revisor)} celdas de texto corregidas; etiquetas intactas")
            else:
                libro(datos, revisor).save(path)
                print(f"{path.name}: creado")
        except PermissionError:
            print(f"{path.name}: abierto en Excel; ciérrelo y repita")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
