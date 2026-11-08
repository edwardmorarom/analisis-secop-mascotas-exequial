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


INTERIM_EDAD = RAIZ / "data/interim/eevv_defunciones_edad.parquet"


@pytest.mark.skipif(not INTERIM_EDAD.exists(), reason="requiere data/interim/eevv_defunciones_edad.parquet")
def test_defunciones_por_edad_suman_el_total_dane():
    d = pd.read_parquet(INTERIM_EDAD)
    assert d.groupby("anio")["defunciones"].sum().to_dict() == TOTALES_DANE


def test_repartir_edad_desconocida_conserva_el_total():
    from src.modelos.causas_robustez import repartir_edad_desconocida

    e = pd.DataFrame({"anio": 2022, "cod_dpto": "05", "grupo_causa": "circulatorio", "grupo_edad": ["15_44", "45_64", "desconocida"], "defunciones": [10, 30, 4]})
    r = repartir_edad_desconocida(e)
    assert r["defunciones"].sum() == pytest.approx(44) and r.set_index("grupo_edad").loc["45_64", "defunciones"] == pytest.approx(33)


def test_grupos_de_edad_simple_coinciden_con_los_del_cuadro_5():
    from src.modelos.causas_robustez import grupo_edad_simple

    assert [grupo_edad_simple(x) for x in (0, 1, 4, 5, 44, 45, 64, 65, 85, 100, 105)] == ["menor_1", "1_4", "1_4", "5_14", "15_44", "45_64", "45_64", "65_84", "85_99", "100_mas", "100_mas"]


@pytest.mark.skipif(not (RAIZ / "data/raw/dane/dane_proyecciones_departamentales_area_sexo_edad_2018_2050.xlsx").exists(), reason="requiere la proyección departamental por edad")
def test_poblacion_por_edad_suma_la_poblacion_municipal():
    from src.modelos.causas_defuncion import poblacion_departamental
    from src.etl.comun import cargar_config
    from src.modelos.causas_robustez import poblacion_por_edad

    c = cargar_config()
    a = poblacion_por_edad(c).groupby(["cod_dpto", "anio"])["poblacion_edad"].sum().reset_index().merge(poblacion_departamental(c), on=["cod_dpto", "anio"])
    assert len(a) == 198 and (a["poblacion_edad"] - a["poblacion"]).abs().max() < 1


def test_cameron_trivedi_robusto_detecta_sobredispersion_con_pocas_observaciones_grandes():
    rng = np.random.default_rng(3)
    mu = np.r_[np.full(190, 3.0), np.full(8, 150.0)]
    y = rng.negative_binomial(1 / 0.3, 1 / (1 + 0.3 * mu))
    ct = cameron_trivedi(y, mu)
    assert ct["p"] < 0.05 and {"p_homocedastico", "estadistico_t_homocedastico"} <= set(ct)
