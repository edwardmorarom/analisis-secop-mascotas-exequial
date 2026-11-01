"""Sección «Análisis exploratorio (D98)» de docs/resultados/patrones_compra.md."""
import json

import numpy as np
import pandas as pd

from src.modelos.patrones_informe import f, leer, regla
from src.modelos.patrones_lca import salida
from src.modelos.perfil_variables import tabla


def existe(nombre):
    return (salida() / nombre).exists()


def seccion_valor():
    q = leer("valor_d98_cuantiles.csv")
    o = leer("valor_d98_lmm_gamma.csv")
    t = q.merge(o, on="termino")
    t = t[t["termino"] != "(Intercept)"].copy()

    def firma(lo, hi):
        return "sí" if (lo > 0 or hi < 0) else "no"

    for c in ("qr", "lmm", "gamma"):
        t[c + "_sig"] = [firma(a, b) for a, b in zip(t[c + "_ic_bajo"], t[c + "_ic_alto"])]
        t[c + "_signo"] = np.sign(t[c + "_estimador"])
    t["cambia_signo"] = t[["qr_signo", "lmm_signo", "gamma_signo"]].nunique(axis=1) > 1
    t["cambia_significancia"] = t[["qr_sig", "lmm_sig", "gamma_sig"]].nunique(axis=1) > 1

    def celda(r, c):
        return f"{f(r[c + '_estimador'], 3)} ({f(r[c + '_ic_bajo'], 3)} a {f(r[c + '_ic_alto'], 3)})"

    vista = pd.DataFrame({"término": t["termino"], "mediana (IC 95 % bootstrap por entidad)": t.apply(lambda r: celda(r, "qr"), axis=1),
                          "lineal mixto, errores robustos (IC 95 %)": t.apply(lambda r: celda(r, "lmm"), axis=1),
                          "gamma log mixto (IC 95 % de Wald)": t.apply(lambda r: celda(r, "gamma"), axis=1),
                          "significativo (mediana / lineal / gamma)": t.apply(lambda r: f"{r['qr_sig']} / {r['lmm_sig']} / {r['gamma_sig']}", axis=1),
                          "cambia de signo": t["cambia_signo"].map({True: "sí", False: "no"}),
                          "cambia de significancia": t["cambia_significancia"].map({True: "sí", False: "no"})})
    cs = t[t["cambia_signo"]]["termino"].tolist()
    cg = t[t["cambia_significancia"]]["termino"].tolist()
    texto = ["### 1. Valor: regresión por cuantiles frente a los modelos de D97", "",
             "Modelo principal: regresión por cuantiles en la **mediana** del log del valor constante de 2025, con las explicativas de D97 y bootstrap agrupado por entidad (500 remuestreos, semilla 2034, 912 entidades). "
             "Sensibilidad: el lineal mixto de D97 con errores robustos agrupados por entidad (CR1) y el gamma log mixto de D97. Los coeficientes de la mediana y del lineal mixto están en escala log del valor; los del gamma, en escala log de la media, "
             "y son comparables en signo y significancia, no en magnitud. Referencias: alcaldía y municipio; mínima cuantía; 2020; SECOP I.", "", tabla(vista), "",
             f"- **Cambian de signo** entre los tres estimadores puntuales: {len(cs)} de {len(t)} coeficientes" + (f" ({', '.join(cs)})." if cs else "."),
             f"- **Cambian de significancia** (al 5 %) entre los tres: {len(cg)} de {len(t)}" + (f" ({', '.join(cg)})." if cg else "."),
             f"- Significativos en los tres a la vez: {int(((t['qr_sig'] == 'sí') & (t['lmm_sig'] == 'sí') & (t['gamma_sig'] == 'sí')).sum())}; no significativos en ninguno: {int(((t['qr_sig'] == 'no') & (t['lmm_sig'] == 'no') & (t['gamma_sig'] == 'no')).sum())}.", ""]
    return "\n".join(texto)


def seccion_estacionalidad():
    eb = leer("estacionalidad_d98_bic.csv")
    ed = leer("estacionalidad_d98_diagnosticos.csv")
    co = leer("estacionalidad_d98_coeficientes.csv")
    nt = leer("estacionalidad_d98_notas.csv")
    ee = eb.merge(ed, on="modelo")
    sel = regla(eb, ee["falla_alguna"].to_numpy())
    tab = pd.DataFrame({"modelo": ee["modelo"], "parámetros": ee["parametros"], "BIC (71 meses)": ee["BIC"].map(lambda v: f(v, 1)), "ΔBIC": ee["dBIC"].map(lambda v: f(v, 1)),
                        "Ljung-Box 6 (p)": ee["ljung_box_6_p"].map(lambda v: f(v, 3)), "Ljung-Box 12 (p)": ee["ljung_box_12_p"].map(lambda v: f(v, 3)),
                        "asimetría RQ": ee["asimetria_rq"].map(lambda v: f(v, 2)), "exceso de curtosis RQ": ee["exceso_curtosis_rq"].map(lambda v: f(v, 2)),
                        "supuestos que falla": ee.apply(lambda r: ", ".join(n for n, x in (("sobredispersión", r.falla_sobredispersion), ("autocorrelación", r.falla_autocorrelacion),
                                                                                         ("normalidad RQ", r.falla_normalidad_rq)) if x) or "ninguno", axis=1)})
    clave = co[co["termino"].str.match(r"^(lagy|covid|t|s12|c12|s6|c6)\d?$")].copy()
    clave["término"] = clave["termino"].str.replace(r"(lagy|covid)1$", r"\1", regex=True).map({"lagy": "autorregresivo log(conteo previo + 1)", "covid": "indicadora jul–sep 2020", "t": "tendencia (por mes)",
                                                                                              "s12": "seno 12 meses", "c12": "coseno 12 meses", "s6": "seno 6 meses", "c6": "coseno 6 meses"})
    clave["modelo corto"] = clave["modelo"].str[:2]
    ct = pd.DataFrame({"modelo": clave["modelo corto"], "término": clave["término"], "estimador": clave["estimador"].map(lambda v: f(v, 3)),
                       "EE del modelo": clave["se_modelo"].map(lambda v: f(v, 3)), "EE Newey-West": clave["se_newey_west"].map(lambda v: f(v, 3)),
                       "p del modelo": clave["p_modelo"].map(lambda v: f(v, 4)), "p Newey-West": clave["p_newey_west"].map(lambda v: f(v, 4))})
    d97 = leer("estacionalidad_diagnosticos.csv")
    pasan = ee[~ee["falla_alguna"]]["modelo"].tolist()
    texto = ["### 3. Estacionalidad: término autorregresivo e indicadora de julio a septiembre de 2020", "",
             f"Todos los modelos se ajustan a los mismos {int(nt['n'].iloc[0])} meses (febrero de 2020 a diciembre de 2025), porque el término autorregresivo no existe en enero de 2020. Los modelos 1, 2 y 3 son los de D97 reajustados a esos 71 meses; "
             "2b y 3b agregan `log(conteo del mes anterior + 1)` y una indicadora de julio, agosto y septiembre de 2020 (aproximación del pico de mortalidad por COVID-19, sin verificar con la serie mensual del INS; D98).", "", tabla(tab), "",
             f"- **Pasan todos los supuestos:** {', '.join(m.split()[0] for m in pasan) if pasan else 'ninguno'}. Aplicando la regla de BIC de D97 entre ellos, **queda {sel['modelo'] if sel is not None else 'ninguno'}**" +
             (f" (ΔBIC de {f(eb.sort_values('BIC').iloc[1]['dBIC'], 1)} frente al siguiente, {eb.sort_values('BIC').iloc[1]['modelo'].split()[0]}; mayor que 2, así que no entra la cláusula del más simple)." if sel is not None else "."),
             f"- **Sensibilidad del Ljung-Box a la muestra:** con los 72 meses de D97, los modelos 2 y 3 daban p = {f(d97.iloc[1]['ljung_box_12_p'], 3)} y {f(d97.iloc[2]['ljung_box_12_p'], 3)} a 12 rezagos (fallaban); con los 71 meses sin enero de 2020 dan p = {f(ed.iloc[1]['ljung_box_12_p'], 3)} y {f(ed.iloc[2]['ljung_box_12_p'], 3)} (pasan). "
             "Quitar un solo mes cambia la conclusión de autocorrelación en esos modelos, lo que indica que ese supuesto está cerca del umbral y que el resultado de D97 y el de aquí son frágiles.",
             f"- Errores estándar de Newey-West (Bartlett, rezago {int(nt['rezago_newey_west'].iloc[0])}, T = {int(nt['n'].iloc[0])}) frente a los del modelo de verosimilitud en los coeficientes de 2b y 3b:", "", tabla(ct), "",
             f"- La indicadora de julio a septiembre de 2020 y el término autorregresivo tienen p de Newey-West de {f(clave[clave['término'].str.startswith('indicadora')]['p_newey_west'].min(), 4)} a {f(clave[clave['término'].str.startswith('indicadora')]['p_newey_west'].max(), 4)} y de {f(clave[clave['término'].str.startswith('autorregresivo')]['p_newey_west'].min(), 3)} a {f(clave[clave['término'].str.startswith('autorregresivo')]['p_newey_west'].max(), 3)}, respectivamente. "
             f"Gráfico de las autocorrelaciones: `graficos/patrones/estacionalidad_d98_acf.png`.", ""]
    return "\n".join(texto)


def seccion_tipologia():
    t = leer("polca_comparacion.csv")
    top97 = leer("d98_bvr_completo_m3_k7.csv")
    top1 = leer("d98_bvr_completo_m1_k6.csv")
    t["falla_bvr"] = t["bvr_maximo"] > 10
    t["falla_arranques"] = t["arranques_con_el_maximo"] < 5
    t["falla_tamano"] = t["tamano_minimo_pct"] < 1
    t["cumple"] = ~(t["falla_bvr"] | t["falla_arranques"])
    vista = pd.DataFrame({"covariables": t["covariables"], "clases": t["clases"], "parámetros": t["parametros"], "BIC": t["BIC"].map(lambda v: f(v, 1)), "ΔBIC": t["dBIC"].map(lambda v: f(v, 1)),
                          "entropía relativa": t["entropia_relativa"].map(lambda v: f(v, 2)), "arranques con el máximo (de 100)": t["arranques_con_el_maximo"], "clase más pequeña (%)": t["tamano_minimo_pct"].map(lambda v: f(v, 1)),
                          "BVR máximo": t["bvr_maximo"].map(lambda v: f(v, 1)), "pares con BVR > 10": t["pares_bvr_mayor_10"],
                          "cumple (BVR ≤ 10 y ≥ 5 arranques)": t["cumple"].map({True: "sí", False: "no"})})

    def top(df, n=12):
        x = df.head(n).copy()
        return pd.DataFrame({"posición": x["posicion"], "variable 1": x["var1"], "variable 2": x["var2"], "BVR": x["bvr"].map(lambda v: f(v, 1))})

    r = top97[((top97["var1"] == "tipo_contrato_hom") & (top97["var2"] == "ataudes_bienes")) | ((top97["var2"] == "tipo_contrato_hom") & (top97["var1"] == "ataudes_bienes"))].iloc[0]
    texto = ["### 2. Tipología: sin variables redundantes y con `poLCA`", "",
             "**Paso 1: residuos bivariados más altos (BVR) del modelo de menor BIC de D97** (fuente y año, 7 clases):", "", tabla(top(top97)), "",
             "Y del de menor BIC sin covariables (6 clases):", "", tabla(top(top1)), "",
             f"**Paso 2: variables que se quitan.** `cuartil_valor` se quita siempre (el valor se modela aparte). El par `tipo_contrato_hom` con `ataudes_bienes` está en la posición {int(r['posicion'])} del modelo de menor BIC de D97 (BVR {f(r['bvr'], 1)}), "
             "fuera de los 5 más altos; por la regla de D98, **`tipo_contrato_hom` se conserva**. Quedan 10 variables: tipo de entidad, grupo de modalidad, tipo de contrato homologado, territorial o nacional y los seis componentes.", "",
             f"**Paso 3: `poLCA` (versión 1.6.0.2), 100 arranques, 2 a 10 clases, tres modelos.** Cumplen el criterio (BVR máximo ≤ 10 y mejor ajuste en al menos 5 arranques): **{int(t['cumple'].sum())} de {len(t)}**. "
             f"El BVR máximo más bajo alcanzado es {f(t['bvr_maximo'].min(), 1)} ({t.sort_values('bvr_maximo').iloc[0]['covariables']}, {int(t.sort_values('bvr_maximo').iloc[0]['clases'])} clases); "
             f"{int((~t['falla_arranques']).sum())} modelos repiten su mejor ajuste en al menos 5 arranques.", "", tabla(vista), ""]
    return "\n".join(texto), t


def md_d98():
    partes = ["", "## Análisis exploratorio (D98)", "",
              "**Esta sección es exploratoria.** D98 se decidió después de ver los resultados de D97 (ningún modelo cumplió los supuestos en ninguna pregunta); los umbrales y modelos de D97 no se tocaron y sus resultados siguen arriba. "
              "Los hallazgos de esta sección deben confirmarse antes de apoyar una conclusión. Descripción de los datos, sin conclusiones de negocio.", ""]
    partes.append(seccion_valor())
    tip, tabla_polca = seccion_tipologia() if existe("polca_comparacion.csv") else ("### 2. Tipología\n\nPendiente.", None)
    partes.append(tip)
    if tabla_polca is not None and not tabla_polca["cumple"].any():
        partes.append(seccion_hcpc(tabla_polca))
    elif tabla_polca is not None:
        partes.append(seccion_cumplen(tabla_polca))
    partes.append(seccion_estacionalidad())
    partes.append("
".join(["### Limitaciones del análisis exploratorio", "",
                             "- Los tres análisis se decidieron después de ver los resultados de D97; son exploratorios y no sustituyen a los de D97.",
                             "- **Valor:** los intervalos de la mediana por bootstrap agrupado son anchos en las categorías con pocos contratos (otras entidades, otras modalidades, operación de cementerio); los de Wald del gamma son los más angostos porque son del modelo y no robustos; "
                             "«cambia de signo» incluye coeficientes cercanos a cero, cuyo signo no es informativo; la regresión por cuantiles describe la mediana del log del valor y no la media, de modo que no es comparable en magnitud con el gamma.",
                             "- **Tipología:** `poLCA` con covariables no convergió a soluciones útiles a partir de 5 clases (clases vacías y BIC creciente), y sin covariables el único modelo con BVR ≤ 10 (10 clases) no reproduce su mejor ajuste; no se probó más de 100 arranques ni otro programa. "
                             "Los mayores residuos bivariados están entre componentes (traslado con atención a vulnerables, inhumación con plan exequial, ataúdes con operación de cementerio), que `poLCA` no logra explicar con clases. El ACM + HCPC es descriptivo, sin modelo probabilístico.",
                             "- **Estacionalidad:** la indicadora de julio a septiembre de 2020 es una aproximación sin verificar con la serie mensual del INS; el Ljung-Box de los modelos 2 y 3 cambia de conclusión al quitar enero de 2020 (con 72 meses fallaban, con 71 pasan), de modo que el supuesto está cerca del umbral y la elección del modelo 3b es frágil; "
                             "con 71 observaciones los errores de Newey-West tienen poca precisión.", ""]))
    return "\n".join(partes)


def seccion_hcpc(t):
    tam = leer("hcpc_d98_tamanos.csv")
    est = leer("hcpc_d98_estabilidad.csv")
    ine = leer("hcpc_d98_inercia.csv")
    vista = pd.DataFrame({"grupo": est["grupo"], "contratos": est["contratos"], "%": tam["pct"].map(lambda v: f(v, 1)), "Jaccard medio (bootstrap)": est["jaccard_medio"].map(lambda v: f(v, 2)),
                          "Jaccard percentil 5": est["jaccard_p05"].map(lambda v: f(v, 2)), "remuestreos en que se disuelve (Jaccard < 0,5, %)": est["pct_remuestreos_disueltos"].map(lambda v: f(v, 1))})
    bajos = t[t["bvr_maximo"] <= 10]
    matiz = ("; ".join(f"{r.covariables}, {int(r.clases)} clases (BVR máximo {f(r.bvr_maximo, 1)}, mejor ajuste en {int(r.arranques_con_el_maximo)} de 100 arranques, ΔBIC {f(r.dBIC, 1)})" for r in bajos.itertuples())
             if len(bajos) else "ninguno")
    degenerados = int((t["tamano_minimo_pct"] < 0.05).sum())
    return "\n".join([f"**Resultado: no hay tipología latente que cumpla independencia local.** Ninguno de los {len(t)} modelos de `poLCA` cumple a la vez BVR máximo ≤ 10 y mejor ajuste en al menos 5 de 100 arranques. "
                      f"Matiz: los modelos con BVR máximo ≤ 10 son: {matiz}; su mejor ajuste no se reproduce, de modo que no se distingue de un máximo local. "
                      f"En {degenerados} modelos con covariables la mejor solución tiene una clase vacía (0,0 %): el ajuste con covariables no convergió a una solución útil (el BIC de esos modelos sube con el número de clases). "
                      "Según D98, la tipología de clases latentes queda sin elegir y se deja el **ACM + HCPC solo como descripción**.", "",
                      f"**ACM + HCPC (descriptivo).** Variables: las 10 de arriba. Las dos primeras dimensiones retienen {f(ine['pct_varianza'].iloc[0], 1)} % y {f(ine['pct_varianza'].iloc[1], 1)} % de la inercia ({f(ine['pct_acumulado'].iloc[4], 1)} % las cinco primeras). "
                      f"HCPC sugiere {len(est)} grupos. Estabilidad por bootstrap (200 remuestreos, semilla 2034; Jaccard de cada grupo frente a su mejor coincidencia, umbral de 0,60):", "", tabla(vista), "",
                      f"{int((est['jaccard_medio'] < 0.60).sum())} de {len(est)} grupos tienen un Jaccard medio inferior a 0,60. Los dos grupos grandes (1 y 5, con {f(tam['pct'].iloc[0] + tam['pct'].iloc[4], 1)} % de los contratos) son los más estables; "
                      f"el grupo 7 (206 contratos) se disuelve en {f(est.loc[est['grupo'] == 7, 'pct_remuestreos_disueltos'].iloc[0], 0)} % de los remuestreos y los grupos 2, 3 y 8 tienen percentiles 5 de 0,07 a 0,33. "
                      f"El grupo 11 es un solo contrato y solo aparece en {int(est['remuestreos_validos'].iloc[-1])} de 200 remuestreos, así que su Jaccard no es informativo.", ""])


def seccion_cumplen(t):
    c = t[t["cumple"]].sort_values("BIC")
    return "\n".join(["**Hay modelos que cumplen el criterio de D98** (BVR máximo ≤ 10 y al menos 5 arranques con el mejor ajuste). Se listan en la tabla con «cumple = sí»; la estabilidad por bootstrap y la regla de BIC se aplican en la sección siguiente.", ""])
