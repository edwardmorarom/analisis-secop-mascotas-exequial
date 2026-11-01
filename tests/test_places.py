import pandas as pd

from src.etl import places
from src.etl.comun import cargar_config
from src.etl.diagnostico_places import nucleo, parece_persona


def test_muestra_prueba_reproducible_y_estratificada():
    config = cargar_config()
    a = places.muestra_prueba(config, config["seed"])
    b = places.muestra_prueba(config, config["seed"])
    pd.testing.assert_frame_equal(a, b)
    assert a["estrato"].value_counts().to_dict() == {"grande": 3, "mediano": 4, "pequeno": 3}
    assert {"73001", "50001"} <= set(a["cod_divipola"])
    assert a["cod_divipola"].is_unique and a["cod_divipola"].str.len().eq(5).all()


def test_marco_cubre_divipola_y_cuerpo_sin_clave():
    m = places.marco(0.1)
    assert len(m) == 1122 and m[["minx", "miny", "maxx", "maxy"]].notna().all().all()
    assert m.loc[m["sin_poligono"], "cod_divipola"].tolist() == ["27493"]
    c = places.cuerpo("cremación de mascotas", m.iloc[0])
    assert "key" not in str(c).lower() and c["pageSize"] == 20 and "pageToken" not in c
    assert places.cuerpo("x", m.iloc[0], token="t")["pageToken"] == "t"


def test_nombres_genericos_y_personas():
    assert nucleo("Funeraria de Mascotas") == ""
    assert nucleo("Previsan Ltda.") == "PREVISAN"
    assert parece_persona("Juan Perez Gomez")
    assert not parece_persona("Funeraria Los Olivos")
