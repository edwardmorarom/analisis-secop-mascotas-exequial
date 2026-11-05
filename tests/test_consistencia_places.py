import pytest
from openpyxl import Workbook, load_workbook

from src.evaluacion.consistencia_places import COLUMNAS, N, comparar_consistencia, preparar

CLASES = ["prestador_mascotas", "no_prestador", "mixto", "no_determinable"]


def libro(ruta, n=60, vacias=0):
    wb = Workbook()
    ws = wb.active
    ws.title = "revision"
    ws.append(COLUMNAS)
    for i in range(1, n + 1):
        clase = None if i <= vacias else CLASES[i % 4]
        ws.append([f"L{i:03d}", "final", f"n{i}", "d", "m", "t", clase, "google_maps", "nota"])
    wb.save(ruta)


def test_prepara_25_filas_sin_etiquetas_y_reproducibles(tmp_path):
    libro(tmp_path / "e.xlsx")
    ids = preparar(tmp_path / "e.xlsx", tmp_path / "c.xlsx")
    assert len(ids) == N and ids == preparar(tmp_path / "e.xlsx", tmp_path / "c2.xlsx")
    filas = list(load_workbook(tmp_path / "c.xlsx")["revision"].iter_rows(min_row=2, values_only=True))
    assert sorted(f[0] for f in filas) == ids
    assert all(f[6] is None and f[7] is None and f[8] is None for f in filas)


def test_exige_la_ronda_final_completa(tmp_path):
    libro(tmp_path / "e.xlsx", vacias=3)
    with pytest.raises(ValueError):
        preparar(tmp_path / "e.xlsx", tmp_path / "c.xlsx")


def test_kappa_es_uno_si_repite_las_mismas_clases(tmp_path):
    libro(tmp_path / "e.xlsx")
    preparar(tmp_path / "e.xlsx", tmp_path / "c.xlsx")
    wb = load_workbook(tmp_path / "c.xlsx")
    ws = wb["revision"]
    for r in range(2, ws.max_row + 1):
        ws.cell(r, 7).value = CLASES[int(ws.cell(r, 1).value[1:]) % 4]
        ws.cell(r, 8).value = "google_maps"
    wb.save(tmp_path / "c.xlsx")
    r = comparar_consistencia(tmp_path / "e.xlsx", tmp_path / "c.xlsx")
    assert r["n"] == N and r["kappa"] == pytest.approx(1.0)
