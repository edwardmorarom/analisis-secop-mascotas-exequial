# F4 · Mercado público funerario (SECOP 2020–2025)

Generado por `python -m src.modelos.mercado` y `python -m src.modelos.mercado_informe`. Las tablas están en `data/processed/resultados_secop/` (no se versionan). **Las secciones marcadas «borrador» no tienen conclusiones.** Cifras en miles de millones de pesos («mm»). Modelo de clasificación: TF-IDF (`clase_final`, D63); como sensibilidad, TF-IDF con `mixto`, e5 y e5 con `mixto`.

> **Cobertura (D70, D73, D74).** SECOP I se extendió a 2023–2025 (5.080 contratos candidatos más, D73), así que la serie cubre SECOP I y SECOP II en los seis años. Limitación: ni la muestra de 400 ni la validación de 60 incluyen contratos de SECOP I de 2023–2025; el error de clasificación en ese bloque se medirá con los 30 contratos de `docs/revision_f4/secop1_nuevos.xlsx`.

## 1. Cruce de la ubicación de la entidad con DIVIPOLA (D66)

Tabla de origen: `tasa_cruce_ubicacion.csv`.

| | contratos | funerarios (TF-IDF) |
|---|---|---|
| universo | 39,870 | 4,992 |
| con municipio DIVIPOLA | 38,136 (95.7%) | 4,841 |
| con departamento | 39,774 (99.8%) | 4,985 |

Sin municipio quedan los contratos con la entidad registrada en «No Definido» y unos pocos nombres sin equivalente. Los cruces aproximados fueron revisados por Edward (20 de 20 correctos, D66). **Decisión D66** (vigente).

## 2. Número y valor por año (D67)

Tabla de origen: `serie_anual.csv`; gráfico `docs/resultados/graficos/1_serie_anual_pesos_constantes.png`. Escenario principal (TF-IDF, solo `funerario`):

| año | contratos | valor corriente (mm) | valor constante 2025 (mm) |
|---|---|---|---|
| 2020 | 1.066 | 34,1 | 48,6 |
| 2021 | 973 | 39,2 | 54,2 |
| 2022 | 805 | 28,8 | 36,5 |
| 2023 | 765 | 30,5 | 34,3 |
| 2024 | 691 | 32,4 | 34,0 |
| 2025 | 692 | 55,3 | 55,4 |

Por fuente (`serie_anual_fuente.csv`):

| anio | fuente | contratos | valor constante 2025 (mm) |
|---|---|---|---|
| 2020 | secop1 | 982 | 27,0 |
| 2020 | secop2 | 84 | 21,6 |
| 2021 | secop1 | 816 | 20,1 |
| 2021 | secop2 | 157 | 34,1 |
| 2022 | secop1 | 598 | 15,3 |
| 2022 | secop2 | 207 | 21,1 |
| 2023 | secop1 | 525 | 13,2 |
| 2023 | secop2 | 240 | 21,0 |
| 2024 | secop1 | 396 | 10,0 |
| 2024 | secop2 | 295 | 24,0 |
| 2025 | secop1 | 339 | 9,6 |
| 2025 | secop2 | 353 | 45,8 |

Sensibilidad (suma 2020–2025; `serie_anual.csv`):

| escenario | contratos | valor constante 2025 (mm) |
|---|---|---|
| e5_con_mixto | 5.056 | 399,6 |
| e5_sin_mixto | 4.920 | 235,6 |
| tfidf_con_mixto | 5.096 | 413,8 |
| tfidf_sin_mixto | 4.992 | 262,9 |

**Decisión D67** (propuesta): pesos constantes de 2025 con el IPC mensual del mes de firma; valor inicial sin adiciones.

## 3. Territorio y por 100.000 habitantes (D66, D67)

Tablas: `departamento_resumen.csv`, `departamento_anual.csv`, `municipio_resumen.csv`, `municipio_anual.csv`; gráfico `2_departamentos_por_100mil.png`. La ubicación es la sede de la entidad compradora. Población DANE del año de firma. Diez departamentos con mayor valor por 100.000 habitantes (promedio anual 2020–2025):

| departamento | contratos | valor por 100.000 hab. al año (millones de 2025) | contratos por 100.000 hab. al año |
|---|---|---|---|
| GUAINÍA | 28 | 425,0 | 8,5 |
| VAUPÉS | 17 | 242,0 | 7,9 |
| GUAVIARE | 36 | 202,5 | 7,1 |
| VICHADA | 39 | 196,0 | 4,9 |
| BOGOTÁ, D.C. | 153 | 186,9 | 0,3 |
| AMAZONAS | 23 | 178,4 | 4,7 |
| ARCHIPIÉLAGO DE SAN ANDRÉS, PROVIDENCIA Y SANTA CATALINA | 1 | 158,9 | 1,6 |
| ARAUCA | 47 | 118,9 | 2,8 |
| SUCRE | 181 | 118,1 | 3,0 |
| NARIÑO | 416 | 117,2 | 4,1 |

Diez municipios con más contratos funerarios:

| municipio | departamento | contratos | valor constante 2025 (mm) |
|---|---|---|---|
| BOGOTÁ, D.C. | BOGOTÁ, D.C. | 126 | 45,7 |
| ARMENIA | QUINDÍO | 74 | 2,4 |
| SANTIAGO DE CALI | VALLE DEL CAUCA | 67 | 5,7 |
| BUCARAMANGA | SANTANDER | 42 | 5,5 |
| MEDELLÍN | ANTIOQUIA | 34 | 4,8 |
| PEREIRA | RISARALDA | 34 | 2,0 |
| EL ROSARIO | NARIÑO | 34 | 0,6 |
| POPAYÁN | CAUCA | 29 | 1,9 |
| PITALITO | HUILA | 25 | 0,4 |
| FLORENCIA | CAQUETÁ | 25 | 1,1 |

Los departamentos pequeños (Guainía, Vaupés, Amazonas, Vichada) lideran la tasa por su población reducida y pocos contratos; no son comparables con los grandes sin intervalos.

## 4. Patrones de compra (borrador)

Todo lo de esta sección es borrador sin conclusiones; usa los contratos `funerario` del escenario principal.

**Tipo de entidad** (reglas sobre el nombre de la entidad; `borrador_tipo_entidad.csv`). También: `borrador_orden_entidad.csv` (orden por fuente) y `borrador_sector_secop2.csv`.

| tipo_entidad | contratos | pct_contratos | pct_valor |
|---|---|---|---|
| alcaldia_municipio | 4.429 | 88,7 | 59,9 |
| educacion_universidad | 12 | 0,2 | 0,1 |
| gobernacion_departamento | 100 | 2,0 | 2,9 |
| otra_entidad | 229 | 4,6 | 14,0 |
| salud_hospital_ese | 89 | 1,8 | 3,3 |
| seguridad_justicia | 12 | 0,2 | 10,9 |
| servicios_publicos_empresa | 121 | 2,4 | 8,9 |

**Modalidad** (`borrador_modalidad.csv`; gráfico `3_modalidad.png`):

| modalidad_grupo | contratos | pct_contratos | pct_valor |
|---|---|---|---|
| contratacion_directa | 521 | 10,4 | 11,1 |
| licitacion_concurso | 9 | 0,2 | 14,2 |
| minima_cuantia | 4.014 | 80,4 | 38,4 |
| otra | 6 | 0,1 | 0,1 |
| regimen_especial | 167 | 3,3 | 8,0 |
| seleccion_abreviada | 275 | 5,5 | 28,2 |

**Participación de la contratación directa en el valor**, por año y fuente (`borrador_modalidad_directa_anual.csv`):

| anio | fuente | contratos | pct_valor_directa | pct_valor_directa_y_especial |
|---|---|---|---|---|
| 2020 | secop1 | 982 | 25,1 | 31,1 |
| 2020 | secop2 | 84 | 20,9 | 44,7 |
| 2021 | secop1 | 816 | 5,0 | 12,3 |
| 2021 | secop2 | 157 | 17,0 | 19,2 |
| 2022 | secop1 | 598 | 3,8 | 5,7 |
| 2022 | secop2 | 207 | 13,1 | 15,0 |
| 2023 | secop1 | 525 | 2,9 | 2,9 |
| 2023 | secop2 | 240 | 9,0 | 12,2 |
| 2024 | secop1 | 396 | 3,5 | 3,5 |
| 2024 | secop2 | 295 | 6,7 | 9,7 |
| 2025 | secop1 | 339 | 3,0 | 3,2 |
| 2025 | secop2 | 353 | 7,0 | 28,6 |

**Mes de firma** (`borrador_mes_firma.csv`):

| mes | contratos | pct_contratos | pct_valor |
|---|---|---|---|
| 1 | 362 | 7,3 | 5,0 |
| 2 | 727 | 14,6 | 11,8 |
| 3 | 797 | 16,0 | 12,4 |
| 4 | 627 | 12,6 | 11,6 |
| 5 | 512 | 10,3 | 8,3 |
| 6 | 398 | 8,0 | 6,5 |
| 7 | 332 | 6,7 | 5,5 |
| 8 | 267 | 5,3 | 7,9 |
| 9 | 261 | 5,2 | 5,7 |
| 10 | 247 | 4,9 | 4,9 |
| 11 | 221 | 4,4 | 9,4 |
| 12 | 241 | 4,8 | 11,0 |

**Componentes del servicio** (indicadores no excluyentes sobre el objeto; `componentes.csv`, `componentes_anual.csv`; gráfico `4_componentes.png`). Un contrato puede incluir varios componentes, así que los porcentajes no suman 100. Plan exequial solo con plan, póliza, auxilio funerario o afiliación; «servicios exequiales» por sí solo es servicio directo:

| componente | contratos | % de contratos que lo incluye | % del valor que lo incluye |
|---|---|---|---|
| incluye_inhumacion_cremacion | 3.058 | 61,3 | 68,6 |
| incluye_traslado | 305 | 6,1 | 4,0 |
| incluye_ataudes_bienes | 1.675 | 33,6 | 18,8 |
| incluye_plan_exequial | 413 | 8,3 | 4,8 |
| incluye_operacion_cementerio | 61 | 1,2 | 7,6 |
| incluye_disposicion_animales | 0 | 0,0 | 0,0 |
| incluye_atencion_vulnerables_NN | 4.045 | 81,0 | 59,8 |
| ninguno_de_los_componentes | 181 | 3,6 | 6,1 |

**Acierto de cada indicador** contra los 40 contratos que Edward revisó (`acierto_indicadores.csv`). **La medición es optimista: las reglas se ajustaron con esos mismos casos.** Además, Edward marcó un solo subtipo por contrato, así que la sensibilidad es confiable (los positivos que marcó son reales) pero la precisión es un mínimo: un componente presente que no era el marcado cuenta como falso positivo.

| indicador | positivos_marcados_por_edward | marcados_por_la_regla | aciertos | acierto | precision | sensibilidad |
|---|---|---|---|---|---|---|
| incluye_inhumacion_cremacion | 11 | 24 | 27 | 0.68 | 0.46 | 1.00 |
| incluye_traslado | 5 | 9 | 36 | 0.90 | 0.56 | 1.00 |
| incluye_ataudes_bienes | 8 | 13 | 35 | 0.88 | 0.62 | 1.00 |
| incluye_plan_exequial | 5 | 6 | 39 | 0.97 | 0.83 | 1.00 |
| incluye_operacion_cementerio | 3 | 3 | 40 | 1.00 | 1.00 | 1.00 |
| incluye_disposicion_animales | 0 | 0 | 40 | 1.00 |  |  |
| incluye_atencion_vulnerables_NN | 11 | 28 | 23 | 0.57 | 0.39 | 1.00 |

**Decisión D68** (propuesta, borrador): indicadores de componentes, que reemplazan al subtipo único con prioridad.

## 5. Proveedores (borrador)

Participación, HHI y CR4 por valor constante (`proveedores_hhi_cr4_anual.csv`, `proveedores_hhi_departamento.csv`, `proveedores_top_participacion.csv`; gráfico `5_concentracion_proveedores.png`). El identificador es el NIT (SECOP I, personas jurídicas) o el código de proveedor (SECOP II); las personas naturales van seudonimizadas (D15) y no se unen entre SECOP I y II, por lo que un mismo proveedor puede contarse dos veces en 2020–2022.

| anio | proveedores | HHI | CR4 |
|---|---|---|---|
| 2020 | 607 | 290 | 28.4 |
| 2021 | 534 | 470 | 36.1 |
| 2022 | 476 | 294 | 25.3 |
| 2023 | 471 | 267 | 26.5 |
| 2024 | 426 | 379 | 31.3 |
| 2025 | 440 | 769 | 50.1 |

HHI por departamento (2020–2025, departamentos con 5 o más proveedores, n = 32): percentiles 10, 25, 50, 75 y 90 = 489, 763, 1,251, 1,674, 2,525; 4 de 32 superan 2.500. Los cinco proveedores de mayor valor suman el 21.9 % del valor total (`proveedores_top_participacion.csv`).

**Decisión D69** (propuesta, borrador): identificador de proveedor y medidas de concentración.

## Limitaciones

- Clasificación con TF-IDF: F1 ponderado de 0,93 en la validación cruzada de 400 casos y 0,65 (0,86 sin ponderar) en la validación externa de 60, donde un solo caso de peso 3.293 explica la diferencia (D63).
- La serie mezcla SECOP I y SECOP II; un mismo proveedor puede figurar en ambos con identificadores distintos (D15).
- Ni la muestra de 400 ni la validación de 60 incluyen contratos de SECOP I de 2023–2025 (D74).
- La ubicación es la sede de la entidad, no el lugar de ejecución.
