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

EJEMPLOS = {
    "funerario": ["22-13-13268646-12323242", "CO1.PCCNTR.8004130"],
    "no_funerario": ["21-12-12425554-11507189", "CO1.PCCNTR.7800399"],
    "mixto": ["CO1.PCCNTR.3260174", "CO1.PCCNTR.3579155"],
}
NOTAS = {
    "CO1.PCCNTR.7800399": "forense = 1",
    "CO1.PCCNTR.3579155": "forense = 1 (inhumación de NN)",
}
CRITERIO = {
    "funerario": "El contrato compra servicios o bienes funerarios: inhumación, exhumación, cremación, "
                 "ataúdes, traslado de cuerpos con fin funerario, administración u operación de cementerios.",
    "no_funerario": "No hay objeto funerario, o solo hay obras, mantenimiento físico, estudios o diseños "
                    "(incluso si mencionan un cementerio), personal administrativo o de apoyo a una dependencia "
                    "funeraria, o contratación forense sin componente funerario.",
    "mixto": "Un mismo contrato mezcla un componente funerario claro con otro que no lo es "
             "(aseo y ornato, necropsias).",
}
EJEMPLO_PERSONAL = "CO1.PCCNTR.6323489"


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
    assert not muestra & ({k for v in EJEMPLOS.values() for k in v} | {EJEMPLO_PERSONAL}), \
        "ejemplo dentro de la muestra"

    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.59), Cm(27.94)
    sec.left_margin = sec.right_margin = Cm(1.6)
    sec.top_margin = sec.bottom_margin = Cm(1.3)
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(9)

    t = parrafo(doc, "Guía de etiquetado — contratos funerarios en SECOP", True, 14, 1)
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
            if len(texto) > 210:
                texto = texto[:207] + "…"
            r = p.add_run(f"«{texto}»")
            r.font.size = Pt(8)
            r.italic = True
            if k in NOTAS:
                p.add_run(f"  → {NOTAS[k]}").font.size = Pt(8)
    for row in tabla.rows:
        row.cells[0].width, row.cells[1].width, row.cells[2].width = Cm(2.4), Cm(6.0), Cm(9.9)

    parrafo(doc, "", tamano=3, espacio=0)
    parrafo(doc, "Marca forense y regla de coherencia", True, 10.5, 1)
    vineta(doc, "forense = 1 si el contrato es de necropsias, autopsias, disección, medicina legal, identificación o "
                "transporte de cadáveres con fin judicial. No es una cuarta clase: va en su propia columna (0 o 1).")
    vineta(doc, "Regla de coherencia: si forense = 1, la etiqueta es no_funerario. Excepción: si hay un componente funerario "
                "claro (p. ej. inhumación de cuerpos no identificados), la etiqueta es mixto.")
    vineta(doc, "forense = 1 con funerario es un error y se devuelve para revisión. Lo forense se reporta aparte y queda "
                "fuera del tamaño de mercado.")

    parrafo(doc, "", tamano=3, espacio=0)
    parrafo(doc, "Cementerios", True, 10.5, 1)
    vineta(doc, "Operación o administración del cementerio (inhumación, exhumación, bóvedas, concesión) = funerario. "
                "Ejemplo: «Administración y operación de los cementerios públicos del Distrito de Cartagena».")
    vineta(doc, "Obras civiles, mantenimiento físico (luminarias, limpieza, vías), estudios y diseños = no_funerario, "
                "aunque el texto diga «cementerio».")
    vineta(doc, "Si el contrato mezcla ambas cosas, mixto. Si el texto no permite decidir, anótelo en notas.")

    parrafo(doc, "", tamano=3, espacio=0)
    parrafo(doc, "Personal administrativo o de apoyo", True, 10.5, 1)
    ejemplo = " ".join(anonimizar(a.loc[EJEMPLO_PERSONAL, "objeto"]).split())
    vineta(doc, "Contratar personal administrativo o de apoyo a una dependencia funeraria (supervisión, PQRS, "
                "correspondencia, apoyo financiero o jurídico) = no_funerario: no compra servicios funerarios. "
                f"Ejemplo: «{ejemplo[:190]}»")

    parrafo(doc, "", tamano=3, espacio=0)
    p = parrafo(doc, "Llene solo las celdas amarillas del Excel (lista desplegable en etiqueta y forense). No cambie el orden de "
                     "las filas. Los ejemplos son casos reales ya censurados; Harold decide los desacuerdos.", tamano=8)
    p.runs[0].italic = True

    destino = (Path(carpeta) if carpeta else RAIZ / "docs" / "etiquetado") / "guia_etiquetado.docx"
    doc.save(destino)
    print("guardado", destino)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
