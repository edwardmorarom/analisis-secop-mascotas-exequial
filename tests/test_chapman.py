import pytest

from src.modelos.chapman import bootstrap, chapman, estimar


def test_chapman_calculado_a_mano():
    # n1=60, n2=50, m=20: N = 61·51/21 − 1 = 3111/21 − 1 = 147,142857
    # Var = 61·51·40·30 / (21²·22) = 3.733.200 / 9.702 = 384,7866; ee = 19,6159; mitad = 1,96·ee = 38,4472
    r = chapman(60, 50, 20)
    assert r["estimado"] == pytest.approx(147.142857, abs=1e-6)
    assert r["varianza"] == pytest.approx(384.7866, abs=1e-3)
    assert (r["ic_inf"], r["ic_sup"]) == pytest.approx((108.6957, 185.5900), abs=1e-2)


def test_limite_inferior_es_lo_ya_observado():
    # n1=10, n2=8, m=4: N = 11·9/5 − 1 = 18,8; Var = 11·9·6·4 / (25·6) = 15,84; mitad = 7,8005 → 11,0 < 14 observados
    r = chapman(10, 8, 4)
    assert r["estimado"] == pytest.approx(18.8) and r["varianza"] == pytest.approx(15.84)
    assert r["observados"] == 14 and r["ic_inf"] == 14 and r["ic_sup"] == pytest.approx(18.8 + 1.96 * 15.84 ** 0.5)


def test_sin_recapturas_y_captura_completa():
    assert chapman(10, 10, 0)["estimado"] == pytest.approx(120.0)
    r = chapman(10, 10, 10)
    assert r["estimado"] == pytest.approx(10.0) and r["varianza"] == 0


def test_valores_invalidos():
    with pytest.raises(ValueError):
        chapman(10, 5, 6)


def test_bootstrap_solo_con_pocos_pares_y_reproducible():
    assert "bootstrap_inf" in estimar(10, 8, 4) and "bootstrap_inf" not in estimar(60, 50, 20)
    inf, sup = bootstrap(10, 8, 4)
    assert (inf, sup) == bootstrap(10, 8, 4) and inf < 18.8 < sup
