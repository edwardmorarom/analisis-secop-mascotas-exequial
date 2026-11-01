from openpyxl import Workbook, load_workbook

from src.etl.comun import guardar_libro
from src.modelos import lotes_etiquetado


def libro(valor):
    wb = Workbook()
    wb.active["A1"] = valor
    return wb


def test_no_sobrescribe_un_libro_existente(tmp_path):
    destino = tmp_path / "etiquetado.xlsx"
    assert guardar_libro(libro("original"), destino) is True
    antes = destino.read_bytes()
    assert guardar_libro(libro("nuevo"), destino) is False
    assert destino.read_bytes() == antes
    assert load_workbook(destino).active["A1"].value == "original"


def test_crea_la_carpeta_si_no_existe(tmp_path):
    destino = tmp_path / "nueva" / "lote.xlsx"
    assert guardar_libro(libro("x"), destino) is True
    assert destino.exists()


def test_guardar_de_los_lotes_tambien_protege(tmp_path):
    destino = tmp_path / "lote.xlsx"
    lotes_etiquetado.guardar(libro("original"), destino)
    antes = destino.read_bytes()
    lotes_etiquetado.guardar(libro("otro"), destino)
    assert destino.read_bytes() == antes
