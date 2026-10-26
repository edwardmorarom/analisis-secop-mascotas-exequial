import sys
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from src.etl.anonimizar import anonimizar
from src.etl.comun import RAIZ, cargar_config, ruta
from src.evaluacion.reglas_etiquetado import D20, D21, PROPUESTAS_PENDIENTES

EJEMPLOS = {
    "funerario": ["22-13-13268646-12323242", "CO1.PCCNTR.5713117"],
    "no_funerario": ["21-12-12425554-11507189", "21-12-11665962-10795571", "CO1.PCCNTR.7800399"],
    "mixto": ["20-12-10759323-9885240", "CO1.PCCNTR.3579155"],
}
NOTAS = {
    "CO1.PCCNTR.7800399": "forense = 1",
    "CO1.PCCNTR.3579155": "forense = 1 (necropsia + servicio funerario)",
}
CRITERIO = {
    "funerario": "El contrato compra servicios o bienes funerarios: inhumación, exhumación, cremación, ataúdes, "
                 "planes exequiales, traslado de cuerpos con fin funerario, administración u operación de cementerios.",
    "no_funerario": "No se compra nada funerario: obras, mantenimiento físico, estudios o diseños (aunque mencionen "
                    "un cementerio); aseo, cafetería, vigilancia, custodia; personal administrativo o de apoyo a una "
                    "dependencia funeraria; contratación forense sin componente funerario.",
    "mixto": "Un mismo contrato mezcla un componente funerario claro con otro que no lo es (p. ej. sepulturero "
             "con albañilería y pintura; servicio funerario con necropsia).",
}
EJEMPLO_PERSONAL = "CO1.PCCNTR.6323489"
EJEMPLO_CEMENTERIO = "CO1.PCCNTR.7377636"


def recortar(texto, n):
    if len(texto) <= n:
        return texto
    return texto[:n].rsplit(" ", 1)[0].rstrip(";,.") + "…"


def sombrear(celda, color):
    pr = celda._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:fill"), color)
    pr.append(sh)


def parrafo(doc, texto, negrita=False, tamano=9, espacio=2):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(espacio)
    p.paragraph_format.space_before = Pt(0)
    r = p.add_run(texto)
    r.bold = negrita
    r.font.size = Pt(tamano)
    return p


def vineta(doc, texto, tamano=9):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(1)
    r = p.add_run(texto)
    r.font.size = Pt(tamano)


def main(carpeta=None):
    config = cargar_config()
    interim = ruta(config, "interim")
    a = pd.concat([pd.read_parquet(interim / f"{n}_senales.parquet") for n in ("secop1", "secop2")],
                  ignore_index=True).set_index("llave")
    muestra = set(pd.read_parquet(ruta(config, "processed") / "muestra_secop_maestra.parquet").llave)
    assert not muestra & ({k for v in EJEMPLOS.values() for k in v} | {EJEMPLO_PERSONAL, EJEMPLO_CEMENTERIO}), \
        "ejemplo dentro de la muestra"

    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.59), Cm(27.94)
    sec.left_margin = sec.right_margin = Cm(1.6)
    sec.top_margin = sec.bottom_margin = Cm(1.3)
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(9)

    t = parrafo(doc, "Criterio de etiquetado — contratos funerarios en SECOP", True, 14, 1)
    t.runs[0].font.color.rgb = RGBColor(0x1F, 0x1F, 0x1F)
    parrafo(doc, "Lea el objeto y la descripción del contrato (no el nombre del proveedor). Asigne una de tres clases y, "
                 "aparte, la marca forense. Etiquete cada caso por separado y sin consultar durante la calibración (filas 1–40).",
            tamano=9, espacio=4)

    tabla = doc.add_table(rows=1, cols=3)
    tabla.style = "Table Grid"
    for celda, txt in zip(tabla.rows[0].cells, ["Clase", "Cuándo se asigna", "Ejemplos reales (fuera de la muestra)"]):
        celda.text = ""
        r = celda.paragraphs[0].add_run(txt)
        r.bold = True
        r.font.size = Pt(9)
        sombrear(celda, "DDEBF7")
    for clase, llaves in EJEMPLOS.items():
        fila = tabla.add_row().cells
        fila[0].text = ""
        r = fila[0].paragraphs[0].add_run(clase)
        r.bold = True
        r.font.size = Pt(9)
        fila[1].text = ""
        fila[1].paragraphs[0].add_run(CRITERIO[clase]).font.size = Pt(8.5)
        fila[2].text = ""
        for i, k in enumerate(llaves):
            p = fila[2].paragraphs[0] if i == 0 else fila[2].add_paragraph()
            p.paragraph_format.space_after = Pt(2)
            texto = " ".join(anonimizar(a.loc[k, "objeto"]).split())
            r = p.add_run(f"«{recortar(texto, 210)}»")
            r.font.size = Pt(8)
            r.italic = True
            if k in NOTAS:
                p.add_run(f"  → {NOTAS[k]}").font.size = Pt(8)
    for row in tabla.rows:
        row.cells[0].width, row.cells[1].width, row.cells[2].width = Cm(2.4), Cm(6.3), Cm(9.6)

    parrafo(doc, "", tamano=3, espacio=0)
    parrafo(doc, "Reglas del libro de códigos (D21)", True, 10.5, 1)
    ejemplos = {4: EJEMPLO_CEMENTERIO, 6: EJEMPLO_PERSONAL}
    for i, regla in enumerate(D21, 1):
        p = parrafo(doc, f"{i}. {regla}", tamano=9, espacio=1)
        p.paragraph_format.left_indent = Cm(0.4)
        if i in ejemplos:
            texto = " ".join(anonimizar(a.loc[ejemplos[i], "objeto"]).split())
            e = parrafo(doc, f"Ejemplo real: «{recortar(texto, 170)}»", tamano=8, espacio=1)
            e.paragraph_format.left_indent = Cm(0.8)
            e.runs[0].italic = True

    parrafo(doc, "", tamano=3, espacio=0)
    parrafo(doc, "Clases y marca forense (D20)", True, 10.5, 1)
    for regla in D20:
        vineta(doc, regla)
    pend = parrafo(doc, PROPUESTAS_PENDIENTES, tamano=8.5, espacio=1)
    pend.runs[0].bold = True

    parrafo(doc, "", tamano=3, espacio=0)
    p = parrafo(doc, "Documento de referencia: recoge el criterio con el que se etiquetaron los 400 casos de la muestra; no se "
                     "re-etiquetó. Los ejemplos son casos reales fuera de la muestra, ya censurados.", tamano=8)
    p.runs[0].italic = True

    destino = (Path(carpeta) if carpeta else RAIZ / "docs" / "etiquetado") / "guia_etiquetado.docx"
    doc.save(destino)
    print("guardado", destino)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
