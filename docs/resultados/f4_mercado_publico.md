# F4 · Mercado público funerario (SECOP 2020–2025)

Generado por `python -m src.modelos.mercado` y `python -m src.modelos.mercado_informe`. Las tablas están en `data/processed/resultados_secop/` (no se versionan). **Las secciones marcadas «borrador» no tienen conclusiones.** Cifras en miles de millones de pesos («mm»). Modelo de clasificación: TF-IDF (`clase_final`, D63); como sensibilidad, TF-IDF con `mixto`, e5 y e5 con `mixto`.

> **Advertencia de cobertura (D70).** SECOP I se descargó solo para 2020–2022, pero en `f789-7hwg` hay 1.914, 1.841 y 1.647 contratos candidatos firmados en 2023, 2024 y 2025 (misma consulta y estados de D42). Por eso la caída de 2022 a 2023 y la subida del HHI pueden ser, en buena parte, un efecto de cobertura y no un cambio del mercado. Las series de 2023–2025 están incompletas hasta que se decida si se descarga ese tramo.

## 1. Cruce de la ubicación de la entidad con DIVIPOLA (D66)

Tabla de origen: `tasa_cruce_ubicacion.csv`.

| | contratos | funerarios (TF-IDF) |
|---|---|---|
| universo | 34,790 | 3,732 |
| con municipio DIVIPOLA | 33,060 (95.0%) | 3,583 |
| con departamento | 34,694 (99.7%) | 3,725 |

Sin municipio quedan 1.706 contratos con la entidad en «No Definido» y 24 de otros nombres. Los cruces aproximados (22 pares) están en `docs/revision_f4/cruces_secop.xlsx` para revisión. **Decisión D66** (propuesta).

## 2. Número y valor por año (D67)

Tabla de origen: `serie_anual.csv`; gráfico `docs/resultados/graficos/1_serie_anual_pesos_constantes.png`. Escenario principal (TF-IDF, solo `funerario`):

| año | contratos | valor corriente (mm) | valor constante 2025 (mm) |
|---|---|---|---|
| 2020 | 1.066 | 34,1 | 48,6 |
| 2021 | 973 | 39,2 | 54,2 |
| 2022 | 805 | 28,8 | 36,5 |
| 2023 | 240 | 18,8 | 21,0 |
| 2024 | 295 | 22,9 | 24,0 |
| 2025 | 353 | 45,8 | 45,8 |

Por fuente (`serie_anual_fuente.csv`): SECOP I cubre solo 2020–2022, así que la caída de 2022 a 2023 es un cambio de fuente.

| anio | fuente | contratos | valor constante 2025 (mm) |
|---|---|---|---|
| 2020 | secop1 | 982 | 27,0 |
| 2020 | secop2 | 84 | 21,6 |
| 2021 | secop1 | 816 | 20,1 |
| 2021 | secop2 | 157 | 34,1 |
| 2022 | secop1 | 598 | 15,3 |
| 2022 | secop2 | 207 | 21,1 |
| 2023 | secop2 | 240 | 21,0 |
| 2024 | secop2 | 295 | 24,0 |
| 2025 | secop2 | 353 | 45,8 |

Sensibilidad (suma 2020–2025; `serie_anual.csv`):

| escenario | contratos | valor constante 2025 (mm) |
|---|---|---|
| e5_con_mixto | 3.753 | 365,9 |
| e5_sin_mixto | 3.639 | 202,8 |
| tfidf_con_mixto | 3.821 | 380,5 |
| tfidf_sin_mixto | 3.732 | 230,1 |

**Decisión D67** (propuesta): pesos constantes de 2025 con el IPC mensual del mes de firma; valor inicial sin adiciones.

## 3. Territorio y por 100.000 habitantes (D66, D67)

Tablas: `departamento_resumen.csv`, `departamento_anual.csv`, `municipio_resumen.csv`, `municipio_anual.csv`; gráfico `2_departamentos_por_100mil.png`. La ubicación es la sede de la entidad compradora. Población DANE del año de firma. Diez departamentos con mayor valor por 100.000 habitantes (promedio anual 2020–2025):

| departamento | contratos | valor por 100.000 hab. al año (millones de 2025) | contratos por 100.000 hab. al año |
|---|---|---|---|
| GUAINÍA | 18 | 592,7 | 11,2 |
| VAUPÉS | 10 | 233,2 | 7,8 |
| AMAZONAS | 20 | 197,2 | 4,9 |
| BOGOTÁ, D.C. | 153 | 186,9 | 0,3 |
| VICHADA | 21 | 184,5 | 5,5 |
| ARCHIPIÉLAGO DE SAN ANDRÉS, PROVIDENCIA Y SANTA CATALINA | 1 | 158,9 | 1,6 |
| GUAVIARE | 19 | 141,8 | 5,7 |
| QUINDÍO | 135 | 105,1 | 4,1 |
| NARIÑO | 253 | 102,3 | 3,0 |
| CESAR | 105 | 90,2 | 1,3 |

Diez municipios con más contratos funerarios:

| municipio | departamento | contratos | valor constante 2025 (mm) |
|---|---|---|---|
| BOGOTÁ, D.C. | BOGOTÁ, D.C. | 126 | 45,7 |
| ARMENIA | QUINDÍO | 74 | 2,4 |
| SANTIAGO DE CALI | VALLE DEL CAUCA | 67 | 5,7 |
| BUCARAMANGA | SANTANDER | 42 | 5,5 |
| MEDELLÍN | ANTIOQUIA | 34 | 4,8 |
| PEREIRA | RISARALDA | 32 | 2,0 |
| POPAYÁN | CAUCA | 29 | 1,9 |
| FLORENCIA | CAQUETÁ | 25 | 1,1 |
| PITALITO | HUILA | 25 | 0,4 |
| SAN JOSÉ DE CÚCUTA | NORTE DE SANTANDER | 22 | 1,5 |

Los departamentos pequeños (Guainía, Vaupés, Amazonas, Vichada) lideran la tasa por su población reducida y pocos contratos; no son comparables con los grandes sin intervalos.

## 4. Patrones de compra (borrador)

Todo lo de esta sección es borrador sin conclusiones; usa los contratos `funerario` del escenario principal.

**Tipo de entidad** (reglas sobre el nombre de la entidad; `borrador_tipo_entidad.csv`). También: `borrador_orden_entidad.csv` (orden por fuente) y `borrador_sector_secop2.csv`.

| tipo_entidad | contratos | pct_contratos | pct_valor |
|---|---|---|---|
| alcaldia_municipio | 3.185 | 85,3 | 54,4 |
| educacion_universidad | 12 | 0,3 | 0,1 |
| gobernacion_departamento | 92 | 2,5 | 3,2 |
| otra_entidad | 224 | 6,0 | 16,0 |
| salud_hospital_ese | 87 | 2,3 | 3,7 |
| seguridad_justicia | 12 | 0,3 | 12,4 |
| servicios_publicos_empresa | 120 | 3,2 | 10,2 |

**Modalidad** (`borrador_modalidad.csv`; gráfico `3_modalidad.png`):

| modalidad_grupo | contratos | pct_contratos | pct_valor |
|---|---|---|---|
| contratacion_directa | 495 | 13,3 | 12,2 |
| licitacion_concurso | 9 | 0,2 | 16,2 |
| minima_cuantia | 2.839 | 76,1 | 32,8 |
| otra | 2 | 0,1 | 0,2 |
| regimen_especial | 166 | 4,4 | 9,1 |
| seleccion_abreviada | 221 | 5,9 | 29,5 |

**Participación de la contratación directa en el valor**, por año y fuente (`borrador_modalidad_directa_anual.csv`):

| anio | fuente | contratos | pct_valor_directa | pct_valor_directa_y_especial |
|---|---|---|---|---|
| 2020 | secop1 | 982 | 25,1 | 31,1 |
| 2020 | secop2 | 84 | 20,9 | 44,7 |
| 2021 | secop1 | 816 | 5,0 | 12,3 |
| 2021 | secop2 | 157 | 17,0 | 19,2 |
| 2022 | secop1 | 598 | 3,8 | 5,7 |
| 2022 | secop2 | 207 | 13,1 | 15,0 |
| 2023 | secop2 | 240 | 9,0 | 12,2 |
| 2024 | secop2 | 295 | 6,7 | 9,7 |
| 2025 | secop2 | 353 | 7,0 | 28,6 |

**Mes de firma** (`borrador_mes_firma.csv`):

| mes | contratos | pct_contratos | pct_valor |
|---|---|---|---|
| 1 | 269 | 7,2 | 4,8 |
| 2 | 498 | 13,3 | 11,0 |
| 3 | 570 | 15,3 | 11,3 |
| 4 | 451 | 12,1 | 11,2 |
| 5 | 380 | 10,2 | 7,8 |
| 6 | 319 | 8,5 | 6,5 |
| 7 | 248 | 6,6 | 5,4 |
| 8 | 214 | 5,7 | 8,2 |
| 9 | 205 | 5,5 | 6,0 |
| 10 | 189 | 5,1 | 5,1 |
| 11 | 180 | 4,8 | 10,4 |
| 12 | 209 | 5,6 | 12,4 |

**Subtipo de servicio**, reglas sobre el objeto (`borrador_subtipo.csv`, `borrador_subtipo_anual.csv`; gráfico `4_subtipo.png`). Se dejaron 40 contratos para validar en `docs/revision_f4/subtipos.xlsx`:

| subtipo | contratos | pct_contratos | pct_valor |
|---|---|---|---|
| cofres_y_bienes | 129 | 3,5 | 1,3 |
| cremacion | 153 | 4,1 | 5,0 |
| disposicion_animales | 2 | 0,1 | 0,0 |
| inhumacion_NN_vulnerables | 2.241 | 60,0 | 43,6 |
| operacion_cementerio | 58 | 1,6 | 9,5 |
| otro | 551 | 14,8 | 32,9 |
| plan_o_poliza_exequial | 450 | 12,1 | 5,6 |
| traslado | 148 | 4,0 | 1,9 |

**Decisión D68** (propuesta, borrador): agrupación de modalidades, reglas de tipo de entidad y de subtipo.

## 5. Proveedores (borrador)

Participación, HHI y CR4 por valor constante (`proveedores_hhi_cr4_anual.csv`, `proveedores_hhi_departamento.csv`, `proveedores_top_participacion.csv`; gráfico `5_concentracion_proveedores.png`). El identificador es el NIT (SECOP I, personas jurídicas) o el código de proveedor (SECOP II); las personas naturales van seudonimizadas (D15) y no se unen entre SECOP I y II, por lo que un mismo proveedor puede contarse dos veces en 2020–2022.

| anio | proveedores | HHI | CR4 |
|---|---|---|---|
| 2020 | 607 | 290 | 28.4 |
| 2021 | 534 | 470 | 36.1 |
| 2022 | 476 | 294 | 25.3 |
| 2023 | 139 | 676 | 43.2 |
| 2024 | 167 | 742 | 44.3 |
| 2025 | 204 | 1120 | 60.6 |

HHI por departamento (2020–2025, departamentos con 5 o más proveedores, n = 31): percentiles 10, 25, 50, 75 y 90 = 633, 918, 1,328, 1,941, 2,778; 4 de 31 superan 2.500. Los cinco proveedores de mayor valor suman el 25.0 % del valor total (`proveedores_top_participacion.csv`).

**Decisión D69** (propuesta, borrador): identificador de proveedor y medidas de concentración.

## Limitaciones

- Clasificación con TF-IDF: F1 ponderado de 0,93 en la validación cruzada de 400 casos y 0,65 (0,86 sin ponderar) en la validación externa de 60, donde un solo caso de peso 3.293 explica la diferencia (D63).
- SECOP I cubre 2020–2022 y SECOP II 2020–2025: la serie nacional mezcla fuentes.
- La ubicación es la sede de la entidad, no el lugar de ejecución.
