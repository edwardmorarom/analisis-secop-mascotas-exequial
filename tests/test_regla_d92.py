import pandas as pd

from src.modelos.etiquetas_humanas import CORRECCION_D92, CORRECCION_D92_VALIDACION, aplicar_correccion_d92, corregir_validacion_d92
from src.modelos.regla_servicios_profesionales import FUNERARIO, PERSONAL


def lote():
    return pd.DataFrame({"id_muestra": ["H005", "H006", "H009", "H028", "H030", "H031"],
                         "etiqueta": ["mixto", "funerario", "mixto", "mixto", "mixto", "mixto"]})


def test_los_cinco_contratos_de_narino_pasan_a_no_funerario_y_se_conserva_la_etiqueta_del_excel():
    r = aplicar_correccion_d92(lote(), "humanitarios_40")
    d92 = {"H005", "H009", "H028", "H030", "H031"}
    assert CORRECCION_D92["humanitarios_40"] == d92
    assert (r.loc[r["id_muestra"].isin(d92), "etiqueta"] == "no_funerario").all()
    assert r.loc[r["id_muestra"] == "H006", "etiqueta"].iloc[0] == "funerario"
    assert (r.loc[r["id_muestra"].isin(d92), "etiqueta_excel"] == "mixto").all()


def test_la_correccion_no_modifica_el_original_ni_otros_lotes():
    original = lote()
    aplicar_correccion_d92(original, "humanitarios_40")
    assert (original["etiqueta"] == ["mixto", "funerario", "mixto", "mixto", "mixto", "mixto"]).all()
    assert aplicar_correccion_d92(original, "estrato_d_150") is original
    assert aplicar_correccion_d92(None, "humanitarios_40") is None


def test_ssf013_v046_pasa_a_no_funerario_en_la_validacion_de_60():
    e = pd.DataFrame({"etiqueta": ["funerario", "funerario"], "forense": ["0", "0"]}, index=["V045", "V046"])
    r = corregir_validacion_d92(e)
    assert CORRECCION_D92_VALIDACION == {"V046": "no_funerario"}
    assert r.loc["V046", "etiqueta"] == "no_funerario"
    assert r.loc["V045", "etiqueta"] == "funerario"
    assert e.loc["V046", "etiqueta"] == "funerario"


def test_el_patron_de_D92_requiere_personal_y_termino_funerario():
    def patron(texto):
        return bool(PERSONAL.search(texto)) and bool(FUNERARIO.search(texto))
    assert patron("PRESTACION DE SERVICIOS PROFESIONALES PARA APOYAR LA ASISTENCIA FUNERARIA")
    assert patron("APOYO A LA GESTION EN LA SUBDIRECCION DE SERVICIOS FUNERARIOS")
    assert not patron("SUMINISTRO DE COFRES PARA LA INHUMACION DE PERSONAS POBRES")
    assert not patron("PRESTACION DE SERVICIOS PROFESIONALES EN ARQUITECTURA")
