# F4 · Mercado público funerario (SECOP 2020–2025)

Generado por `python -m src.modelos.mercado` y `python -m src.modelos.mercado_informe`. Las tablas están en `data/processed/resultados_secop/` (no se versionan). **Las secciones marcadas «borrador» no tienen conclusiones.** Cifras en miles de millones de pesos («mm»). Modelo de clasificación: TF-IDF (`clase_final`, D63). **La cifra principal es solo `funerario` (D89); los `mixto` van aparte y no se suman.** El estimador principal es el de la sección 2c (D90, D93); el caso A de D85 se reporta al lado.

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
| 2020 | 1.066 | 31,4 | 44,8 |
| 2021 | 973 | 30,3 | 41,9 |
| 2022 | 809 | 28,9 | 36,6 |
| 2023 | 765 | 30,4 | 34,2 |
| 2024 | 690 | 33,4 | 35,0 |
| 2025 | 689 | 38,2 | 38,2 |

Por fuente (`serie_anual_fuente.csv`):

| anio | fuente | contratos | valor constante 2025 (mm) |
|---|---|---|---|
| 2020 | secop1 | 983 | 28,0 |
| 2020 | secop2 | 83 | 16,8 |
| 2021 | secop1 | 816 | 20,0 |
| 2021 | secop2 | 157 | 21,8 |
| 2022 | secop1 | 599 | 15,4 |
| 2022 | secop2 | 210 | 21,2 |
| 2023 | secop1 | 526 | 13,2 |
| 2023 | secop2 | 239 | 21,0 |
| 2024 | secop1 | 396 | 10,0 |
| 2024 | secop2 | 294 | 25,0 |
| 2025 | secop1 | 339 | 9,6 |
| 2025 | secop2 | 350 | 28,7 |

Sensibilidad (suma 2020–2025; `serie_anual.csv`). Los escenarios con `mixto` no son un límite superior del mercado (D89); se conservan solo como cálculo:

| escenario | contratos | valor constante 2025 (mm) |
|---|---|---|
| e5_con_mixto | 5.060 | 381,4 |
| e5_sin_mixto | 4.920 | 223,2 |
| tfidf_con_mixto | 5.103 | 388,1 |
| tfidf_sin_mixto | 4.992 | 230,6 |

**Decisión D67** (propuesta): pesos constantes de 2025 con el IPC mensual del mes de firma; valor inicial sin adiciones.

## 2b. Estimación principal del total (D84, D85, D86)

**Jerarquía (D84):** en el mercado, toda etiqueta humana reemplaza a la predicción del modelo (muestra de 400, validación de 60 revisada, los 30 de SECOP I 2023–2025, los 2 de D81 y los 50 de la revisión por valor). Las métricas de evaluación siguen usando las predicciones fuera de pliegue.

**Estimación principal del total, 2020–2025, en miles de millones de pesos de 2025** (estimador de diferencia, Särndal, Swensson y Wretman 1992: total del modelo más la corrección de la revisión censal de los 50 de mayor valor y de los 2 de D81, más la suma en la muestra de 400 de peso × (indicador humano − indicador predicho) × valor, con intervalo bootstrap estratificado):

| modelo | mixto | sin corregir | con etiquetas humanas | estimador (solo muestra) | ESTIMADOR PRINCIPAL | IC 95 % |
|---|---|---|---|---|---|---|
| TF-IDF | sin mixto | 262.9 | 230.6 | 227.8 | 198.4 | 79.2 a 284.3 |
| TF-IDF | con mixto | 413.8 | 388.1 | 449.1 | 421.2 | 388.0 a 472.1 |
| e5 | sin mixto | 235.6 | 223.2 | 181.1 | 172.8 | 71.9 a 228.2 |
| e5 | con mixto | 399.6 | 381.4 | 415.1 | 395.9 | 380.4 a 415.3 |

Mercado funerario con TF-IDF (sin y con `mixto` por separado) con y sin la revisión por valor (A: sin revisión; B: jerarquía sin los 50; C: jerarquía completa; `mercado_con_y_sin_revision.csv`):

| estado | mixto | contratos | valor_mm | v2020 | v2021 | v2022 | v2023 | v2024 | v2025 |
|---|---|---|---|---|---|---|---|---|---|
| A: sin revisión (modelo y las 2 etiquetas de D81) | sin | 4.990 | 246.2 | 48.6 | 54.2 | 36.5 | 34.3 | 34.0 | 38.7 |
| A: sin revisión (modelo y las 2 etiquetas de D81) | con | 5.095 | 406.1 | 186.0 | 54.5 | 39.6 | 38.3 | 36.9 | 50.9 |
| B: jerarquía sin la revisión por valor (400, 60, 30, D81 y lotes de D91) | sin | 4.994 | 243.8 | 48.5 | 51.3 | 36.6 | 34.2 | 35.0 | 38.2 |
| B: jerarquía sin la revisión por valor (400, 60, 30, D81 y lotes de D91) | con | 5.109 | 407.9 | 186.1 | 54.7 | 40.0 | 38.2 | 38.2 | 50.7 |
| C: jerarquía completa (con los 50 por valor y los lotes de D91) | sin | 4.992 | 230.6 | 44.8 | 41.9 | 36.6 | 34.2 | 35.0 | 38.2 |
| C: jerarquía completa (con los 50 por valor y los lotes de D91) | con | 5.103 | 388.1 | 177.8 | 45.2 | 37.3 | 38.2 | 39.5 | 50.1 |

**Revisión por valor (D83, D86):** Edward etiquetó los 50 contratos de mayor valor: 28 funerario (55.0 miles de millones), 8 mixto (142.4 miles de millones), 14 no_funerario (46.1 miles de millones). Precisión y sensibilidad de los modelos en esos 50, por contratos y ponderadas por valor constante (`top_valor_evaluacion.csv`):

| definicion | modelo | predichos | humanos | aciertos | precision_por_contratos | precision_por_valor | sensibilidad_por_valor |
|---|---|---|---|---|---|---|---|
| sin mixto | tfidf | 30 | 28 | 27 | 0.900 | 0.780 | 0.967 |
| sin mixto | e5 | 30 | 28 | 24 | 0.800 | 0.797 | 0.929 |
| con mixto | tfidf | 42 | 36 | 35 | 0.833 | 0.903 | 0.993 |
| con mixto | e5 | 44 | 36 | 32 | 0.727 | 0.859 | 0.980 |

## 2c. Estimador principal con los lotes nuevos (D90, D93)

Caso C de D90: los 317 contratos humanitarios con componente funerario forman un estrato aparte. Los 21 con etiqueta previa se corrigen exactamente; los 296 restantes se estiman con la muestra de 40 (estimador de diferencia dentro de cada estrato A1 y A2, pesos de D91: 8,33 y 4,60). El estrato D suma los 150 nuevos a los 50 de la muestra de 400 (200 con peso común). Intervalo bootstrap estratificado (2.000 remuestreos, semilla 2026). Miles de millones de pesos de 2025, solo `funerario`.

| modelo | total sin corregir | corrección censal | corrección muestra 400 y D | corrección humanitarios (40) | **estimador principal** | IC 95 % |
|---|---|---|---|---|---|---|
| TF-IDF | 262.9 | -33.5 | 24.6 | 0.09 | **254.0** | 225.4 a 304.5 |
| e5 | 235.6 | -12.4 | -1.3 | 0.06 | **221.9** | 215.4 a 228.2 |

**Caso A (D85, para transparencia; M214 dentro de la muestra de A2):** TF-IDF 198.4 (IC 79.2 a 284.3).

**Contratos con componente funerario no separable (`mixto`, D89)**, aparte y sin sumarse: 111 contratos, 157.4 miles de millones de pesos de 2025 (TF-IDF con la jerarquía de etiquetas). Por año:

| año | contratos mixto | valor constante 2025 (mm) |
|---|---|---|
| 2020 | 14 | 133,0 |
| 2021 | 18 | 3,3 |
| 2022 | 21 | 0,7 |
| 2023 | 18 | 4,0 |
| 2024 | 21 | 4,5 |
| 2025 | 19 | 11,8 |

**Estrato D, cota de funerarios ocultos:** 0 funerarios en 208 contratos etiquetados (50 de la muestra de 400, 150 nuevos y 8 de la validación de 60). Regla del tres: la proporción de funerarios en D es menor que 1.44% con 95 % de confianza, es decir, hasta 381 de los 26,396 contratos de D (cifra ilustrativa de valor con el valor medio de un contrato de D, 73 millones: 28.0 miles de millones). No es una estimación, es un límite superior.

**TF-IDF en los lotes nuevos** (predicciones del modelo entrenado con los 400, sin haber visto estos contratos; `f1_lotes_nuevos.csv`). Humanitarios 40, `funerario`:

| modelo | escala | precision | sensibilidad | f1 | f1_ic_bajo | f1_ic_alto |
|---|---|---|---|---|---|---|
| TF-IDF | ponderado | 1.000 | 0.953 | 0.976 | 0.934 | 1.000 |
| TF-IDF | sin ponderar | 1.000 | 0.943 | 0.971 | 0.925 | 1.000 |
| e5 | ponderado | 1.000 | 0.969 | 0.985 | 0.950 | 1.000 |
| e5 | sin ponderar | 1.000 | 0.971 | 0.986 | 0.952 | 1.000 |

Estrato D, 150 contratos (todos `no_funerario`; sin positivos el F1 no está definido):

| modelo | falsos_positivos | verdaderos_negativos | positivos_reales |
|---|---|---|---|
| TF-IDF | 0,0 | 150,0 | 0,0 |
| e5 | 0,0 | 150,0 | 0,0 |

## 3. Territorio y por 100.000 habitantes (D66, D67)

Tablas: `departamento_resumen.csv`, `departamento_anual.csv`, `municipio_resumen.csv`, `municipio_anual.csv`; gráfico `2_departamentos_por_100mil.png`. La ubicación es la sede de la entidad compradora. Población DANE del año de firma. Diez departamentos con mayor valor por 100.000 habitantes (promedio anual 2020–2025):

| departamento | contratos | valor por 100.000 hab. al año (millones de 2025) | contratos por 100.000 hab. al año |
|---|---|---|---|
| GUAINÍA | 28 | 425,0 | 8,5 |
| VAUPÉS | 17 | 242,0 | 7,9 |
| GUAVIARE | 36 | 202,5 | 7,1 |
| VICHADA | 39 | 196,0 | 4,9 |
| AMAZONAS | 24 | 179,5 | 4,9 |
| ARCHIPIÉLAGO DE SAN ANDRÉS, PROVIDENCIA Y SANTA CATALINA | 1 | 158,9 | 1,6 |
| BOGOTÁ, D.C. | 150 | 123,7 | 0,3 |
| ARAUCA | 47 | 118,9 | 2,8 |
| SUCRE | 181 | 118,3 | 3,0 |
| QUINDÍO | 143 | 110,6 | 4,3 |

Diez municipios con más contratos funerarios:

| municipio | departamento | contratos | valor constante 2025 (mm) |
|---|---|---|---|
| BOGOTÁ, D.C. | BOGOTÁ, D.C. | 124 | 20,7 |
| ARMENIA | QUINDÍO | 75 | 2,5 |
| SANTIAGO DE CALI | VALLE DEL CAUCA | 67 | 5,7 |
| BUCARAMANGA | SANTANDER | 40 | 5,3 |
| PEREIRA | RISARALDA | 34 | 2,0 |
| MEDELLÍN | ANTIOQUIA | 34 | 4,8 |
| EL ROSARIO | NARIÑO | 34 | 0,6 |
| POPAYÁN | CAUCA | 29 | 1,9 |
| PITALITO | HUILA | 26 | 0,4 |
| FLORENCIA | CAQUETÁ | 25 | 1,1 |

Los departamentos pequeños (Guainía, Vaupés, Amazonas, Vichada) lideran la tasa por su población reducida y pocos contratos; no son comparables con los grandes sin intervalos.

## 4. Patrones de compra (borrador)

Todo lo de esta sección es borrador sin conclusiones; usa los contratos `funerario` del escenario principal.

**Tipo de entidad** (reglas sobre el nombre de la entidad; `borrador_tipo_entidad.csv`). También: `borrador_orden_entidad.csv` (orden por fuente) y `borrador_sector_secop2.csv`.

| tipo_entidad | contratos | pct_contratos | pct_valor |
|---|---|---|---|
| alcaldia_municipio | 4.430 | 88,7 | 63,4 |
| educacion_universidad | 13 | 0,3 | 0,1 |
| gobernacion_departamento | 99 | 2,0 | 3,2 |
| otra_entidad | 233 | 4,7 | 16,6 |
| salud_hospital_ese | 85 | 1,7 | 1,6 |
| seguridad_justicia | 13 | 0,3 | 12,4 |
| servicios_publicos_empresa | 119 | 2,4 | 2,7 |

**Modalidad** (`borrador_modalidad.csv`; gráfico `3_modalidad.png`):

| modalidad_grupo | contratos | pct_contratos | pct_valor |
|---|---|---|---|
| contratacion_directa | 523 | 10,5 | 11,7 |
| licitacion_concurso | 7 | 0,1 | 8,7 |
| minima_cuantia | 4.020 | 80,5 | 43,9 |
| otra | 5 | 0,1 | 0,1 |
| regimen_especial | 162 | 3,2 | 3,0 |
| seleccion_abreviada | 275 | 5,5 | 32,6 |

**Participación de la contratación directa en el valor**, por año y fuente (`borrador_modalidad_directa_anual.csv`):

| anio | fuente | contratos | pct_valor_directa | pct_valor_directa_y_especial |
|---|---|---|---|---|
| 2020 | secop1 | 983 | 28,5 | 34,2 |
| 2020 | secop2 | 83 | 26,8 | 28,9 |
| 2021 | secop1 | 816 | 5,1 | 11,8 |
| 2021 | secop2 | 157 | 12,8 | 16,2 |
| 2022 | secop1 | 599 | 3,8 | 5,7 |
| 2022 | secop2 | 210 | 13,3 | 15,2 |
| 2023 | secop1 | 526 | 2,9 | 2,9 |
| 2023 | secop2 | 239 | 8,8 | 12,0 |
| 2024 | secop1 | 396 | 3,5 | 3,5 |
| 2024 | secop2 | 294 | 5,6 | 8,5 |
| 2025 | secop1 | 339 | 3,0 | 3,2 |
| 2025 | secop2 | 350 | 10,4 | 13,4 |

**Mes de firma** (`borrador_mes_firma.csv`):

| mes | contratos | pct_contratos | pct_valor |
|---|---|---|---|
| 1 | 364 | 7,3 | 5,2 |
| 2 | 728 | 14,6 | 9,5 |
| 3 | 796 | 15,9 | 14,1 |
| 4 | 626 | 12,5 | 13,2 |
| 5 | 513 | 10,3 | 9,9 |
| 6 | 398 | 8,0 | 7,3 |
| 7 | 333 | 6,7 | 6,0 |
| 8 | 266 | 5,3 | 4,9 |
| 9 | 262 | 5,2 | 6,5 |
| 10 | 246 | 4,9 | 5,6 |
| 11 | 221 | 4,4 | 8,6 |
| 12 | 239 | 4,8 | 9,1 |

**Componentes del servicio** (indicadores no excluyentes sobre el objeto; `componentes.csv`, `componentes_anual.csv`; gráfico `4_componentes.png`). Solo se reportan los componentes con 35 o más aciertos de 40 contra la revisión de Edward. Un contrato puede incluir varios componentes, así que los porcentajes no suman 100. Plan exequial solo con plan, póliza, auxilio funerario o afiliación; «servicios exequiales» por sí solo es servicio directo:

| componente | contratos | % de contratos que lo incluye | % del valor que lo incluye |
|---|---|---|---|
| incluye_traslado | 306 | 6,1 | 4,5 |
| incluye_ataudes_bienes | 1.674 | 33,5 | 21,4 |
| incluye_plan_exequial | 414 | 8,3 | 5,4 |
| incluye_operacion_cementerio | 61 | 1,2 | 1,2 |
| incluye_disposicion_animales | 0 | 0,0 | 0,0 |

**Acierto de los componentes reportados** contra los 40 contratos (`acierto_indicadores.csv`). **La medición es optimista: las reglas se ajustaron con esos mismos casos.** Además, Edward marcó un solo subtipo por contrato, así que la sensibilidad es confiable pero la precisión es un mínimo.

| indicador | aciertos | acierto | precision | sensibilidad |
|---|---|---|---|---|
| incluye_traslado | 36 | 0.90 | 0.56 | 1.00 |
| incluye_ataudes_bienes | 35 | 0.88 | 0.62 | 1.00 |
| incluye_plan_exequial | 39 | 0.97 | 0.83 | 1.00 |
| incluye_operacion_cementerio | 40 | 1.00 | 1.00 | 1.00 |
| incluye_disposicion_animales | 40 | 1.00 |  |  |

**Indicadores en revisión** (menos de 35 aciertos de 40; no se reportan sus porcentajes): `incluye_inhumacion_cremacion` y `incluye_atencion_vulnerables_NN`. Casi todos los contratos funerarios mencionan servicios directos y población vulnerable, y la verdad de referencia tiene un solo subtipo por contrato, de modo que esos indicadores no se pueden evaluar bien con estos 40 casos.

| indicador | aciertos | acierto | precision | sensibilidad |
|---|---|---|---|---|
| incluye_inhumacion_cremacion | 27 | 0.68 | 0.46 | 1.00 |
| incluye_atencion_vulnerables_NN | 23 | 0.57 | 0.39 | 1.00 |

**Disposición de animales** (evaluada aparte): el estrato B de la muestra de 400 son los 23 contratos «posible disposición de animales» (todo el estrato: N = n = 23), y todos son `no_funerario`. Casi todos son gestión de residuos peligrosos de centros de zoonosis; solo uno (M078) incluye «animales muertos» de más de 50 kg. El indicador lo marca y no marca los otros 22; ningún contrato clasificado como `funerario` lo activa (D78).

**Decisión D68** (propuesta, borrador): indicadores de componentes, que reemplazan al subtipo único con prioridad; D78 fija cuáles se reportan.

## 5. Proveedores (D69, vigente con condiciones)

**Medida principal: HHI por departamento** (el mercado es local; `proveedores_hhi_departamento.csv`, `proveedores_hhi_departamento_anual.csv`, `proveedores_hhi_departamento_resumen_anual.csv`). El HHI nacional va solo como contexto. Participación y concentración por valor constante; el identificador es el NIT (SECOP I, personas jurídicas) o el código de proveedor (SECOP II). **Limitación: las personas naturales van seudonimizadas (D15) y no se unen entre SECOP I y II, así que un mismo proveedor puede contarse dos veces y la concentración puede estar subestimada.**

HHI por departamento y año (departamentos con 5 o más proveedores; mediana y cuartiles entre departamentos):

| año | departamentos | HHI_mediana | HHI_p25 | HHI_p75 | con HHI > 2.500 |
|---|---|---|---|---|---|
| 2020 | 28 | 1297 | 983 | 2222 | 4 |
| 2021 | 27 | 1495 | 903 | 2224 | 6 |
| 2022 | 27 | 1826 | 976 | 2195 | 4 |
| 2023 | 27 | 1716 | 1086 | 2368 | 5 |
| 2024 | 26 | 2034 | 960 | 2494 | 7 |
| 2025 | 28 | 1832 | 1037 | 3031 | 9 |

Pooled 2020–2025 (n = 32 departamentos con 5 o más proveedores): percentiles 10, 25, 50, 75 y 90 = 446, 755, 1,302, 1,766, 2,525; 4 de 32 superan 2.500. Los cinco proveedores de mayor valor suman el 22.4 % del valor total (`proveedores_top_participacion.csv`).

**Contexto: HHI y CR4 nacionales por año** (`proveedores_hhi_cr4_anual.csv`; gráfico `5_concentracion_proveedores.png`). El de 2025 se reporta después de corregir los dos contratos de D81; la sensibilidad sin los tres mayores contratos está más abajo:

| anio | proveedores | HHI | CR4 |
|---|---|---|---|
| 2020 | 604 | 240 | 24.1 |
| 2021 | 532 | 228 | 22.9 |
| 2022 | 477 | 292 | 25.2 |
| 2023 | 471 | 268 | 26.6 |
| 2024 | 425 | 417 | 33.9 |
| 2025 | 438 | 651 | 33.3 |

**Decisión D69** (vigente con condiciones): medida principal por departamento, HHI nacional como contexto, HHI de 2025 después de las correcciones de D81 y con la sensibilidad sin los tres mayores.

### Descomposición del HHI de 2025 (D77)

Los 10 mayores contratos funerarios de 2025 (`hhi_2025_top10_contratos.csv`; el proveedor solo se muestra si es persona jurídica):

| entidad | valor (mm corrientes) | % del valor de 2025 | proveedor | modalidad | prob. funerario TF-IDF | prob. funerario e5 |
|---|---|---|---|---|---|---|
| DIRECCION DE BIENESTAR DE LA POLICIA NACIONAL | 6.45 | 16.7 | COORDINADORA DE SERVICIOS DE PARQUE CEMENTERIO S.A.S. | Licitación pública | 0.85 | 0.98 |
| CENTRAL ADMINISTRATIVA Y CONTABLE CENAC PERSONAL | 1.95 | 5.2 | COORDINADORA DE SERVICIOS DE PARQUE CEMENTERIO S.A.S. | Selección Abreviada de Menor Cuantía | 1.00 | 1.00 |
| CENTRAL ADMINISTRATIVA Y CONTABLE CENAC PERSONAL | 1.79 | 4.6 | LA ASCENSION S.A. | Selección Abreviada de Menor Cuantía | 0.99 | 1.00 |
| ALCALDÍA DEL DISTRITO TURÍSTICO Y CULTURAL DE CARTAGENA DE INDIAS | 0.78 | 2.0 | NADAD Y CIA SAS | Selección Abreviada de Menor Cuantía | 0.90 | 1.00 |
| ALCALDIA MUNICIPAL DE VALLEDUPAR | 0.55 | 1.4 | ULTRAVIDA PREVISION EXEQUIAL S.A.S. | Selección abreviada subasta inversa | 0.93 | 0.97 |
| UNIDAD ADMINISTRATIVA ESPECIAL DE SERVICIOS PÚBLICOS. | 0.52 | 1.4 | INSTITUTO DISTRITAL PARA LA PROTECCIÓN DE LA NIÑEZ Y LA JUVENTUD - IDIPRON* | Contratación directa | 0.54 | 0.20 |
| ALCALDIA DISTRITAL DE BUENAVENTURA-VALLE | 0.52 | 1.4 | (persona natural: no se muestra) | Selección Abreviada de Menor Cuantía | 1.00 | 1.00 |
| DISTRITO ESPECIAL DE CIENCIA TECNOLOGIA E INNOVACION DE MEDELLIN | 0.49 | 1.3 | FUNERARIA SAN VICENTE S.A. | Selección abreviada subasta inversa | 1.00 | 1.00 |
| MUNICIPIO DE ARMENIA QUINDIO | 0.37 | 1.0 | FUNDACION PARQUE CEMENTERIO JARDINES DE ARMENIA | Contratación régimen especial (con ofertas) | 0.99 | 1.00 |
| MUNICIPIO DE BUCARAMANGA | 0.38 | 1.0 | (persona natural: no se muestra) | Selección abreviada subasta inversa | 0.99 | 0.98 |

HHI de 2025 quitando los mayores contratos (`hhi_2025_sin_mayores.csv`):

| sin los N mayores contratos | contratos | valor constante (mm) | proveedores | HHI | CR4 |
|---|---|---|---|---|---|
| 0 | 689 | 38.2 | 438 | 651 | 33.3 |
| 1 | 688 | 31.8 | 438 | 175 | 20.0 |
| 2 | 687 | 29.9 | 438 | 116 | 14.7 |
| 3 | 686 | 28.1 | 437 | 92 | 11.9 |
| 5 | 684 | 26.8 | 437 | 86 | 11.9 |
| 10 | 679 | 24.5 | 436 | 71 | 10.0 |

HHI según el modelo que define `funerario` (`proveedores_hhi_por_clasificacion.csv`):

| clasificacion | anio | proveedores | HHI | CR4 |
|---|---|---|---|---|
| TF-IDF | 2023 | 471 | 268 | 26.6 |
| TF-IDF | 2024 | 425 | 417 | 33.9 |
| TF-IDF | 2025 | 438 | 651 | 33.3 |
| e5 | 2023 | 478 | 267 | 26.3 |
| e5 | 2024 | 419 | 423 | 34.2 |
| e5 | 2025 | 426 | 686 | 34.2 |
| ambos modelos | 2023 | 448 | 296 | 28.0 |
| ambos modelos | 2024 | 400 | 452 | 35.5 |
| ambos modelos | 2025 | 407 | 733 | 35.5 |

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
