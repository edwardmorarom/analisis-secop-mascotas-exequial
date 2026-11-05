from openpyxl import load_workbook

from src.etl.clasificar_places import LIBROS

HOJA_ORIGINAL = "ronda1_original"
CAMPOS = ("id_revision", "nombre", "clase", "verificado_en", "nota")


def preparar(ruta):
    """Marca como «final» toda fila que no sea calibracion_2 y vacía la clase de la ronda 1, guardándola antes."""
    wb = load_workbook(ruta)
    if HOJA_ORIGINAL in wb.sheetnames:
        raise ValueError(f"{HOJA_ORIGINAL} ya existe: la ronda final ya fue preparada")
    ws = wb["revision"]
    cab = [c.value for c in ws[1]]
    col = {n: cab.index(n) + 1 for n in cab}
    original = wb.create_sheet(HOJA_ORIGINAL)
    original.append(list(CAMPOS))
    ronda1 = 0
    final = 0
    for r in range(2, ws.max_row + 1):
        ronda = ws.cell(r, col["ronda"]).value
        if ronda == "calibracion_2":
            continue
        if ronda == "calibracion":
            original.append([ws.cell(r, col[c]).value for c in CAMPOS])
            ws.cell(r, col["clase"]).value = None
            ronda1 += 1
        ws.cell(r, col["ronda"]).value = "final"
        final += 1
    wb.save(ruta)
    return {"final": final, "ronda1_vaciadas": ronda1}


def main():
    print(preparar(LIBROS["edward"]))


if __name__ == "__main__":
    main()
