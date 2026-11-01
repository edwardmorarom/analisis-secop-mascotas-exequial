# Perfil de variables de los contratos `funerario` (SECOP I y II, 2020–2025)

Solo diagnóstico: no propone método, no corre modelos y no registra decisiones. Generado por `python -m src.modelos.perfil_variables`. Universo: contratos con clase final `funerario` (TF-IDF con la jerarquía de etiquetas, D84): **4.992** (3.659 de SECOP I y 1.333 de SECOP II).

Convenciones: «faltante» es nulo o vacío; «centinela» es un valor que nombra la ausencia («No Definido», «No aplica», «UNSPECIFIED», «Otro»). Las categorías raras tienen menos de 1 % de los contratos con dato de su fuente.

## 1. Inventario de columnas útiles para patrones

| concepto | SECOP I | SECOP II | equivalencia | nota |
|---|---|---|---|---|
| Entidad (nombre, NIT) | nombre_entidad, nit_de_la_entidad | nombre_entidad, nit_entidad | directa |  |
| Orden | orden_entidad (11 valores, con nivel municipal 1 a 6) | orden (2 valores) | parcial | SECOP II no trae la categoría municipal |
| Nivel o sector | nivel_entidad (territorial o nacional) | sector (18 valores) y rama (4) | parcial | SECOP I no tiene sector ni rama; SECOP II no tiene un nivel aparte de orden |
| Ubicación de la entidad | departamento_entidad, municipio_entidad | departamento, ciudad | directa | cruce con DIVIPOLA en D66 |
| Lugar de ejecución | municipios_ejecucion (texto) | localizaci_n y direcci_n_de_ejecuci_n_del_contrato (texto) | parcial | formatos distintos; la dirección de SECOP II es texto libre |
| Modalidad | modalidad_de_contratacion (6 valores) | modalidad_de_contratacion (10 valores) | parcial | vocabularios distintos; se agrupan con `modalidad_grupo` |
| Tipo de contrato | tipo_de_contrato (10 valores) | tipo_de_contrato (13 valores) | parcial | SECOP II separa seguros, servicios financieros y Decreto 092 |
| Estado | estado_del_proceso (filtrado a Celebrado, Liquidado y Terminado sin Liquidar) | estado_contrato (7 valores) | no comparable | la selección de SECOP I ya filtra por estado (CLAUDE.md) |
| Destino del gasto | destino_gasto | destino_gasto | directa | centinelas distintos («No aplica» frente a «No Definido») |
| Origen de los recursos | — | origen_de_los_recursos | sin equivalente en SECOP I |  |
| Valor inicial | cuantia_contrato | valor_del_contrato | directa | base de las series (D67) |
| Valor con adiciones | valor_contrato_con_adiciones, valor_total_de_adiciones | — | sin equivalente en SECOP II | SECOP II solo trae `dias_adicionados` |
| Valor facturado y pagado | — | valor_facturado, valor_pagado | sin equivalente en SECOP I |  |
| Fecha de firma | fecha_de_firma_del_contrato | fecha_de_firma | directa | año y estacionalidad |
| Fechas de inicio y fin | fecha_ini_ejec_contrato, fecha_fin_ejec_contrato | fecha_de_inicio_del_contrato, fecha_de_fin_del_contrato | directa |  |
| Duración | plazo_de_ejec_del_contrato (número sin unidad) | duraci_n_del_contrato (texto con unidad: Dia(s), Mes(es)) | parcial | la unidad de SECOP I no está en el conjunto descargado |
| Adición en tiempo | — | dias_adicionados | sin equivalente en SECOP I |  |
| Proveedor (identificador, tipo de documento) | identificacion_del_contratista, tipo_identifi_del_contratista | codigo_proveedor, tipodocproveedor | parcial | identificadores distintos (D15) |
| Tamaño de empresa | es_mipyme | es_pyme | parcial | SECOP I tiene «No definido»; SECOP II solo Si y No |
| Categoría UNSPSC | id_clase, id_familia, nombre_clase | codigo_de_categoria_principal (con prefijo V1.) | directa | ver CLAUDE.md |
| Número de oferentes | — | — | no existe en ninguno de los dos conjuntos | está en los conjuntos de procesos, que no se descargaron |

## 2. Calidad por variable y fuente

### 2a. Variables categóricas

| variable | fuente | % faltante | % centinela | categorías | categorías raras (< 1 %) | % de contratos en raras |
|---|---|---|---|---|---|---|
| entidad | secop1 | 0,0 | 0,0 | 789 | 789 | 100,0 |
| entidad | secop2 | 0,0 | 0,0 | 313 | 304 | 79,7 |
| nit_entidad | secop1 | 0,0 | 5,5 | 715 | 715 | 94,5 |
| nit_entidad | secop2 | 0,0 | 0,0 | 308 | 298 | 78,1 |
| orden | secop1 | 0,0 | 0,0 | 10 | 2 | 0,4 |
| orden | secop2 | 0,0 | 0,0 | 2 | 0 | 0,0 |
| nivel_o_sector | secop1 | 0,0 | 0,0 | 2 | 1 | 0,3 |
| nivel_o_sector | secop2 | 0,0 | 25,5 | 17 | 9 | 2,5 |
| rama | secop1 | no existe |  |  |  |  |
| rama | secop2 | 0,0 | 0,0 | 4 | 2 | 0,7 |
| departamento_entidad | secop1 | 0,0 | 0,0 | 32 | 7 | 4,4 |
| departamento_entidad | secop2 | 0,0 | 0,5 | 30 | 7 | 3,6 |
| municipio_entidad | secop1 | 0,0 | 0,0 | 680 | 680 | 100,0 |
| municipio_entidad | secop2 | 0,0 | 10,6 | 221 | 203 | 52,1 |
| lugar_ejecucion | secop1 | 0,0 | 0,0 | 680 | 680 | 100,0 |
| lugar_ejecucion | secop2 | 0,0 | 0,0 | 245 | 228 | 61,8 |
| modalidad | secop1 | 0,0 | 0,0 | 6 | 1 | 0,1 |
| modalidad | secop2 | 0,0 | 0,0 | 10 | 5 | 1,7 |
| tipo_contrato | secop1 | 0,0 | 0,0 | 10 | 6 | 0,6 |
| tipo_contrato | secop2 | 0,0 | 2,9 | 12 | 6 | 0,7 |
| estado | secop1 | 0,0 | 0,0 | 3 | 1 | 0,6 |
| estado | secop2 | 0,0 | 0,0 | 7 | 2 | 0,2 |
| destino_gasto | secop1 | 0,0 | 7,2 | 2 | 0 | 0,0 |
| destino_gasto | secop2 | 0,0 | 0,2 | 2 | 0 | 0,0 |
| origen_recursos | secop1 | no existe |  |  |  |  |
| origen_recursos | secop2 | 0,0 | 0,0 | 2 | 0 | 0,0 |
| es_pyme | secop1 | 0,0 | 71,7 | 2 | 0 | 0,0 |
| es_pyme | secop2 | 0,0 | 0,0 | 2 | 0 | 0,0 |
| tipo_doc_proveedor | secop1 | 0,0 | 0,0 | 6 | 3 | 0,2 |
| tipo_doc_proveedor | secop2 | 0,0 | 1,9 | 3 | 1 | 0,2 |
| categoria_unspsc | secop1 | 0,0 | 0,0 | 104 | 98 | 7,2 |
| categoria_unspsc | secop2 | 0,0 | 3,8 | 75 | 63 | 11,1 |

### 2b. Variables numéricas, fechas y duración

| variable | fuente | % faltante | % ≤ 0 | mínimo | mediana | máximo |
|---|---|---|---|---|---|---|
| valor_inicial | secop1 | 0,0 | 0,1 | 0 | 15.405.000 | 1.254.250.000 |
| valor_inicial | secop2 | 0,0 | 0,4 | 0 | 29.700.000 | 6.450.073.078 |
| valor_con_adiciones | secop1 | 0,0 | 0,1 | 0 | 16.310.000 | 1.597.000.000 |
| valor_con_adiciones | secop2 | no existe |  |  |  |  |
| valor_adiciones | secop1 | 0,0 | 91,3 | 0 | 0 | 342.750.000 |
| valor_adiciones | secop2 | no existe |  |  |  |  |
| valor_facturado | secop1 | no existe |  |  |  |  |
| valor_facturado | secop2 | 0,0 | 38,6 | 0 | 7.500.000 | 6.448.700.000 |
| valor_pagado | secop1 | no existe |  |  |  |  |
| valor_pagado | secop2 | 0,0 | 47,7 | 0 | 1.740.000 | 6.448.700.000 |
| dias_adicionados | secop1 | no existe |  |  |  |  |
| dias_adicionados | secop2 | 0,0 | 87,1 | 0 | 0 | 376 |
| fecha_firma | secop1 | 0,0 |  | 2020-01-01 | 2022-01-21 | 2025-12-30 |
| fecha_firma | secop2 | 0,0 |  | 2020-01-27 | 2023-12-04 | 2025-12-30 |
| fecha_inicio | secop1 | 0,0 |  | 2020-01-01 | 2022-01-21 | 2026-03-17 |
| fecha_inicio | secop2 | 1,3 |  | 2020-01-27 | 2023-12-05 | 2026-01-29 |
| fecha_fin | secop1 | 0,0 |  | 2020-02-01 | 2022-05-26 | 2050-10-15 |
| fecha_fin | secop2 | 0,0 |  | 2020-05-29 | 2024-03-29 | 2026-12-31 |
| duracion (días; SECOP I sin unidad) | secop1 | 0,0 | 0,1 | 0 | 10 | 850 |
| duracion (días; SECOP I sin unidad) | secop2 | 1,0 | 0,0 | 3 | 210 | 8.910 |

### 2c. Valores inconsistentes

Contratos (y porcentaje de la fuente) que violan cada regla; «no aplica» cuando la columna no existe en esa fuente.

| regla | SECOP I | SECOP II |
|---|---|---|
| fecha de fin anterior a la de inicio | 0 (0,0 %) | 0 (0,0 %) |
| fecha de inicio más de 30 días antes de la firma | 0 (0,0 %) | 0 (0,0 %) |
| fecha de inicio más de 365 días después de la firma | 2 (0,1 %) | 1 (0,1 %) |
| alguna fecha fuera de 2000–2035 | 3 (0,1 %) | 0 (0,0 %) |
| valor inicial ≤ 0 | 2 (0,1 %) | 5 (0,4 %) |
| valor con adiciones menor que el inicial | 0 (0,0 %) | no aplica |
| valor con adiciones distinto de inicial + adiciones | 0 (0,0 %) | no aplica |
| valor facturado mayor que el valor del contrato | no aplica | 0 (0,0 %) |
| valor pagado mayor que el facturado | no aplica | 0 (0,0 %) |
| días adicionados negativos | no aplica | 0 (0,0 %) |
| plazo de SECOP I frente a los días entre inicio y fin: razón 0,9–1,1 (días) / 25–35 (meses de 30 días) / otra | 1759 (48,1 %) / 1802 (49,2 %) / 98 (2,7 %) | no aplica |
| duración declarada de SECOP II coincide (±3 días) con los días entre inicio y fin | no aplica | 580 de 1320 (43,9 %) |

## 3. Homologación entre SECOP I y SECOP II

### Modalidad (agrupada con `modalidad_grupo`)

| fuente | modalidad | modalidad_grupo | contratos |
|---|---|---|---|
| secop1 | Contratación Directa (Ley 1150 de 2007) | contratacion_directa | 271 |
| secop1 | Contratación Mínima Cuantía | minima_cuantia | 3.139 |
| secop1 | Contratos y convenios con más de dos partes | otra | 5 |
| secop1 | Régimen Especial | regimen_especial | 111 |
| secop1 | Selección Abreviada de Menor Cuantía (Ley 1150 de 2007) | seleccion_abreviada | 66 |
| secop1 | Subasta | seleccion_abreviada | 67 |
| secop2 | Concurso de méritos abierto | licitacion_concurso | 3 |
| secop2 | Contratación Directa (con ofertas) | contratacion_directa | 3 |
| secop2 | Contratación directa | contratacion_directa | 249 |
| secop2 | Contratación régimen especial | regimen_especial | 40 |
| secop2 | Contratación régimen especial (con ofertas) | regimen_especial | 11 |
| secop2 | Licitación pública | licitacion_concurso | 4 |
| secop2 | Mínima cuantía | minima_cuantia | 881 |
| secop2 | Seleccion Abreviada Menor Cuantia Sin Manifestacion Interes | seleccion_abreviada | 1 |
| secop2 | Selección Abreviada de Menor Cuantía | seleccion_abreviada | 90 |
| secop2 | Selección abreviada subasta inversa | seleccion_abreviada | 51 |

### Tipo de contrato

| SECOP I | SECOP II |
|---|---|
| Prestación de Servicios | Prestación de servicios |
| Suministro | Suministros |
| Compraventa | Compraventa |
| Arrendamiento | Arrendamiento de inmuebles | Arrendamiento de muebles |
| Obra | Obra |
| Consultoría | Consultoría |
| Concesión | Concesión |
| Comodato | Comodato |
| Otro Tipo de Contrato | Otro |
| Acuerdo Marco | — |
| — | Seguros |
| — | Decreto 092 de 2017 |
| — | Servicios financieros |

Contratos en categorías sin equivalente en la otra fuente (las que aparecen con «—»): SECOP I 1,5 %, SECOP II 6,1 %. «Otro» y «Otro Tipo de Contrato» se tratan como correspondientes aunque no se sabe qué contienen.

### Destino del gasto

| SECOP I | SECOP II |
|---|---|
| Inversion | Inversión |
| Funcionamiento | Funcionamiento |
| No aplica | No Definido (no equivale) |

### Tipo de documento del proveedor

| SECOP I | SECOP II |
|---|---|
| Nit de Persona Jurídica | NIT (incluye personas naturales con NIT) |
| Nit de Persona Natural | NIT (no se distingue) |
| Cédula de Ciudadanía | Cédula de Ciudadanía |
| Nit de Extranjería | Cédula de Extranjería (aproximada) |
| Nuip | Otro |
| Carné Diplomático | Otro |

### Orden, nivel y sector

SECOP I: `nivel_entidad` (territorial o nacional) y `orden_entidad` (11 valores, con nivel municipal 1 a 6 y departamental centralizado o descentralizado). SECOP II: `orden` (territorial o nacional), `sector` (18 valores) y `rama` (4). Se pueden unir en territorial o nacional; la categoría municipal de SECOP I y el sector de SECOP II no tienen equivalente en la otra fuente.

### Qué se puede unir y con qué pérdida

- **Sin pérdida:** entidad (nombre, NIT), ubicación de la entidad, valor inicial, fechas de firma, inicio y fin, objeto, categoría UNSPSC.
- **Con pérdida:** modalidad (se agrupa y se pierden las variantes «con ofertas» y las precisiones de ley), tipo de contrato (SECOP II separa seguros, servicios financieros y Decreto 092; SECOP I no), orden (se pierde la categoría municipal), tipo de documento del proveedor (SECOP II junta personas naturales y jurídicas bajo NIT), tamaño de empresa («No definido» en SECOP I).
- **No se unen:** sector y rama (solo SECOP II), origen de los recursos (solo SECOP II), valor con adiciones (solo SECOP I), valor facturado y pagado y días adicionados (solo SECOP II), estado (SECOP I está filtrado por estado), lugar de ejecución (formatos distintos), número de oferentes (no existe en ninguno de los dos conjuntos).

## 4. Variables derivadas para validar

`docs/revision_f4/derivadas.xlsx` (no se versiona): 20 contratos al azar (semilla 2030) por cada variable derivada, en tres hojas (`tipo_entidad`, `modalidad_grupo` y `componentes`), con una columna `correcto` (sí o no) y otras para la corrección. El texto de los objetos va anonimizado.

Tipo de entidad derivado, por fuente (todos los contratos `funerario`):

| tipo_entidad | secop1 | secop2 |
|---|---|---|
| alcaldia_municipio | 3474 | 956 |
| educacion_universidad | 12 | 1 |
| gobernacion_departamento | 32 | 72 |
| otra_entidad | 57 | 171 |
| salud_hospital_ese | 61 | 24 |
| seguridad_justicia | 0 | 13 |
| servicios_publicos_empresa | 23 | 96 |

## 5. Exploración

### 5a. Distribución del valor (pesos constantes de 2025)

| grupo | contratos | media (millones) | asimetría | asimetría de ln(valor) | curtosis | p1 (millones) | p5 (millones) | p10 (millones) | p25 (millones) | p50 (millones) | p75 (millones) | p90 (millones) | p95 (millones) | p99 (millones) | máximo (millones) | % del valor en el 1 % mayor | % del valor en los 10 mayores |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| todos | 4.992 | 46,2 | 20,4 | -0,46 | 519 | 1,59 | 4,58 | 6,46 | 11,33 | 22,24 | 35,30 | 64,58 | 117,51 | 439,59 | 6.394 | 29,0 | 15,6 |
| secop1 | 3.659 | 26,3 | 21,4 | -0,46 | 746 | 1,80 | 4,47 | 6,06 | 10,69 | 20,31 | 33,81 | 38,90 | 56,24 | 154,94 | 1.807 | 11,9 | 6,4 |
| secop2 | 1.333 | 100,9 | 11,1 | -1,14 | 150 | 0,84 | 5,21 | 7,89 | 14,69 | 33,48 | 69,04 | 156,01 | 331,05 | 1.233,97 | 6.394 | 30,5 | 26,8 |

### 5b. V de Cramér entre pares de variables categóricas (con corrección de sesgo)

La V va de 0 (sin asociación) a 1. Se calcula sobre las variables homologadas para que no mida solo que las dos plataformas usen vocabularios distintos.

| variable | fuente | año | tipo de entidad | grupo de modalidad | tipo de contrato (homologado) | destino del gasto (homologado) | territorial o nacional | cuartil del valor | componente: inhumacion_cremacion | componente: traslado | componente: ataudes_bienes | componente: plan_exequial | componente: operacion_cementerio | componente: atencion_vulnerables_NN |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fuente |  | 0,33 | 0,36 | 0,24 | 0,28 | 0,16 | 0,20 | 0,30 | 0,11 | 0,01 | 0,22 | 0,01 | 0,12 | 0,16 |
| año | 0,33 |  | 0,04 | 0,08 | 0,02 | 0,32 | 0,02 | 0,10 | 0,02 | 0,06 | 0,03 | 0,02 | 0,05 | 0,10 |
| tipo de entidad | 0,36 | 0,04 |  | 0,38 | 0,12 | 0,13 | 0,29 | 0,14 | 0,11 | 0,10 | 0,21 | 0,34 | 0,26 | 0,56 |
| grupo de modalidad | 0,24 | 0,08 | 0,38 |  | 0,31 | 0,14 | 0,11 | 0,26 | 0,14 | 0,05 | 0,24 | 0,24 | 0,26 | 0,43 |
| tipo de contrato (homologado) | 0,28 | 0,02 | 0,12 | 0,31 |  | 0,06 | 0,04 | 0,08 | 0,35 | 0,03 | 0,62 | 0,14 | 0,43 | 0,23 |
| destino del gasto (homologado) | 0,16 | 0,32 | 0,13 | 0,14 | 0,06 |  | 0,06 | 0,07 | 0,03 | 0,01 | 0,07 | 0,03 | 0,06 | 0,14 |
| territorial o nacional | 0,20 | 0,02 | 0,29 | 0,11 | 0,04 | 0,06 |  | 0,04 | 0,00 | 0,03 | 0,06 | 0,07 | 0,03 | 0,17 |
| cuartil del valor | 0,30 | 0,10 | 0,14 | 0,26 | 0,08 | 0,07 | 0,04 |  | 0,13 | 0,01 | 0,12 | 0,13 | 0,04 | 0,08 |
| componente: inhumacion_cremacion | 0,11 | 0,02 | 0,11 | 0,14 | 0,35 | 0,03 | 0,00 | 0,13 |  | 0,03 | 0,35 | 0,28 | 0,00 | 0,06 |
| componente: traslado | 0,01 | 0,06 | 0,10 | 0,05 | 0,03 | 0,01 | 0,03 | 0,01 | 0,03 |  | 0,03 | 0,00 | 0,02 | 0,07 |
| componente: ataudes_bienes | 0,22 | 0,03 | 0,21 | 0,24 | 0,62 | 0,07 | 0,06 | 0,12 | 0,35 | 0,03 |  | 0,13 | 0,06 | 0,22 |
| componente: plan_exequial | 0,01 | 0,02 | 0,34 | 0,24 | 0,14 | 0,03 | 0,07 | 0,13 | 0,28 | 0,00 | 0,13 |  | 0,03 | 0,20 |
| componente: operacion_cementerio | 0,12 | 0,05 | 0,26 | 0,26 | 0,43 | 0,06 | 0,03 | 0,04 | 0,00 | 0,02 | 0,06 | 0,03 |  | 0,13 |
| componente: atencion_vulnerables_NN | 0,16 | 0,10 | 0,56 | 0,43 | 0,23 | 0,14 | 0,17 | 0,08 | 0,06 | 0,07 | 0,22 | 0,20 | 0,13 |  |

### 5c. V de Cramér de cada variable con la fuente

Las filas con «(texto original)» comparan las categorías tal como vienen: si el vocabulario de las dos plataformas no coincide, la V sube por construcción (la última columna indica qué parte de los contratos está en categorías presentes en las dos fuentes). Las variables homologadas y derivadas separan mejor la forma de comprar de la plataforma. Se reporta también por período porque SECOP I domina 2020–2022.

| variable | V con la fuente (todos) | V con la fuente (2020–2022) | V con la fuente (2023–2025) | % de contratos en categorías presentes en ambas fuentes |
|---|---|---|---|---|
| año | 0,33 | 0,20 | 0,16 | 100,0 |
| tipo de entidad | 0,36 | 0,38 | 0,37 | 99,7 |
| grupo de modalidad | 0,24 | 0,25 | 0,34 | 99,8 |
| tipo de contrato (homologado) | 0,28 | 0,25 | 0,31 | 100,0 |
| destino del gasto (homologado) | 0,16 | 0,15 | 0,05 | 100,0 |
| territorial o nacional | 0,20 | 0,22 | 0,19 | 100,0 |
| cuartil del valor | 0,30 | 0,35 | 0,20 | 100,0 |
| componente: inhumacion_cremacion | 0,11 | 0,10 | 0,12 | 100,0 |
| componente: traslado | 0,01 | 0,00 | 0,00 | 100,0 |
| componente: ataudes_bienes | 0,22 | 0,19 | 0,26 | 100,0 |
| componente: plan_exequial | 0,01 | 0,00 | 0,05 | 100,0 |
| componente: operacion_cementerio | 0,12 | 0,09 | 0,14 | 100,0 |
| componente: atencion_vulnerables_NN | 0,16 | 0,12 | 0,27 | 100,0 |
| modalidad (texto original) | 1,00 | 1,00 | 1,00 | 0,0 |
| tipo de contrato (texto original) | 0,99 | 0,99 | 0,98 | 6,2 |
| orden (texto original) | 1,00 | 1,00 | 1,00 | 0,0 |
| destino del gasto (texto original) | 0,77 | 0,76 | 0,77 | 43,9 |
