import json
import warnings

import numpy as np
import pandas as pd

from src.etl.comun import RAIZ, cargar_config, ruta
from src.modelos.causas_defuncion import ANIOS, CAUSAS, SALIDA, UMBRAL_P, calcular, guardar
from src.modelos.causas_robustez import CAUSA_FOCO, calcular_robustez, guardar_robustez

GRAFICOS = RAIZ / "docs/resultados/graficos/causas"
NOMBRES = {"agresiones_homicidios": "Agresiones (homicidios)", "accidentes_transporte": "Accidentes de transporte", "otros_accidentes_causas_externas": "Otras causas externas (no homicidio ni transporte)",
           "covid19": "COVID-19", "circulatorio": "Sistema circulatorio", "neoplasias": "Neoplasias", "demas_causas": "Demás causas"}


def fmt(x, d=1):
    return "—" if x is None or pd.isna(x) else f"{x:,.{d}f}".replace(",", "#").replace(".", ",").replace("#", ".")


def pf(p):
    return "< 0,001" if p < 0.001 else f"{p:.3f}".replace(".", ",")


def tabla(filas, cab):
    return ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)] + ["| " + " | ".join(str(x) for x in f) + " |" for f in filas]


def ins_anual():
    config = cargar_config()
    d = pd.DataFrame([json.loads(l) for l in open(ruta(config, "raw") / "covid" / "ins_covid_fallecidos_mes_20261101.jsonl", encoding="utf-8")])
    d["anio"] = d["mes"].str[:4].astype(int)
    return d.groupby("anio")["fallecidos"].apply(lambda s: s.astype(int).sum())


def dispersion(r, nombre_corto):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    media = r["transversal"]["media_2020_2025"]
    c = r["contratos"]
    c3 = c[c["anio"].isin([2020, 2021, 2022])].groupby("cod_dpto")["contratos_x100mil"].mean()
    nombres = r["tasas"].drop_duplicates("cod_dpto").set_index("cod_dpto")["nombre_dpto"].map(lambda x: "San Andrés" if "SAN ANDR" in str(x).upper() else "".join(ch for ch in str(x).title() if ch.isalpha() or ch == " "))
    fig, ejes = plt.subplots(1, 2, figsize=(12, 5), facecolor="#fcfcfb")
    for ax, (causa, y, titulo, nota) in zip(ejes, [("agresiones_homicidios", media["contratos_x100mil"], "Homicidios (promedio 2020–2025)", "contratos por 100.000, promedio anual 2020–2025"),
                                                  ("covid19", c3, "COVID-19 (promedio 2020–2022)", "contratos por 100.000, promedio anual 2020–2022")]):
        x = media[causa].dropna()
        y = y.reindex(x.index)
        rho = pd.Series(x).corr(y, method="spearman")
        ax.scatter(x, y, s=38, color="#2a78d6", edgecolor="#fcfcfb", linewidth=0.8, zorder=3)
        grandes = (x.rank() >= len(x) - 2) | (y.rank() >= len(y) - 2) | (y.rank() <= 1)
        for k in x.index[grandes.values]:
            ax.annotate(nombres[k], (x[k], y[k]), xytext=(4, 4), textcoords="offset points", fontsize=8, color="#52514e")
        ax.set(xlabel="Defunciones por 100.000 habitantes", ylabel=nota.capitalize(), title=titulo)
        ax.text(0.97, 0.95, f"Spearman ρ = {fmt(rho, 2)}" + chr(10) + "33 departamentos", transform=ax.transAxes, ha="right", va="top", fontsize=9, color="#52514e")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(color="#e8e7e2", lw=0.8, zorder=0)
        ax.set_facecolor("#fcfcfb")
    fig.tight_layout()
    GRAFICOS.mkdir(parents=True, exist_ok=True)
    destino = GRAFICOS / nombre_corto
    fig.savefig(destino, dpi=140)
    plt.close(fig)
    return destino


def seccion_datos(r):
    ver = pd.read_csv(RAIZ / "data/processed/resultados_secop/causas/verificacion_totales.csv")
    u07 = pd.read_csv(RAIZ / "data/processed/resultados_secop/causas/covid_u07_cuadro16.csv")
    ins = ins_anual()
    tasas = r["tasas"]
    L = ["## 1. Datos y verificación", "",
         "Seis cuadros unificados de defunciones no fetales del DANE (cifras definitivas 2020 a 2025; la de 2025 se publicó el 24 de septiembre de 2026), Cuadro 5 (departamento de residencia × lista 6/67 de la OPS) y, para la COVID-19, Cuadro 16 (`U07`). Archivos en `data/raw/dane/eevv/` con URL, fecha, tamaño y SHA-256 en el manifiesto. El equivalente de cada grupo en la lista 6/67 y el tratamiento de la COVID-19 están en la enmienda de D107.", "",
         "**Verificación de totales nacionales** (suma de los 33 departamentos más «Extranjero» y «Sin información» frente al Índice del DANE y a la fila `TOTAL` del Cuadro 5):", ""]
    L += tabla([(int(f.anio), fmt(f.total_indice_dane, 0), fmt(f.total_nacional_cuadro5, 0), fmt(f.suma_departamentos_mas_no_asignados, 0), fmt(f.suma_grupos, 0), fmt(f.total_indice_dane - f.suma_grupos, 0)) for f in ver.itertuples()],
                ["Año", "Total publicado (Índice)", "Total nacional (Cuadro 5)", "Suma de departamentos y no asignados", "Suma de los siete grupos", "Diferencia"])
    nac = u07.groupby("anio")["u07"].sum()
    L += ["", "La diferencia es 0 en los seis años. **COVID-19** (EEVV: `U07` del Cuadro 16; INS: fallecidos por fecha de muerte en `data/raw/covid/`):", ""]
    filas = []
    for a in (2020, 2021, 2022):
        e = int(ver.loc[ver["anio"] == a, "covid_u07_suma_departamentos"].iloc[0])
        filas.append((a, fmt(e, 0), fmt(ins.get(a), 0), fmt(ins.get(a) - e, 0), fmt((ins.get(a) / e - 1) * 100) + " %"))
    L += tabla(filas, ["Año", "EEVV (U07, suma de departamentos)", "INS (fallecidos)", "INS − EEVV", "Diferencia relativa"])
    L += ["", f"El INS cuenta fallecidos con COVID-19 confirmado por fecha de muerte y las EEVV cuentan la causa certificada por residencia, de modo que no tienen por qué coincidir: el INS supera a las EEVV en 2021 y en 2022 (en 2020 la diferencia es de {fmt((ins.get(2020) / int(ver.loc[ver['anio'] == 2020, 'covid_u07_suma_departamentos'].iloc[0]) - 1) * 100)} %). Esta diferencia se reporta y no se corrige. De 2023 en adelante la COVID-19 no se observa en las EEVV por departamento (queda dentro de «demás causas»), mientras el INS registra {fmt(ins.get(2023), 0)} fallecidos en 2023.", "",
          "**Cobertura de la COVID-19 por departamento.** `U07` aparece entre las diez primeras causas en " + ", ".join(f"{a}: {int((tasas[(tasas['anio'] == a) & (tasas['grupo_causa'] == 'covid19')]['defunciones'].notna()).sum())} de 33 departamentos" for a in (2020, 2021, 2022)) + "; los demás quedan en «demás causas» y la COVID-19 de esos departamentos-año es **faltante** (no 0): el modelo de COVID-19 los excluye (n = 98). En 2023 a 2025 no es observable (faltante).", "",
          "**Tasas por 100.000 habitantes** (mediana de los 33 departamentos, mínimo y máximo de los promedios anuales 2020–2025; COVID-19: 2020–2022):", ""]
    media = r["transversal"]["media_2020_2025"]
    L += tabla([(NOMBRES[c], fmt(media[c].median()), fmt(media[c].min()), fmt(media[c].max())) for c in CAUSAS], ["Causa", "Mediana", "Mínimo", "Máximo"])
    return L + [""]


def seccion_transversal(r):
    t = r["transversal"]["2020_2025"]
    t24 = r["transversal"]["2020_2024"].set_index(["resultado", "causa"])
    L = ["## 2. Transversal por departamento (Spearman, 33 departamentos)", "",
         "Tasa promedio de cada causa 2020–2025 (COVID-19: 2020–2022) frente a contratos funerarios y valor, por 100.000 habitantes (promedio anual 2020–2025). Holm por causa (7) dentro de cada resultado. IC 95 % por transformación de Fisher (aproximado). La última columna es la sensibilidad con el promedio 2020–2024 (p de Holm).", ""]
    for res in t["resultado"].unique():
        L += [f"**{res.capitalize()}**", ""]
        L += tabla([(NOMBRES[f.causa], f.n, fmt(f.rho, 2), f"{fmt(f.ic95_inf, 2)} a {fmt(f.ic95_sup, 2)}", pf(f.p), pf(f.p_holm), "sí" if f.p_holm < UMBRAL_P else "no", pf(t24.loc[(res, f.causa), "p_holm"]) + f" (ρ = {fmt(t24.loc[(res, f.causa), 'rho'], 2)})") for f in t[t["resultado"] == res].itertuples()],
                    ["Causa", "n", "ρ", "IC 95 %", "p", "p de Holm", "p de Holm < 0,05", "Sin 2025: p de Holm"]) + [""]
    return L


def seccion_panel(r):
    cj, por, res, ver = r["conjunto"], r["por_causa"], r["supuestos"], r["veredicto"]
    dg = cj["diagnosticos"]
    L = ["## 3. Panel departamento × año (binomial negativa)", "",
         f"Contratos funerarios por departamento-año (n = {cj['n']}: 33 departamentos × 6 años), offset log(población), efectos fijos de año, errores agrupados por departamento. Razón de tasas (IRR) **por cada duplicación de (1 + tasa)**: `exp(β·ln 2)`.", "",
         "### 3.1 Modelo conjunto sin COVID-19 (B1a, 2020–2025)", ""]
    quit_txt = "; ".join(f"{NOMBRES[c]} (VIF {fmt(v, 1)})" for c, v in cj["quitadas"]) or "ninguna"
    L += [f"Variables eliminadas por VIF ≥ 5 (en orden): {quit_txt}. VIF finales: " + ", ".join(f"{NOMBRES[c]} {fmt(v, 2)}" for c, v in cj["vif"].items()) + f". α estimado = {fmt(cj['alpha'], 3)}.", ""]
    L += tabla([(NOMBRES[f.causa], fmt(f.irr_por_duplicacion, 2), f"{fmt(f.ic95_inf, 2)} a {fmt(f.ic95_sup, 2)}", pf(f.p), pf(f.p_holm)) for f in cj["irr"].itertuples()], ["Causa", "IRR por duplicación", "IC 95 %", "p", "p de Holm (entre las del modelo)"])
    cc = r["conjunto_covid"]
    quit_c = "; ".join(f"{NOMBRES[c]} (VIF {fmt(v, 1)})" for c, v in cc["quitadas"]) or "ninguna"
    L += ["", f"### 3.1b Modelo conjunto con COVID-19 (B1b, solo 2020–2022, n = {cc['n']})", "", f"Variables eliminadas por VIF ≥ 5: {quit_c}. α estimado = {fmt(cc['alpha'], 3)}. Con tres años y la tasa de COVID-19 correlacionada con las demás, el modelo es inestable; se muestra sin interpretación.", ""]
    L += tabla([(NOMBRES[f.causa], fmt(f.irr_por_duplicacion, 2), f"{fmt(f.ic95_inf, 2)} a {fmt(f.ic95_sup, 2)}", pf(f.p), pf(f.p_holm)) for f in cc["irr"].itertuples()], ["Causa", "IRR por duplicación", "IC 95 %", "p", "p de Holm (entre las del modelo)"])
    L += ["", "### 3.2 Un modelo por causa (B2)", "", "Una causa a la vez con efectos fijos de año; COVID-19 solo con 2020–2022 y departamentos-año observados (n = 98). Holm entre las siete causas.", ""]
    L += tabla([(NOMBRES[f.causa], fmt(f.irr_por_duplicacion, 2), f"{fmt(f.ic95_inf, 2)} a {fmt(f.ic95_sup, 2)}", pf(f.p), pf(f.p_holm), int(f.n)) for f in por.itertuples()], ["Causa", "IRR por duplicación", "IC 95 %", "p", "p de Holm", "n"])
    L += ["", "**Sensibilidad** (IRR; p nominal), con la regla de D107: sin Bogotá D.C., sin San Andrés, sin 2020 y sin 2025 (en COVID-19, sin 2025 no aplica):", ""]
    cab = ["Causa", "Sin Bogotá", "Sin San Andrés", "Sin 2020", "Sin 2025"]
    filas = []
    for f in por.itertuples():
        s = res[f.causa]["sensibilidad"]
        filas.append((NOMBRES[f.causa],) + tuple(f"{fmt(s[k]['irr'], 2)} (p {pf(s[k]['p'])})" if k in s else "n. a." for k in ("sin_bogota", "sin_san_andres", "sin_2020", "sin_2025")))
    L += tabla(filas, cab)
    L += ["", "### 3.3 Supuestos (estadístico, gl, p y decisión)", "",
          "Sobredispersión: Cameron-Trivedi en el Poisson (t de la regresión auxiliar con errores robustos HC3, gl, p, según D107b; se agrega el t homocedástico de D107; justifica la binomial negativa si p < 0,05) y χ² de Pearson/gl del Poisson (> 1,5 apoya la sobredispersión); dispersión residual del modelo binomial negativo (χ² de Pearson/gl ≤ 1,5); residuos cuantílicos aleatorizados (semilla 2035: |asimetría| ≤ 1 y |exceso de curtosis| ≤ 3); Cook (máximo ≤ 1); VIF < 5 (modelo conjunto).", ""]
    filas = []
    for nombre, d in [("B1a conjunto sin COVID-19", dg), ("B1b conjunto con COVID-19", r["conjunto_covid"]["diagnosticos"])] + [(f"B2 {NOMBRES[c]}", res[c]["diagnosticos"]) for c in CAUSAS]:
        ct = d["cameron_trivedi"]
        filas.append((nombre, f"t = {fmt(ct['estadistico_t'], 2)}, gl {ct['gl']}, p {pf(ct['p'])}; homocedástico: t = {fmt(ct['estadistico_t_homocedastico'], 2)}, p {pf(ct['p_homocedastico'])}", fmt(d["pearson_gl_poisson"], 1), "sí" if d["pasa_sobredispersion"] else "no", fmt(d["pearson_gl_nb"], 2), "sí" if d["pasa_dispersion_nb"] else "no",
                      f"{fmt(d['asimetria_rq'], 2)} / {fmt(d['curtosis_exceso_rq'], 2)}", "sí" if d["pasa_residuos"] else "no", fmt(d["cook_max"], 2), "sí" if d["pasa_cook"] else "no", len(d["cook_indices_4n"])))
    L += tabla(filas, ["Modelo", "Cameron-Trivedi (Poisson)", "Pearson/gl Poisson", "Sobredispersión (ambas)", "Pearson/gl NB", "Dispersión NB ≤ 1,5", "Asimetría / curtosis", "Residuos", "Cook máx.", "Cook ≤ 1", "Cook > 4/n"])
    L += ["", "VIF del modelo conjunto: " + ", ".join(f"{NOMBRES[c]} {fmt(v, 2)}" for c, v in cj["vif"].items()) + " (todos < 5 tras eliminar las variables indicadas).", "",
          "### 3.4 Lectura según la regla de D107", "", "Una asociación se reporta como resultado solo si es significativa tras Holm en B2, el modelo pasa los supuestos y conserva signo y significación nominal en las sensibilidades:", ""]
    L += tabla([(NOMBRES[c], "sí" if v["significativo_holm"] else "no", "sí" if v["supuestos"] else "no", "sí" if v["estable"] else "no", "**resultado**" if v["resultado"] else "no concluyente") for c, v in ver.items()], ["Causa", "Holm < 0,05", "Supuestos", "Estable en las sensibilidades", "Lectura"])
    return L + [""]


def seccion_forma(r):
    f = r["forma"]
    L = ["## 4. Por forma de compra (grupos de HCPC de D98)", "",
         "Spearman entre la tasa promedio por causa (2020–2025; COVID-19: 2020–2022) y la participación de cada grupo en los contratos funerarios del departamento (contratos del grupo / contratos de los 8 grupos reportados), en los 31 departamentos con al menos 20 contratos. Grupo 1: alcaldías, prestación de servicios; Grupo 2: alcaldías, suministro con ataúdes (D99). Holm entre las 7 causas dentro de cada grupo.", ""]
    for g, nombre in (("part_grupo1", "Grupo 1 (alcaldías: servicio)"), ("part_grupo2", "Grupo 2 (alcaldías: ataúdes)")):
        L += [f"**{nombre}**", ""]
        L += tabla([(NOMBRES[x.causa], x.n, fmt(x.rho, 2), f"{fmt(x.ic95_inf, 2)} a {fmt(x.ic95_sup, 2)}", pf(x.p), pf(x.p_holm), "sí" if x.p_holm < UMBRAL_P else "no") for x in f[f["participacion"] == g].itertuples()],
                    ["Causa", "n", "ρ", "IC 95 %", "p", "p de Holm", "p de Holm < 0,05"]) + [""]
    return L


LIMITACIONES = [
    "El contrato se ubica en la **sede de la entidad** y la defunción en la **residencia** del fallecido (D66, D67); la contratación de una capital puede atender a población de otros departamentos.",
    "Es un análisis **ecológico**: los coeficientes describen departamentos, no personas ni causas (falacia ecológica). No se interpretan como causales.",
    "Las tasas de las secciones 2, 3 y 4 son **crudas**: los departamentos con población más envejecida tienen tasas más altas de causas circulatorias, neoplasias y demás causas, y se confunden con la estructura de edad. Las secciones 2b y 3.5 repiten el análisis con tasas estandarizadas por edad (método directo, Colombia 2020), salvo la COVID-19, que no trae edad. Las proyecciones de población del DANE de 2020 en adelante se revisaron tras la pandemia.",
    "**COVID-19:** no está separada en las listas 6/67 ni Colombia 105; solo se observa (`U07`, Cuadro 16) en 2020–2022 y en casi todos los departamentos. De 2023 en adelante queda dentro de «demás causas» y es faltante en el panel (no 0); los departamentos-año de 2020–2022 donde no aparece entre las diez primeras causas también son faltantes. Por eso «demás causas» incluye COVID-19 de 2023 en adelante y, en el análisis estandarizado, también la de 2020 a 2022.",
    "**Pocos departamentos** (33) para inferencia transversal: baja potencia; un resultado no significativo no es evidencia de ausencia de asociación. Con 31 departamentos en la comparación por forma de compra.",
    "Los siete grupos de causa son excluyentes y sus tasas están correlacionadas (por eso el VIF eliminó a las neoplasias del modelo conjunto); los contratos de un mismo departamento y de una misma entidad no son independientes (por eso los errores agrupados y los valores p orientativos).",
    "La contratación pública funeraria atiende sobre todo a población vulnerable y NN y a servicios de apoyo, no a la mortalidad total: no se espera proporcionalidad con las defunciones. «Otras causas externas (no homicidio ni transporte)» incluye suicidios, caídas y eventos de intención no determinada; no se separan por ahora.",
    "Los departamentos de poca población (Guainía, Vaupés, Guaviare) tienen tasas de contratación altas por un denominador pequeño (pocos contratos); pesan mucho en las correlaciones de rango y en las razones de tasas, y los errores agrupados no corrigen eso por completo.",
    "Los universos difieren levemente: `departamento_anual.csv` usa el mercado vigente (D66) y la participación de los grupos de HCPC usa los 4.992 contratos de D97 a D99 (D105).",
]


def seccion_robustez(r, rb):
    t = rb["tabla"].set_index("modelo")
    nombres = {"base": "Modelo base (B2, tasa cruda)", "a_efectos_fijos_departamento": "(a) Efectos fijos de departamento", "b_control_ruralidad": "(b) Control de ruralidad y densidad", "c_tasas_estandarizadas": "(c) Tasas estandarizadas por edad"}
    L = ["### 3.5 Robustez de «" + NOMBRES[CAUSA_FOCO] + "» (D107b)", "",
         "Modelo por causa (NB2, offset log(población), efectos fijos de año, errores agrupados por departamento); razón de tasas por duplicación de (1 + tasa). **Regla fijada antes de correr:** el resultado se mantiene solo si la razón de tasas es > 1 con IC 95 % que excluye 1 en (b) y en (c); (a) se reporta sin regla.", ""]
    L += tabla([(nombres[m], fmt(f.irr, 2), f"{fmt(f.ic95_inf, 2)} a {fmt(f.ic95_sup, 2)}", pf(f.p), f"{fmt(f.irr_poisson, 2)} ({fmt(f.ic95_inf_poisson, 2)} a {fmt(f.ic95_sup_poisson, 2)})", fmt(f.alpha, 3), "sí" if f.convergio else "no", ("sí" if f.supera_regla == 1 else "no") if m in ("b_control_ruralidad", "c_tasas_estandarizadas") else "—") for m, f in t.iterrows()],
                ["Modelo", "Razón de tasas (NB)", "IC 95 %", "p", "Razón de tasas (Poisson, errores agrupados)", "α (NB)", "NB convergió", "Cumple la regla"])
    b = t.loc["b_control_ruralidad"]
    a = t.loc["a_efectos_fijos_departamento"]
    L += ["", f"En (b), por cada aumento de 1 en la proporción de población rural la razón de tasas de contratos es {fmt(b.irr_share_rural, 2)} (p {pf(b.p_share_rural)}), y por cada aumento de 1 en el log de la densidad, {fmt(b.irr_log_densidad, 2)} (p {pf(b.p_log_densidad)}). En (a) el NB converge a α ≈ 0 (frontera del espacio de parámetros: los efectos fijos absorben la sobredispersión) y equivale al Poisson; por eso se muestra también el Poisson con errores agrupados, la estimación más fiable con efectos fijos. La razón de tasas dentro de cada departamento ({fmt(a.irr, 2)}, IC {fmt(a.ic95_inf, 2)} a {fmt(a.ic95_sup, 2)}) **no excluye 1**: la asociación se apoya en diferencias **entre** departamentos y no en cambios de un año a otro dentro de cada uno (esperable con 6 años de datos).", ""]
    L += [f"**Resultado de la regla:** {'se mantiene' if (t.loc['b_control_ruralidad', 'supera_regla'] == 1 and t.loc['c_tasas_estandarizadas', 'supera_regla'] == 1) else 'no se mantiene'} en (b) y (c).", ""]
    return L


def seccion_estandarizada(r, rb):
    t = rb["transversal"]["2020_2025"]
    t24 = rb["transversal"]["2020_2024"].set_index(["resultado", "causa"])
    peso = rb["peso_estandar"]
    L = ["## 2b. Transversal con tasas estandarizadas por edad (D107b)", "",
         "Misma prueba de la sección 2 (Spearman, promedio 2020–2025, Holm entre 7 causas) con tasas estandarizadas por el método directo, población estándar Colombia 2020 (pesos por grupo de edad: " + ", ".join(f"{g.replace('_', ' ')} {fmt(v * 100, 1)} %" for g, v in peso.items()) + "). Las defunciones de edad desconocida se reparten en proporción. **La COVID-19 no se puede estandarizar** (el Cuadro 16 no trae edad): se usa su tasa cruda de 2020–2022, y «demás causas» incluye la COVID-19 de 2020–2022.", ""]
    for res in t["resultado"].unique():
        L += [f"**{res.capitalize()}**", ""]
        L += tabla([(NOMBRES[f.causa], f.n, fmt(f.rho, 2), f"{fmt(f.ic95_inf, 2)} a {fmt(f.ic95_sup, 2)}", pf(f.p), pf(f.p_holm), "sí" if f.p_holm < UMBRAL_P else "no", pf(t24.loc[(res, f.causa), "p_holm"]) + f" (ρ = {fmt(t24.loc[(res, f.causa), 'rho'], 2)})") for f in t[t["resultado"] == res].itertuples()],
                    ["Causa", "n", "ρ", "IC 95 %", "p", "p de Holm", "p de Holm < 0,05", "Sin 2025: p de Holm"]) + [""]
    return L


def resumen_robustez(rb):
    t = rb["tabla"].set_index("modelo")
    f = lambda m: f"{fmt(t.loc[m, 'irr'], 2)} ({fmt(t.loc[m, 'ic95_inf'], 2)} a {fmt(t.loc[m, 'ic95_sup'], 2)})"
    cumple = t.loc["b_control_ruralidad", "supera_regla"] == 1 and t.loc["c_tasas_estandarizadas", "supera_regla"] == 1
    return (f"La razón de tasas es {f('base')} en el modelo base, {f('a_efectos_fijos_departamento')} con efectos fijos de departamento, {f('b_control_ruralidad')} con control de ruralidad y densidad y {f('c_tasas_estandarizadas')} con tasas estandarizadas. "
            + ("El resultado se mantiene según la regla (b y c)" if cumple else "El resultado no se mantiene según la regla (b y c)") + ", pero con efectos fijos de departamento el IC incluye 1: la asociación proviene de diferencias entre departamentos, no de la variación anual dentro de cada uno.")


def resumen_estandarizado(rb):
    t = rb["transversal"]["2020_2025"]
    sig = t[t["p_holm"] < UMBRAL_P]
    return (f"tras Holm, {len(sig)} de 14 asociaciones son significativas: " + "; ".join(f"{NOMBRES[f.causa]} con {f.resultado} (ρ = {fmt(f.rho, 2)}, p de Holm {pf(f.p_holm)})" for f in sig.itertuples())
            + ". Con la edad controlada desaparecen las asociaciones negativas con circulatorio, neoplasias y demás causas de la sección 2, lo que confirma que eran un efecto de la estructura de edad. La COVID-19 va con tasa cruda y «demás causas» incluye COVID-19.")


def resumen_conjuntos(r):
    a, b = r["conjunto"]["irr"].set_index("causa"), r["conjunto_covid"]["irr"].set_index("causa")
    c = CAUSA_FOCO
    return (f"sin COVID-19 (2020–2025, n = {r['conjunto']['n']}), «{NOMBRES[c]}» tiene IRR {fmt(a.loc[c, 'irr_por_duplicacion'], 2)} (IC 95 % {fmt(a.loc[c, 'ic95_inf'], 2)} a {fmt(a.loc[c, 'ic95_sup'], 2)}, p de Holm {pf(a.loc[c, 'p_holm'])}); con COVID-19 (solo 2020–2022, n = {r['conjunto_covid']['n']}), {fmt(b.loc[c, 'irr_por_duplicacion'], 2)} (IC {fmt(b.loc[c, 'ic95_inf'], 2)} a {fmt(b.loc[c, 'ic95_sup'], 2)}, p de Holm {pf(b.loc[c, 'p_holm'])}) y la COVID-19 {fmt(b.loc['covid19', 'irr_por_duplicacion'], 2)} (IC {fmt(b.loc['covid19', 'ic95_inf'], 2)} a {fmt(b.loc['covid19', 'ic95_sup'], 2)}, p {pf(b.loc['covid19', 'p'])}). El resto de coeficientes es inestable entre ambas versiones (cambian de magnitud, signo o significación) y no se interpreta.")


def conclusiones(r, rb):
    t = r["transversal"]["2020_2025"]
    por, ver, forma = r["por_causa"].set_index("causa"), r["veredicto"], r["forma"]
    otros = por.loc["otros_accidentes_causas_externas"]
    sig_trans = t[t["p_holm"] < UMBRAL_P]
    sig_forma = forma[forma["p_holm"] < UMBRAL_P]
    L = ["## 6. Conclusiones", "",
         "- **Totales:** los totales nacionales de 2020 a 2025 coinciden exactamente con los del DANE (diferencia 0); la COVID-19 de las EEVV es menor que la del INS en 2021 y 2022.",
         f"- **Transversal:** tras Holm, {len(sig_trans)} de 14 asociaciones son significativas: " + "; ".join(f"{NOMBRES[f.causa]} con {f.resultado} (ρ = {fmt(f.rho, 2)}, p de Holm {pf(f.p_holm)})" for f in sig_trans.itertuples()) + ". Las asociaciones negativas con circulatorio, neoplasias y demás causas son compatibles con el efecto de la estructura de edad (tasas crudas) y no se interpretan.",
         f"- **Panel:** solo «{NOMBRES['otros_accidentes_causas_externas']}» cumple la regla de D107 (IRR {fmt(otros['irr_por_duplicacion'], 2)}, IC 95 % {fmt(otros['ic95_inf'], 2)} a {fmt(otros['ic95_sup'], 2)}, p de Holm {pf(otros['p_holm'])}; supuestos y sensibilidades superados): duplicar (1 + tasa) se asocia con una razón de tasas de contratos de {fmt(otros['irr_por_duplicacion'], 1)}. Las demás causas son **no concluyentes**. Homicidios no se asocian con la contratación funeraria (IRR {fmt(por.loc['agresiones_homicidios', 'irr_por_duplicacion'], 2)}, p {pf(por.loc['agresiones_homicidios', 'p'])}).",
         "- **Robustez (D107b, sección 3.5):** " + resumen_robustez(rb),
         "- **Transversal estandarizado (sección 2b):** " + resumen_estandarizado(rb),
         "- **Modelo conjunto:** " + resumen_conjuntos(r),
         "- **Supuestos:** todos los modelos pasan dispersión residual, residuos cuantílicos y Cook, y el modelo conjunto sin COVID-19 cumple VIF < 5 tras eliminar neoplasias. **Cameron-Trivedi (revisión, D107b):** la forma de la prueba era correcta; en transporte el t homocedástico (p 0,21) no detectaba la sobredispersión porque la varianza de la variable auxiliar crece con μ² bajo la alternativa. Con errores robustos HC3 la prueba rechaza H₀ en los siete modelos (transporte: t = " + fmt(r["supuestos"]["accidentes_transporte"]["diagnosticos"]["cameron_trivedi"]["estadistico_t"], 2) + ", p < 0,001) y todos pasan la sobredispersión.",
         f"- **Forma de compra:** {len(sig_forma)} asociación(es) significativa(s) tras Holm" + (": " + "; ".join(f"{x.participacion.replace('part_grupo', 'Grupo ')} con {NOMBRES[x.causa]} (ρ = {fmt(x.rho, 2)}, p de Holm {pf(x.p_holm)})" for x in sig_forma.itertuples()) if len(sig_forma) else "") + "; las demás no superan la corrección. Con 31 departamentos y tasas crudas, es una pista y no un resultado.",
         "- **Sobre la pregunta de partida:** la contratación funeraria pública no sigue la mortalidad violenta ni la COVID-19 de forma detectable en este diseño; la señal está en «otras causas externas (no homicidio ni transporte)» (que incluye suicidios y caídas), se mantiene con ruralidad y con edad estandarizada, pero no dentro de cada departamento a lo largo del tiempo; debe leerse como asociación ecológica entre departamentos, sin causalidad.", ""]
    return L


def informe(r, rb):
    gr = dispersion(r, "dispersion_homicidios_covid_contratos.png")
    L = ["# Causas de defunción y contratación funeraria pública por departamento (D107)", "",
         "> **Análisis exploratorio y ecológico (D107 aprobada por Edward el 2026-11-08; D107b, pendiente de revisión).** No se interpreta ninguna asociación como causal; la unidad es el departamento (la entidad contratante y el residente fallecido pueden estar en departamentos distintos). Rama `causas-defuncion`, sin integrar a `main`.", ""]
    L += seccion_datos(r) + seccion_transversal(r) + seccion_estandarizada(r, rb) + seccion_panel(r) + seccion_robustez(r, rb) + seccion_forma(r)
    L += ["## 5. Gráfico", "", "![Dispersión de homicidios y COVID-19 frente a contratos por 100.000](graficos/causas/dispersion_homicidios_covid_contratos.png)", "",
          "Un punto por departamento. Izquierda: tasa de homicidios promedio 2020–2025 frente a contratos por 100.000 (promedio anual 2020–2025). Derecha: tasa de COVID-19 promedio 2020–2022 frente a contratos por 100.000 en esos tres años (el ρ del gráfico es descriptivo y difiere del transversal de la sección 2, que usa 2020–2025). Se rotulan los puntos extremos.", ""]
    L += conclusiones(r, rb) + ["## 7. Limitaciones", ""] + [f"{i}. {x}" for i, x in enumerate(LIMITACIONES, 1)]
    destino = RAIZ / "docs/resultados/causas_defuncion.md"
    destino.write_text(chr(10).join(L).rstrip() + chr(10), encoding="utf-8")
    return destino


def main():
    warnings.filterwarnings("ignore")
    r = calcular()
    guardar(r)
    rb = calcular_robustez(r)
    guardar_robustez(rb, SALIDA)
    print(informe(r, rb))


if __name__ == "__main__":
    main()
