import pandas as pd
import pytest

from src.modelos.oferta_municipal import contar, tabla_oferta


def prestadores():
    return pd.DataFrame({
        "id_fuente": ["a", "b", "c", "d", "d2", "e"], "cod_divipola": ["00001", "00001", "00001", "00002", "00002", "00001"],
        "clase": ["prestador_mascotas", "mixto", "no_prestador", "prestador_mascotas", "prestador_mascotas", "prestador_mascotas"],
        "ambito": ["mascotas", "mascotas", "mascotas", "mascotas", "mascotas", "personas"]})


def panel():
    return pd.DataFrame({
        "cod_divipola": ["00001", "00002", "00003", "00001"], "anio": [2024, 2024, 2024, 2023],
        "pob_dane": [200_000.0, 50_000.0, 10_000.0, 1.0], "vacunados_perros": [40_000.0, 0.0, 500.0, 1.0]})


def test_cuenta_con_y_sin_mixtos_y_excluye_personas():
    c = contar(prestadores())
    assert c.loc["00001"].tolist() == [1, 2] and c.loc["00002"].tolist() == [2, 2]


def test_tabla_por_cien_mil_con_datos_sinteticos():
    t = tabla_oferta(prestadores(), panel(), 2024).set_index("cod_divipola")
    assert t.loc["00001", "por_100mil_hab_sin_mixto"] == pytest.approx(0.5)
    assert t.loc["00001", "por_100mil_hab_con_mixto"] == pytest.approx(1.0)
    assert t.loc["00001", "por_100mil_perros_vacunados_con_mixto"] == pytest.approx(5.0)
    assert t.loc["00002", "por_100mil_hab_sin_mixto"] == pytest.approx(4.0) and pd.isna(t.loc["00002", "por_100mil_perros_vacunados_sin_mixto"])
    assert t.loc["00003", "prestadores_con_mixto"] == 0 and t.loc["00003", "por_100mil_hab_con_mixto"] == 0
    assert len(t) == 3 and (t["anio"] == 2024).all()
