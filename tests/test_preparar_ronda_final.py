import pytest
from openpyxl import Workbook, load_workbook

from src.etl.preparar_ronda_final import HOJA_ORIGINAL, preparar


def libro(ruta):
    wb = Workbook()
    ws = wb.active
    ws.title = "revision"
    ws.append(["id_revision", "ronda", "nombre", "clase", "verificado_en", "nota"])
    for i in range(1, 41):
        ronda = "calibracion" if i <= 10 else "calibracion_2" if i <= 15 else None
        clase = "mixto" if ronda else None
        ws.append([f"L{i:03d}", ronda, f"n{i}", clase, "solo_nombre" if ronda else None, "x" if ronda else None])
    wb.save(ruta)


def test_prepara_sin_tocar_calibracion_2_y_guarda_la_ronda_1(tmp_path):
    ruta = tmp_path / "e.xlsx"
    libro(ruta)
    assert preparar(ruta) == {"final": 35, "ronda1_vaciadas": 10}
    wb = load_workbook(ruta)
    filas = list(wb["revision"].iter_rows(min_row=2, values_only=True))
    assert [f[1] for f in filas].count("final") == 35
    assert all(f[1] == "calibracion_2" and f[3] == "mixto" for f in filas[10:15])
    assert all(f[3] is None for f in filas[:10]) and all(f[4] == "solo_nombre" for f in filas[:10])
    original = list(wb[HOJA_ORIGINAL].iter_rows(min_row=2, values_only=True))
    assert len(original) == 10 and all(o[2] == "mixto" for o in original)


def test_no_se_ejecuta_dos_veces(tmp_path):
    ruta = tmp_path / "e.xlsx"
    libro(ruta)
    preparar(ruta)
    with pytest.raises(ValueError):
        preparar(ruta)
