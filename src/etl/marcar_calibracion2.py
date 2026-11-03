import random

from openpyxl import load_workbook

from src.etl.clasificar_places import LIBROS

SEMILLA = 2027
N = 25
RONDA = "calibracion_2"


def elegir(ids_libres):
    return set(random.Random(SEMILLA).sample(sorted(ids_libres), N))


def marcar(rutas):
    libros = [load_workbook(r) for r in rutas]
    cols = []
    for wb in libros:
        ws = wb["revision"]
        cab = [c.value for c in ws[1]]
        cols.append((ws, cab.index("id_revision") + 1, cab.index("ronda") + 1))
    libres = [[ws.cell(r, ci).value for r in range(2, ws.max_row + 1) if not ws.cell(r, cr).value] for ws, ci, cr in cols]
    if any(set(l) != set(libres[0]) for l in libres):
        raise ValueError("los libros no tienen las mismas filas sin ronda")
    elegidas = elegir(libres[0])
    for ws, ci, cr in cols:
        for r in range(2, ws.max_row + 1):
            if ws.cell(r, ci).value in elegidas:
                ws.cell(r, cr).value = RONDA
    for wb, ruta in zip(libros, rutas):
        wb.save(ruta)
    return sorted(elegidas)


def main():
    print(marcar(list(LIBROS.values())))


if __name__ == "__main__":
    main()
