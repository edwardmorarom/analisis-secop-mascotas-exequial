"""Arma docs/resultados/patrones_compra.md con las tablas y la aplicación de la regla de D97."""
import json

import numpy as np
import pandas as pd

from src.etl.comun import RAIZ
from src.modelos.patrones_lca import MODELOS, salida
from src.modelos.perfil_variables import coma, tabla

DESTINO = RAIZ / "docs" / "resultados" / "patrones_compra.md"
GRAFICOS = "graficos/patrones"
SI, NO = "sí", "no"


def f(v, d=1):
    return coma(v, d)


def leer(nombre):
    return pd.read_csv(salida() / nombre)


def regla(df, falla):
    """Aplica la regla de D97: descarta los que fallan; entre los que pasan, menor BIC y, con ΔBIC < 2, el de menos parámetros."""
    pasan = df[~falla]
    if pasan.empty:
        return None
    mejor = pasan["BIC"].min()
    return pasan[pasan["BIC"] - mejor < 2].sort_values("parametros").iloc[0]


def seccion_lca():
    t = leer("lca_comparacion.csv")
    t["dBIC"] = t["BIC"] - t["BIC"].min()
    boot = {}
    for r in t.itertuples():
        p = salida() / f"lca_estabilidad_m{r.modelo}_k{r.clases}.json"
        boot[(r.modelo, r.clases)] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
    t["falla_bvr"] = t["bvr_maximo"] > 10
    t["falla_identificabilidad"] = t["arranques_con_el_maximo"] < 3
    t["falla_tamano"] = t["tamano_minimo_pct"] < 1
    t["jaccard_min"] = [boot[(m, k)]["jaccard_minimo_medio"] if boot[(m, k)] else np.nan for m, k in zip(t["modelo"], t["clases"])]
    t["falla_estabilidad"] = t["jaccard_min"] < 0.60
    t["falla_sin_bootstrap"] = t["falla_bvr"] | t["falla_identificabilidad"] | t["falla_tamano"]
    t["falla_alguna"] = t["falla_sin_bootstrap"] | t["falla_estabilidad"].fillna(False)
    elegido = regla(t, t["falla_alguna"])
    vista = pd.DataFrame({"covariables": t["covariables"], "clases": t["clases"], "parámetros": t["parametros"], "logLik": t["logLik"].map(lambda v: f(v, 0)),
                          "BIC": t["BIC"].map(lambda v: f(v, 1)), "ΔBIC": t["dBIC"].map(lambda v: f(v, 1)), "AIC": t["AIC"].map(lambda v: f(v, 1)),
                          "entropía relativa": t["entropia_relativa"].map(lambda v: f(v, 2)), "arranques con el máximo (de 20)": t["arranques_con_el_maximo"],
                          "clase más pequeña (%)": t["tamano_minimo_pct"].map(lambda v: f(v, 1)), "BVR máximo": t["bvr_maximo"].map(lambda v: f(v, 1)),
                          "pares con BVR > 10": t["pares_bvr_mayor_10"],
                          "Jaccard mínimo (bootstrap)": t["jaccard_min"].map(lambda v: "no evaluado" if pd.isna(v) else f(v, 2)),
                          "supuestos que falla": t.apply(lambda r: ", ".join(n for n, x in (("independencia local", r.falla_bvr), ("identificabilidad", r.falla_identificabilidad),
                                                                                         ("tamaño de clase", r.falla_tamano), ("estabilidad", r.falla_estabilidad is True)) if x) or "ninguno", axis=1)})
    return t, boot, elegido, vista


def resumen_minimo_bic(t):
    return t.sort_values("BIC").iloc[0]


def md():
    t, boot, elegido, vista = seccion_lca()
    minb = resumen_minimo_bic(t)
    m, k = int(minb["modelo"]), int(minb["clases"])
    tam = leer(f"lca_tamanos_m{m}_k{k}.csv")
    perf = leer(f"lca_perfiles_m{m}_k{k}.csv")
    bvr = leer(f"lca_bvr_m{m}_k{k}.csv")
    hc = json.loads((salida() / "lca_vs_hcpc.json").read_text(encoding="utf-8"))
    cruce = pd.read_csv(salida() / "lca_vs_hcpc_cruce.csv")
    inercia = leer("acm_inercia.csv")
    b = boot[(m, k)]
    vb = leer("valor_bic.csv"); vd = leer("valor_diagnosticos.csv"); vi = leer("valor_icc.csv"); vc = leer("valor_validacion_cruzada.csv")
    vco = leer("valor_coeficientes_mixto.csv")
    notas = dict(l.split(": ", 1) for l in (salida() / "valor_notas.txt").read_text(encoding="utf-8").splitlines() if ": " in l)
    eb = leer("estacionalidad_bic.csv"); ed = leer("estacionalidad_diagnosticos.csv"); ect = leer("estacionalidad_cameron_trivedi.csv")
    ea = leer("estacionalidad_efecto_anio.csv"); es = leer("estacionalidad_sensibilidad_2020.csv"); ep = leer("estacionalidad_perfil_mensual.csv")
    th = leer("estacionalidad_theta.csv"); serie = leer("estacionalidad_serie.csv")

    vb["ΔBIC"] = vb["BIC"] - vb["BIC"].min()
    vv = vb.merge(vd[["modelo", "falla_normalidad", "falla_varianza", "falla_cook", "falla_colinealidad", "falla_alguna"]], on="modelo")
    valor_tabla = pd.DataFrame({"modelo": vv["modelo"], "parámetros": vv["parametros"], "logLik en escala del valor": vv["logLik_valor"].map(lambda v: f(v, 1)),
                                "BIC": vv["BIC"].map(lambda v: f(v, 1)), "AIC": vv["AIC"].map(lambda v: f(v, 1)), "ΔBIC": vv["ΔBIC"].map(lambda v: f(v, 1)),
                                "supuestos que falla": vv.apply(lambda r: ", ".join(n for n, x in (("normalidad", r.falla_normalidad), ("varianza constante", r.falla_varianza),
                                                                                                 ("influencia", r.falla_cook), ("colinealidad", r.falla_colinealidad)) if x) or "ninguno", axis=1)})
    valor_diag = pd.DataFrame({"modelo": vd["modelo"], "asimetría": vd["asimetria_residuos"].map(lambda v: f(v, 2)), "exceso de curtosis": vd["exceso_curtosis"].map(lambda v: f(v, 2)),
                               "Spearman (valor absoluto del residuo y ajustado)": vd["spearman_abs_res_ajustado"].map(lambda v: f(v, 2)), "Cook máximo": vd["cook_maximo"].map(lambda v: f(v, 2)),
                               "GVIF^(1/2gl) máximo": vd["gvif_maximo"].map(lambda v: f(v, 2))})
    cv = pd.DataFrame({"modelo": vc["modelo"], "contratos en prueba": vc["n_prueba"].map(lambda v: f(v, 0)), "RMSE (log)": vc["rmse_log"].map(lambda v: f(v, 3)), "MAE (log)": vc["mae_log"].map(lambda v: f(v, 3))})
    coefs = vco[vco["termino"] != "(Intercept)"].copy()
    coefs["razón multiplicativa (exp)"] = np.exp(coefs["Estimate"])
    coefs["|t|"] = coefs["t value"].abs()
    coefs = coefs.sort_values("|t|", ascending=False).head(8)
    coef_t = pd.DataFrame({"término": coefs["termino"], "estimador (log)": coefs["Estimate"].map(lambda v: f(v, 3)), "razón multiplicativa": coefs["razón multiplicativa (exp)"].map(lambda v: f(v, 2)),
                           "t": coefs["t value"].map(lambda v: f(v, 1))})
    sele_valor = regla(vb.assign(parametros=vb["parametros"]), vv["falla_alguna"].to_numpy())

    eb["ΔBIC"] = eb["BIC"] - eb["BIC"].min()
    ee = eb.merge(ed, on="modelo")
    est_tabla = pd.DataFrame({"modelo": ee["modelo"], "parámetros": ee["parametros"], "logLik": ee["logLik"].map(lambda v: f(v, 1)), "BIC": ee["BIC"].map(lambda v: f(v, 1)),
                              "AIC": ee["AIC"].map(lambda v: f(v, 1)), "ΔBIC": ee["ΔBIC"].map(lambda v: f(v, 1)),
                              "supuestos que falla": ee.apply(lambda r: ", ".join(n for n, x in (("sobredispersión", r.falla_sobredispersion), ("autocorrelación (Ljung-Box 12)", r.falla_autocorrelacion),
                                                                                               ("normalidad de residuos cuantílicos", r.falla_normalidad_rq)) if x) or "ninguno", axis=1)})
    est_diag = pd.DataFrame({"modelo": ed["modelo"], "Ljung-Box 6 (p)": ed["ljung_box_6_p"].map(lambda v: f(v, 3)), "Ljung-Box 12 (p)": ed["ljung_box_12_p"].map(lambda v: f(v, 3)),
                             "asimetría RQ": ed["asimetria_rq"].map(lambda v: f(v, 2)), "exceso de curtosis RQ": ed["exceso_curtosis_rq"].map(lambda v: f(v, 2)),
                             "media RQ": ed["media_rq"].map(lambda v: f(v, 2)), "desv. est. RQ": ed["sd_rq"].map(lambda v: f(v, 2)), "χ² de Pearson / gl": ed["pearson_chi2_sobre_gl"].map(lambda v: f(v, 2))})
    sele_est = regla(eb, ee["falla_alguna"].to_numpy())
    anios = ea.copy(); anios["razón vs 2025"] = anios["razon_de_tasas_vs_2025"].map(lambda v: f(v, 2)); anios["p"] = anios["p_valor"].map(lambda v: f(v, 3))
    anios_t = anios[["modelo", "anio", "razón vs 2025", "p"]].rename(columns={"anio": "año"})
    sens = pd.DataFrame({"modelo": es["modelo"], "meses": es["n"], "tendencia por mes (log)": es["tendencia_por_mes"].map(lambda v: f(v, 4)), "p de la tendencia": es["p_tendencia"].map(lambda v: f(v, 4)),
                         "amplitud 12 meses": es["amplitud_12"].map(lambda v: f(v, 2)), "amplitud 6 meses": es["amplitud_6"].map(lambda v: f(v, 2)),
                         "razón de 2020": es["razon_2020"].map(lambda v: "" if pd.isna(v) else f(v, 2)), "p de 2020": es["p_2020"].map(lambda v: "" if pd.isna(v) else f(v, 3)),
                         "BIC (no comparable entre filas)": es["BIC"].map(lambda v: f(v, 1)), "parámetros": es["parametros"]})
    perfil_m = ep.copy()
    perfil_m["razón vs enero (modelo 2)"] = perfil_m["razon_vs_enero"].map(lambda v: "1,00 (referencia)" if pd.isna(v) else f(v, 2))
    perfil_m["promedio de contratos por mes"] = perfil_m["promedio_contratos"].map(lambda v: f(v, 1))
    perfil_t = perfil_m[["mes", "promedio de contratos por mes", "razón vs enero (modelo 2)"]]

    tam_t = pd.DataFrame({"clase": tam["clase"], "contratos": tam["contratos"].map(lambda v: f(v, 0)), "%": tam["pct"].map(lambda v: f(v, 1)), "probabilidad posterior media": tam["prob_media_posterior"].map(lambda v: f(v, 2))})
    if b:
        tam_t["Jaccard medio (bootstrap)"] = [f(v, 2) for v in b["jaccard_medio_por_clase"]]
    dominantes = []
    for kk in range(1, k + 1):
        x = perf[(perf["clase"] == kk) & (perf["prob_en_clase"] > 0.5)].sort_values("prob_en_clase", ascending=False)
        dominantes.append({"clase": kk, "categorías con probabilidad > 0,5 dentro de la clase": "; ".join(f"{r.variable}={r.categoria} ({f(r.prob_en_clase, 2)})" for r in x.itertuples())})
    bvr_t = bvr.head(8).assign(bvr=bvr.head(8)["bvr"].map(lambda v: f(v, 1)))[["var1", "var2", "bvr"]].rename(columns={"var1": "variable 1", "var2": "variable 2", "bvr": "BVR"})
    cruce_t = cruce.rename(columns={"clase_lca": "clase LCA \\ grupo HCPC"})
    t_ac = t.copy()

    def titulo_regla(sel, nombre):
        return f"**{nombre}**" if sel is not None else "ninguno"

    ocurre = {1: "ninguna", 2: "ninguno"}
    n_pasa_lca = int((~t["falla_alguna"]).sum())
    resumen = pd.DataFrame([
        {"pregunta": "1. Tipología (clases latentes)", "candidatos": "18 (3 modelos × 2 a 7 clases)", "candidatos que pasan los supuestos": f"{n_pasa_lca} de 18",
         "modelo elegido según la regla": ("ninguno" if elegido_is_none(t) else "ver sección 1"),
         "menor BIC (descriptivo)": f"{minb['covariables']}, {k} clases (BIC {f(minb['BIC'], 1)})"},
        {"pregunta": "2. Valor del contrato", "candidatos": "3", "candidatos que pasan los supuestos": f"{int((~vv['falla_alguna']).sum())} de 3",
         "modelo elegido según la regla": "ninguno" if sele_valor is None else sele_valor["modelo"], "menor BIC (descriptivo)": vb.sort_values("BIC").iloc[0]["modelo"]},
        {"pregunta": "3. Estacionalidad mensual", "candidatos": "3", "candidatos que pasan los supuestos": f"{int((~ee['falla_alguna']).sum())} de 3",
         "modelo elegido según la regla": "ninguno" if sele_est is None else sele_est["modelo"], "menor BIC (descriptivo)": eb.sort_values("BIC").iloc[0]["modelo"]}])

    L = ["# Patrones de compra de los contratos funerarios (SECOP I y II, 2020–2025)", "",
         "Descripción de lo que muestran los datos; no se sacan conclusiones de negocio. Método, modelos candidatos, supuestos y regla de decisión: **D97**, registrada y versionada antes de correr los modelos. "
         "Universo: los **4.992** contratos `funerario` (D84). Generado por `python -m src.modelos.patrones_informe`; los modelos están en `src/modelos/patrones_*.py` y `patrones_*.R`. "
         "Las cifras monetarias son pesos constantes de 2025.", "",
         "**Regla (D97):** gana el menor BIC; con ΔBIC < 2 gana el más simple; ΔBIC > 10 es evidencia fuerte (Kass y Raftery 1995); un modelo que falle los supuestos no se elige aunque tenga el menor BIC; si todos fallan, no se elige ninguno y el de menor BIC se reporta solo como descripción.", "",
         "## Resumen", "", tabla(resumen), "",
         "En las tres preguntas la regla de D97 no elige ningún modelo, porque todos los candidatos fallan al menos un supuesto fijado de antemano. Las secciones siguientes reportan, para cada pregunta, la comparación completa, los supuestos que falla cada modelo y, solo como descripción, el modelo de menor BIC.", "",
         "## 1. Tipología (clases latentes)", "",
         f"Variables: tipo de entidad (categorías con menos de 1 % agrupadas), grupo de modalidad, tipo de contrato homologado, territorial o nacional, cuartil del valor y seis componentes. Semilla 2033, 20 arranques por modelo y número de clases, EM propio (n = 4.992). "
         "Los modelos 2 y 3 usan la fuente (y el año) como covariables de la pertenencia a la clase.", "",
         "### 1.1 Comparación de los 18 modelos", "", tabla(vista), "",
         f"- **ΔBIC entre modelos de igual número de clases (7):** sin covariables {f(t[(t.modelo==1)&(t.clases==7)]['BIC'].iloc[0]-minb['BIC'], 1)}, fuente {f(t[(t.modelo==2)&(t.clases==7)]['BIC'].iloc[0]-minb['BIC'], 1)}, fuente y año 0,0 (frente al menor BIC global).",
         f"- El BIC sigue bajando hasta 7 clases en los modelos 2 y 3, que es el límite superior del rango fijado en D97; en el modelo 1 el mínimo está en 6 clases (BIC {f(t[(t.modelo==1)&(t.clases==6)]['BIC'].iloc[0], 1)}) y 7 clases queda {f(t[(t.modelo==1)&(t.clases==7)]['BIC'].iloc[0]-t[(t.modelo==1)&(t.clases==6)]['BIC'].iloc[0], 1)} por encima.",
         f"- **Independencia local:** el BVR máximo va de {f(t['bvr_maximo'].min(), 1)} a {f(t['bvr_maximo'].max(), 1)} y ningún modelo queda por debajo del umbral de 10; los 18 fallan este supuesto (el menor BVR máximo es el del modelo de {t.sort_values('bvr_maximo').iloc[0]['covariables']} con {int(t.sort_values('bvr_maximo').iloc[0]['clases'])} clases).",
         f"- **Identificabilidad:** {int((~t['falla_identificabilidad']).sum())} de 18 modelos repiten su mejor log-verosimilitud en al menos 3 de los 20 arranques; el de menor BIC la alcanza en {int(minb['arranques_con_el_maximo'])} de 20, de modo que no se puede descartar un máximo local mejor.",
         f"- **Tamaño de clase:** ninguna clase baja de 1 % de los contratos (la más pequeña es {f(t['tamano_minimo_pct'].min(), 1)} %).", "",
         f"### 1.2 Aplicación de la regla", "",
         f"Pasan todos los supuestos {n_pasa_lca} de 18 candidatos; **no se elige ninguna tipología**. Por tanto, lo que sigue describe la de menor BIC ({minb['covariables']}, {k} clases) sin proponerla como elegida. "
         f"Su BIC es {f(t.sort_values('BIC').iloc[1]['dBIC'], 1)} puntos menor que el del siguiente ({t.sort_values('BIC').iloc[1]['covariables']}, {int(t.sort_values('BIC').iloc[1]['clases'])} clases) y {f(t.sort_values('BIC').iloc[2]['dBIC'], 1)} o más que el de los demás: "
         "ΔBIC > 10 en todos los casos, evidencia fuerte de mejor ajuste, pero con supuestos incumplidos.",
         "Como ningún candidato pasa los supuestos que no requieren bootstrap, la regla de D97 no obliga a correrlo; se corrió, de forma descriptiva y con los 200 remuestreos fijados, para el modelo de menor BIC de cada familia (fuente y año con 7 clases, fuente con 7 y sin covariables con 6); el resto figura como «no evaluado». "
         "Un Jaccard mínimo inferior a 0,60 (como el del modelo de fuente con 7 clases) añade el supuesto de estabilidad a los incumplidos.", "",
         f"### 1.3 Tipología de menor BIC (descriptiva): {minb['covariables']}, {k} clases", "", tabla(tam_t), "", tabla(pd.DataFrame(dominantes)), "",
         "**Residuos bivariados más altos (BVR):**", "", tabla(bvr_t), "",
         ("**Estabilidad por bootstrap (200 remuestreos, 5 arranques cada uno):** " + (f"Jaccard medio por clase {', '.join(f(v, 2) for v in b['jaccard_medio_por_clase'])}; mínimo {f(b['jaccard_minimo_medio'], 2)} (umbral de D97: 0,60); "
          f"índice de Rand ajustado entre cada remuestreo y la solución original, media {f(b['ari_medio'], 2)} y percentil 5 {f(b['ari_p05'], 2)}." if b else "no evaluada.")), "",
         f"**ACM + HCPC (descriptiva).** Las dos primeras dimensiones de la ACM retienen {f(inercia['pct_varianza'].iloc[0], 1)} % y {f(inercia['pct_varianza'].iloc[1], 1)} % de la inercia ({f(inercia['pct_acumulado'].iloc[4], 1)} % las cinco primeras). "
         f"HCPC con {k} grupos (tamaños {', '.join(str(x) for x in hc['tamanos_hcpc'])}) frente a la tipología de menor BIC: **índice de Rand ajustado {f(hc['ari_acm_hcpc_vs_lca'], 2)}**. Como no hay tipología elegida, la comparación es con la de menor BIC.", "",
         tabla(cruce_t), "",
         "Gráficos y tablas completas (perfiles por clase, BVR, bootstrap) en `data/processed/resultados_secop/patrones/` (no se versiona).", "",
         "## 2. Valor del contrato", "",
         f"Variable: log del valor constante de 2025 (n = {int(vb['n'].iloc[0])}; {notas['excluidos_valor_no_positivo']} contratos con valor no positivo o nulo, excluidos). Explicativas: tipo de entidad, grupo de modalidad, seis componentes, año y fuente. "
         f"Entidad = NIT (o nombre si falta): {int(vi['entidades'].iloc[0])} entidades. BIC calculado en la escala del valor (log-verosimilitud de los modelos 1 y 2 menos Σ log valor).", "",
         "### 2.1 Comparación", "", tabla(valor_tabla), "",
         f"- ΔBIC: el gamma log mixto queda {f(vb.sort_values('BIC').iloc[1]['ΔBIC'], 0)} puntos por debajo del siguiente (el lineal mixto) y {f(vb.sort_values('BIC').iloc[2]['ΔBIC'], 0)} del lineal: evidencia fuerte de mejor ajuste en la escala del valor.",
         f"- **ICC:** {f(vi['icc_nulo'].iloc[0], 2)} sin covariables y {f(vi['icc_con_covariables'].iloc[0], 2)} con ellas (modelo lineal mixto); en el gamma, {f(vi['icc_gamma_escala_latente'].iloc[0], 2)} en la escala latente; la dispersión gamma estimada es {f(vi['dispersion_gamma'].iloc[0], 2)}.", "",
         "### 2.2 Diagnósticos (umbrales de D97)", "", tabla(valor_diag), "",
         f"Todos los modelos fallan el supuesto de normalidad (asimetría con |valor| > 1 o exceso de curtosis > 3); el gamma es el que menos se aleja (asimetría {f(vd.iloc[2]['asimetria_residuos'], 2)}, exceso de curtosis {f(vd.iloc[2]['exceso_curtosis'], 2)}). "
         f"Varianza no constante, influencia (Cook máximo del modelo 1: {f(vd.iloc[0]['cook_maximo'], 2)}; {int(vd['cook_mayor_4_sobre_n_modelo1'].iloc[0])} contratos con Cook > 4/n) y colinealidad no fallan. Gráficos: `{GRAFICOS}/valor_qq_y_residuos.png` y `{GRAFICOS}/valor_cook_y_efectos_aleatorios.png`.", "",
         "### 2.3 Validación cruzada de 5 pliegues agrupada por entidad", "", tabla(cv), "",
         "Predicción de población (sin efecto aleatorio) para entidades fuera del pliegue; en el gamma, la esperanza del logaritmo de una gamma. El error más bajo en escala log es el del modelo lineal, aunque su BIC en la escala del valor sea el peor.", "",
         "### 2.4 Efectos más fuertes del modelo lineal mixto (descriptivo, escala log)", "", tabla(coef_t), "",
         "Referencias: tipo de entidad alcaldía y municipio; modalidad mínima cuantía; año 2020; fuente SECOP I. No hay modelo elegido por la regla; estos coeficientes describen el lineal mixto, que tampoco cumple los supuestos de normalidad.", "",
         "## 3. Estacionalidad mensual", "",
         f"Conteos mensuales por fecha de firma, enero de 2020 a diciembre de 2025 (72 meses, {int(serie['y'].sum())} contratos, ningún mes con cero).", "",
         "### 3.1 Comparación", "", tabla(est_tabla), "",
         f"- Cameron y Trivedi sobre el Poisson: α = {f(ect['alfa'].iloc[0], 3)} (error estándar {f(ect['error_estandar'].iloc[0], 3)}, p = {f(ect['p_valor'].iloc[0], 5)}): hay sobredispersión. χ² de Pearson sobre grados de libertad del Poisson: {f(ed['pearson_chi2_sobre_gl'].iloc[0], 2)}.",
         f"- La dispersión de la binomial negativa es θ = {f(th['valor'].iloc[0], 1)} (modelo 2) y {f(th['valor'].iloc[1], 1)} (modelo 3).",
         f"- El modelo 3 tiene {int(eb.iloc[2]['parametros'])} parámetros frente a {int(eb.iloc[1]['parametros'])} del modelo 2: ΔBIC de {f(eb.iloc[1]['ΔBIC'], 1)} entre ambos y {f(eb.iloc[0]['ΔBIC'], 1)} con el Poisson.", "",
         "### 3.2 Diagnósticos", "", tabla(est_diag), "",
         "Los tres modelos fallan la autocorrelación (Ljung-Box a 12 rezagos con p < 0,05); el Poisson también falla la sobredispersión. Los residuos cuantílicos de los tres cumplen el umbral de normalidad. "
         f"Gráficos: `{GRAFICOS}/estacionalidad_serie_y_diagnosticos.png`.", "",
         "### 3.3 Perfil mensual", "", tabla(perfil_t), "",
         "Promedio de contratos por mes calendario sobre los seis años, y razón de tasas de cada mes frente a enero según el modelo 2 (con año).", "",
         "### 3.4 Efecto de 2020 (reportado aparte)", "", tabla(anios_t), "",
         "Con 2025 como referencia, la razón de tasas de 2020 es " + f"{f(ea[(ea['modelo']=='1 Poisson')&(ea['anio']==2020)]['razon_de_tasas_vs_2025'].iloc[0], 2)} en el Poisson y {f(ea[(ea['modelo']=='2 binomial negativa')&(ea['anio']==2020)]['razon_de_tasas_vs_2025'].iloc[0], 2)} en la binomial negativa; "
         "el año 2024 no se distingue de 2025.", "",
         "Sensibilidad del modelo 3 (armónicos y tendencia): con y sin 2020, y con una indicadora de 2020. Los BIC de estas filas no son comparables entre sí (distinto n o distintas variables).", "", tabla(sens), "",
         "## 4. Limitaciones", "",
         "- **Ningún modelo cumple los supuestos fijados en D97 en ninguna de las tres preguntas**, de modo que la regla no elige modelo; los resultados del modelo de menor BIC son descriptivos.",
         "- **Clases latentes:** (a) el BVR de todos los modelos supera el umbral de independencia local de 10, es decir, hay dependencia entre variables que las clases no explican, sobre todo entre componentes; "
         f"(b) el modelo de menor BIC alcanza su mejor log-verosimilitud en {int(minb['arranques_con_el_maximo'])} de 20 arranques, así que puede no ser el máximo global; (c) el BIC sigue bajando en el límite del rango (7 clases) en los modelos con covariables; "
         "(d) los EM son propios (no hay `poLCA` ni `stepmix` instalados); el cálculo de parámetros y del BIC es el estándar, pero no se contrastó con otro programa; (e) el bootstrap empareja clases con asignación óptima y mide estabilidad en todos los contratos, no solo en los remuestreados.",
         "- **Valor:** la distribución del residuo tiene colas más pesadas que la normal en los tres modelos (incluido el gamma, residuos cuantílicos con exceso de curtosis de " + f"{f(vd.iloc[2]['exceso_curtosis'], 1)}); "
         "el gamma mixto de `lme4` estima la dispersión de forma aproximada (Laplace); el BIC en la escala del valor penaliza igual a los tres modelos por parámetro, sin contar el efecto aleatorio por entidad como parámetros individuales; "
         "la validación cruzada usa predicción de población y no premia el efecto aleatorio; Cook no está disponible para los modelos mixtos; una entidad con pocos contratos tiene un efecto aleatorio poco determinado.",
         "- **Estacionalidad:** 72 meses; el Ljung-Box a 12 rezagos tiene poca potencia con ese tamaño y no se ajustó por los grados de libertad de cada modelo; los p de 0,02 a 0,04 de los modelos 2 y 3 son cercanos al umbral de 0,05; 2020 está atravesado por la pandemia y reportado aparte; el modelo 3 asume una tendencia lineal.",
         "- **General:** los umbrales de «falla» son convencionales y se fijaron antes de ver los datos; con n = 4.992 el BIC favorece estructuras sencillas; la ubicación de las entidades es la sede, no el lugar de ejecución; el universo es el de los contratos clasificados `funerario` por TF-IDF (D84), con sus errores de clasificación (D93).", ""]
    return "\n".join(L)


def elegido_is_none(t):
    return bool(t["falla_alguna"].all())


def main():
    from src.modelos.patrones_informe_d98 import md_d98
    texto = md() + md_d98()
    DESTINO.write_text(texto, encoding="utf-8")
    print("escrito", DESTINO, len(texto))


if __name__ == "__main__":
    main()
