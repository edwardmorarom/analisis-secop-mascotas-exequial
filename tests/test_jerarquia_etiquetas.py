import pandas as pd
import pytest

from src.modelos.etiquetas_humanas import ORDEN_PRECEDENCIA, fusionar


def parte(origen, filas):
    return pd.DataFrame(filas, columns=["fuente", "llave", "etiqueta", "forense"]).assign(origen=origen)


def etiqueta_de(todo, llave):
    return todo.loc[todo["llave"] == llave, "etiqueta"].iloc[0]


def test_la_jerarquia_es_la_de_D84():
    assert ORDEN_PRECEDENCIA[0] == "top_valor"
    assert ORDEN_PRECEDENCIA[-1] == "muestra_400"
    assert ORDEN_PRECEDENCIA.index("humanitarios_40") < ORDEN_PRECEDENCIA.index("validacion_60_revisada") < ORDEN_PRECEDENCIA.index("muestra_400")


def test_manda_la_fuente_de_mayor_precedencia():
    todo = fusionar([
        parte("muestra_400", [("secop2", "X", "funerario", 0), ("secop2", "Y", "funerario", 0)]),
        parte("validacion_60_revisada", [("secop2", "X", "no_funerario", 0)]),
        parte("top_valor", [("secop2", "X", "mixto", 0)]),
        parte("humanitarios_40", [("secop2", "Y", "no_funerario", 0)]),
    ])
    assert len(todo) == 2
    assert etiqueta_de(todo, "X") == "mixto"
    assert etiqueta_de(todo, "Y") == "no_funerario"


def test_cuenta_los_conflictos_entre_etiquetas():
    todo = fusionar([
        parte("muestra_400", [("secop2", "X", "funerario", 0), ("secop2", "Z", "funerario", 0)]),
        parte("validacion_60_revisada", [("secop2", "X", "no_funerario", 0), ("secop2", "Z", "funerario", 0)]),
    ])
    assert todo.attrs["conflictos"] == 1


def test_un_contrato_en_otra_fuente_no_se_mezcla():
    todo = fusionar([parte("muestra_400", [("secop1", "X", "funerario", 0), ("secop2", "X", "no_funerario", 0)])])
    assert len(todo) == 2


def test_normaliza_mayusculas_y_espacios_y_rechaza_etiquetas_invalidas():
    todo = fusionar([parte("muestra_400", [("secop2", "X", " Funerario ", 0)])])
    assert etiqueta_de(todo, "X") == "funerario"
    with pytest.raises(AssertionError):
        fusionar([parte("muestra_400", [("secop2", "X", "otra", 0)])])
