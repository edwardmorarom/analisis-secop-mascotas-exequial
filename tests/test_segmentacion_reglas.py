import numpy as np
import pandas as pd
import pytest

from src.etl.comun import RAIZ
from src.modelos import segmentacion_reglas as sr

DATOS = RAIZ / "data/processed/resultados_secop/universo_mercado.parquet"
requiere_datos = pytest.mark.skipif(not DATOS.exists(), reason="requiere data/processed/resultados_secop/universo_mercado.parquet")


@pytest.fixture(scope="module")
def datos():
    return sr.cargar_datos()


def marco(**kw):
    base = {"tipo_entidad": "alcaldia_municipio", "orden_nivel": "TERRITORIAL", "plan_exequial": 0, "ataudes_bienes": 0, "inhumacion_cremacion": 0, "traslado": 0}
    return pd.DataFrame([base | k for k in kw["filas"]])


def test_prioridad_del_objeto_y_permutaciones():
    d = marco(filas=[{"plan_exequial": 1, "inhumacion_cremacion": 1}, {"ataudes_bienes": 1}, {"ataudes_bienes": 1, "inhumacion_cremacion": 1}, {"traslado": 1, "inhumacion_cremacion": 1}, {}])
    assert list(sr.objeto(d)) == ["Plan exequial", "Ataúdes y bienes", "Servicio de inhumación", "Traslado", "Otro"]
    assert list(sr.objeto(d, ("servicio", "traslado", "bienes", "plan")))[:1] == ["Servicio de inhumación"]


def test_comprador_reglas():
    d = marco(filas=[{}, {"tipo_entidad": "gobernacion_departamento"}, {"tipo_entidad": "salud_hospital_ese"}, {"tipo_entidad": "servicios_publicos_empresa"},
                     {"tipo_entidad": "otra_entidad", "orden_nivel": "NACIONAL"}, {"tipo_entidad": "otra_entidad"}, {"tipo_entidad": "otras", "orden_nivel": "otras"}])
    assert list(sr.comprador(d)) == ["Alcaldía", "Gobernación", "Hospital", "Servicios públicos", "Nacional", "Otra", "Otra"]


@requiere_datos
def test_cada_contrato_en_un_unico_segmento_y_totales_cuadran(datos):
    v = datos[datos["vigente"]]
    assert len(datos) == 4992 and len(v) == 4985
    assert datos["segmento_completo"].notna().all() and set(datos["objeto"]) <= set(sr.NOMBRE_OBJETO.values()) | {sr.OTRO_OBJETO}
    pequenos = sr.segmentos_pequenos(v["segmento_completo"])
    seg = sr.agrupar_pequenos(v["segmento_completo"], pequenos)
    assert seg.value_counts().sum() == 4985 and (seg.value_counts().drop(sr.OTROS_SEGMENTOS, errors="ignore") >= 0.01 * 4985).all()
    u = pd.read_parquet(DATOS, columns=["clase_final", "valor_constante_2025"])
    assert v["valor"].sum() == pytest.approx(u.loc[u["clase_final"] == "funerario", "valor_constante_2025"].sum())
    assert sr.resumen(v, "comprador")["contratos"].sum() == 4985


@requiere_datos
def test_bootstrap_reproducible_con_la_semilla(datos):
    v = datos[datos["vigente"]].head(800).copy()
    cats = {"comprador": sr.COMPRADORES}
    a = sr.bootstrap_entidades(v, cats, replicas=30, semilla=sr.SEMILLA)["comprador"]
    b = sr.bootstrap_entidades(v, cats, replicas=30, semilla=sr.SEMILLA)["comprador"]
    c = sr.bootstrap_entidades(v, cats, replicas=30, semilla=7)["comprador"]
    pd.testing.assert_frame_equal(a, b)
    assert not np.allclose(a["pct_valor_ic_inf"].fillna(0), c["pct_valor_ic_inf"].fillna(0))
