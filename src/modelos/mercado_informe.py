import numpy as np
import pandas as pd

from src.etl.comun import RAIZ, cargar_config, ruta

DESTINO = RAIZ / "docs" / "resultados" / "f4_mercado_publico.md"
TABLAS = "data/processed/resultados_secop"


SIN_SEPARADOR = {"año", "anio", "mes"}


def es_(v, c, formatos):
    if pd.isna(v):
        return ""
    if c in formatos:
        return formatos[c].format(v)
    if c in SIN_SEPARADOR:
        return str(int(v))
    if isinstance(v, (int, np.integer)):
        return f"{v:,}".replace(",", ".")
    if isinstance(v, (float, np.floating)):
        return f"{v:,.1f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return str(v)


def tabla(df, formatos=None):
    formatos = formatos or {}
    cols = list(df.columns)
    filas = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for r in df.itertuples(index=False):
        filas.append("| " + " | ".join(es_(v, c, formatos) for c, v in zip(cols, r)) + " |")
    return "\n".join(filas)


def mm(x):
    return x / 1e9


def main():
    s = ruta(cargar_config(), "processed") / "resultados_secop"
    sa = pd.read_csv(s / "serie_anual.csv")
    saf = pd.read_csv(s / "serie_anual_fuente.csv")
    cruce = pd.read_csv(s / "tasa_cruce_ubicacion.csv", index_col=0)
    dep = pd.read_csv(s / "departamento_resumen.csv")
    mun = pd.read_csv(s / "municipio_resumen.csv")
    tipo = pd.read_csv(s / "borrador_tipo_entidad.csv")
    orden = pd.read_csv(s / "borrador_orden_entidad.csv")
    sector = pd.read_csv(s / "borrador_sector_secop2.csv")
    modal = pd.read_csv(s / "borrador_modalidad.csv")
    directa = pd.read_csv(s / "borrador_modalidad_directa_anual.csv")
    mes = pd.read_csv(s / "borrador_mes_firma.csv")
    sub = pd.read_csv(s / "componentes.csv")
    hh = pd.read_csv(s / "proveedores_hhi_cr4_anual.csv")
    hd = pd.read_csv(s / "proveedores_hhi_departamento.csv")
    top = pd.read_csv(s / "proveedores_top_participacion.csv")
    est = pd.read_csv(s / "estimador_diferencia.csv")
    est_c = est[est["con_censo"]].copy()
    est_sc = est[~est["con_censo"]].set_index(["modelo", "mixto"])
    est_c["modelo"] = est_c["modelo"].map({"tfidf": "TF-IDF", "e5": "e5"})
    est_c["sin corregir"] = est_c["total_sin_corregir"] / 1e9
    est_c["con etiquetas humanas"] = est_c["total_con_etiquetas_humanas"] / 1e9
    est_c["estimador (solo muestra)"] = [est_sc.loc[(m, x), "estimador_diferencia"] / 1e9 for m, x in zip(est["modelo"][est["con_censo"]], est["mixto"][est["con_censo"]])]
    est_c["ESTIMADOR PRINCIPAL"] = est_c["estimador_diferencia"] / 1e9
    est_c["IC 95 %"] = [f"{a / 1e9:.1f} a {b / 1e9:.1f}" for a, b in zip(est_c["ic95_bajo"], est_c["ic95_alto"])]
    d_est = est_c[["modelo", "mixto", "sin corregir", "con etiquetas humanas", "estimador (solo muestra)", "ESTIMADOR PRINCIPAL", "IC 95 %"]]
    rev = pd.read_csv(s / "mercado_con_y_sin_revision.csv")
    d_rev_mercado = rev[(rev["modelo"] == "tfidf")][["estado", "mixto", "contratos", "valor_mm", "v2020", "v2021", "v2022", "v2023", "v2024", "v2025"]]
    tv = pd.read_csv(s / "top_valor_evaluacion.csv")
    d_tv = tv[["definicion", "modelo", "predichos", "humanos", "aciertos", "precision_por_contratos", "precision_por_valor", "sensibilidad_por_valor"]]
    tvl = pd.read_csv(s / "top_valor_etiquetas.csv")

    ep = pd.read_csv(s / "estimador_principal.csv").set_index("modelo")
    cota = pd.read_csv(s / "cota_estrato_d.csv", index_col=0).iloc[:, 0]
    f1n = pd.read_csv(s / "f1_lotes_nuevos.csv")
    mixa = pd.read_csv(s / "mixtos_aparte.csv", index_col=0).iloc[:, 0]
    caso_a = est_c[(est_c["modelo"] == "TF-IDF") & (est_c["mixto"] == "sin mixto")].iloc[0]
    principal = sa[sa["escenario"] == "tfidf_sin_mixto"].copy()
    principal["valor corriente (mm)"] = mm(principal["valor_corriente"])
    principal["valor constante 2025 (mm)"] = mm(principal["valor_constante_2025"])
    con = sa[sa["escenario"] == "tfidf_con_mixto"].set_index("anio")
    sin = principal.set_index("anio")
    mixtos_anual = pd.DataFrame({"año": sin.index.astype(int), "contratos mixto": (con["contratos"] - sin["contratos"]).values,
                                 "valor constante 2025 (mm)": mm(con["valor_constante_2025"] - sin["valor_constante_2025"]).values})
    f1_40 = f1n[(f1n["lote"] == "humanitarios 40") & (f1n["definicion"] == "funerario")][["modelo", "escala", "precision", "sensibilidad", "f1", "f1_ic_bajo", "f1_ic_alto"]]
    f1_150 = f1n[f1n["lote"] == "estrato D 150"][["modelo", "falsos_positivos", "verdaderos_negativos", "positivos_reales"]]
    anual = principal[["anio", "contratos", "valor corriente (mm)", "valor constante 2025 (mm)"]].rename(columns={"anio": "año"})
    anual["año"] = anual["año"].astype(int)
    sens = sa.groupby("escenario").agg(contratos=("contratos", "sum"), valor_constante=("valor_constante_2025", "sum")).reset_index()
    sens["valor constante 2025 (mm)"] = mm(sens["valor_constante"])
    sens = sens[["escenario", "contratos", "valor constante 2025 (mm)"]]
    fuente = saf.assign(valor=mm(saf["valor_constante_2025"]))[["anio", "fuente", "contratos", "valor"]].rename(columns={"valor": "valor constante 2025 (mm)"})
    fuente["anio"] = fuente["anio"].astype(int)
    d2 = dep.sort_values("valor_constante_x100mil_anual", ascending=False).head(10).assign(
        valor_x100mil=lambda t: t["valor_constante_x100mil_anual"] / 1e6, contratos_x100mil=lambda t: t["contratos_x100mil_anual"])
    d2 = d2[["departamento", "contratos", "valor_x100mil", "contratos_x100mil"]].rename(columns={
        "valor_x100mil": "valor por 100.000 hab. al año (millones de 2025)", "contratos_x100mil": "contratos por 100.000 hab. al año"})
    m2 = mun.sort_values("contratos", ascending=False).head(10)[["municipio", "departamento", "contratos"]].assign(
        valor=lambda t: mun.loc[t.index, "valor_constante_2025"] / 1e9).rename(columns={"valor": "valor constante 2025 (mm)"})
    d_tipo = tipo[["tipo_entidad", "contratos", "pct_contratos", "pct_valor"]]
    d_mod = modal[["modalidad_grupo", "contratos", "pct_contratos", "pct_valor"]]
    d_dir = directa[["anio", "fuente", "contratos", "pct_valor_directa", "pct_valor_directa_y_especial"]].copy()
    d_dir["anio"] = d_dir["anio"].astype(int)
    d_mes = mes[["mes", "contratos", "pct_contratos", "pct_valor"]].copy()
    d_mes["mes"] = d_mes["mes"].astype(int)
    ac = pd.read_csv(s / "acierto_indicadores.csv")
    publicables = ac.loc[ac["aciertos"] >= 35, "indicador"].tolist()
    d_sub = sub[sub["componente"].isin(publicables)][["componente", "contratos", "pct_contratos", "pct_valor"]].rename(columns={
        "pct_contratos": "% de contratos que lo incluye", "pct_valor": "% del valor que lo incluye"})
    d_ac = ac[ac["indicador"].isin(publicables)][["indicador", "aciertos", "acierto", "precision", "sensibilidad"]]
    d_rev = ac[~ac["indicador"].isin(publicables)][["indicador", "aciertos", "acierto", "precision", "sensibilidad"]]
    top10 = pd.read_csv(s / "hhi_2025_top10_contratos.csv")
    top10 = top10.assign(valor_mm=top10["valor"] / 1e9, valor_constante_mm=top10["valor_constante_2025"] / 1e9)[
        ["entidad", "valor_mm", "pct_valor_anio", "proveedor", "modalidad", "p_tfidf_funerario", "p_e5_funerario"]].rename(columns={
            "valor_mm": "valor (mm corrientes)", "pct_valor_anio": "% del valor de 2025",
            "p_tfidf_funerario": "prob. funerario TF-IDF", "p_e5_funerario": "prob. funerario e5"})
    sinm = pd.read_csv(s / "hhi_2025_sin_mayores.csv")
    sinm = sinm.assign(valor_mm=sinm["valor_constante_2025"] / 1e9)[["sin_los_mayores", "contratos", "valor_mm", "proveedores", "HHI", "CR4"]].rename(
        columns={"sin_los_mayores": "sin los N mayores contratos", "valor_mm": "valor constante (mm)"})
    porcl = pd.read_csv(s / "proveedores_hhi_por_clasificacion.csv")
    porcl = porcl[porcl["anio"] >= 2023][["clasificacion", "anio", "proveedores", "HHI", "CR4"]]
    porcl["anio"] = porcl["anio"].astype(int)
    d_hh = hh.copy()
    d_hh["anio"] = d_hh["anio"].astype(int)
    d_hh["proveedores"] = d_hh["proveedores"].astype(int)
    con5 = hd[hd["proveedores"] >= 5]
    hdep = pd.read_csv(s / "proveedores_hhi_departamento_resumen_anual.csv")
    d_hdep = hdep.rename(columns={"anio": "año", "departamentos_con_5_o_mas_proveedores": "departamentos", "HHI_mediana": "HHI mediana",
                                  "HHI_p25": "HHI p25", "HHI_p75": "HHI p75", "departamentos_HHI_mayor_2500": "con HHI > 2.500"})
    d_hdep = d_hdep.rename(columns={"HHI mediana": "HHI_mediana", "HHI p25": "HHI_p25", "HHI p75": "HHI_p75"})
    cuantiles = con5["HHI"].quantile([0.1, 0.25, 0.5, 0.75, 0.9]).round(0)

    c = lambda k: cruce.loc[k]
    txt = f"""# F4 · Mercado público funerario (SECOP 2020–2025)

Generado por `python -m src.modelos.mercado` y `python -m src.modelos.mercado_informe`. Las tablas están en `{TABLAS}/` (no se versionan). **Las secciones marcadas «borrador» no tienen conclusiones.** Cifras en miles de millones de pesos («mm»). Modelo de clasificación: TF-IDF (`clase_final`, D63). **La cifra principal es solo `funerario` (D89); los `mixto` van aparte y no se suman.** El estimador principal es el de la sección 2c (D90, D93); el caso A de D85 se reporta al lado.

> **Cobertura (D70, D73, D74).** SECOP I se extendió a 2023–2025 (5.080 contratos candidatos más, D73), así que la serie cubre SECOP I y SECOP II en los seis años. Limitación: ni la muestra de 400 ni la validación de 60 incluyen contratos de SECOP I de 2023–2025; el error de clasificación en ese bloque se medirá con los 30 contratos de `docs/revision_f4/secop1_nuevos.xlsx`.

## 1. Cruce de la ubicación de la entidad con DIVIPOLA (D66)

Tabla de origen: `tasa_cruce_ubicacion.csv`.

| | contratos | funerarios (TF-IDF) |
|---|---|---|
| universo | {int(c('contratos')['universo']):,} | {int(c('contratos')['funerario_tfidf']):,} |
| con municipio DIVIPOLA | {int(c('con_municipio_DIVIPOLA')['universo']):,} ({c('con_municipio_DIVIPOLA')['tasa_universo']:.1%}) | {int(c('con_municipio_DIVIPOLA')['funerario_tfidf']):,} |
| con departamento | {int(c('con_departamento')['universo']):,} ({c('con_departamento')['tasa_universo']:.1%}) | {int(c('con_departamento')['funerario_tfidf']):,} |

Sin municipio quedan los contratos con la entidad registrada en «No Definido» y unos pocos nombres sin equivalente. Los cruces aproximados fueron revisados por Edward (20 de 20 correctos, D66). **Decisión D66** (vigente).

## 2. Número y valor por año (D67)

Tabla de origen: `serie_anual.csv`; gráfico `docs/resultados/graficos/1_serie_anual_pesos_constantes.png`. Escenario principal (TF-IDF, solo `funerario`):

{tabla(anual)}

Por fuente (`serie_anual_fuente.csv`):

{tabla(fuente)}

Sensibilidad (suma 2020–2025; `serie_anual.csv`). Los escenarios con `mixto` no son un límite superior del mercado (D89); se conservan solo como cálculo:

{tabla(sens)}

**Decisión D67** (propuesta): pesos constantes de 2025 con el IPC mensual del mes de firma; valor inicial sin adiciones.

## 2b. Estimación principal del total (D84, D85, D86)

**Jerarquía (D84):** en el mercado, toda etiqueta humana reemplaza a la predicción del modelo (muestra de 400, validación de 60 revisada, los 30 de SECOP I 2023–2025, los 2 de D81 y los 50 de la revisión por valor). Las métricas de evaluación siguen usando las predicciones fuera de pliegue.

**Estimación principal del total, 2020–2025, en miles de millones de pesos de 2025** (estimador de diferencia, Särndal, Swensson y Wretman 1992: total del modelo más la corrección de la revisión censal de los 50 de mayor valor y de los 2 de D81, más la suma en la muestra de 400 de peso × (indicador humano − indicador predicho) × valor, con intervalo bootstrap estratificado):

{tabla(d_est, {"sin corregir": "{:.1f}", "con etiquetas humanas": "{:.1f}", "estimador (solo muestra)": "{:.1f}", "ESTIMADOR PRINCIPAL": "{:.1f}"})}

Mercado funerario con TF-IDF (sin y con `mixto` por separado) con y sin la revisión por valor (A: sin revisión; B: jerarquía sin los 50; C: jerarquía completa; `mercado_con_y_sin_revision.csv`):

{tabla(d_rev_mercado, {"valor_mm": "{:.1f}", "v2020": "{:.1f}", "v2021": "{:.1f}", "v2022": "{:.1f}", "v2023": "{:.1f}", "v2024": "{:.1f}", "v2025": "{:.1f}"})}

**Revisión por valor (D83, D86):** Edward etiquetó los 50 contratos de mayor valor: {', '.join(f"{int(r.contratos)} {r.etiqueta} ({r.valor_constante:.1f} miles de millones)" for r in tvl.itertuples())}. Precisión y sensibilidad de los modelos en esos 50, por contratos y ponderadas por valor constante (`top_valor_evaluacion.csv`):

{tabla(d_tv, {"precision_por_contratos": "{:.3f}", "precision_por_valor": "{:.3f}", "sensibilidad_por_valor": "{:.3f}"})}

## 2c. Estimador principal con los lotes nuevos (D90, D93)

Caso C de D90: los 317 contratos humanitarios con componente funerario forman un estrato aparte. Los 21 con etiqueta previa se corrigen exactamente; los 296 restantes se estiman con la muestra de 40 (estimador de diferencia dentro de cada estrato A1 y A2, pesos de D91: 8,33 y 4,60). El estrato D suma los 150 nuevos a los 50 de la muestra de 400 (200 con peso común). Intervalo bootstrap estratificado (2.000 remuestreos, semilla 2026). Miles de millones de pesos de 2025, solo `funerario`.

| modelo | total sin corregir | corrección censal | corrección muestra 400 y D | corrección humanitarios (40) | **estimador principal** | IC 95 % |
|---|---|---|---|---|---|---|
| TF-IDF | {ep.loc['tfidf','total_sin_corregir'] / 1e9:.1f} | {ep.loc['tfidf','correccion_censo'] / 1e9:.1f} | {ep.loc['tfidf','correccion_muestra_400_y_D150'] / 1e9:.1f} | {ep.loc['tfidf','correccion_humanitarios_40'] / 1e9:.2f} | **{ep.loc['tfidf','estimador'] / 1e9:.1f}** | {ep.loc['tfidf','ic95_bajo'] / 1e9:.1f} a {ep.loc['tfidf','ic95_alto'] / 1e9:.1f} |
| e5 | {ep.loc['e5','total_sin_corregir'] / 1e9:.1f} | {ep.loc['e5','correccion_censo'] / 1e9:.1f} | {ep.loc['e5','correccion_muestra_400_y_D150'] / 1e9:.1f} | {ep.loc['e5','correccion_humanitarios_40'] / 1e9:.2f} | **{ep.loc['e5','estimador'] / 1e9:.1f}** | {ep.loc['e5','ic95_bajo'] / 1e9:.1f} a {ep.loc['e5','ic95_alto'] / 1e9:.1f} |

**Caso A (D85, para transparencia; M214 dentro de la muestra de A2):** TF-IDF {caso_a['ESTIMADOR PRINCIPAL']:.1f} (IC {caso_a['IC 95 %']}).

**Contratos con componente funerario no separable (`mixto`, D89)**, aparte y sin sumarse: {int(mixa['contratos'])} contratos, {mixa['valor_mm']:.1f} miles de millones de pesos de 2025 (TF-IDF con la jerarquía de etiquetas). Por año:

{tabla(mixtos_anual)}

**Estrato D, cota de funerarios ocultos:** {int(cota['funerarios'])} funerarios en {int(cota['etiquetados'])} contratos etiquetados (50 de la muestra de 400, 150 nuevos y 8 de la validación de 60). Regla del tres: la proporción de funerarios en D es menor que {cota['cota_proporcion_95']:.2%} con 95 % de confianza, es decir, hasta {cota['contratos_ocultos_max']:.0f} de los {int(cota['tamano_D']):,} contratos de D (cifra ilustrativa de valor con el valor medio de un contrato de D, {cota['valor_medio_contrato_D_mm'] * 1000:.0f} millones: {cota['valor_ilustrativo_mm']:.1f} miles de millones). No es una estimación, es un límite superior.

**TF-IDF en los lotes nuevos** (predicciones del modelo entrenado con los 400, sin haber visto estos contratos; `f1_lotes_nuevos.csv`). Humanitarios 40, `funerario`:

{tabla(f1_40, {"precision": "{:.3f}", "sensibilidad": "{:.3f}", "f1": "{:.3f}", "f1_ic_bajo": "{:.3f}", "f1_ic_alto": "{:.3f}"})}

Estrato D, 150 contratos (todos `no_funerario`; sin positivos el F1 no está definido):

{tabla(f1_150)}

## 3. Territorio y por 100.000 habitantes (D66, D67)

Tablas: `departamento_resumen.csv`, `departamento_anual.csv`, `municipio_resumen.csv`, `municipio_anual.csv`; gráfico `2_departamentos_por_100mil.png`. La ubicación es la sede de la entidad compradora. Población DANE del año de firma. Diez departamentos con mayor valor por 100.000 habitantes (promedio anual 2020–2025):

{tabla(d2)}

Diez municipios con más contratos funerarios:

{tabla(m2)}

Los departamentos pequeños (Guainía, Vaupés, Amazonas, Vichada) lideran la tasa por su población reducida y pocos contratos; no son comparables con los grandes sin intervalos.

## 4. Patrones de compra (borrador)

Todo lo de esta sección es borrador sin conclusiones; usa los contratos `funerario` del escenario principal.

**Tipo de entidad** (reglas sobre el nombre de la entidad; `borrador_tipo_entidad.csv`). También: `borrador_orden_entidad.csv` (orden por fuente) y `borrador_sector_secop2.csv`.

{tabla(d_tipo)}

**Modalidad** (`borrador_modalidad.csv`; gráfico `3_modalidad.png`):

{tabla(d_mod)}

**Participación de la contratación directa en el valor**, por año y fuente (`borrador_modalidad_directa_anual.csv`):

{tabla(d_dir)}

**Mes de firma** (`borrador_mes_firma.csv`):

{tabla(d_mes)}

**Componentes del servicio** (indicadores no excluyentes sobre el objeto; `componentes.csv`, `componentes_anual.csv`; gráfico `4_componentes.png`). Solo se reportan los componentes con 35 o más aciertos de 40 contra la revisión de Edward. Un contrato puede incluir varios componentes, así que los porcentajes no suman 100. Plan exequial solo con plan, póliza, auxilio funerario o afiliación; «servicios exequiales» por sí solo es servicio directo:

{tabla(d_sub)}

**Acierto de los componentes reportados** contra los 40 contratos (`acierto_indicadores.csv`). **La medición es optimista: las reglas se ajustaron con esos mismos casos.** Además, Edward marcó un solo subtipo por contrato, así que la sensibilidad es confiable pero la precisión es un mínimo.

{tabla(d_ac, {"acierto": "{:.2f}", "precision": "{:.2f}", "sensibilidad": "{:.2f}"})}

**Indicadores en revisión** (menos de 35 aciertos de 40; no se reportan sus porcentajes): `incluye_inhumacion_cremacion` y `incluye_atencion_vulnerables_NN`. Casi todos los contratos funerarios mencionan servicios directos y población vulnerable, y la verdad de referencia tiene un solo subtipo por contrato, de modo que esos indicadores no se pueden evaluar bien con estos 40 casos.

{tabla(d_rev, {"acierto": "{:.2f}", "precision": "{:.2f}", "sensibilidad": "{:.2f}"})}

**Disposición de animales** (evaluada aparte): el estrato B de la muestra de 400 son los 23 contratos «posible disposición de animales» (todo el estrato: N = n = 23), y todos son `no_funerario`. Casi todos son gestión de residuos peligrosos de centros de zoonosis; solo uno (M078) incluye «animales muertos» de más de 50 kg. El indicador lo marca y no marca los otros 22; ningún contrato clasificado como `funerario` lo activa (D78).

**Decisión D68** (propuesta, borrador): indicadores de componentes, que reemplazan al subtipo único con prioridad; D78 fija cuáles se reportan.

## 5. Proveedores (D69, vigente con condiciones)

**Medida principal: HHI por departamento** (el mercado es local; `proveedores_hhi_departamento.csv`, `proveedores_hhi_departamento_anual.csv`, `proveedores_hhi_departamento_resumen_anual.csv`). El HHI nacional va solo como contexto. Participación y concentración por valor constante; el identificador es el NIT (SECOP I, personas jurídicas) o el código de proveedor (SECOP II). **Limitación: las personas naturales van seudonimizadas (D15) y no se unen entre SECOP I y II, así que un mismo proveedor puede contarse dos veces y la concentración puede estar subestimada.**

HHI por departamento y año (departamentos con 5 o más proveedores; mediana y cuartiles entre departamentos):

{tabla(d_hdep, {"HHI_mediana": "{:.0f}", "HHI_p25": "{:.0f}", "HHI_p75": "{:.0f}"})}

Pooled 2020–2025 (n = {len(con5)} departamentos con 5 o más proveedores): percentiles 10, 25, 50, 75 y 90 = {', '.join(f'{v:,.0f}' for v in cuantiles)}; {int((con5['HHI'] > 2500).sum())} de {len(con5)} superan 2.500. Los cinco proveedores de mayor valor suman el {top.head(5)['participacion_valor_pct'].sum():.1f} % del valor total (`proveedores_top_participacion.csv`).

**Contexto: HHI y CR4 nacionales por año** (`proveedores_hhi_cr4_anual.csv`; gráfico `5_concentracion_proveedores.png`). El de 2025 se reporta después de corregir los dos contratos de D81; la sensibilidad sin los tres mayores contratos está más abajo:

{tabla(d_hh, {"HHI": "{:.0f}", "CR4": "{:.1f}"})}

**Decisión D69** (vigente con condiciones): medida principal por departamento, HHI nacional como contexto, HHI de 2025 después de las correcciones de D81 y con la sensibilidad sin los tres mayores.

### Descomposición del HHI de 2025 (D77)

Los 10 mayores contratos funerarios de 2025 (`hhi_2025_top10_contratos.csv`; el proveedor solo se muestra si es persona jurídica):

{tabla(top10, {"valor (mm corrientes)": "{:.2f}", "% del valor de 2025": "{:.1f}", "prob. funerario TF-IDF": "{:.2f}", "prob. funerario e5": "{:.2f}"})}

HHI de 2025 quitando los mayores contratos (`hhi_2025_sin_mayores.csv`):

{tabla(sinm, {"HHI": "{:.0f}", "CR4": "{:.1f}", "valor constante (mm)": "{:.1f}"})}

HHI según el modelo que define `funerario` (`proveedores_hhi_por_clasificacion.csv`):

{tabla(porcl, {"HHI": "{:.0f}", "CR4": "{:.1f}"})}

## Limitaciones

- **Validación de 60 revisada (D80).** TF-IDF obtiene un F1 ponderado de `funerario` de 0,956 (IC 95 % 0,908–0,996; 0,913 sin ponderar) con las etiquetas revisadas y la corrección de D92 (V046). Con las etiquetas originales era 0,648 (0,389–0,970), porque un solo caso de peso 3.293 dominaba el resultado (D63); se conservan las tres versiones.
- **SECOP I 2023–2025.** Ni la muestra de 400 ni la validación de 60 incluyen esos contratos (D74); se evaluaron aparte con 30 contratos, sin errores de TF-IDF ni de e5 (D80), lo que acota el error de cada grupo en 18,1 % pero mide poco los funerarios que el modelo deja pasar.
- **Estimador principal (D93).** El total de solo `funerario` es 254,0 miles de millones de pesos de 2025 con TF-IDF (IC 95 % 225,4–304,5) y 221,9 con e5 (215,4–228,2); el caso A de D85 (198,4; 79,2–284,3) se reporta aparte. El estrato de humanitarios se definió después de ver el problema de M214 (D90). El intervalo solo recoge la variabilidad del muestreo de las correcciones, no el error del modelo en contratos que ninguna muestra cubre; el de e5 es angosto por esa razón.
- **Estrato D (D93).** Con 0 funerarios en 208 contratos etiquetados, la proporción de funerarios sin señal es menor que 1,44 % (regla del tres), es decir, hasta 380 de 26.396 contratos de D.
- **No recuperados sin etiquetar (D22).** Los 100 contratos que la consulta original no recupera no se han etiquetado y no entran en ningún cálculo; se etiquetarán solo como prueba de lo que la búsqueda deja escapar, no para corregir el total. Hasta entonces el total es una cota inferior respecto de lo que la búsqueda no recupera.
- **Palabras de contexto en TF-IDF.** Entre los 20 términos que más empujan hacia `funerario` hay palabras de contexto y no de servicio («población», «personas», «vulnerable», «del distrito», «funcionarios», «víctimas»), y entre los que más empujan en contra aparecen «rosario» y «servicios profesionales» (`coeficientes_tfidf.md`).
- **Personal de apoyo (D92).** Los 117 contratos sin etiqueta humana con el patrón «servicios profesionales o apoyo a la gestión» que TF-IDF marca `funerario` pueden ser personal y no servicios: efecto máximo de 3,9 miles de millones, 1,5 % del total.
- La serie mezcla SECOP I y SECOP II; un mismo proveedor puede figurar en ambos con identificadores distintos (D15).
- **Ubicación.** Es la sede de la entidad, no el lugar de ejecución; las cifras por territorio siguen la ubicación de la entidad.
"""
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(txt, encoding="utf-8")
    print("escrito", DESTINO, len(txt))


if __name__ == "__main__":
    main()
