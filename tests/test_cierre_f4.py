import pandas as pd
import pytest

from src.etl.comun import cargar_config, ruta
from src.modelos import cierre_f4

RES = ruta(cargar_config(), "processed") / "resultados_secop"
pytestmark = pytest.mark.skipif(not (RES / "estimador_principal.csv").exists(), reason="resultados de F4 no disponibles")


def documento():
    return cierre_f4.SALIDA.read_text(encoding="utf-8")


def test_documento_coincide_con_la_generacion():
    assert documento() == cierre_f4.construir()


def test_cifras_clave_coinciden_con_los_csv():
    d = documento()
    ep = pd.read_csv(RES / "estimador_principal.csv").set_index("modelo")
    for col in ("estimador", "ic95_bajo", "ic95_alto"):
        assert cierre_f4.mm(ep.loc["tfidf", col]) in d
    mr = pd.read_csv(RES / "mercado_con_y_sin_revision.csv")
    fila = mr[mr["estado"].str.startswith("C") & (mr["modelo"] == "tfidf") & (mr["mixto"] == "sin")].iloc[0]
    assert f"{cierre_f4.mm(fila['valor_mm'] * 1e9)} en {cierre_f4.fm(fila['contratos'], 0)} contratos" in d
    hhi = pd.read_csv(RES / "proveedores_hhi_cr4_anual.csv").set_index("anio")
    assert f"| 2023 | {cierre_f4.fm(hhi.loc[2023, 'proveedores'], 0)} | {cierre_f4.fm(hhi.loc[2023, 'HHI'], 0)} |" in d


def test_cifras_publicadas_de_la_estimacion_principal():
    d = documento()
    assert "**254,0** (IC 95 %: 225,4 a 304,5)" in d
    assert "229,6 en 4.985 contratos" in d
