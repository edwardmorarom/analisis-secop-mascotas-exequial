import pandas as pd
from openpyxl import load_workbook

from src.etl.clasificar_places import aplicar_reglas, escribir_libro, regla, seleccion


def test_reglas_de_d102():
    assert regla("TRAFUNPET Funeraria y Cremación de mascotas", "pet_care") == ("R1", "prestador_mascotas")
    assert regla("FUNERARIA DE MASCOTAS", "cemetery") == ("R1", "prestador_mascotas")
    assert regla("Fauna Centro Veterinario", "veterinary_care")[0] == "R2"
    assert regla("MascoPlus EPS", "hospital")[0] == "R2"
    assert regla("Funeraria Los Olivos Bucaramanga", "funeral_home") == ("R3", "no_prestador")
    assert regla("Jardines La Colina - Sede Administrativa", None) == ("R4", "revision")


def _tabla(n):
    return pd.DataFrame({
        "place_id": [f"id{i}" for i in range(n)], "nombre": [f"Lugar {i}" for i in range(n)], "direccion": "Calle 1",
        "tipos": [["point_of_interest"]] * n, "tipo_principal": "cemetery", "estado_negocio": "OPERATIONAL",
        "municipio": "IBAGUÉ", "departamento": "TOLIMA"})


def test_seleccion_todos_si_son_300_o_menos_y_muestreo_si_son_mas():
    u = aplicar_reglas(_tabla(300))
    assert seleccion(u, 2026)["incluido"].all()
    mas = aplicar_reglas(_tabla(301))
    s = seleccion(mas, 2026)
    assert s["incluido"].sum() == 60 and s["peso"].iloc[0] == 301 / 60


def test_libro_a_ciegas(tmp_path):
    u = seleccion(aplicar_reglas(_tabla(5)), 2026)
    ids, guardado = escribir_libro(u, 2026, tmp_path / "libro.xlsx")
    assert guardado and len(ids) == 5
    ws = load_workbook(tmp_path / "libro.xlsx")["revision"]
    assert [c.value for c in ws[1]] == ["id_revision", "nombre", "direccion", "municipio", "tipos", "clase"]
    assert all(ws.cell(row=r, column=6).value is None for r in range(2, 7))
    assert "R1" not in str([[c.value for c in f] for f in ws.iter_rows()])
