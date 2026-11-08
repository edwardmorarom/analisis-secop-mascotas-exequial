"""Robustez de «otras causas externas» (D107b): efectos fijos de departamento, control de ruralidad y tasas estandarizadas por edad."""
import re

import geopandas as gpd
import numpy as np
import pandas as pd
import statsmodels.api as sm

from src.etl.comun import cargar_config, ruta
from src.etl.extraer_eevv import GRUPOS_EDAD
from src.modelos.causas_defuncion import ANIOS, CAUSAS, matriz, transversal

CAUSA_FOCO = "otros_accidentes_causas_externas"
LIMITES_EDAD = {"menor_1": (0, 0), "1_4": (1, 4), "5_14": (5, 14), "15_44": (15, 44), "45_64": (45, 64), "65_84": (65, 84), "85_99": (85, 99), "100_mas": (100, 200)}
EDADES = [g for g in GRUPOS_EDAD if g != "desconocida"]
ANIO_ESTANDAR = 2020
ARCHIVO_EDAD = "dane_proyecciones_departamentales_area_sexo_edad_2018_2050.xlsx"
HOJA_EDAD = "PobDepartamentalxÁreaSexoEdad"


def grupo_edad_simple(edad):
    return next(g for g, (a, b) in LIMITES_EDAD.items() if a <= edad <= b)


def poblacion_por_edad(config=None):
    config = config or cargar_config()
    d = pd.read_excel(ruta(config, "raw") / "dane" / ARCHIVO_EDAD, sheet_name=HOJA_EDAD, header=None, dtype=str)
    etiquetas = d.iloc[8]
    cuerpo = d.iloc[9:].copy()
    cuerpo = cuerpo[cuerpo[3].astype(str).str.strip() == "Total"]
    cuerpo = cuerpo[cuerpo[2].astype(int).isin(ANIOS)]
    edades = {}
    for j, e in etiquetas.items():
        m = re.match(r"(Hombres|Mujeres) (\d+)", str(e))
        if m:
            edades[j] = grupo_edad_simple(int(m.group(2)))
    num = cuerpo[list(edades)].apply(pd.to_numeric)
    num.columns = [edades[j] for j in num.columns]
    num = num.T.groupby(level=0).sum().T
    num.insert(0, "cod_dpto", cuerpo[0].astype(str).str.zfill(2).values)
    num.insert(1, "anio", cuerpo[2].astype(int).values)
    return num.melt(id_vars=["cod_dpto", "anio"], var_name="grupo_edad", value_name="poblacion_edad")


def ruralidad(config=None):
    config = config or cargar_config()
    d = pd.read_excel(ruta(config, "raw") / "dane" / "dane_proyecciones_municipales_2018_2042.xlsx", sheet_name="PobMunicipalxÁrea", header=7, dtype=str)
    d = d[d["AÑO"].isin([str(a) for a in ANIOS])]
    d["cod_dpto"] = d["DP"].str.zfill(2)
    d["anio"] = d["AÑO"].astype(int)
    d["valor"] = d["TOTAL"].astype(float)
    area = d["ÁREA GEOGRÁFICA"].str.strip()
    ancho = d.assign(tipo=np.where(area == "Total", "total", np.where(area.str.startswith("Centros"), "rural", "cabecera"))).pivot_table(index=["cod_dpto", "anio"], columns="tipo", values="valor", aggfunc="sum").reset_index()
    ancho["share_rural"] = ancho["rural"] / ancho["total"]
    mgn = gpd.read_file(ruta(config, "raw") / "dane" / "mgn" / "MGN_ADM_MPIO_GRAFICO.shp", ignore_geometry=True)
    km2 = mgn.groupby("dpto_ccdgo")["mpio_narea"].sum().rename("area_km2")
    ancho = ancho.merge(km2, left_on="cod_dpto", right_index=True, how="left", validate="many_to_one")
    ancho["log_densidad"] = np.log(ancho["total"] / ancho["area_km2"])
    return ancho[["cod_dpto", "anio", "share_rural", "area_km2", "log_densidad"]]


def repartir_edad_desconocida(e):
    """Reparte las defunciones de edad desconocida en proporción a la distribución por edad del mismo departamento, año y causa."""
    conocidas = e[e["grupo_edad"] != "desconocida"].copy()
    desconocidas = e[e["grupo_edad"] == "desconocida"].set_index(["anio", "cod_dpto", "grupo_causa"])["defunciones"]
    total = conocidas.groupby(["anio", "cod_dpto", "grupo_causa"])["defunciones"].transform("sum")
    extra = desconocidas.reindex(pd.MultiIndex.from_frame(conocidas[["anio", "cod_dpto", "grupo_causa"]])).fillna(0).to_numpy()
    conocidas["defunciones"] = conocidas["defunciones"] + np.where(total > 0, conocidas["defunciones"] / total.replace(0, np.nan) * extra, 0.0)
    return conocidas


def tasas_estandarizadas(config=None):
    """Tasa directa por 100.000 con población estándar Colombia 2020; ancho como `ancho_tasas`. La COVID-19 (sin edad en el Cuadro 16) queda con su tasa cruda de 2020-2022."""
    config = config or cargar_config()
    e = pd.read_parquet(ruta(config, "interim") / "eevv_defunciones_edad.parquet")
    e = repartir_edad_desconocida(e)
    pe = poblacion_por_edad(config)
    estandar = pe[pe["anio"] == ANIO_ESTANDAR].groupby("grupo_edad")["poblacion_edad"].sum()
    peso = (estandar / estandar.sum()).rename("peso")
    deptos = sorted(pe["cod_dpto"].unique())
    malla = pd.MultiIndex.from_product([deptos, ANIOS, [c for c in CAUSAS if c != "covid19"], EDADES], names=["cod_dpto", "anio", "grupo_causa", "grupo_edad"]).to_frame(index=False)
    m = malla.merge(e, how="left", on=["cod_dpto", "anio", "grupo_causa", "grupo_edad"]).merge(pe, on=["cod_dpto", "anio", "grupo_edad"], how="left", validate="many_to_one")
    m["defunciones"] = m["defunciones"].fillna(0)
    m["componente"] = m["defunciones"] / m["poblacion_edad"] * m["grupo_edad"].map(peso)
    est = m.groupby(["cod_dpto", "anio", "grupo_causa"])["componente"].sum().mul(1e5).unstack("grupo_causa").reset_index()
    crudo = pd.read_csv(ruta(config, "processed") / "resultados_secop" / "causas" / "tasas_dpto_anio.csv", dtype={"cod_dpto": str})
    cv = crudo[crudo["grupo_causa"] == "covid19"][["cod_dpto", "anio", "tasa_100mil"]].rename(columns={"tasa_100mil": "covid19"})
    w = est.merge(cv, on=["cod_dpto", "anio"], how="left")
    w["covid_observado"] = w["covid19"].notna()
    return w[["cod_dpto", "anio", *CAUSAS, "covid_observado"]], peso


def ajustar(panel, causas, extras=(), efectos_departamento=False):
    """NB2 con offset log(población), efectos fijos de año y errores agrupados por departamento; devuelve el modelo y los nombres de las variables de interés."""
    x = matriz(panel, causas)
    for c in extras:
        x[c] = panel[c].to_numpy()
    if efectos_departamento:
        d = pd.get_dummies(panel["cod_dpto"], prefix="dpto", drop_first=True).astype(float).reset_index(drop=True)
        x = pd.concat([x.reset_index(drop=True), d], axis=1)
    y = panel["contratos"].values
    off = np.log(panel["poblacion"].values)
    grupos = pd.factorize(panel["cod_dpto"])[0]
    inicio = np.r_[sm.GLM(y, x, family=sm.families.Poisson(), offset=off).fit().params.values, 0.4]
    nb = sm.NegativeBinomial(y, x, offset=off, loglike_method="nb2").fit(start_params=inicio, method="bfgs", disp=0, maxiter=5000, cov_type="cluster", cov_kwds={"groups": grupos})
    poisson = sm.GLM(y, x, family=sm.families.Poisson(), offset=off).fit(cov_type="cluster", cov_kwds={"groups": grupos})
    return nb, poisson, x


def razon_tasas(modelo, x, variable, por_duplicacion=True):
    i = list(x.columns).index(variable)
    k = np.log(2) if por_duplicacion else 1.0
    ci = modelo.conf_int()
    return {"irr": float(np.exp(modelo.params.iloc[i] * k)), "ic95_inf": float(np.exp(ci.iloc[i, 0] * k)), "ic95_sup": float(np.exp(ci.iloc[i, 1] * k)), "p": float(modelo.pvalues.iloc[i])}


def tabla_robustez(panel_crudo, panel_estandarizado, causa=CAUSA_FOCO):
    """Modelo base, (a) efectos fijos de departamento, (b) control de ruralidad y (c) tasas estandarizadas, para una causa."""
    filas = []

    def agregar(nombre, p, extras=(), fe=False):
        nb, pois, x = ajustar(p, [causa], extras, fe)
        r = razon_tasas(nb, x, causa)
        rp = razon_tasas(pois, x, causa)
        convergio = bool(nb.mle_retvals.get("converged", True))
        fila = {"modelo": nombre, "n": len(p), "alpha": float(nb.params.iloc[-1]), "convergio": convergio, **r, "irr_poisson": rp["irr"], "ic95_inf_poisson": rp["ic95_inf"], "ic95_sup_poisson": rp["ic95_sup"], "p_poisson": rp["p"]}
        for e in extras:
            re_ = razon_tasas(nb, x, e, por_duplicacion=False)
            fila[f"irr_{e}"], fila[f"p_{e}"] = re_["irr"], re_["p"]
        filas.append(fila)

    agregar("base", panel_crudo)
    agregar("a_efectos_fijos_departamento", panel_crudo, fe=True)
    agregar("b_control_ruralidad", panel_crudo, extras=("share_rural", "log_densidad"))
    agregar("c_tasas_estandarizadas", panel_estandarizado)
    t = pd.DataFrame(filas)
    t["supera_regla"] = np.nan
    for modelo in ("b_control_ruralidad", "c_tasas_estandarizadas"):
        f = t["modelo"] == modelo
        t.loc[f, "supera_regla"] = ((t.loc[f, "irr"] > 1) & (t.loc[f, "ic95_inf"] > 1)).astype(float)
    return t


def panel_con_controles(panel, rur):
    return panel.merge(rur, on=["cod_dpto", "anio"], how="left", validate="one_to_one")


def calcular_robustez(r, config=None):
    config = config or cargar_config()
    w_est, peso = tasas_estandarizadas(config)
    contratos = r["contratos"]
    trans = transversal(w_est, contratos)
    panel_est = r["panel"][["cod_dpto", "anio", "contratos", "poblacion"]].merge(w_est, on=["cod_dpto", "anio"], validate="one_to_one")
    panel_crudo = panel_con_controles(r["panel"], ruralidad(config))
    return {"ancho_estandarizado": w_est, "peso_estandar": peso, "transversal": trans, "tabla": tabla_robustez(panel_crudo, panel_est), "panel_controles": panel_crudo}


def guardar_robustez(rb, destino):
    w = rb["ancho_estandarizado"].melt(id_vars=["cod_dpto", "anio", "covid_observado"], var_name="grupo_causa", value_name="tasa_estandarizada_100mil")
    w.loc[(w["grupo_causa"] == "covid19") & ~w["covid_observado"], "tasa_estandarizada_100mil"] = np.nan
    w["tipo_tasa"] = np.where(w["grupo_causa"] == "covid19", "cruda (sin edad en el Cuadro 16)", "estandarizada directa, Colombia 2020")
    w.drop(columns="covid_observado").to_csv(destino / "tasas_estandarizadas_dpto_anio.csv", index=False, encoding="utf-8-sig")
    for k in ("2020_2025", "2020_2024"):
        rb["transversal"][k].to_csv(destino / f"spearman_transversal_estandarizado_{k}.csv", index=False)
    rb["tabla"].to_csv(destino / "robustez_otras_causas_externas.csv", index=False)
    rb["peso_estandar"].to_csv(destino / "poblacion_estandar_colombia_2020_pesos.csv")
