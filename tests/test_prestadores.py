import pandas as pd

from src.etl.prestadores import COLUMNAS, cruzar, desde_camaras, desde_facebook, desde_places, normalizar, similitud


def places():
    return desde_places(pd.DataFrame({
        "place_id": ["p1", "p2", "p3"], "nombre": ["Funeraria Huellitas S.A.S.", "Pequeñas Almas Colombia", "Funeraria de Mascotas"],
        "cod_divipola": ["73001", "73001", "50001"], "clase": ["prestador_mascotas"] * 3, "verificado_en": ["sitio_web", "google_maps", "solo_nombre"]}))


def facebook():
    return desde_facebook(pd.DataFrame({
        "nombre": ["HUELLITAS Funeraria", "Pequenas Almas", "Funeraria de Mascotas Villavicencio"],
        "cod_divipola": ["73001", "73001", "50001"], "cremacion_individual": [True, False, True]}))


def test_normaliza_sin_tildes_ni_sufijos():
    assert normalizar("Funeraria Huellitas S.A.S.") == "funeraria huellitas"
    assert normalizar("Pequeñas Almas LTDA") == "pequenas almas"


def test_esquema_y_niveles_de_evidencia():
    p = places()
    assert list(p.columns) == COLUMNAS
    assert p["nivel_evidencia"].tolist() == ["sitio_web_verificado", "ficha_google", "ficha_google"]
    assert desde_facebook(pd.DataFrame({"nombre": ["x"], "cod_divipola": ["73001"]}))["nivel_evidencia"].iloc[0] == "solo_red_social"


def test_camaras_excluye_personas_naturales_y_va_como_personas():
    c = desde_camaras(pd.DataFrame({"razon_social": ["Funeraria A", "PN-abc"], "es_persona_natural": [False, True], "cod_divipola": ["73001"] * 2}))
    assert len(c) == 1 and c["ambito"].iloc[0] == "personas" and c["nivel_evidencia"].iloc[0] == "registro_formal"


def test_cruce_por_nombre_y_municipio_con_pares_dudosos():
    seguros, dudosos = cruzar(places(), facebook())
    assert set(seguros["id_a"]) == {"p1"}
    d = dudosos.set_index("id_a")
    assert set(d.index) == {"p2", "p3"} and 75 <= d.loc["p2", "similitud"] < 90 and d.loc["p3", "similitud"] <= 80
    assert d.loc["p3", "cod_divipola"] == "50001"


def test_no_cruza_entre_municipios_ni_por_palabras_genericas():
    a = places().iloc[[0]]
    b = facebook().iloc[[0]].assign(cod_divipola="50001")
    assert cruzar(a, b)[0].empty and cruzar(a, b)[1].empty
    assert similitud(normalizar("Funeraria Los Olivos"), normalizar("Funeraria Mascotas Eternas")) < 75
