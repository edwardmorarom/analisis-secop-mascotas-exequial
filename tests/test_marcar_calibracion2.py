from openpyxl import Workbook, load_workbook

from src.etl.marcar_calibracion2 import N, RONDA, marcar


def libro(ruta, etiquetas):
    wb = Workbook()
    ws = wb.active
    ws.title = "revision"
    ws.append(["id_revision", "ronda", "clase"])
    for i in range(1, 56):
        ws.append([f"L{i:03d}", "calibracion" if i <= 25 else None, etiquetas.get(i)])
    wb.save(ruta)


def test_marca_las_mismas_filas_en_ambos_libros_sin_tocar_etiquetas(tmp_path):
    a, b = tmp_path / "a.xlsx", tmp_path / "b.xlsx"
    libro(a, {1: "mixto"})
    libro(b, {1: "no_prestador"})
    elegidas = marcar([a, b])
    assert len(elegidas) == N and all(int(i[1:]) > 25 for i in elegidas)
    for ruta, clase in ((a, "mixto"), (b, "no_prestador")):
        ws = load_workbook(ruta)["revision"]
        filas = list(ws.iter_rows(min_row=2, values_only=True))
        assert sorted(f[0] for f in filas if f[1] == RONDA) == elegidas
        assert sum(f[1] == "calibracion" for f in filas) == 25
        assert filas[0][2] == clase
