import pandas as pd

from src.modelos.diagnostico_grupo5 import AFIN, SENAL, plano


def con_senal(texto):
    return bool(SENAL.search(plano(texto)))


def test_senal_funeraria_sin_tildes_y_osario_como_palabra():
    assert con_senal("SUMINISTRO DE ATAÚDES") and con_senal("Servicios Funerarios")
    assert con_senal("PLAN EXEQUIAL") and con_senal("INHUMACIÓN DE CADÁVERES") and con_senal("BÓVEDAS DEL CEMENTERIO")
    assert con_senal("construcción de osarios") and not con_senal("EL ROSARIO ANTIOQUIA")
    assert not con_senal("SUMINISTRO DE KITS ESCOLARES")


def test_palabras_afines_distinguen_servicios_que_la_lista_no_cubre():
    assert AFIN.search(plano("CAJAS MORTUORIAS")) and AFIN.search(plano("HONRAS FÚNEBRES"))
    assert not AFIN.search(plano("ALIMENTOS PARA ADULTOS MAYORES")) and not SENAL.search(plano("CAJAS MORTUORIAS"))
