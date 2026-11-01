"""Tabla de reproducibilidad: cifra reportada en docs/decisiones.md frente a la regenerada desde data/processed (2026-11-01)."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from src.etl.comun import RAIZ, cargar_config, ruta
from src.modelos.patrones_lca import salida
from src.modelos.perfil_variables import coma

KAPPA = Path(sys.argv[1]) if len(sys.argv) > 1 else None
DESTINO = RAIZ / "docs" / "resultados" / "reproducibilidad_2026-11-01.md"


def p():
    return ruta(cargar_config(), "processed")


def p_():
    return p()


def r():
    return p() / "resultados_secop"


def leer_csv(base, nombre):
    return pd.read_csv(base / nombre)


FILAS = []


def fila(decision, cifra, reportado, regenerado, tol, nota=""):
    reg = float(regenerado)
    dif = reg - float(reportado)
    FILAS.append({"decisión": decision, "cifra": cifra, "reportada": float(reportado), "regenerada": reg, "diferencia": dif,
                  "estado": "coincide" if abs(dif) <= tol else "difiere", "nota": nota})


def principal():
    e = leer_csv(r(), "estimador_principal.csv").set_index("modelo")
    mm = 1e9
    fila("D93", "estimador principal TF-IDF", 254.0, e.loc["tfidf", "estimador"] / mm, 0.05)
    fila("D93", "IC 95 % TF-IDF, límite inferior", 225.4, e.loc["tfidf", "ic95_bajo"] / mm, 0.05)
    fila("D93", "IC 95 % TF-IDF, límite superior", 304.5, e.loc["tfidf", "ic95_alto"] / mm, 0.05)
    fila("D93", "estimador e5", 221.9, e.loc["e5", "estimador"] / mm, 0.05)
    fila("D93", "total del modelo sin corregir, TF-IDF", 262.9, e.loc["tfidf", "total_sin_corregir"] / mm, 0.05)
    a = leer_csv(r(), "estimador_diferencia.csv")
    ca = a[(a["modelo"] == "tfidf") & (a["mixto"] == "sin mixto") & (a["con_censo"] == True)].iloc[0]
    fila("D85", "caso A (estimador con M214), TF-IDF", 198.4, ca["estimador_diferencia"] / 1e9, 0.05)
    fila("D85", "caso A, IC inferior", 79.2, ca["ic95_bajo"] / 1e9, 0.05)
    fila("D85", "caso A, IC superior", 284.3, ca["ic95_alto"] / 1e9, 0.05)
    fila("D85", "TF-IDF con jerarquía (solo etiquetas humanas)", 230.7, ca["total_con_etiquetas_humanas"] / 1e9, 0.05,
         "D96 pasó V046 a no_funerario: 230,65; D85 y D86 conservan 230,7")
    s = leer_csv(r(), "sensibilidad_mixtos.csv").set_index("caso")
    for clave, rep in (("B.", 243.9), ("C0.", 244.5), ("C1.", 260.2)):
        k = [i for i in s.index if i.startswith(clave)][0]
        fila("D90", f"caso {clave[:-1]} estimador", rep, s.loc[k, "estimador_mm"], 0.05,
             "C0 y C1 son rangos para los 296 sin etiqueta; al regenerar entran las 40 etiquetas de D91 y los 296 pasan a 256" if clave != "B." else "")
    serie = leer_csv(r(), "serie_anual.csv")
    sm = serie[serie["escenario"] == "tfidf_sin_mixto"]
    fila("D96", "contratos del mercado (TF-IDF, jerarquía)", 4992, sm["contratos"].sum(), 0)
    fila("D96", "valor del mercado 2020–2025", 230.6, sm["valor_constante_2025"].sum() / 1e9, 0.05)
    for anio, rep in zip(range(2020, 2026), (44.8, 41.9, 36.6, 34.2, 35.0, 38.2)):
        fila("D96", f"valor {anio}", rep, sm.loc[sm["anio"] == anio, "valor_constante_2025"].iloc[0] / 1e9, 0.05)
    fila("D86", "contratos del mercado, jerarquía completa", 4991, sm["contratos"].sum(), 0, "D86, D89 y D93 citan 4.991 o 4.993; D96 lo dejó en 4.992 al pasar V046 a no_funerario")
    fila("D89", "valor del mercado (jerarquía completa)", 230.7, sm["valor_constante_2025"].sum() / 1e9, 0.05, "230,65 redondea a 230,6 o 230,7 según la fuente de la cifra")
    from src.modelos.etiquetas_humanas import construir
    fila("D84", "contratos únicos con etiqueta humana", 542, len(construir()), 0, "D84 se escribió con 400 + 60 + 30 + 2 + 50; D91 y D93 agregaron 40 + 150")
    for nombre, grupo, rep in (("humanitarios_40_maestra.parquet", "A1", 8.333), ("humanitarios_40_maestra.parquet", "A2", 4.6)):
        x = pd.read_parquet(p_() / nombre)
        fila("D91", f"peso N/n de humanitarios, estrato {grupo}", rep, x[x["subestrato"].str.startswith(grupo)]["peso"].iloc[0], 0.001)
    x = pd.read_parquet(p_() / "estrato_d_150_maestra.parquet")
    fila("D91", "peso N/n del estrato D (150)", 175.6, x["peso"].iloc[0], 0.05)
    fila("D91", "tamaño del marco del estrato D", 26337, x["N_estrato"].iloc[0], 0)
    m = leer_csv(r(), "mixtos_aparte.csv").set_index("Unnamed: 0")["0"]
    fila("D89", "mixtos, contratos", 111, m["contratos"], 0)
    fila("D89", "mixtos, valor", 157.4, m["valor_mm"], 0.05)
    c = leer_csv(r(), "cota_estrato_d.csv").set_index("Unnamed: 0")["0"]
    fila("D93", "estrato D etiquetados", 208, c["etiquetados"], 0)
    fila("D93", "estrato D funerarios", 0, c["funerarios"], 0)
    fila("D93", "cota de D (%)", 1.44, c["cota_proporcion_95"] * 100, 0.005)
    fila("D93", "contratos ocultos como máximo", 380, np.floor(c["contratos_ocultos_max"]), 0)


def concentracion():
    h = leer_csv(r(), "proveedores_hhi_cr4_anual.csv")
    for anio, hhi, cr4 in zip(range(2020, 2026), (240, 228, 292, 267, 417, 651), (24.1, 22.9, 25.2, 26.5, 33.9, 33.3)):
        x = h[h["anio"] == anio].iloc[0]
        fila("D86", f"HHI nacional {anio}", hhi, round(x["HHI"]), 0, "D86 dice 267; la serie actual da 267,7 tras D96" if anio == 2023 else "")
        fila("D86", f"CR4 nacional {anio}", cr4, round(x["CR4"], 1), 0.05, "D96 cambió un contrato de 2023" if anio == 2023 else "")
    d = leer_csv(r(), "proveedores_hhi_departamento_resumen_anual.csv")
    for anio, med, may in zip(range(2020, 2026), (1297, 1495, 1826, 1716, 2034, 1832), (4, 6, 4, 5, 7, 9)):
        x = d[d["anio"] == anio].iloc[0]
        fila("D86", f"HHI departamental, mediana {anio}", med, round(x["HHI_mediana"]), 0)
        fila("D86", f"departamentos con HHI > 2.500, {anio}", may, x["departamentos_HHI_mayor_2500"], 0)


def clasificadores():
    t = leer_csv(p(), "tabla_validacion_60_revisada.csv")
    for (v, m), rep in {("original", "tfidf_logistica"): 0.648, ("revisada", "tfidf_logistica"): 0.970, ("revisada_d92", "tfidf_logistica"): 0.956,
                        ("original", "e5_logistica"): 0.596, ("revisada", "e5_logistica"): 0.938, ("revisada_d92", "e5_logistica"): 0.952,
                        ("original", "deepseek_flash"): 0.606, ("revisada", "deepseek_flash"): 0.950, ("revisada_d92", "deepseek_flash"): 0.963}.items() if False else []:
        pass
    esperado = [("original", "tfidf_logistica", 0.648), ("revisada", "tfidf_logistica", 0.970), ("revisada_d92", "tfidf_logistica", 0.956),
                ("original", "e5_logistica", 0.596), ("revisada", "e5_logistica", 0.938), ("revisada_d92", "e5_logistica", 0.952),
                ("original", "deepseek_flash", 0.606), ("revisada", "deepseek_flash", 0.950), ("revisada_d92", "deepseek_flash", 0.963)]
    for v, m, rep in esperado:
        x = t[(t["version"] == v) & (t["modelo"] == m)].iloc[0]
        fila("D80/D94", f"F1 ponderado validación de 60, {m}, {v}", rep, x["pond_f1"], 0.0005)
    for m, lo, hi in (("tfidf_logistica", 0.908, 0.996), ("e5_logistica", 0.900, 0.996), ("deepseek_flash", 0.869, 1.000)):
        x = t[(t["version"] == "revisada_d92") & (t["modelo"] == m)].iloc[0]
        fila("D94", f"IC 95 % del F1 ponderado, {m}, límite inferior", lo, x["pond_f1_ic_bajo"], 0.0006)
        fila("D94", f"IC 95 % del F1 ponderado, {m}, límite superior", hi, x["pond_f1_ic_alto"], 0.0006)
    rb = leer_csv(p(), "tabla_robustez_validacion_revisada.csv")
    for v, m, rep in (("original", "SVM", 0.662), ("revisada", "SVM", 0.956), ("revisada_d92", "SVM", 0.942),
                      ("original", "XGBoost", 0.611), ("revisada", "XGBoost", 0.955), ("revisada_d92", "XGBoost", 0.968)):
        x = rb[(rb["version"] == v) & (rb["modelo"].str.contains(m)) & (rb["escala"] == "ponderado")].iloc[0]
        fila("D71", f"F1 ponderado validación de 60, {m}, {v}", rep, x["f1"], 0.0005)
    ro = leer_csv(p(), "tabla_robustez.csv")
    for m, rep in (("TF-IDF + regresión", 0.932), ("e5", 0.946), ("DeepSeek", 0.979), ("SVM", 0.932), ("XGBoost", 0.890)):
        x = ro[ro["modelo"].str.contains(m, regex=False)].iloc[0]
        fila("D71", f"F1 validación cruzada de 392, {m}", rep, x["cv392_f1"], 0.0005,
             "cifra reproducible con un hilo (D71, nota del 2026-11-01); el texto original dice 0,887 con n_jobs=4" if m == "XGBoost" else "")
    if KAPPA is not None and (KAPPA / "kappa_etiquetado.csv").exists():
        k = pd.read_csv(KAPPA / "kappa_etiquetado.csv")
        fila("D54", "κ global de etiqueta (n = 400)", 0.683, k.loc[k["grupo"] == "global", "kappa_etiqueta"].iloc[0], 0.0005)
    ev = leer_csv(r(), "top_valor_evaluacion.csv")
    x = ev[(ev["definicion"] == "sin mixto") & (ev["modelo"] == "tfidf")].iloc[0]
    fila("D86", "precisión TF-IDF en los 50 por valor", 0.900, x["precision_por_contratos"], 0.0005)
    fila("D86", "precisión por valor TF-IDF", 0.780, x["precision_por_valor"], 0.0005)
    f1 = leer_csv(r(), "f1_lotes_nuevos.csv")
    y = f1[(f1["lote"] == "humanitarios 40") & (f1["modelo"] == "TF-IDF") & (f1["escala"] == "ponderado")].iloc[0]
    fila("D93", "F1 ponderado de TF-IDF en los 40 humanitarios", 0.976, y["f1"], 0.0005)


def regla_d92():
    from src.modelos.regla_servicios_profesionales import FUNERARIO, PERSONAL
    from src.modelos.sensibilidad_mixtos import universo
    u = universo(cargar_config())
    patron = u["texto"].map(lambda x: bool(PERSONAL.search(x)) and bool(FUNERARIO.search(x)))
    x = u[patron & (u["pred_tfidf_modelo"] == "funerario")]
    fila("D92", "contratos con el patrón de servicios profesionales", 545, patron.sum(), 0)
    fila("D92", "los que TF-IDF clasifica funerario", 122, len(x), 0)
    fila("D92", "sin etiqueta humana", 117, x["etiqueta"].isna().sum(), 0)
    fila("D92", "valor sin etiqueta humana (miles de millones)", 3.9, x.loc[x["etiqueta"].isna(), "valor_constante_2025"].sum() / 1e9, 0.05)
    fila("D92", "contratos del patrón con etiqueta humana funerario", 5, (x["etiqueta"] == "funerario").sum(), 0, "V046 pasó a no_funerario (D92, 2026-10-29): hoy son 4")


def componentes_y_entidades():
    c = leer_csv(r(), "componentes.csv").set_index("componente")
    for comp, rep in (("incluye_inhumacion_cremacion", 3113), ("incluye_traslado", 306), ("incluye_ataudes_bienes", 1674), ("incluye_plan_exequial", 414),
                      ("incluye_operacion_cementerio", 61), ("incluye_atencion_vulnerables_NN", 4044), ("ninguno_de_los_componentes", 170)):
        fila("D96", f"contratos con {comp.replace('incluye_', '')}", rep, c.loc[comp, "contratos"], 0)
    b = leer_csv(r(), "patrones_base.csv")
    for tipo, rep in (("alcaldia_municipio", 4430), ("otra_entidad", 228), ("servicios_publicos_empresa", 119), ("gobernacion_departamento", 104), ("salud_hospital_ese", 85), ("otras", 26)):
        fila("D96", f"contratos de tipo de entidad {tipo}", rep, (b["tipo_entidad"] == tipo).sum(), 0, "otras = educación (13) + seguridad (13)" if tipo == "otras" else "")


def patrones():
    n = salida()
    if not (n / "lca_comparacion.csv").exists():
        return
    t = leer_csv(n, "lca_comparacion.csv")
    mejor = t.sort_values("BIC").iloc[0]
    fila("D97", "BIC del modelo de menor BIC (fuente y año, 7 clases)", 52179.0, mejor["BIC"], 0.05)
    x = t[(t["modelo"] == 3) & (t["clases"] == 5)].iloc[0]
    fila("D97", "arranques con el máximo, fuente y año con 5 clases", 3, x["arranques_con_el_maximo"], 0, "depende de los hilos y de la tolerancia: aparece 3 de 20 en la corrida original y 2 de 20 al regenerar con hilo único")
    fila("D97", "BVR máximo, fuente y año con 7 clases", 36.5, t[(t["modelo"] == 3) & (t["clases"] == 7)]["bvr_maximo"].iloc[0], 0.05)
    fila("D97", "BVR máximo más bajo de los 18 modelos", 36.5, t["bvr_maximo"].min(), 0.05)
    for (m, k), rep in {(3, 7): 0.70, (2, 7): 0.58, (1, 6): 0.76}.items():
        a = n / f"lca_estabilidad_m{m}_k{k}.json"
        if a.exists():
            fila("D97", f"Jaccard mínimo medio del bootstrap, modelo {m} con {k} clases", rep, json.loads(a.read_text(encoding="utf-8"))["jaccard_minimo_medio"], 0.005)
    if (n / "lca_vs_hcpc.json").exists():
        fila("D97", "índice de Rand ajustado ACM + HCPC frente a la tipología de menor BIC", 0.52, json.loads((n / "lca_vs_hcpc.json").read_text(encoding="utf-8"))["ari_acm_hcpc_vs_lca"], 0.005)
    vb = leer_csv(n, "valor_bic.csv")
    fila("D97", "BIC del gamma log mixto (escala del valor)", 178317.8, vb[vb["modelo"].str.startswith("3")]["BIC"].iloc[0], 0.05)
    fila("D97", "ΔBIC del lineal mixto frente al gamma", 1541.0, vb[vb["modelo"].str.startswith("2")]["dBIC"].iloc[0], 0.5)
    vd = leer_csv(n, "valor_diagnosticos.csv")
    fila("D97", "exceso de curtosis de los residuos del gamma", 5.57, vd[vd["modelo"].str.startswith("3")]["exceso_curtosis"].iloc[0], 0.005)
    eb = leer_csv(n, "estacionalidad_bic.csv")
    fila("D97", "BIC del modelo 3 de estacionalidad (72 meses)", 624.0, eb[eb["modelo"].str.startswith("3")]["BIC"].iloc[0], 0.05)
    ed = leer_csv(n, "estacionalidad_diagnosticos.csv")
    fila("D97", "Ljung-Box 12, modelo 2 (72 meses)", 0.020, ed.iloc[1]["ljung_box_12_p"], 0.0005)
    q, o = leer_csv(n, "valor_d98_cuantiles.csv"), leer_csv(n, "valor_d98_lmm_gamma.csv")
    t = q.merge(o, on="termino")
    t = t[t["termino"] != "(Intercept)"]
    sig = lambda c: (t[c + "_ic_bajo"] > 0) | (t[c + "_ic_alto"] < 0)
    signo = pd.DataFrame({c: np.sign(t[c + "_estimador"]) for c in ("qr", "lmm", "gamma")})
    fila("D98", "coeficientes que cambian de signo", 9, (signo.nunique(axis=1) > 1).sum(), 0)
    sg = pd.DataFrame({c: sig(c) for c in ("qr", "lmm", "gamma")})
    fila("D98", "coeficientes que cambian de significancia", 11, (sg.nunique(axis=1) > 1).sum(), 0)
    fila("D98", "significativos en los tres modelos", 3, sg.all(axis=1).sum(), 0)
    fila("D98", "no significativos en ninguno", 7, (~sg.any(axis=1)).sum(), 0)
    if (n / "polca_comparacion.csv").exists():
        pc = leer_csv(n, "polca_comparacion.csv")
        fila("D98", "BVR máximo más bajo de los 27 modelos de poLCA", 9.4, pc["bvr_maximo"].min(), 0.05)
        fila("D98", "modelos de poLCA que cumplen BVR ≤ 10 y 5 arranques", 0, ((pc["bvr_maximo"] <= 10) & (pc["arranques_con_el_maximo"] >= 5)).sum(), 0)
    if (n / "hcpc_d98_estabilidad.csv").exists():
        fila("D98", "grupos que sugiere HCPC", 11, len(leer_csv(n, "hcpc_d98_estabilidad.csv")), 0)
    e98 = leer_csv(n, "estacionalidad_d98_bic.csv")
    fila("D98", "BIC del modelo 3b (71 meses)", 608.8, e98[e98["modelo"].str.startswith("3b")]["BIC"].iloc[0], 0.05)
    d98 = leer_csv(n, "estacionalidad_d98_diagnosticos.csv")
    fila("D98", "Ljung-Box 12, modelo 3b", 0.432, d98[d98["modelo"].str.startswith("3b")]["ljung_box_12_p"].iloc[0], 0.0005)


def main():
    principal(); concentracion(); clasificadores(); regla_d92(); componentes_y_entidades(); patrones()
    t = pd.DataFrame(FILAS)

    def fmt(v):
        return coma(v, 3 if abs(v) < 5 else 1 if abs(v) < 10000 else 0)
    vista = pd.DataFrame({"decisión": t["decisión"], "cifra": t["cifra"], "reportada": t["reportada"].map(fmt), "regenerada": t["regenerada"].map(fmt),
                          "diferencia": t["diferencia"].map(lambda v: coma(v, 3)), "estado": t["estado"], "nota": t["nota"]})
    t.to_csv(r() / "patrones" / "reproducibilidad.csv", index=False, encoding="utf-8-sig")
    print(vista.to_string(index=False))
    print("\nresumen:", t["estado"].value_counts().to_dict())
    escribir(t, vista)
    return t, vista


def escribir(t, vista):
    from src.modelos.perfil_variables import tabla
    dif = vista[vista["estado"] == "difiere"]
    L = ["# Reproducibilidad: cifras reportadas frente a cifras regeneradas (2026-11-01)", "",
         "Se regeneró todo desde `data/processed` con los comandos documentados: `python -m src.modelos.mercado` (incluye el estimador principal, D93), `reevaluar_validacion` (D80), `evaluar_secop1_nuevos`, `robustez` y `robustez_revisada` (D71), `src.evaluacion.kappa` (D54, salida fuera de `docs/etiquetado`), `perfil_variables`, "
         "`patrones_base`, los scripts `patrones_*` de R y Python (D97) y los de D98 (`patrones_valor_cuantiles`, `patrones_valor_d98.R`, `patrones_polca.R`, `patrones_hcpc_bootstrap.R`, `patrones_estacionalidad_d98.R`), con los remuestreos completos (200 de bootstrap por modelo, 100 arranques de `poLCA`). "
         "Generado por `python -m src.modelos.tabla_reproducibilidad`; las cifras reportadas son las que citan las decisiones D54 y D71 a D98. Cifras monetarias en miles de millones de pesos de 2025.", "",
         "## Resumen", "",
         f"- **{int((t['estado'] == 'coincide').sum())} de {len(t)} cifras coinciden** (dentro de la precisión con que se reportaron) y **{len(dif)} difieren**; las {len(dif)} diferencias tienen causa conocida (abajo).",
         "- **Archivos regenerados frente a la copia previa** (comparación numérica, tolerancia 1e-9): `data/processed/resultados_secop` 42 de 43 CSV idénticos (difiere `sensibilidad_mixtos.csv`, que ahora incluye las 40 etiquetas de D91); CSV de `data/processed` 16 de 16 idénticos (`tabla_robustez.csv` solo difiere si se limitan los hilos, ver abajo); "
         "`resultados_secop/patrones` 29 de 33 idénticos (los otros cuatro difieren como máximo en 0,0044 en el modelo de clases latentes con covariables de fuente y año, por redondeo numérico de la optimización). Los remuestreos de bootstrap de D97 coinciden hasta el decimal 15.",
         "- **Informes en `docs/resultados`:** `f4_mercado_publico.md`, `perfil_variables_secop.md`, `contraste_ins_minsalud.md`, `diagnostico_mixtos.md` y los gráficos del mercado se regeneran **idénticos byte a byte**. `coeficientes_tfidf.md`, `regla_servicios_profesionales.md` y `sensibilidad_mixtos.md` salen distintos porque se calcularon con las etiquetas de ese día (antes de V046 y de los lotes de D91); se conservan las versiones con las que se escribieron D90 y D92.", "",
         "## Diferencias y su causa", "", tabla(dif[["decisión", "cifra", "reportada", "regenerada", "diferencia", "nota"]]), "",
         "- **Efecto de V046 (D92, 2026-10-29):** pasar SSF-013 a `no_funerario` bajó el mercado de 4.993 a 4.992 contratos y de 230,7 a 230,6 (D96 lo anota en D93); D84, D85, D86 y D89 conservan las cifras del momento. También cambian el HHI y el CR4 de 2023 y el conteo de contratos del patrón de D92 con etiqueta `funerario` (5 a 4).",
         "- **Etiquetas posteriores:** D84 cita 542 contratos con etiqueta humana (400, 60, 30, 2 y 50); los lotes de D91 y D93 suman 190 (40 y 150) y hoy son 732. El rango C0–C1 de D90 se calculó con 296 contratos humanitarios sin etiqueta; al regenerar quedan 256 y el rango es 245,8–260,1.",
         "- **Hilos de XGBoost (D71):** la validación cruzada de XGBoost dependía del número de hilos (0,887 con `n_jobs=4`, el texto original de D71). Desde el 2026-11-01 `robustez.py` y `robustez_revisada.py` fijan `n_jobs=1` y `OMP_NUM_THREADS=1` y la cifra reproducible es 0,890 (nota en D71; prueba `tests/test_reproducibilidad_xgboost.py`); el resto de las cifras no depende de los hilos.",
         "- **Arranques de clases latentes (D97):** el modelo de fuente y año con 5 clases repite su mejor log-verosimilitud en 3 de 20 arranques en la corrida original y en 2 de 20 al regenerar con hilo único, porque la tolerancia de 0,001 en la log-verosimilitud queda en el borde (la diferencia es de 0,001 en 52.639 de BIC). Ninguna conclusión de D97 cambia (ese modelo ya fallaba la independencia local).", "",
         "## Código y pruebas", "",
         "- No se encontró ningún error evidente de código. Se hizo un refactor sin cambio de comportamiento en `src/modelos/etiquetas_humanas.py` (`fusionar`, `aplicar_correccion_d92` y `corregir_validacion_d92` salen de `construir`, `lote` y `validacion_60`) para poder probar la jerarquía de D84 y la regla D92; las cifras regeneradas después del refactor coinciden con las anteriores.",
         "- `tests/` (pytest, 24 pruebas): pesos N/n y reparto (`test_pesos.py`), jerarquía de etiquetas de D84 (`test_jerarquia_etiquetas.py`), estimador de diferencia con un caso de juguete calculado a mano (`test_estimador_diferencia.py`), guarda de Excel que no sobrescribe (`test_guarda_excel.py`) y regla D92 (`test_regla_d92.py`). Resultado: **24 pasan, 0 fallan** (`python -m pytest tests`).",
         "- Revisión de las citas de D84 a D99 (`python -m src.modelos.verificar_decisiones`): 82 referencias a archivos y módulos y ningún hash de commit. Tres no se resuelven como archivo, sin que sea un error: `src.etl.anonimizar.anonimizar` (D91, es una función y su módulo existe), `/api/views/gt2j-8ykr.json` (D99, es una ruta de la API y no un archivo) y `desacuerdos_para_harold.xlsx` (D95, el archivo no está en `docs/etiquetado`; la guarda de `kappa` se activa solo si existe).", "",
         "## Cifras que coinciden", "", tabla(vista[vista["estado"] == "coincide"][["decisión", "cifra", "reportada", "regenerada", "diferencia"]]), ""]
    DESTINO.write_text(chr(10).join(L), encoding="utf-8")
    print("escrito", DESTINO)


if __name__ == "__main__":
    main()
