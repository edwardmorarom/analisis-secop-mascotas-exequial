import pandas as pd
import pytest

from src.etl.comun import cargar_config, ruta
from src.modelos.lotes_etiquetado import asignar_proporcional, muestrear
from src.modelos.muestra_secop import reparto


def marco_de_juguete():
    filas = [("A", "secop2", f"a{i}") for i in range(10)] + [("B", "secop2", f"b{i}") for i in range(4)]
    return pd.DataFrame(filas, columns=["subestrato", "fuente", "llave"])


def test_peso_es_N_sobre_n_por_estrato():
    m = muestrear(marco_de_juguete(), {"A": 2, "B": 4}, semilla=2026, prefijo="X")
    pesos = m.groupby("subestrato")["peso"].first()
    assert pesos["A"] == pytest.approx(10 / 2)
    assert pesos["B"] == pytest.approx(4 / 4)
    assert (m["N_estrato"] == m["subestrato"].map({"A": 10, "B": 4})).all()


def test_los_pesos_de_la_muestra_suman_el_marco_si_se_muestrea_cada_estrato():
    m = muestrear(marco_de_juguete(), {"A": 5, "B": 2}, semilla=2026, prefijo="X")
    assert m["peso"].sum() == pytest.approx(len(marco_de_juguete()))


def test_muestreo_reproducible_con_la_misma_semilla():
    a = muestrear(marco_de_juguete(), {"A": 3, "B": 2}, semilla=2026, prefijo="X")
    b = muestrear(marco_de_juguete(), {"A": 3, "B": 2}, semilla=2026, prefijo="X")
    assert a["llave"].tolist() == b["llave"].tolist()


def test_reparto_suma_n():
    celdas = pd.Series({"c1": 7, "c2": 5, "c3": 3})
    assert reparto(celdas, 6).sum() == 6


def test_asignacion_proporcional_respeta_total_y_minimo():
    tamanos = pd.Series({"A1": 250, "A2": 46})
    cuota = asignar_proporcional(tamanos, 40, minimo=10)
    assert cuota.sum() == 40
    assert (cuota >= 10).all()
    assert cuota.to_dict() == {"A1": 30, "A2": 10}


def test_pesos_de_la_muestra_de_400_suman_34790():
    config = cargar_config()
    archivo = ruta(config, "processed") / "muestra_secop_maestra.parquet"
    if not archivo.exists():
        pytest.skip("no hay data/processed")
    m = pd.read_parquet(archivo)
    assert len(m) == 400
    assert m["peso"].sum() == pytest.approx(34790)
