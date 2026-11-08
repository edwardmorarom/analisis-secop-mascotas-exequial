import numpy as np
import pandas as pd
import pytest
from scipy import stats

from src.etl.comun import RAIZ
from src.etl.extraer_eevv import bloques_cuadro5, codigo_dpto, grupo_de
from src.modelos.causas_defuncion import cameron_trivedi, eliminar_por_vif, fisher_ic, irr, residuos_cuantilicos

TOTALES_DANE = {2020: 300853, 2021: 363089, 2022: 287251, 2023: 268411, 2024: 275778, 2025: 284254}
INTERIM = RAIZ / "data/interim/eevv_defunciones.parquet"


@pytest.mark.skipif(not INTERIM.exists(), reason="requiere data/interim/eevv_defunciones.parquet (python -m src.etl.extraer_eevv)")
def test_totales_nacionales_cuadran_con_el_dane():
    d = pd.read_parquet(INTERIM)
    suma = d.groupby("anio")["defunciones"].sum()
    assert suma.to_dict() == TOTALES_DANE
    assert set(d["grupo_causa"]) == {"agresiones_homicidios", "accidentes_transporte", "otros_accidentes_causas_externas", "covid19", "circulatorio", "neoplasias", "demas_causas"}
    assert d.loc[d["anio"] >= 2023, "grupo_causa"].ne("covid19").all()


@pytest.mark.skipif(not INTERIM.exists(), reason="requiere data/interim/eevv_defunciones.parquet")
def test_departamentos_coinciden_con_divipola():
    from src.etl.extraer_eevv import nombres_divipola

    d = pd.read_parquet(INTERIM)
    assert set(d["cod_dpto"]) - set(nombres_divipola().index) == {"01", "75"}


def test_grupos_por_codigo_de_la_lista_6_67():
    assert grupo_de(512) == "agresiones_homicidios" and grupo_de(501) == "accidentes_transporte" and grupo_de(502) == "otros_accidentes_causas_externas"
    assert grupo_de(303) == "circulatorio" and grupo_de(215) == "neoplasias" and grupo_de(109) == "demas_causas" and grupo_de(0) == "demas_causas"


def test_codigo_dpto_toma_el_codigo_de_la_etiqueta():
    assert codigo_dpto(5.0, "05 Antioquia") == "05" and codigo_dpto(3.0, "Total Nacional") == "03"


def test_bloques_cuadro5_ignora_municipios_y_suma_cuadra():
    f = [[5.0, np.nan, np.nan, np.nan, "Total", 10], [5.0, np.nan, np.nan, np.nan, "512 Agresiones", 4], [5.0, np.nan, np.nan, np.nan, "303 Isquemicas", 6],
         [5.0, np.nan, np.nan, "Medellín", "Total", 99], [5.0, np.nan, np.nan, np.nan, "512 Agresiones", 99],
         [8.0, np.nan, "08 Atlántico", np.nan, "Total", 3], [8.0, np.nan, np.nan, np.nan, "512 Agresiones", 3]]
    d = pd.DataFrame(f)
    d[2] = d[2].astype(object)
    d.loc[0, 2] = "05 Antioquia"
    filas = list(bloques_cuadro5(d))
    assert [(c, causa, n) for c, causa, n, _ in filas] == [("05", "TOTAL", 10), ("05", 512, 4), ("05", 303, 6), ("08", "TOTAL", 3), ("08", 512, 3)]


def test_fisher_ic_contiene_rho():
    lo, hi = fisher_ic(0.5, 33)
    assert lo < 0.5 < hi


def test_cameron_trivedi_detecta_sobredispersion_y_no_en_poisson():
    rng = np.random.default_rng(1)
    mu = np.full(400, 10.0)
    assert cameron_trivedi(rng.poisson(mu), mu)["p"] > 0.01
    assert cameron_trivedi(rng.negative_binomial(2, 2 / (2 + 10), 400), mu)["p"] < 0.001


def test_residuos_cuantilicos_son_normales_si_el_modelo_es_correcto():
    rng = np.random.default_rng(2)
    mu = rng.uniform(5, 40, 3000)
    alpha = 0.4
    y = rng.negative_binomial(1 / alpha, 1 / (1 + alpha * mu))
    r = residuos_cuantilicos(y, mu, alpha)
    assert abs(r.mean()) < 0.06 and abs(r.std() - 1) < 0.06 and abs(stats.skew(r)) < 0.15


def test_eliminar_por_vif_quita_la_variable_colineal():
    rng = np.random.default_rng(3)
    a = rng.normal(size=200)
    x = pd.DataFrame({"a": a, "b": a + rng.normal(scale=0.05, size=200), "c": rng.normal(size=200)})
    final, quitadas, v = eliminar_por_vif(x)
    assert len(quitadas) == 1 and quitadas[0][0] in ("a", "b") and (v < 5).all()


def test_irr_por_duplicacion_es_exp_beta_ln2():
    class Falso:
        params = pd.Series([0.1, 0.5, 0.3])
        bse = pd.Series([0.1, 0.1, 0.1])
        pvalues = pd.Series([0.5, 0.01, 0.2])

        @staticmethod
        def conf_int():
            return pd.DataFrame([[0, 0.2], [0.3, 0.7], [0.1, 0.5]])

    x = pd.DataFrame(columns=["const", "causa", "anio_2021"])
    t = irr(Falso, x, ["causa"])
    assert t.loc[0, "irr_por_duplicacion"] == pytest.approx(2 ** 0.5) and t.loc[0, "ic95_inf"] == pytest.approx(2 ** 0.3)
