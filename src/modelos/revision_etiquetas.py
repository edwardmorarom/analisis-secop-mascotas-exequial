import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from src.etl.anonimizar import anonimizar
from src.etl.comun import RAIZ, cargar_config, guardar_libro, ruta
from src.modelos.datos_clasificacion import CLASES
from src.modelos.evaluar_validacion import LIBRO, universo

REGLAS = {
    "V006": "Regla 1 y 5: se etiqueta por lo que se compra; el mantenimiento físico de estructuras y vallas es no_funerario, sin componente funerario en el objeto.",
    "V054": "Regla 1: se etiqueta por lo que se compra; un servicio de cuerpo de bomberos no es un servicio funerario.",
    "V057": "Regla 5: obras, construcción y adecuación física, aunque sean bóvedas de cementerio, son no_funerario.",
    "V027": "Regla 6: aseo, limpieza y apoyo de un cementerio son no_funerario (se compra aseo, no un servicio funerario).",
    "V015": "Regla 6: personal administrativo o de apoyo (asistencia administrativa) de una dependencia funeraria es no_funerario.",
    "V046": "Regla 6: personal profesional de apoyo de una dependencia funeraria (acompañamiento psicológico) es no_funerario.",
    "V030": "Regla 4: el arrendamiento de espacios del cementerio para inhumar es funerario (hoy está como no_funerario).",
}
DESTINO = RAIZ / "docs" / "revision_f4" / "revision_7_etiquetas.xlsx"


def main():
    config = cargar_config()
    maestra = pd.read_parquet(ruta(config, "processed") / "validacion_externa_maestra.parquet")[["id_muestra", "fuente", "llave"]]
    u = universo(config)
    interim = ruta(config, "interim")
    desc = pd.concat([pd.read_parquet(interim / f"{f}_senales.parquet", columns=["llave", "objeto", "descripcion"]).assign(fuente=f)
                      for f in ("secop1", "secop2")])
    d = maestra[maestra["id_muestra"].isin(REGLAS)].merge(desc, on=["fuente", "llave"])
    etiquetas = pd.read_excel(LIBRO, sheet_name="Etiquetado", dtype=str)[["id_muestra", "etiqueta", "forense"]]
    d = d.merge(etiquetas, on="id_muestra").set_index("id_muestra").loc[list(REGLAS)].reset_index()
    wb = Workbook()
    ws = wb.active
    ws.title = "Revision"
    ws.append(["id_muestra", "objeto", "descripcion", "etiqueta_actual", "forense_actual", "regla_D21_que_posiblemente_incumple",
               "etiqueta_revisada", "forense_revisado", "nota"])
    for c in ws[1]:
        c.font = Font(bold=True)
    for i, r in enumerate(d.itertuples(), 2):
        desc_txt = r.descripcion if isinstance(r.descripcion, str) and r.descripcion != r.objeto else ""
        ws.append([r.id_muestra, anonimizar(r.objeto), anonimizar(desc_txt), r.etiqueta, r.forense, REGLAS[r.id_muestra], None, None, None])
        for col in (2, 3, 6):
            ws.cell(i, col).alignment = Alignment(wrap_text=True, vertical="top")
        for col in (7, 8, 9):
            ws.cell(i, col).fill = PatternFill("solid", fgColor="FFF2CC")
    dv1 = DataValidation(type="list", formula1='"' + ",".join(CLASES) + '"', allow_blank=True)
    dv2 = DataValidation(type="list", formula1='"0,1"', allow_blank=True)
    ws.add_data_validation(dv1)
    ws.add_data_validation(dv2)
    dv1.add(f"G2:G{ws.max_row}")
    dv2.add(f"H2:H{ws.max_row}")
    for letra, ancho in zip("ABCDEFGHI", (11, 70, 50, 14, 10, 60, 16, 12, 35)):
        ws.column_dimensions[letra].width = ancho
    ws.freeze_panes = "B2"
    guardar_libro(wb, DESTINO)
    print(len(d), "filas en", DESTINO)


if __name__ == "__main__":
    main()
