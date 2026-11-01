import numpy as np
import pandas as pd
import pytest

from src.modelos import estimador_diferencia as ed


def juguete():
    """Dos estratos. Corrección calculada a mano (pesos × (y − ŷ) × valor):
    S1 (peso 10): 0 + 10·50 − 10·30 = 200;  S2 (peso 4): 0 + 4·10 = 40, y un mixto predicho funerario de valor 20: −4·20 = −80 sin mixto, 0 con mixto."""
    filas = [
        ("S1", 10, "funerario", "funerario", 100),
        ("S1", 10, "funerario", "no_funerario", 50),
        ("S1", 10, "no_funerario", "funerario", 30),
        ("S2", 4, "no_funerario", "no_funerario", 20),
        ("S2", 4, "funerario", "no_funerario", 10),
        ("S2", 4, "mixto", "funerario", 20),
    ]
    d = pd.DataFrame(filas, columns=["estrato", "peso", "etiqueta", "pred_tfidf_modelo", "valor_constante_2025"])
    d["pred_e5_modelo"] = d["pred_tfidf_modelo"]
    return d


def test_correccion_a_mano_sin_mixto():
    assert ed.correccion(juguete(), "tfidf", con_mixto=False) == pytest.approx(200 + 40 - 80)


def test_correccion_a_mano_con_mixto():
    assert ed.correccion(juguete(), "tfidf", con_mixto=True) == pytest.approx(200 + 40 + 0)


def test_estimador_es_total_del_modelo_mas_correccion():
    d = juguete()
    universo_modelo = 1000.0
    assert universo_modelo + ed.correccion(d, "tfidf", False) == pytest.approx(1160.0)


def test_indicador_de_clase():
    s = pd.Series(["funerario", "mixto", "no_funerario"])
    assert ed.indicador(s, False).tolist() == [1.0, 0.0, 0.0]
    assert ed.indicador(s, True).tolist() == [1.0, 1.0, 0.0]


def test_bootstrap_degenerado_si_los_terminos_de_cada_estrato_son_iguales(monkeypatch):
    monkeypatch.setattr(ed, "REPETICIONES", 25)
    filas = [("S1", 2, "funerario", "no_funerario", 7)] * 3 + [("S2", 5, "no_funerario", "funerario", 3)] * 2
    d = pd.DataFrame(filas, columns=["estrato", "peso", "etiqueta", "pred_tfidf_modelo", "valor_constante_2025"])
    d["pred_e5_modelo"] = d["pred_tfidf_modelo"]
    esperado = 3 * 2 * 7 - 2 * 5 * 3
    salida = ed.bootstrap(d, "tfidf", False, np.random.default_rng(2026))
    assert ed.correccion(d, "tfidf", False) == pytest.approx(esperado)
    assert salida == pytest.approx(np.full(25, esperado))


def test_bootstrap_es_reproducible_con_la_semilla(monkeypatch):
    monkeypatch.setattr(ed, "REPETICIONES", 30)
    a = ed.bootstrap(juguete(), "tfidf", False, np.random.default_rng(2026))
    b = ed.bootstrap(juguete(), "tfidf", False, np.random.default_rng(2026))
    assert (a == b).all()
