import pandas as pd
import pytest
from openpyxl import load_workbook

from src.etl.clasificar_places import aplicar_reglas, escribir_libro, seleccion
from src.etl.guia_places_docx import convertir
from src.evaluacion.kappa_places import comparar, leer


def libro(tmp_path, nombre, clases):
    u = pd.DataFrame({
        "place_id": [f"id{i}" for i in range(30)], "nombre": [f"Lugar {i}" for i in range(30)], "direccion": "Calle 1",
        "tipos": [["point_of_interest"]] * 30, "tipo_principal": "cemetery", "estado_negocio": "OPERATIONAL",
        "municipio": "IBAGUÉ", "departamento": "TOLIMA"})
    escribir_libro(seleccion(aplicar_reglas(u), 2026), 2026, tmp_path / nombre)
    wb = load_workbook(tmp_path / nombre)
    ws = wb["revision"]
    for i, c in enumerate(clases):
        ws.cell(row=i + 2, column=7, value=c)
    wb.save(tmp_path / nombre)
    return tmp_path / nombre


def test_kappa_solo_filas_de_calibracion_y_desacuerdos(tmp_path):
    base = ["prestador_mascotas", "no_prestador", "mixto", "no_determinable", "no_prestador"] * 5
    otra = list(base)
    otra[0], otra[1] = "no_prestador", "mixto"
    r = comparar(leer(libro(tmp_path, "a.xlsx", base)), leer(libro(tmp_path, "b.xlsx", otra)))
    assert r["n"] == 25 and len(r["desacuerdos"]) == 2 and r["acuerdo"] == pytest.approx(23 / 25)
    assert 0.5 < r["kappa"] < 1
    assert comparar(leer(libro(tmp_path, "c.xlsx", base)), leer(libro(tmp_path, "d.xlsx", base)))["kappa"] == 1


def test_entrega_incompleta_o_invalida_falla(tmp_path):
    ok = ["no_prestador"] * 25
    with pytest.raises(ValueError):
        comparar(leer(libro(tmp_path, "a.xlsx", ok)), leer(libro(tmp_path, "b.xlsx", ok[:24])))
    with pytest.raises(ValueError):
        comparar(leer(libro(tmp_path, "c.xlsx", ok)), leer(libro(tmp_path, "d.xlsx", ["otra"] + ok[1:])))


def test_guia_docx_conserva_tablas_y_titulos():
    doc = convertir("# Título\n\n## Sección\n\ntexto con **negrita**\n\n| a | b |\n|---|---|\n| 1 | `2` |\n")
    assert len(doc.tables) == 1 and doc.tables[0].cell(1, 1).text == "2"
    assert any(p.text == "Título" for p in doc.paragraphs)
