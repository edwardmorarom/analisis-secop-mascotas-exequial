import numpy as np
import pandas as pd
import pytest

from src.modelos.validacion_grupos import (agrupar_cochran, chi2_v, clave, CODIGOS_DEPARTAMENTO, concentracion, dunn, lectura_epsilon, lectura_v,
                                           mejor_emparejamiento, residuos, tendencia_ca)


def test_cramer_de_asociacion_perfecta_y_nula():
    perfecta = pd.DataFrame([[10, 0], [0, 10]])
    assert chi2_v(perfecta)["V"] == pytest.approx(1.0)
    nula = pd.DataFrame([[10, 20], [5, 10]])
    assert chi2_v(nula)["V"] == pytest.approx(0.0, abs=1e-12)


def test_lecturas():
    assert [lectura_v(x) for x in (0.05, 0.2, 0.4, 0.6)] == ["despreciable", "pequeña", "mediana", "grande"]
    assert lectura_epsilon(0.143) == "moderado"


def test_residuos_ajustados_de_tabla_con_calculo_a_mano():
    t = pd.DataFrame([[30, 10], [10, 30]])
    r = residuos(t)
    assert r.iloc[0, 0] == pytest.approx((30 - 20) / np.sqrt(20 * 0.5 * 0.5))
    assert r.iloc[0, 1] == pytest.approx(-r.iloc[0, 0])


def test_tendencia_cochran_armitage_a_mano():
    z, p = tendencia_ca([1, 2, 3], [10, 10, 10])
    assert z ** 2 == pytest.approx(1.25)
    assert 0 < p < 1


def test_dunn_con_dos_grupos_y_holm():
    t = dunn([1, 2, 3, 4], ["a", "a", "b", "b"])
    assert t.loc[0, "z"] == pytest.approx((1.5 - 3.5) / np.sqrt(4 * 5 / 12 * (1 / 2 + 1 / 2)))
    assert t.loc[0, "p_holm"] == pytest.approx(t.loc[0, "p"])


def test_concentracion_hhi_y_cr4():
    hhi, cr4 = concentracion(pd.Series([1, 1, 1, 1]))
    assert hhi == pytest.approx(2500) and cr4 == pytest.approx(100)
    hhi, cr4 = concentracion(pd.Series([97, 1, 1, 1, 0.5, 0.5]))
    assert cr4 == pytest.approx(100 * 100 / 101, rel=1e-6)


def test_agrupar_cochran_junta_columnas_pequenas():
    t = pd.DataFrame({"A": [50, 50], "B": [40, 45], "C": [1, 0], "D": [0, 1]}, index=["g1", "g2"])
    a = agrupar_cochran(t)
    assert "Otros" in a.columns and a.values.sum() == t.values.sum()
    esp = pd.DataFrame(chi2_v(a)["esperada"])
    assert (esp >= 1).all().all()


def test_mejor_emparejamiento():
    ref = np.array([1, 1, 1, 2, 2, 3])
    nuevo = np.array([7, 7, 8, 9, 9, 9])
    m = mejor_emparejamiento(ref, nuevo, 1)
    assert m["grupo_nuevo"] == 7 and m["jaccard"] == pytest.approx(2 / 3)


def test_claves_de_departamento_con_caracteres_dañados():
    assert CODIGOS_DEPARTAMENTO[clave("Nari\ufffdo")] == "52"
    assert CODIGOS_DEPARTAMENTO[clave("Distrito Capital de Bogot\ufffd")] == "11"
    assert clave("Norte De Santander") == clave("Norte de Santander")
