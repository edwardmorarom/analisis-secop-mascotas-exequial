"""Causas de defunción (EEVV, DANE) y contratación funeraria por departamento (D107). Exploratorio y ecológico; el plan y los umbrales están en D107."""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.outliers_influence import variance_inflation_factor

from src.etl.comun import RAIZ, cargar_config, ruta
from src.etl.extraer_eevv import ANIOS_COVID, ORDEN_GRUPOS, nombres_divipola
from src.etl.extraer_minsalud import cargar_pob_dane

SEMILLA_RESIDUOS = 2035
ANIOS = list(range(2020, 2026))
CAUSAS = ORDEN_GRUPOS
VIF_MAXIMO = 5.0
UMBRAL_P = 0.05
ASIMETRIA_MAXIMA, CURTOSIS_MAXIMA, COOK_MAXIMO = 1.0, 3.0, 1.0
DISPERSION_MAXIMA = 1.5
MIN_CONTRATOS_GRUPO = 20
SALIDA = RAIZ / "data/processed/resultados_secop/causas"


def poblacion_departamental(config, anios=ANIOS):
    filas = []
    for a in anios:
        p = cargar_pob_dane(config, a)
        s = p.groupby(p.index.str[:2]).sum()
        filas += [{"cod_dpto": c, "anio": a, "poblacion": v} for c, v in s.items()]
    return pd.DataFrame(filas)


def tasas(config=None):
    config = config or cargar_config()
    d = pd.read_parquet(ruta(config, "interim") / "eevv_defunciones.parquet")
    deptos = nombres_divipola(config)
    d = d[d["cod_dpto"].isin(deptos.index)]
    pob = poblacion_departamental(config)
    malla = pd.MultiIndex.from_product([sorted(deptos.index), ANIOS, CAUSAS], names=["cod_dpto", "anio", "grupo_causa"]).to_frame(index=False)
    t = malla.merge(d[["cod_dpto", "anio", "grupo_causa", "defunciones"]], how="left", on=["cod_dpto", "anio", "grupo_causa"]).merge(pob, on=["cod_dpto", "anio"], how="left", validate="many_to_one")
    t.loc[t["grupo_causa"] != "covid19", "defunciones"] = t.loc[t["grupo_causa"] != "covid19", "defunciones"].fillna(0)
    t["tasa_100mil"] = t["defunciones"] / t["poblacion"] * 1e5
    t["nombre_dpto"] = t["cod_dpto"].map(deptos)
    return t


def contratacion(config=None):
    config = config or cargar_config()
    d = pd.read_csv(RAIZ / "data/processed/resultados_secop/departamento_anual.csv")
    d["cod_dpto"] = d["cod_dpto"].astype(int).map("{:02d}".format)
    pob = poblacion_departamental(config)
    malla = pd.MultiIndex.from_product([sorted(nombres_divipola(config).index), ANIOS], names=["cod_dpto", "anio"]).to_frame(index=False)
    m = malla.merge(pob, on=["cod_dpto", "anio"], how="left").merge(d[["cod_dpto", "anio", "contratos", "valor_constante_2025"]], how="left", on=["cod_dpto", "anio"])
    m[["contratos", "valor_constante_2025"]] = m[["contratos", "valor_constante_2025"]].fillna(0)
    m["contratos_x100mil"] = m["contratos"] / m["poblacion"] * 1e5
    m["valor_x100mil"] = m["valor_constante_2025"] / m["poblacion"] * 1e5
    return m


def ancho_tasas(t):
    """Tasa por departamento-año y causa; la COVID-19 no observada queda como faltante (D107, aprobación)."""
    w = t.pivot_table(index=["cod_dpto", "anio"], columns="grupo_causa", values="tasa_100mil", aggfunc="first", dropna=False)
    observado = w["covid19"].notna()
    w = w[CAUSAS].reset_index()
    w["covid_observado"] = observado.values
    return w


def fisher_ic(rho, n):
    z, se = np.arctanh(rho), 1.06 / np.sqrt(n - 3)
    return float(np.tanh(z - 1.96 * se)), float(np.tanh(z + 1.96 * se))


def spearman_tabla(tasa_media, resultado, etiqueta):
    filas = []
    for c in CAUSAS:
        x = tasa_media[c].dropna()
        y = resultado.reindex(x.index)
        rho, p = stats.spearmanr(x, y)
        lo, hi = fisher_ic(rho, len(x))
        filas.append({"resultado": etiqueta, "causa": c, "n": len(x), "rho": rho, "ic95_inf": lo, "ic95_sup": hi, "p": p})
    t = pd.DataFrame(filas)
    t["p_holm"] = multipletests(t["p"], method="holm")[1]
    return t


def transversal(w, c):
    out = {}
    for nombre, anios in (("2020_2025", ANIOS), ("2020_2024", ANIOS[:-1])):
        sub = w[w["anio"].isin(anios)].copy()
        sub.loc[~sub["covid_observado"], "covid19"] = np.nan
        sub.loc[~sub["anio"].isin(ANIOS_COVID), "covid19"] = np.nan
        media = sub.groupby("cod_dpto")[CAUSAS].mean()
        res = c[c["anio"].isin(anios)].groupby("cod_dpto")[["contratos_x100mil", "valor_x100mil"]].mean()
        out[nombre] = pd.concat([spearman_tabla(media, res["contratos_x100mil"], "contratos por 100.000"), spearman_tabla(media, res["valor_x100mil"], "valor por 100.000")], ignore_index=True)
        out[f"media_{nombre}"] = media.join(res)
    return out


def disenio(panel, causas):
    x = np.log1p(panel[causas]).copy()
    return x


def vif(x):
    m = sm.add_constant(x.values, has_constant="add")
    return pd.Series([variance_inflation_factor(m, i + 1) for i in range(x.shape[1])], index=x.columns)


def eliminar_por_vif(x):
    quitadas = []
    x = x.copy()
    while x.shape[1] > 1:
        v = vif(x)
        if v.max() < VIF_MAXIMO:
            break
        peor = v.idxmax()
        quitadas.append((peor, float(v.max())))
        x = x.drop(columns=peor)
    return x, quitadas, vif(x) if x.shape[1] > 1 else pd.Series({x.columns[0]: 1.0})


def matriz(panel, causas):
    anios = pd.get_dummies(panel["anio"].astype(int), prefix="anio", drop_first=True).astype(float)
    x = pd.concat([np.log1p(panel[causas]).reset_index(drop=True), anios.reset_index(drop=True)], axis=1)
    return sm.add_constant(x, has_constant="add")


def ajustar_nb(panel, causas):
    x = matriz(panel, causas)
    y = panel["contratos"].values
    off = np.log(panel["poblacion"].values)
    grupos = pd.factorize(panel["cod_dpto"])[0]
    inicio = np.r_[sm.GLM(y, x, family=sm.families.Poisson(), offset=off).fit().params.values, 0.4]
    nb = sm.NegativeBinomial(y, x, offset=off, loglike_method="nb2").fit(start_params=inicio, method="bfgs", disp=0, maxiter=2000, cov_type="cluster", cov_kwds={"groups": grupos})
    return nb, x, y, off, grupos


def irr(nb, x, causas):
    ln2 = np.log(2)
    ci = nb.conf_int()
    filas = []
    for c in causas:
        i = list(x.columns).index(c)
        b, se = nb.params.iloc[i], nb.bse.iloc[i]
        filas.append({"causa": c, "irr_por_duplicacion": float(np.exp(b * ln2)), "ic95_inf": float(np.exp(ci.iloc[i, 0] * ln2)), "ic95_sup": float(np.exp(ci.iloc[i, 1] * ln2)), "p": float(nb.pvalues.iloc[i])})
    return pd.DataFrame(filas)


def cameron_trivedi(y, mu):
    """Regresión sin intercepto de ((y - mu)^2 - y) / mu sobre mu; la decisión usa el t robusto HC3 (D107b)."""
    z = ((y - mu) ** 2 - y) / mu
    r = sm.OLS(z, mu).fit()
    h = sm.OLS(z, mu).fit(cov_type="HC3")
    return {"estadistico_t": float(h.tvalues[0]), "gl": int(r.df_resid), "p": float(h.pvalues[0]), "coeficiente": float(r.params[0]),
            "estadistico_t_homocedastico": float(r.tvalues[0]), "p_homocedastico": float(r.pvalues[0])}


def residuos_cuantilicos(y, mu, alpha):
    rng = np.random.default_rng(SEMILLA_RESIDUOS)
    n = 1 / alpha
    p = 1 / (1 + alpha * mu)
    inf = stats.nbinom.cdf(y - 1, n, p)
    sup = stats.nbinom.cdf(y, n, p)
    u = np.clip(rng.uniform(inf, sup), 1e-12, 1 - 1e-12)
    return stats.norm.ppf(u)


def diagnosticos(nb, x, y, off, causas_vif=None):
    """Supuestos de D107: sobredispersión (Poisson), VIF, residuos cuantílicos y Cook."""
    pois = sm.GLM(y, x, family=sm.families.Poisson(), offset=off).fit()
    mu_p = pois.mu
    ct = cameron_trivedi(y, mu_p)
    gl = int(pois.df_resid)
    pearson_p = float(pois.pearson_chi2 / gl)
    mu = nb.predict(x, offset=off)
    alpha = float(nb.params.iloc[-1])
    pearson_nb = float(((y - mu) ** 2 / (mu + alpha * mu ** 2)).sum() / (len(y) - len(nb.params) + 1))
    rq = residuos_cuantilicos(y, np.asarray(mu), alpha)
    asim, curt = float(stats.skew(rq)), float(stats.kurtosis(rq))
    glm = sm.GLM(y, x, family=sm.families.NegativeBinomial(alpha=alpha), offset=off).fit()
    cook = glm.get_influence().cooks_distance[0]
    return {"alpha": alpha, "cameron_trivedi": ct, "pearson_gl_poisson": pearson_p, "pearson_gl_nb": pearson_nb, "gl_residual": gl,
            "asimetria_rq": asim, "curtosis_exceso_rq": curt, "cook_max": float(cook.max()), "cook_indices_4n": np.flatnonzero(cook > 4 / len(y)).tolist(),
            "pasa_sobredispersion": ct["p"] < UMBRAL_P and pearson_p > DISPERSION_MAXIMA, "pasa_dispersion_nb": pearson_nb <= DISPERSION_MAXIMA,
            "pasa_residuos": abs(asim) <= ASIMETRIA_MAXIMA and abs(curt) <= CURTOSIS_MAXIMA, "pasa_cook": float(cook.max()) <= COOK_MAXIMO}


def preparar_panel(w, c):
    p = w.merge(c, on=["cod_dpto", "anio"], validate="one_to_one")
    return p.sort_values(["cod_dpto", "anio"]).reset_index(drop=True)


SENSIBILIDADES = {"sin_bogota": lambda p: p[p["cod_dpto"] != "11"], "sin_san_andres": lambda p: p[p["cod_dpto"] != "88"],
                  "sin_2020": lambda p: p[p["anio"] != 2020], "sin_2025": lambda p: p[p["anio"] != 2025]}


def panel_conjunto(p, causas_modelo=CAUSAS):
    x_cov, quitadas, v = eliminar_por_vif(np.log1p(p[causas_modelo]))
    causas = list(x_cov.columns)
    nb, x, y, off, _ = ajustar_nb(p, causas)
    tabla = irr(nb, x, causas)
    tabla["p_holm"] = multipletests(tabla["p"], method="holm")[1]
    return {"causas": causas, "quitadas": quitadas, "vif": v, "irr": tabla, "diagnosticos": diagnosticos(nb, x, y, off), "n": len(y), "alpha": float(nb.params.iloc[-1])}


def panel_por_causa(p):
    resultados, filas = {}, []
    for c in CAUSAS:
        base = p[p["anio"].isin(ANIOS_COVID) & p["covid_observado"]] if c == "covid19" else p
        nb, x, y, off, _ = ajustar_nb(base, [c])
        fila = irr(nb, x, [c]).iloc[0].to_dict()
        fila["n"] = len(y)
        d = diagnosticos(nb, x, y, off)
        sens = {}
        for nombre, f in SENSIBILIDADES.items():
            if c == "covid19" and nombre == "sin_2025":
                continue
            sub = f(base)
            nbs, xs, _, _, _ = ajustar_nb(sub, [c])
            r = irr(nbs, xs, [c]).iloc[0]
            sens[nombre] = {"irr": float(r["irr_por_duplicacion"]), "p": float(r["p"]), "n": len(sub)}
        resultados[c] = {"diagnosticos": d, "sensibilidad": sens}
        fila.update({f"irr_{k}": v["irr"] for k, v in sens.items()}), fila.update({f"p_{k}": v["p"] for k, v in sens.items()})
        filas.append(fila)
    t = pd.DataFrame(filas)
    t["p_holm"] = multipletests(t["p"], method="holm")[1]
    return t, resultados


def veredicto(t, resultados):
    out = {}
    for _, f in t.iterrows():
        d = resultados[f["causa"]]["diagnosticos"]
        supuestos = d["pasa_sobredispersion"] and d["pasa_dispersion_nb"] and d["pasa_residuos"] and d["pasa_cook"]
        sens = resultados[f["causa"]]["sensibilidad"]
        signo = np.sign(np.log(f["irr_por_duplicacion"]))
        estable = all(np.sign(np.log(s["irr"])) == signo and s["p"] < UMBRAL_P for s in sens.values())
        sig = f["p_holm"] < UMBRAL_P
        out[f["causa"]] = {"significativo_holm": bool(sig), "supuestos": bool(supuestos), "estable": bool(estable), "resultado": bool(sig and supuestos and estable)}
    return out


def participacion_grupos(config=None):
    from src.modelos.validacion_grupos import cargar_validacion

    d, _ = cargar_validacion()
    r = d[d["grupo"].notna() & d["cod_dpto"].notna()]
    tot = r.groupby("cod_dpto").size().rename("contratos_8_grupos")
    g = r.groupby(["cod_dpto", "grupo"]).size().unstack(fill_value=0)
    p = pd.DataFrame({"contratos_8_grupos": tot, "part_grupo1": g["Grupo 1"] / tot * 100, "part_grupo2": g["Grupo 2"] / tot * 100})
    return p[p["contratos_8_grupos"] >= MIN_CONTRATOS_GRUPO]


def por_forma_de_compra(media, part):
    filas = []
    for grupo in ("part_grupo1", "part_grupo2"):
        sub = []
        for c in CAUSAS:
            x = media[c].reindex(part.index).dropna()
            rho, p = stats.spearmanr(x, part.loc[x.index, grupo])
            lo, hi = fisher_ic(rho, len(x))
            sub.append({"participacion": grupo, "causa": c, "n": len(x), "rho": rho, "ic95_inf": lo, "ic95_sup": hi, "p": p})
        t = pd.DataFrame(sub)
        t["p_holm"] = multipletests(t["p"], method="holm")[1]
        filas.append(t)
    return pd.concat(filas, ignore_index=True)


def calcular(config=None):
    config = config or cargar_config()
    t = tasas(config)
    c = contratacion(config)
    w = ancho_tasas(t)
    trans = transversal(w, c)
    p = preparar_panel(w, c)
    conj = panel_conjunto(p, [c for c in CAUSAS if c != "covid19"])
    conj_covid = panel_conjunto(p[p["anio"].isin(ANIOS_COVID) & p["covid_observado"]].reset_index(drop=True))
    por, res = panel_por_causa(p)
    forma = por_forma_de_compra(trans["media_2020_2025"], participacion_grupos(config))
    return {"tasas": t, "contratos": c, "ancho": w, "transversal": trans, "panel": p, "conjunto": conj, "conjunto_covid": conj_covid, "por_causa": por, "supuestos": res, "veredicto": veredicto(por, res), "forma": forma}


def guardar(r):
    SALIDA.mkdir(parents=True, exist_ok=True)
    r["tasas"].to_csv(SALIDA / "tasas_dpto_anio.csv", index=False, encoding="utf-8-sig")
    for k in ("2020_2025", "2020_2024"):
        r["transversal"][k].to_csv(SALIDA / f"spearman_transversal_{k}.csv", index=False)
        r["transversal"][f"media_{k}"].to_csv(SALIDA / f"promedios_por_departamento_{k}.csv")
    r["conjunto"]["irr"].to_csv(SALIDA / "panel_nb_conjunto_irr.csv", index=False)
    r["conjunto_covid"]["irr"].to_csv(SALIDA / "panel_nb_conjunto_con_covid_2020_2022_irr.csv", index=False)
    r["por_causa"].to_csv(SALIDA / "panel_nb_por_causa_irr.csv", index=False)
    r["forma"].to_csv(SALIDA / "spearman_forma_de_compra.csv", index=False)
    filas = []
    for c, d in r["supuestos"].items():
        dg = d["diagnosticos"]
        filas.append({"modelo": f"B2_{c}", "alpha": dg["alpha"], "ct_t": dg["cameron_trivedi"]["estadistico_t"], "ct_gl": dg["cameron_trivedi"]["gl"], "ct_p": dg["cameron_trivedi"]["p"],
                      "pearson_gl_poisson": dg["pearson_gl_poisson"], "pearson_gl_nb": dg["pearson_gl_nb"], "asimetria_rq": dg["asimetria_rq"], "curtosis_exceso_rq": dg["curtosis_exceso_rq"],
                      "cook_max": dg["cook_max"], "n_cook_sobre_4n": len(dg["cook_indices_4n"])})
    dg = r["conjunto"]["diagnosticos"]
    filas.append({"modelo": "B1_conjunto", "alpha": dg["alpha"], "ct_t": dg["cameron_trivedi"]["estadistico_t"], "ct_gl": dg["cameron_trivedi"]["gl"], "ct_p": dg["cameron_trivedi"]["p"],
                  "pearson_gl_poisson": dg["pearson_gl_poisson"], "pearson_gl_nb": dg["pearson_gl_nb"], "asimetria_rq": dg["asimetria_rq"], "curtosis_exceso_rq": dg["curtosis_exceso_rq"],
                  "cook_max": dg["cook_max"], "n_cook_sobre_4n": len(dg["cook_indices_4n"])})
    pd.DataFrame(filas).to_csv(SALIDA / "panel_nb_supuestos.csv", index=False)
    r["conjunto"]["vif"].rename("vif").to_csv(SALIDA / "panel_nb_conjunto_vif.csv")
