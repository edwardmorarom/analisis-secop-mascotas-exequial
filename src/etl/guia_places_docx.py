import re

from docx import Document

from src.etl.comun import RAIZ

FUENTE = RAIZ / "docs/oferta/guia_places.md"
DESTINO = RAIZ / "docs/revision_f5/guia_places.docx"


def con_formato(parrafo, texto):
    for trozo in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", texto):
        if trozo.startswith("**"):
            parrafo.add_run(trozo[2:-2]).bold = True
        elif trozo.startswith("`"):
            parrafo.add_run(trozo[1:-1]).font.name = "Consolas"
        elif trozo:
            parrafo.add_run(trozo)


def celdas(linea):
    return [c.strip() for c in linea.strip().strip("|").split("|")]


def convertir(markdown):
    doc = Document()
    lineas = markdown.splitlines()
    i = 0
    while i < len(lineas):
        linea = lineas[i]
        if linea.startswith("|"):
            bloque = []
            while i < len(lineas) and lineas[i].startswith("|"):
                bloque.append(lineas[i])
                i += 1
            filas = [celdas(f) for f in bloque if not re.fullmatch(r"\|[\s:|-]+\|", f)]
            tabla = doc.add_table(rows=len(filas), cols=len(filas[0]), style="Table Grid")
            for r, fila in enumerate(filas):
                for c, texto in enumerate(fila):
                    celda = tabla.cell(r, c)
                    con_formato(celda.paragraphs[0], texto)
                    if r == 0:
                        for run in celda.paragraphs[0].runs:
                            run.bold = True
            continue
        if linea.startswith("# "):
            doc.add_heading(linea[2:], level=0)
        elif linea.startswith("## "):
            doc.add_heading(linea[3:], level=1)
        elif re.match(r"\d+\. ", linea):
            con_formato(doc.add_paragraph(style="List Number"), re.sub(r"^\d+\. ", "", linea))
        elif linea.startswith("- "):
            con_formato(doc.add_paragraph(style="List Bullet"), linea[2:])
        elif linea.strip():
            con_formato(doc.add_paragraph(), linea)
        i += 1
    return doc


def main():
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    convertir(FUENTE.read_text(encoding="utf-8")).save(DESTINO)
    print(DESTINO)


if __name__ == "__main__":
    main()
