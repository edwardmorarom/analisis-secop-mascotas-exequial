import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from src.etl.comun import RAIZ, cargar_config, ruta

REVISORES = ["edward", "natalia"]
CALIBRACION = 40
ENCABEZADO = ["n", "ronda", "id_muestra", "fuente", "anio", "entidad", "objeto", "descripcion", "codigo_unspsc",
              "etiqueta", "forense", "notas"]
ANCHOS = [6, 13, 11, 9, 7, 34, 70, 55, 12, 14, 9, 40]
CLASES = "funerario,no_funerario,mixto"
INSTRUCCIONES = [
    "Etiquete solo las celdas amarillas: etiqueta (lista) y forense (0 o 1); notas es opcional.",
    "Las tres clases: funerario, no_funerario, mixto. forense es una marca aparte, no una cuarta clase.",
    "Regla de coherencia: si forense = 1, la etiqueta es no_funerario, salvo componente funerario claro "
    "(p. ej. inhumación de cuerpos no identificados), que va como mixto.",
    "Cementerio con operación o administración (inhumación, exhumación, bóvedas, concesión) = funerario; "
    "obras civiles, mantenimiento físico, estudios y diseños = no_funerario.",
    "Filas 1–40: ronda de calibración. No consulte con la otra persona hasta terminarla.",
    "No modifique el orden de las filas ni las columnas. Detalle en guia_etiquetado.docx.",
]


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
    guia = wb.create_sheet("Instrucciones")
    guia["A1"] = f"Etiquetado SECOP — revisor: {revisor.capitalize()}"
    guia["A1"].font = Font(bold=True, size=13)
    for i, t in enumerate(INSTRUCCIONES, 3):
        guia.cell(i, 1, t).alignment = Alignment(wrap_text=True, vertical="top")
    guia.column_dimensions["A"].width = 110
    return wb


def main():
    config = cargar_config()
    datos = pd.read_csv(ruta(config, "processed") / "muestra_secop_etiquetado.csv", dtype=str)
    datos["anio"] = datos["anio"].astype(int)
    destino = RAIZ / "docs" / "etiquetado"
    destino.mkdir(parents=True, exist_ok=True)
    for revisor in REVISORES:
        libro(datos, revisor).save(destino / f"etiquetado_{revisor}.xlsx")
    print(len(datos), "casos en", ", ".join(f"etiquetado_{r}.xlsx" for r in REVISORES))


if __name__ == "__main__":
    main()
