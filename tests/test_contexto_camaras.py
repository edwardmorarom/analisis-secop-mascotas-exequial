import pandas as pd

from src.etl.contexto_camaras import AVISO, registros, tabla_municipal


def datos():
    return pd.DataFrame({
        "camara": ["ibague"] * 4, "cod_divipola": ["73001", "73001", "73001", "73861"],
        "razon_social": ["Funeraria A SAS", "PN-abc123", "Funeraria B", "Funeraria C"],
        "es_persona_natural": [False, True, False, False], "organizacion": ["X"] * 4, "nit": ["900", None, "901", "902"],
        "estado_matricula": ["MATRICULA ACTIVA", "MC", "MATRICULA INACTIVA", "INSCRIPCION ACTIVA"],
        "fecha_matricula": ["20040312", "19990101", "20100505", "20200101"],
    })


def test_registros_no_incluyen_nit_y_marcan_activas():
    r = registros(datos())
    assert "nit" not in r.columns and r["aviso"].eq(AVISO).all()
    assert r["matricula_activa"].tolist() == [True, False, False, True] and r["anio_matricula"].tolist() == [2004, 1999, 2010, 2020]
    assert r.loc[r.es_persona_natural, "razon_social"].str.startswith("PN-").all()


def test_tabla_municipal_cuenta_por_camara_y_municipio():
    t = tabla_municipal(registros(datos())).set_index("cod_divipola")
    a = t.loc["73001"]
    assert (a.registros, a.personas_naturales, a.personas_juridicas, a.matriculas_activas, a.estado_codigo_sin_decodificar) == (3, 1, 2, 1, 1)
    assert (a.primera_matricula, a.ultima_matricula) == (1999, 2010) and t.loc["73861", "matriculas_activas"] == 1
