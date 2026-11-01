"""Documento de cierre de F4 (docs/resultados/cierre_f4.md): las cifras se leen de los CSV de resultados, no se escriben a mano."""
import numpy as np
import pandas as pd

from src.etl.comun import RAIZ, cargar_config, ruta

SALIDA = RAIZ / "docs" / "resultados" / "cierre_f4.md"


def fm(v, n=1):
    s = f"{v:,.{n}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def mm(v, n=1):
    return fm(v / 1e9, n)


def tabla(filas, columnas):
    out = ["| " + " | ".join(columnas) + " |", "|" + "---|" * len(columnas)]
    out += ["| " + " | ".join(str(c) for c in f) + " |" for f in filas]
    return "\n".join(out)


def cargar():
    config = cargar_config()
    proc = ruta(config, "processed")
    res = proc / "resultados_secop"
    pat = res / "patrones"
    return proc, res, pat


def cifras():
    """Cifras clave del documento, a partir de los CSV. Las usa también la prueba que compara el documento con los resultados."""
    proc, res, pat = cargar()
    c = {}
    ep = pd.read_csv(res / "estimador_principal.csv").set_index("modelo")
    c["principal"], c["principal_bajo"], c["principal_alto"] = (ep.loc["tfidf", k] for k in ("estimador", "ic95_bajo", "ic95_alto"))
    c["e5"], c["e5_bajo"], c["e5_alto"] = (ep.loc["e5", k] for k in ("estimador", "ic95_bajo", "ic95_alto"))
    c["sin_corregir"] = ep.loc["tfidf", "total_sin_corregir"]
    ed = pd.read_csv(res / "estimador_diferencia.csv")
    a = ed[(ed["modelo"] == "tfidf") & (ed["mixto"] == "sin mixto") & (ed["con_censo"])].iloc[0]
    c["caso_a"], c["caso_a_bajo"], c["caso_a_alto"] = a["estimador_diferencia"], a["ic95_bajo"], a["ic95_alto"]
    mr = pd.read_csv(res / "mercado_con_y_sin_revision.csv")
    k = mr[mr["estado"].str.startswith("C") & (mr["modelo"] == "tfidf") & (mr["mixto"] == "sin")].iloc[0]
    c["etiquetas_contratos"], c["etiquetas_valor"] = int(k["contratos"]), k["valor_mm"]
    mx = pd.read_csv(res / "mixtos_aparte.csv", index_col=0).iloc[:, 0]
    c["mixtos_contratos"], c["mixtos_valor"] = int(mx["contratos"]), mx["valor_mm"]
    c["serie"] = pd.read_csv(res / "serie_anual.csv").query("escenario == 'tfidf_sin_mixto'").set_index("anio")
    cd = pd.read_csv(res / "cota_estrato_d.csv", index_col=0).iloc[:, 0]
    c["d_etiquetados"], c["d_cota"], c["d_ocultos"] = int(cd["etiquetados"]), cd["cota_proporcion_95"] * 100, cd["contratos_ocultos_max"]
    c["dep"] = pd.read_csv(res / "departamento_resumen.csv", dtype={"cod_dpto": str})
    c["hhi"] = pd.read_csv(res / "proveedores_hhi_cr4_anual.csv").set_index("anio")
    c["hhi_dep"] = pd.read_csv(res / "proveedores_hhi_departamento_resumen_anual.csv").set_index("anio")
    c["cv392"] = pd.read_csv(proc / "tabla_comparativa_392.csv").set_index("modelo")
    c["val60"] = pd.read_csv(proc / "tabla_validacion_60_revisada.csv")
    c["comp"] = pd.read_csv(res / "componentes.csv").set_index("componente")
    q = pd.read_csv(pat / "valor_d98_cuantiles.csv").merge(pd.read_csv(pat / "valor_d98_lmm_gamma.csv"), on="termino").set_index("termino")
    c["efectos"] = q.loc[["modalidad_gruposeleccion_abreviada", "tipo_entidadgobernacion_departamento", "fuentesecop2"]]
    lca = pd.read_csv(pat / "lca_comparacion.csv")
    pol = pd.read_csv(pat / "polca_comparacion.csv")
    c["lca_n"], c["lca_bvr_min"], c["lca_bvr_max"] = len(lca), lca["bvr_maximo"].min(), lca["bvr_maximo"].max()
    c["polca_n"], c["polca_bvr_min"] = len(pol), pol["bvr_maximo"].min()
    c["polca_cumple"] = int(((pol["bvr_maximo"] <= 10) & (pol["arranques_con_el_maximo"] >= 5)).sum())
    est, tam = pd.read_csv(pat / "hcpc_d98_estabilidad.csv"), pd.read_csv(pat / "hcpc_d98_tamanos.csv")
    h = est.merge(tam[["grupo", "pct"]], on="grupo")
    h["cumple"] = (h["jaccard_medio"] >= 0.75) & (h["pct"] >= 1.0)
    c["hcpc"] = h
    cm = pd.read_csv(pat / "estacionalidad_covid_modelos.csv")
    cm = cm[cm["muestra"] == "meses con registro de COVID"].copy()
    cm["id"] = cm["modelo"].str.split().str[0]
    cm = cm.set_index("id")
    c["covid"] = cm
    c["covid_pasan"] = cm[~cm["falla_autocorrelacion"] & ~cm["falla_normalidad_rq"]]
    c["covid_serie"] = pd.read_csv(pat / "covid_muertes_mensual.csv")
    c["covid_serie_sin"] = pd.read_csv(pat / "covid_muertes_mensual_sin_filtrar.csv")
    c["base"] = pd.read_csv(res / "patrones_base.csv")
    return c


def construir():
    c = cifras()
    s = c["serie"]
    dep = c["dep"].sort_values("valor_constante_2025", ascending=False)
    hhi, hd = c["hhi"], c["hhi_dep"]
    v60 = c["val60"].set_index(["version", "modelo"])
    cv = c["cv392"]
    ef = c["efectos"]
    h = c["hcpc"]
    cm, pasan = c["covid"], c["covid_pasan"]
    menor = pasan["BIC"].idxmin()
    reg = c["covid_serie"]["fallecidos"].dropna()
    reg_s = c["covid_serie_sin"]["fallecidos"].dropna()
    b = c["base"]
    sin_valor = int((~(b["valor_constante_2025"] > 0)).sum())
    n_dep = int(c["dep"]["contratos"].sum())
    n_mercado = c["etiquetas_contratos"]
    ok = h[h["cumple"]]

    L = ["# Cierre de F4: mercado público funerario (SECOP 2020–2025)", "",
         "Documento de una sola lectura para el informe final. Cada cifra lleva la decisión que la fija (`docs/decisiones.md`) y el archivo de donde sale (`data/processed/`, sin versionar). "
         "Las cifras de este documento se generan con `src/modelos/cierre_f4.py` a partir de los CSV de resultados y una prueba (`tests/test_cierre_f4.py`) verifica que coinciden. Valores monetarios en miles de millones de pesos de 2025. "
         "La rama `modelos` no está integrada en `main`: F4 se considera cerrada solo cuando Edward lo apruebe (ver «Decisiones pendientes»).", "",
         "## 1. Cobertura y universo", "",
         tabla([["Candidatos SECOP I y II, 2020–2025", "39.870", "D73 (34.790 + 5.080 de SECOP I 2023–2025)", "`data/interim/*_senales.parquet`"],
                ["SECOP II (conjunto `jbjy-vk9h`)", "19.306", "D16, D17", "`data/raw/secop/`"],
                ["SECOP I 2020–2022 (conjunto `f789-7hwg`, solo Celebrado, Liquidado, Terminado sin Liquidar; una fila por `uid`)", "15.484", "D42, D18", "`data/raw/secop/`"],
                ["SECOP I 2023–2025", "5.080", "D73", "`data/raw/secop/secop1_candidatos_2023_2025.jsonl`"],
                ["No recuperados por la consulta (muestra de 100)", "0 funerarios de 100 (cota superior de 3 %)", "D22 (nota del 2026-10-31)", "`no_recuperados_100_maestra.parquet`"]],
               ["Cifra", "Valor", "Decisión", "Archivo"]),
         "", "Los candidatos son contratos que cumplen la consulta léxica o de códigos UNSPSC, no contratos funerarios. Los 100 no recuperados no tienen pesos y no corrigen el total: son evidencia de que la consulta no deja escapar funerarios de forma apreciable, no una medida del total.", "",
         "## 2. Clasificación", "",
         "Tres clases (`funerario`, `no_funerario`, `mixto`) más la marca `forense` (D20, D21). La referencia es la revisión humana doble; nunca un LLM. **Modelo elegido: TF-IDF con regresión logística** (D56, D59, D94).", "",
         tabla([["F1 de `funerario`, validación cruzada de 392 casos: reglas / TF-IDF / e5 / DeepSeek",
                 f"{fm(cv.loc['reglas', 'f1'], 3)} / {fm(cv.loc['tfidf_logistica', 'f1'], 3)} ({fm(cv.loc['tfidf_logistica', 'f1_ic_bajo'], 3)}–{fm(cv.loc['tfidf_logistica', 'f1_ic_alto'], 3)}) / {fm(cv.loc['e5_logistica', 'f1'], 3)} / {fm(cv.loc['deepseek_flash', 'f1'], 3)}", "D55, D60", "`tabla_comparativa_392.csv`"],
                ["Validación externa de 60 contratos, F1 ponderado, TF-IDF / DeepSeek: etiquetas originales",
                 f"{fm(v60.loc[('original', 'tfidf_logistica'), 'pond_f1'], 3)} / {fm(v60.loc[('original', 'deepseek_flash'), 'pond_f1'], 3)}", "D63", "`tabla_validacion_60_revisada.csv`"],
                ["Ídem con las siete etiquetas revisadas",
                 f"{fm(v60.loc[('revisada', 'tfidf_logistica'), 'pond_f1'], 3)} / {fm(v60.loc[('revisada', 'deepseek_flash'), 'pond_f1'], 3)}", "D80", "`tabla_validacion_60_revisada.csv`"],
                ["Ídem con la regla D92 (V046 pasa a `no_funerario`)",
                 f"{fm(v60.loc[('revisada_d92', 'tfidf_logistica'), 'pond_f1'], 3)} ({fm(v60.loc[('revisada_d92', 'tfidf_logistica'), 'pond_f1_ic_bajo'], 3)}–{fm(v60.loc[('revisada_d92', 'tfidf_logistica'), 'pond_f1_ic_alto'], 3)}) / {fm(v60.loc[('revisada_d92', 'deepseek_flash'), 'pond_f1'], 3)} ({fm(v60.loc[('revisada_d92', 'deepseek_flash'), 'pond_f1_ic_bajo'], 3)}–{fm(v60.loc[('revisada_d92', 'deepseek_flash'), 'pond_f1_ic_alto'], 3)})", "D92, D94", "`tabla_validacion_60_revisada.csv`"],
                ["Lote de 30 contratos de SECOP I 2023–2025: TF-IDF y e5 coinciden con la etiqueta humana", "30 de 30 (error máximo de 18,1 % por grupo con 95 % de confianza)", "D80", "`evaluacion_secop1_nuevos.csv`"],
                ["Acuerdo entre revisores (κ de Cohen, 400 contratos)", "0,683 (umbral fijado de 0,70: no se cumple)", "D54", "`etiquetas_finales.parquet`"]],
               ["Cifra", "Valor", "Decisión", "Archivo"]),
         "", "**Por qué no otros modelos.** DeepSeek tuvo el F1 más alto en la validación cruzada (su instrucción y sus ocho ejemplos se formularon con esos mismos casos, de modo que la cifra es optimista) y, por la regla D59, solo desplaza a TF-IDF si su intervalo queda por encima del de TF-IDF; en la validación externa los intervalos se solapan en las tres versiones de etiquetas, así que gana el modelo más simple y auditable (D63, D94). "
         "Edward decidió no ejecutar la corrida completa de DeepSeek (D94); la regla de aprobación de D62, reducida al F1 puntual, es inestable con 60 casos (el orden cambia entre versiones de etiquetas por un solo contrato). e5 y la SVM y XGBoost de D71 no superan a TF-IDF. La etiqueta humana manda sobre la del modelo (D84).", "",
         "## 3. Mercado", "",
         tabla([["**Estimación principal** (estimador de diferencia por estratos, solo `funerario`), TF-IDF", f"**{mm(c['principal'])}** (IC 95 %: {mm(c['principal_bajo'])} a {mm(c['principal_alto'])})", "D93, D85, D89", "`estimador_principal.csv`"],
                ["Misma estimación con e5 (sensibilidad)", f"{mm(c['e5'])} ({mm(c['e5_bajo'])} a {mm(c['e5_alto'])})", "D93", "`estimador_principal.csv`"],
                ["Caso A: estimador de D85 sin los lotes posteriores", f"{mm(c['caso_a'])} ({mm(c['caso_a_bajo'])} a {mm(c['caso_a_alto'])})", "D85", "`estimador_diferencia.csv`"],
                ["Total del modelo sin corregir (TF-IDF)", mm(c["sin_corregir"]), "D93", "`estimador_principal.csv`"],
                ["**Suma con etiquetas** (jerarquía completa de D84, sin `mixto`)", f"{mm(c['etiquetas_valor'] * 1e9)} en {fm(c['etiquetas_contratos'], 0)} contratos", "D84, D89, D92, D96", "`mercado_con_y_sin_revision.csv`"],
                ["`mixto`, aparte (fuera de la cifra principal)", f"{fm(c['mixtos_contratos'], 0)} contratos, {mm(c['mixtos_valor'] * 1e9)}", "D89", "`mixtos_aparte.csv`"],
                ["Cota del estrato D (sin señal): funerarios en los etiquetados", f"0 de {c['d_etiquetados']}; proporción < {fm(c['d_cota'], 2)} % (regla del tres), como máximo {fm(c['d_ocultos'], 0)} contratos ocultos", "D93", "`cota_estrato_d.csv`"]],
               ["Cifra", "Valor", "Decisión", "Archivo"]),
         "", "La estimación principal es mayor que la suma con etiquetas porque estima también los funerarios no revisados del universo (la suma con etiquetas es la parte que la revisión humana y el modelo ya clasifican). Los `mixto` y los contratos `forense` quedan fuera del tamaño de mercado (D21, D89). "
         "El total es una cota inferior respecto de los funerarios que la consulta original no recupera, que no se pueden cuantificar (D22).", "",
         "**Serie anual** (TF-IDF, jerarquía completa, sin `mixto`; pesos constantes de 2025; D86, D67; `serie_anual.csv`):", "",
         tabla([[int(a), fm(s.loc[a, "contratos"], 0), mm(s.loc[a, "valor_corriente"]), mm(s.loc[a, "valor_constante_2025"])] for a in s.index], ["Año", "Contratos", "Valor corriente", "Valor constante de 2025"]), "",
         "## 4. Territorio y concentración", "",
         f"Valor por departamento (ubicación de la entidad compradora, cruce con DIVIPOLA, D66; `departamento_resumen.csv`): {fm(n_dep, 0)} de {fm(n_mercado, 0)} contratos tienen departamento. Mayores valores: "
         + "; ".join(f"{r.departamento.title()} {mm(r.valor_constante_2025)} ({fm(r.contratos, 0)} contratos)" for r in dep.head(5).itertuples()) + ". "
         "La tasa por 100.000 habitantes (DANE, D66) se publica en el mismo archivo y en `municipio_resumen.csv`.", "",
         "Concentración de proveedores (`proveedores_hhi_cr4_anual.csv`, `proveedores_hhi_departamento_resumen_anual.csv`; D69, D77):", "",
         tabla([[int(a), fm(hhi.loc[a, "proveedores"], 0), fm(hhi.loc[a, "HHI"], 0), fm(hhi.loc[a, "CR4"], 1), fm(hd.loc[a, "HHI_mediana"], 0), int(hd.loc[a, "departamentos_HHI_mayor_2500"])] for a in hhi.index],
               ["Año", "Proveedores", "HHI nacional", "CR4 nacional (%)", "HHI departamental, mediana", "Departamentos con HHI > 2.500"]), "",
         "El HHI nacional es bajo (menos de 700) y sube desde 2022; la mediana departamental es de 1.297 a 2.034, es decir, los mercados departamentales están bastante más concentrados que el nacional (D86, D77). D69 sigue marcada como propuesta.", "",
         "## 5. Patrones de compra", "",
         "Todo lo de esta sección es **exploratorio** (D98 se decidió después de ver D97) y está sujeto a la aprobación de D99. Universo: " + fm(n_mercado, 0) + " contratos `funerario` (D84). Informe: `docs/resultados/patrones_compra.md`.", "",
         "**Valor** (log del valor constante de 2025; solo se reportan los tres efectos significativos en los tres modelos: regresión por cuantiles en la mediana, lineal mixto y gamma mixto; D99):", "",
         tabla([[n, fm(ef.loc[t, "qr_estimador"], 3), fm(ef.loc[t, "lmm_estimador"], 3), fm(ef.loc[t, "gamma_estimador"], 3)] for n, t in
                (("Selección abreviada frente a mínima cuantía", "modalidad_gruposeleccion_abreviada"), ("Gobernación o departamento frente a alcaldía o municipio", "tipo_entidadgobernacion_departamento"), ("Fuente SECOP II frente a SECOP I", "fuentesecop2"))],
               ["Efecto", "Mediana (cuantiles)", "Lineal mixto", "Gamma mixto"]), "",
         f"Los otros 18 coeficientes son no concluyentes. Archivos: `valor_d98_cuantiles.csv`, `valor_d98_lmm_gamma.csv`. La regresión usa {fm(len(b) - sin_valor, 0)} contratos (se excluyen {sin_valor} con valor 0, D99).", "",
         f"**Tipología.** No hay tipología latente que cumpla independencia local: ninguno de los {c['lca_n']} modelos de D97 (residuo bivariado máximo de {fm(c['lca_bvr_min'], 1)} a {fm(c['lca_bvr_max'], 0)}) ni de los {c['polca_n']} de `poLCA` de D98 (mínimo {fm(c['polca_bvr_min'], 1)}) cumple a la vez BVR ≤ 10 y mejor ajuste en al menos 5 de 100 arranques ({c['polca_cumple']} cumplen; `lca_comparacion.csv`, `polca_comparacion.csv`). "
         f"Como descripción se reportan los grupos de ACM + HCPC con Jaccard medio ≥ 0,75 y al menos 1 % de los contratos (criterio de la enmienda de D99): {len(ok)} de {len(h)}, con {fm(ok['contratos'].sum(), 0)} contratos ({fm(100 * ok['contratos'].sum() / n_mercado, 1)} %): "
         + "; ".join(f"grupo {int(r.grupo)} ({fm(r.contratos, 0)}, Jaccard {fm(r.jaccard_medio, 2)})" for r in ok.itertuples()) + ". Sus categorías características (prueba v) están en `patrones_compra.md` y `hcpc_d98_vtest.csv`; no se les da interpretación de negocio.", "",
         f"**Estacionalidad: indicio, no hallazgo.** Modelos de binomial negativa sobre el conteo mensual de contratos firmados. Con la serie de fallecidos de COVID-19 del INS filtrada por estado «Fallecido» (`gt2j-8ykr`, {fm(reg.sum(), 0)} fallecidos de marzo de 2020 a enero de 2024; sin filtrar eran {fm(reg_s.sum(), 0)}; los 25 meses sin registro son faltantes, no ceros): "
         f"la señal estacional se mantiene en todos los modelos (Wald con Newey-West p < 0,0001; amplitud de 12 meses de {fm(cm['amplitud_12'].min(), 2)} a {fm(cm['amplitud_12'].max(), 2)}); pasan los supuestos los modelos {', '.join(pasan.index)}; el de menor BIC entre ellos es el {menor} ({fm(pasan.loc[menor, 'BIC'], 1)}). "
         "Los meses de mayor contratación del año son marzo, febrero y abril, con ambas series. Archivos: `estacionalidad_covid_modelos.csv`, `perfil_mensual_2e.csv`; decisiones D97, D98, D99.", "",
         "## 6. Tratamiento de faltantes", "",
         tabla([["Contratos con valor 0 (valor no positivo)", f"{sin_valor} contratos: excluidos de la regresión del log del valor; incluidos en los totales (suman 0)", "D99 (enmienda)"],
                ["`forense` de Harold sin dato en 59 filas", "Se completó con 0 (imputación); no afecta el mercado; todo conteo de `forense = 1` es un mínimo", "D54 (nota)"],
                ["Meses sin registro de muertes por COVID (enero y febrero de 2020; desde febrero de 2024)", "Faltantes, no ceros: los modelos con COVID se ajustan a los 47 meses con registro", "D99 (enmienda)"],
                ["Contratos con ubicación «No Definido» o sin municipio", f"Se conservan en las cifras nacionales y por año; sin departamento quedan {fm(n_mercado - n_dep, 0)} contratos del mercado", "D66"],
                ["Población de perros de MinSalud sin municipios en 2022 y 2025", "El denominador de las agresiones del INS usa la población de otro año (2023 y 2024), marcado con `denominador_otro_anio = 1`", "D65, D88"],
                ["Población de animales de MinSalud reproducible con una razón entera (imputada)", "Se detecta y se marca (`imputado`/`posible_medido`: 597 y 524 en perros; 784 y 337 en gatos), no se excluye; los indicadores de densidad solo se interpretan en `posible_medido`", "D43, D49, D29"],
                ["Contratos no recuperados por la consulta", "Sin pesos ni corrección del total; 0 funerarios en 100 etiquetados", "D22"],
                ["Etiqueta humana ausente en la mayoría de los contratos", "Se aplica el modelo; la etiqueta humana manda donde existe (jerarquía); estimador de diferencia para la corrección", "D84, D93"]],
               ["Qué faltaba", "Qué se hizo", "Decisión"]), "",
         "## 7. Limitaciones", "",
         "- El κ entre revisores (0,683) no alcanza el umbral fijado de 0,70; el desempate de Harold no fue ciego y el `forense` de Natalia no es utilizable (D54).",
         "- El intervalo de la estimación principal (225,4 a 304,5) es ancho: depende del estrato D (sin señal), donde se etiquetó una muestra pequeña, y de los 50 contratos de mayor valor revisados uno por uno (D90, D93).",
         "- La validación externa tiene 60 casos y un estrato D con casi todo el peso; el F1 puntual cambia con una sola etiqueta (D94).",
         "- DeepSeek no se evaluó sobre el universo (D94); su F1 en la muestra es optimista (D60).",
         "- El total es una cota inferior respecto de lo que la consulta no recupera (D22) y excluye `mixto` y `forense` (D89).",
         "- La ubicación es la de la entidad compradora, no la de ejecución (D66); las entidades nacionales con sede en Bogotá se ubican en Bogotá aunque el servicio se ejecute en otro lugar.",
         "- SECOP I y SECOP II no son equivalentes (SECOP I solo con contrato firmado y estado de ejecución, D42); el efecto de la fuente aparece como uno de los tres efectos robustos de valor.",
         "- Los patrones de compra son exploratorios; ninguna tipología latente cumple los supuestos; la estacionalidad es un indicio y depende de la especificación de la serie de COVID-19 (143.125 fallecidos frente a unos 142.000 oficiales, cifra no verificada contra una publicación en esta sesión).",
         "- La cifra de XGBoost de D71 depende del número de hilos (0,887 original; 0,890 reproducible con un hilo).",
         "- Mortalidad de mascotas: vacío documentado; no se estiman escenarios de defunciones (decisión cerrada).", "",
         "## 8. Decisiones pendientes de Edward", "",
         "- **Aprobar o rechazar D99** (estado: propuesta): efectos de valor, tipología, criterio de grupos de HCPC, estacionalidad como indicio, serie de COVID filtrada y modelo principal 2e.",
         "- Integrar `modelos` en `main` con `git merge --no-ff` y el resumen de la fase (D55–D99), si se da por cerrada F4.",
         "- D69 (proveedores) y D68 (patrones) siguen como borrador/propuesta; D95 y D96 tienen seguimientos abiertos (variables derivadas y componentes).",
         "- Recalcular el tamaño efectivo de la robustez de D71/D79 con las etiquetas vigentes, si se quiere citar.",
         "- Verificar la cifra oficial de muertes por COVID-19 del INS contra una publicación (el valor de unos 142.000 viene de Edward).", ""]
    return "\n".join(L)


def main():
    SALIDA.write_text(construir(), encoding="utf-8")
    print("escrito", SALIDA)


if __name__ == "__main__":
    main()
