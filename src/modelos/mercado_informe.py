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

    principal = sa[sa["escenario"] == "tfidf_sin_mixto"].copy()
    principal["valor corriente (mm)"] = mm(principal["valor_corriente"])
    principal["valor constante 2025 (mm)"] = mm(principal["valor_constante_2025"])
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
    d_sub = sub[["componente", "contratos", "pct_contratos", "pct_valor"]].rename(columns={
        "pct_contratos": "% de contratos que lo incluye", "pct_valor": "% del valor que lo incluye"})
    ac = pd.read_csv(s / "acierto_indicadores.csv")
    d_ac = ac[["indicador", "positivos_marcados_por_edward", "marcados_por_la_regla", "aciertos", "acierto", "precision", "sensibilidad"]]
    d_hh = hh.copy()
    d_hh["anio"] = d_hh["anio"].astype(int)
    d_hh["proveedores"] = d_hh["proveedores"].astype(int)
    con5 = hd[hd["proveedores"] >= 5]
    cuantiles = con5["HHI"].quantile([0.1, 0.25, 0.5, 0.75, 0.9]).round(0)

    c = lambda k: cruce.loc[k]
    txt = f"""# F4 · Mercado público funerario (SECOP 2020–2025)

Generado por `python -m src.modelos.mercado` y `python -m src.modelos.mercado_informe`. Las tablas están en `{TABLAS}/` (no se versionan). **Las secciones marcadas «borrador» no tienen conclusiones.** Cifras en miles de millones de pesos («mm»). Modelo de clasificación: TF-IDF (`clase_final`, D63); como sensibilidad, TF-IDF con `mixto`, e5 y e5 con `mixto`.

> **Advertencia de cobertura (D70).** SECOP I se descargó solo para 2020–2022, pero en `f789-7hwg` hay 1.914, 1.841 y 1.647 contratos candidatos firmados en 2023, 2024 y 2025 (misma consulta y estados de D42). Por eso la caída de 2022 a 2023 y la subida del HHI pueden ser, en buena parte, un efecto de cobertura y no un cambio del mercado. Las series de 2023–2025 están incompletas hasta que se decida si se descarga ese tramo.

## 1. Cruce de la ubicación de la entidad con DIVIPOLA (D66)

Tabla de origen: `tasa_cruce_ubicacion.csv`.

| | contratos | funerarios (TF-IDF) |
|---|---|---|
| universo | {int(c('contratos')['universo']):,} | {int(c('contratos')['funerario_tfidf']):,} |
| con municipio DIVIPOLA | {int(c('con_municipio_DIVIPOLA')['universo']):,} ({c('con_municipio_DIVIPOLA')['tasa_universo']:.1%}) | {int(c('con_municipio_DIVIPOLA')['funerario_tfidf']):,} |
| con departamento | {int(c('con_departamento')['universo']):,} ({c('con_departamento')['tasa_universo']:.1%}) | {int(c('con_departamento')['funerario_tfidf']):,} |

Sin municipio quedan 1.706 contratos con la entidad en «No Definido» y 24 de otros nombres. Los cruces aproximados (22 pares) están en `docs/revision_f4/cruces_secop.xlsx` para revisión. **Decisión D66** (propuesta).

## 2. Número y valor por año (D67)

Tabla de origen: `serie_anual.csv`; gráfico `docs/resultados/graficos/1_serie_anual_pesos_constantes.png`. Escenario principal (TF-IDF, solo `funerario`):

{tabla(anual)}

Por fuente (`serie_anual_fuente.csv`): SECOP I cubre solo 2020–2022, así que la caída de 2022 a 2023 es un cambio de fuente.

{tabla(fuente)}

Sensibilidad (suma 2020–2025; `serie_anual.csv`):

{tabla(sens)}

**Decisión D67** (propuesta): pesos constantes de 2025 con el IPC mensual del mes de firma; valor inicial sin adiciones.

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

**Componentes del servicio** (indicadores no excluyentes sobre el objeto; `componentes.csv`, `componentes_anual.csv`; gráfico `4_componentes.png`). Un contrato puede incluir varios componentes, así que los porcentajes no suman 100. Plan exequial solo con plan, póliza, auxilio funerario o afiliación; «servicios exequiales» por sí solo es servicio directo:

{tabla(d_sub)}

**Acierto de cada indicador** contra los 40 contratos que Edward revisó (`acierto_indicadores.csv`). **La medición es optimista: las reglas se ajustaron con esos mismos casos.** Además, Edward marcó un solo subtipo por contrato, así que la sensibilidad es confiable (los positivos que marcó son reales) pero la precisión es un mínimo: un componente presente que no era el marcado cuenta como falso positivo.

{tabla(d_ac, {"acierto": "{:.2f}", "precision": "{:.2f}", "sensibilidad": "{:.2f}"})}

**Decisión D68** (propuesta, borrador): indicadores de componentes, que reemplazan al subtipo único con prioridad.

## 5. Proveedores (borrador)

Participación, HHI y CR4 por valor constante (`proveedores_hhi_cr4_anual.csv`, `proveedores_hhi_departamento.csv`, `proveedores_top_participacion.csv`; gráfico `5_concentracion_proveedores.png`). El identificador es el NIT (SECOP I, personas jurídicas) o el código de proveedor (SECOP II); las personas naturales van seudonimizadas (D15) y no se unen entre SECOP I y II, por lo que un mismo proveedor puede contarse dos veces en 2020–2022.

{tabla(d_hh, {"HHI": "{:.0f}", "CR4": "{:.1f}"})}

HHI por departamento (2020–2025, departamentos con 5 o más proveedores, n = {len(con5)}): percentiles 10, 25, 50, 75 y 90 = {', '.join(f'{v:,.0f}' for v in cuantiles)}; {int((con5['HHI'] > 2500).sum())} de {len(con5)} superan 2.500. Los cinco proveedores de mayor valor suman el {top.head(5)['participacion_valor_pct'].sum():.1f} % del valor total (`proveedores_top_participacion.csv`).

**Decisión D69** (propuesta, borrador): identificador de proveedor y medidas de concentración.

## Limitaciones

- Clasificación con TF-IDF: F1 ponderado de 0,93 en la validación cruzada de 400 casos y 0,65 (0,86 sin ponderar) en la validación externa de 60, donde un solo caso de peso 3.293 explica la diferencia (D63).
- SECOP I cubre 2020–2022 y SECOP II 2020–2025: la serie nacional mezcla fuentes.
- La ubicación es la sede de la entidad, no el lugar de ejecución.
"""
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(txt, encoding="utf-8")
    print("escrito", DESTINO, len(txt))


if __name__ == "__main__":
    main()
