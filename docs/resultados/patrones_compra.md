# Patrones de compra de los contratos funerarios (SECOP I y II, 2020–2025)

Descripción de lo que muestran los datos; no se sacan conclusiones de negocio. Método, modelos candidatos, supuestos y regla de decisión: **D97**, registrada y versionada antes de correr los modelos. Universo: los **4.992** contratos `funerario` (D84). Generado por `python -m src.modelos.patrones_informe`; los modelos están en `src/modelos/patrones_*.py` y `patrones_*.R`. Las cifras monetarias son pesos constantes de 2025.

**Regla (D97):** gana el menor BIC; con ΔBIC < 2 gana el más simple; ΔBIC > 10 es evidencia fuerte (Kass y Raftery 1995); un modelo que falle los supuestos no se elige aunque tenga el menor BIC; si todos fallan, no se elige ninguno y el de menor BIC se reporta solo como descripción.

## Resumen

| pregunta | candidatos | candidatos que pasan los supuestos | modelo elegido según la regla | menor BIC (descriptivo) |
|---|---|---|---|---|
| 1. Tipología (clases latentes) | 18 (3 modelos × 2 a 7 clases) | 0 de 18 | ninguno | fuente y año, 7 clases (BIC 52.179,0) |
| 2. Valor del contrato | 3 | 0 de 3 | ninguno | 3 gamma log mixto (entidad) |
| 3. Estacionalidad mensual | 3 | 0 de 3 | ninguno | 3 binomial negativa (armónicos y tendencia) |

En las tres preguntas la regla de D97 no elige ningún modelo, porque todos los candidatos fallan al menos un supuesto fijado de antemano. Las secciones siguientes reportan, para cada pregunta, la comparación completa, los supuestos que falla cada modelo y, solo como descripción, el modelo de menor BIC.

## 1. Tipología (clases latentes)

Variables: tipo de entidad (categorías con menos de 1 % agrupadas), grupo de modalidad, tipo de contrato homologado, territorial o nacional, cuartil del valor y seis componentes. Semilla 2033, 20 arranques por modelo y número de clases, EM propio (n = 4.992). Los modelos 2 y 3 usan la fuente (y el año) como covariables de la pertenencia a la clase.

### 1.1 Comparación de los 18 modelos

| covariables | clases | parámetros | logLik | BIC | ΔBIC | AIC | entropía relativa | arranques con el máximo (de 20) | clase más pequeña (%) | BVR máximo | pares con BVR > 10 | Jaccard mínimo (bootstrap) | supuestos que falla |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sin covariables | 2 | 49 | -28.189 | 56.795,7 | 4.616,7 | 56.476,4 | 0,79 | 19 | 43,1 | 535,2 | 28 | no evaluado | independencia local |
| sin covariables | 3 | 74 | -26.893 | 54.416,8 | 2.237,8 | 53.934,7 | 0,84 | 9 | 10,9 | 250,9 | 14 | no evaluado | independencia local |
| sin covariables | 4 | 99 | -26.470 | 53.783,1 | 1.604,1 | 53.138,0 | 0,84 | 13 | 7,5 | 247,3 | 13 | no evaluado | independencia local |
| sin covariables | 5 | 124 | -26.180 | 53.416,2 | 1.237,2 | 52.608,3 | 0,85 | 1 | 5,0 | 156,8 | 5 | no evaluado | independencia local, identificabilidad |
| sin covariables | 6 | 149 | -25.930 | 53.129,4 | 950,4 | 52.158,5 | 0,87 | 1 | 3,7 | 50,5 | 4 | 0,76 | independencia local, identificabilidad |
| sin covariables | 7 | 174 | -25.829 | 53.138,9 | 959,9 | 52.005,2 | 0,86 | 1 | 2,2 | 38,5 | 3 | no evaluado | independencia local, identificabilidad |
| fuente | 2 | 50 | -27.953 | 56.332,5 | 4.153,6 | 56.006,8 | 0,79 | 20 | 41,8 | 527,7 | 28 | no evaluado | independencia local |
| fuente | 3 | 76 | -26.585 | 53.816,3 | 1.637,3 | 53.321,1 | 0,84 | 1 | 11,5 | 262,9 | 14 | no evaluado | independencia local, identificabilidad |
| fuente | 4 | 102 | -26.071 | 53.010,9 | 831,9 | 52.346,3 | 0,84 | 16 | 10,0 | 258,6 | 13 | no evaluado | independencia local |
| fuente | 5 | 128 | -25.764 | 52.617,4 | 438,4 | 51.783,4 | 0,85 | 3 | 4,6 | 147,7 | 6 | no evaluado | independencia local |
| fuente | 6 | 154 | -25.532 | 52.375,5 | 196,6 | 51.372,1 | 0,87 | 3 | 3,5 | 52,5 | 4 | no evaluado | independencia local |
| fuente | 7 | 180 | -25.337 | 52.206,9 | 27,9 | 51.034,1 | 0,86 | 4 | 3,4 | 45,7 | 6 | 0,58 | independencia local, estabilidad |
| fuente y año | 2 | 55 | -27.939 | 56.345,9 | 4.166,9 | 55.987,5 | 0,78 | 7 | 42,0 | 527,6 | 28 | no evaluado | independencia local |
| fuente y año | 3 | 86 | -26.533 | 53.797,9 | 1.618,9 | 53.237,5 | 0,84 | 5 | 12,0 | 269,1 | 14 | no evaluado | independencia local |
| fuente y año | 4 | 117 | -26.027 | 53.051,3 | 872,3 | 52.289,0 | 0,84 | 13 | 10,1 | 263,1 | 13 | no evaluado | independencia local |
| fuente y año | 5 | 148 | -25.689 | 52.639,3 | 460,3 | 51.674,9 | 0,84 | 3 | 6,8 | 174,0 | 7 | no evaluado | independencia local |
| fuente y año | 6 | 179 | -25.435 | 52.394,8 | 215,9 | 51.228,6 | 0,87 | 1 | 3,9 | 156,9 | 8 | no evaluado | independencia local, identificabilidad |
| fuente y año | 7 | 210 | -25.195 | 52.179,0 | 0,0 | 50.810,7 | 0,86 | 1 | 3,6 | 36,5 | 5 | 0,70 | independencia local, identificabilidad |

- **ΔBIC entre modelos de igual número de clases (7):** sin covariables 959,9, fuente 27,9, fuente y año 0,0 (frente al menor BIC global).
- El BIC sigue bajando hasta 7 clases en los modelos 2 y 3, que es el límite superior del rango fijado en D97; en el modelo 1 el mínimo está en 6 clases (BIC 53.129,4) y 7 clases queda 9,6 por encima.
- **Independencia local:** el BVR máximo va de 36,5 a 535,2 y ningún modelo queda por debajo del umbral de 10; los 18 fallan este supuesto (el menor BVR máximo es el del modelo de fuente y año con 7 clases).
- **Identificabilidad:** 12 de 18 modelos repiten su mejor log-verosimilitud en al menos 3 de los 20 arranques; el de menor BIC la alcanza en 1 de 20, de modo que no se puede descartar un máximo local mejor.
- **Tamaño de clase:** ninguna clase baja de 1 % de los contratos (la más pequeña es 2,2 %).

### 1.2 Aplicación de la regla

Pasan todos los supuestos 0 de 18 candidatos; **no se elige ninguna tipología**. Por tanto, lo que sigue describe la de menor BIC (fuente y año, 7 clases) sin proponerla como elegida. Su BIC es 27,9 puntos menor que el del siguiente (fuente, 7 clases) y 196,6 o más que el de los demás: ΔBIC > 10 en todos los casos, evidencia fuerte de mejor ajuste, pero con supuestos incumplidos.
Como ningún candidato pasa los supuestos que no requieren bootstrap, la regla de D97 no obliga a correrlo; se corrió, de forma descriptiva y con los 200 remuestreos fijados, para el modelo de menor BIC de cada familia (fuente y año con 7 clases, fuente con 7 y sin covariables con 6); el resto figura como «no evaluado». Un Jaccard mínimo inferior a 0,60 (como el del modelo de fuente con 7 clases) añade el supuesto de estabilidad a los incumplidos.

### 1.3 Tipología de menor BIC (descriptiva): fuente y año, 7 clases

| clase | contratos | % | probabilidad posterior media | Jaccard medio (bootstrap) |
|---|---|---|---|---|
| 1 | 241 | 4,8 | 0,96 | 0,85 |
| 2 | 1.691 | 33,9 | 0,90 | 0,91 |
| 3 | 425 | 8,5 | 0,95 | 0,79 |
| 4 | 1.540 | 30,8 | 0,93 | 0,96 |
| 5 | 199 | 4,0 | 0,94 | 0,70 |
| 6 | 182 | 3,6 | 0,91 | 0,74 |
| 7 | 714 | 14,3 | 0,81 | 0,80 |

| clase | categorías con probabilidad > 0,5 dentro de la clase |
|---|---|
| 1 | operacion_cementerio=0 (1,00); atencion_vulnerables_NN=0 (0,99); ataudes_bienes=0 (0,99); traslado=0 (0,96); orden_nivel=TERRITORIAL (0,91); tipo_contrato_hom=prestacion_servicios (0,76); inhumacion_cremacion=0 (0,68); modalidad_grupo=regimen_especial (0,60); cuartil_valor=Q1 (0,58); plan_exequial=1 (0,54) |
| 2 | operacion_cementerio=0 (1,00); modalidad_grupo=minima_cuantia (1,00); orden_nivel=TERRITORIAL (1,00); tipo_entidad=alcaldia_municipio (0,99); plan_exequial=0 (0,98); traslado=0 (0,95); ataudes_bienes=0 (0,93); inhumacion_cremacion=1 (0,91); atencion_vulnerables_NN=1 (0,90); tipo_contrato_hom=prestacion_servicios (0,79) |
| 3 | orden_nivel=TERRITORIAL (1,00); plan_exequial=0 (0,99); tipo_entidad=alcaldia_municipio (0,94); operacion_cementerio=0 (0,93); ataudes_bienes=0 (0,92); traslado=0 (0,87); tipo_contrato_hom=prestacion_servicios (0,83); modalidad_grupo=contratacion_directa (0,77); inhumacion_cremacion=1 (0,71); atencion_vulnerables_NN=1 (0,66) |
| 4 | operacion_cementerio=0 (1,00); modalidad_grupo=minima_cuantia (1,00); orden_nivel=TERRITORIAL (0,99); tipo_entidad=alcaldia_municipio (0,99); plan_exequial=0 (0,97); traslado=0 (0,94); atencion_vulnerables_NN=1 (0,93); ataudes_bienes=1 (0,91); tipo_contrato_hom=suministro (0,78); inhumacion_cremacion=0 (0,70) |
| 5 | traslado=0 (1,00); ataudes_bienes=0 (0,98); plan_exequial=0 (0,95); atencion_vulnerables_NN=0 (0,87); operacion_cementerio=0 (0,86); tipo_contrato_hom=prestacion_servicios (0,86); inhumacion_cremacion=1 (0,81); orden_nivel=TERRITORIAL (0,78); cuartil_valor=Q4 (0,66); modalidad_grupo=contratacion_directa (0,53) |
| 6 | operacion_cementerio=0 (1,00); modalidad_grupo=minima_cuantia (1,00); ataudes_bienes=0 (0,97); traslado=0 (0,97); inhumacion_cremacion=0 (0,97); orden_nivel=TERRITORIAL (0,95); tipo_entidad=alcaldia_municipio (0,92); plan_exequial=1 (0,82); atencion_vulnerables_NN=1 (0,74); tipo_contrato_hom=prestacion_servicios (0,59) |
| 7 | operacion_cementerio=0 (1,00); cuartil_valor=Q4 (1,00); orden_nivel=TERRITORIAL (0,98); plan_exequial=0 (0,97); atencion_vulnerables_NN=1 (0,95); traslado=0 (0,93); tipo_entidad=alcaldia_municipio (0,91); inhumacion_cremacion=1 (0,83); ataudes_bienes=0 (0,79); tipo_contrato_hom=prestacion_servicios (0,67); modalidad_grupo=minima_cuantia (0,59) |

**Residuos bivariados más altos (BVR):**

| variable 1 | variable 2 | BVR |
|---|---|---|
| traslado | atencion_vulnerables_NN | 36,5 |
| inhumacion_cremacion | plan_exequial | 26,4 |
| tipo_contrato_hom | operacion_cementerio | 23,6 |
| tipo_entidad | traslado | 10,7 |
| tipo_entidad | plan_exequial | 10,3 |
| tipo_entidad | orden_nivel | 9,9 |
| tipo_entidad | modalidad_grupo | 8,9 |
| traslado | plan_exequial | 8,7 |

**Estabilidad por bootstrap (200 remuestreos, 5 arranques cada uno):** Jaccard medio por clase 0,85, 0,91, 0,79, 0,96, 0,70, 0,74, 0,80; mínimo 0,70 (umbral de D97: 0,60); índice de Rand ajustado entre cada remuestreo y la solución original, media 0,89 y percentil 5 0,78.

**ACM + HCPC (descriptiva).** Las dos primeras dimensiones de la ACM retienen 11,2 % y 8,3 % de la inercia (37,9 % las cinco primeras). HCPC con 7 grupos (tamaños 1602, 2485, 377, 234, 154, 34, 106) frente a la tipología de menor BIC: **índice de Rand ajustado 0,52**. Como no hay tipología elegida, la comparación es con la de menor BIC.

| clase LCA \ grupo HCPC | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| 1 | 0 | 4 | 2 | 112 | 24 | 6 | 93 |
| 2 | 9 | 1565 | 111 | 6 | 0 | 0 | 0 |
| 3 | 12 | 300 | 58 | 2 | 40 | 11 | 2 |
| 4 | 1435 | 7 | 98 | 0 | 0 | 0 | 0 |
| 5 | 0 | 9 | 28 | 62 | 89 | 11 | 0 |
| 6 | 62 | 84 | 4 | 31 | 0 | 1 | 0 |
| 7 | 84 | 516 | 76 | 21 | 1 | 5 | 11 |

Gráficos y tablas completas (perfiles por clase, BVR, bootstrap) en `data/processed/resultados_secop/patrones/` (no se versiona).

## 2. Valor del contrato

Variable: log del valor constante de 2025 (n = 4985; 7 contratos con valor no positivo o nulo, excluidos). Explicativas: tipo de entidad, grupo de modalidad, seis componentes, año y fuente. Entidad = NIT (o nombre si falta): 912 entidades. BIC calculado en la escala del valor (log-verosimilitud de los modelos 1 y 2 menos Σ log valor).

### 2.1 Comparación

| modelo | parámetros | logLik en escala del valor | BIC | AIC | ΔBIC | supuestos que falla |
|---|---|---|---|---|---|---|
| 1 lineal | 23 | -90.702,5 | 181.600,8 | 181.450,9 | 3.282,9 | normalidad |
| 2 lineal mixto (entidad) | 24 | -89.827,3 | 179.859,0 | 179.702,7 | 1.541,2 | normalidad |
| 3 gamma log mixto (entidad) | 24 | -89.056,7 | 178.317,8 | 178.161,5 | 0,0 | normalidad |

- ΔBIC: el gamma log mixto queda 1.541 puntos por debajo del siguiente (el lineal mixto) y 3.283 del lineal: evidencia fuerte de mejor ajuste en la escala del valor.
- **ICC:** 0,58 sin covariables y 0,52 con ellas (modelo lineal mixto); en el gamma, 0,75 en la escala latente; la dispersión gamma estimada es 0,37.

### 2.2 Diagnósticos (umbrales de D97)

| modelo | asimetría | exceso de curtosis | Spearman (valor absoluto del residuo y ajustado) | Cook máximo | GVIF^(1/2gl) máximo |
|---|---|---|---|---|---|
| 1 lineal | -2,06 | 36,83 | 0,01 | 0,60 | 1,25 |
| 2 lineal mixto (entidad) | -5,17 | 144,98 | -0,07 |  | 1,13 |
| 3 gamma log mixto (entidad) | -0,66 | 5,57 | 0,10 |  | 1,13 |

Todos los modelos fallan el supuesto de normalidad (asimetría con |valor| > 1 o exceso de curtosis > 3); el gamma es el que menos se aleja (asimetría -0,66, exceso de curtosis 5,57). Varianza no constante, influencia (Cook máximo del modelo 1: 0,60; 297 contratos con Cook > 4/n) y colinealidad no fallan. Gráficos: `graficos/patrones/valor_qq_y_residuos.png` y `graficos/patrones/valor_cook_y_efectos_aleatorios.png`.

### 2.3 Validación cruzada de 5 pliegues agrupada por entidad

| modelo | contratos en prueba | RMSE (log) | MAE (log) |
|---|---|---|---|
| 1 lineal | 4.985 | 0,947 | 0,699 |
| 2 lineal mixto (entidad) | 4.985 | 0,971 | 0,723 |
| 3 gamma log mixto (entidad) | 4.985 | 1,004 | 0,759 |

Predicción de población (sin efecto aleatorio) para entidades fuera del pliegue; en el gamma, la esperanza del logaritmo de una gamma. El error más bajo en escala log es el del modelo lineal, aunque su BIC en la escala del valor sea el peor.

### 2.4 Efectos más fuertes del modelo lineal mixto (descriptivo, escala log)

| término | estimador (log) | razón multiplicativa | t |
|---|---|---|---|
| modalidad_gruposeleccion_abreviada | 1,187 | 3,28 | 21,7 |
| tipo_entidadgobernacion_departamento | 0,916 | 2,50 | 6,8 |
| modalidad_grupootras | 1,568 | 4,80 | 6,5 |
| operacion_cementerio | -0,560 | 0,57 | -5,6 |
| fuentesecop2 | 0,238 | 1,27 | 5,4 |
| inhumacion_cremacion | 0,148 | 1,16 | 4,9 |
| modalidad_gruporegimen_especial | 0,267 | 1,31 | 2,1 |
| atencion_vulnerables_NN | 0,077 | 1,08 | 2,0 |

Referencias: tipo de entidad alcaldía y municipio; modalidad mínima cuantía; año 2020; fuente SECOP I. No hay modelo elegido por la regla; estos coeficientes describen el lineal mixto, que tampoco cumple los supuestos de normalidad.

## 3. Estacionalidad mensual

Conteos mensuales por fecha de firma, enero de 2020 a diciembre de 2025 (72 meses, 4992 contratos, ningún mes con cero).

### 3.1 Comparación

| modelo | parámetros | logLik | BIC | AIC | ΔBIC | supuestos que falla |
|---|---|---|---|---|---|---|
| 1 Poisson (mes y año) | 17 | -334,4 | 741,5 | 702,8 | 117,6 | sobredispersión, autocorrelación (Ljung-Box 12) |
| 2 binomial negativa (mes y año) | 18 | -289,7 | 656,4 | 615,4 | 32,5 | autocorrelación (Ljung-Box 12) |
| 3 binomial negativa (armónicos y tendencia) | 7 | -297,0 | 624,0 | 608,0 | 0,0 | autocorrelación (Ljung-Box 12) |

- Cameron y Trivedi sobre el Poisson: α = 0,035 (error estándar 0,008, p = 0,00002): hay sobredispersión. χ² de Pearson sobre grados de libertad del Poisson: 4,39.
- La dispersión de la binomial negativa es θ = 29,9 (modelo 2) y 23,1 (modelo 3).
- El modelo 3 tiene 7 parámetros frente a 18 del modelo 2: ΔBIC de 32,5 entre ambos y 117,6 con el Poisson.

### 3.2 Diagnósticos

| modelo | Ljung-Box 6 (p) | Ljung-Box 12 (p) | asimetría RQ | exceso de curtosis RQ | media RQ | desv. est. RQ | χ² de Pearson / gl |
|---|---|---|---|---|---|---|---|
| 1 Poisson (mes y año) | 0,002 | 0,003 | -0,02 | 0,27 | -0,06 | 1,84 | 4,39 |
| 2 binomial negativa (mes y año) | 0,019 | 0,020 | -0,09 | 0,16 | 0,00 | 0,99 | 1,26 |
| 3 binomial negativa (armónicos y tendencia) | 0,011 | 0,037 | -0,11 | -0,77 | -0,00 | 1,01 | 1,06 |

Los tres modelos fallan la autocorrelación (Ljung-Box a 12 rezagos con p < 0,05); el Poisson también falla la sobredispersión. Los residuos cuantílicos de los tres cumplen el umbral de normalidad. Gráficos: `graficos/patrones/estacionalidad_serie_y_diagnosticos.png`.

### 3.3 Perfil mensual

| mes | promedio de contratos por mes | razón vs enero (modelo 2) |
|---|---|---|
| 1 | 60,7 | 1,00 (referencia) |
| 2 | 121,3 | 2,03 |
| 3 | 132,7 | 2,20 |
| 4 | 104,3 | 1,71 |
| 5 | 85,5 | 1,40 |
| 6 | 66,3 | 1,06 |
| 7 | 55,5 | 0,90 |
| 8 | 44,3 | 0,69 |
| 9 | 43,7 | 0,70 |
| 10 | 41,0 | 0,65 |
| 11 | 36,8 | 0,60 |
| 12 | 39,8 | 0,65 |

Promedio de contratos por mes calendario sobre los seis años, y razón de tasas de cada mes frente a enero según el modelo 2 (con año).

### 3.4 Efecto de 2020 (reportado aparte)

| modelo | año | razón vs 2025 | p |
|---|---|---|---|
| 1 Poisson | 2020 | 1,55 | 0,000 |
| 1 Poisson | 2021 | 1,41 | 0,000 |
| 1 Poisson | 2022 | 1,17 | 0,002 |
| 1 Poisson | 2023 | 1,11 | 0,046 |
| 1 Poisson | 2024 | 1,00 | 0,979 |
| 2 binomial negativa | 2020 | 1,70 | 0,000 |
| 2 binomial negativa | 2021 | 1,42 | 0,000 |
| 2 binomial negativa | 2022 | 1,15 | 0,137 |
| 2 binomial negativa | 2023 | 1,08 | 0,403 |
| 2 binomial negativa | 2024 | 1,02 | 0,850 |

Con 2025 como referencia, la razón de tasas de 2020 es 1,55 en el Poisson y 1,70 en la binomial negativa; el año 2024 no se distingue de 2025.

Sensibilidad del modelo 3 (armónicos y tendencia): con y sin 2020, y con una indicadora de 2020. Los BIC de estas filas no son comparables entre sí (distinto n o distintas variables).

| modelo | meses | tendencia por mes (log) | p de la tendencia | amplitud 12 meses | amplitud 6 meses | razón de 2020 | p de 2020 | BIC (no comparable entre filas) | parámetros |
|---|---|---|---|---|---|---|---|---|---|
| 3 con 2020 (72 meses) | 72 | -0,0089 | 0,0000 | 0,56 | 0,19 |  |  | 624,0 | 7 |
| 3 sin 2020 (60 meses) | 60 | -0,0070 | 0,0000 | 0,64 | 0,20 |  |  | 499,1 | 7 |
| 3 con indicadora de 2020 (72 meses) | 72 | -0,0070 | 0,0002 | 0,57 | 0,19 | 1,17 | 0,105 | 625,6 | 8 |

## 4. Limitaciones

- **Ningún modelo cumple los supuestos fijados en D97 en ninguna de las tres preguntas**, de modo que la regla no elige modelo; los resultados del modelo de menor BIC son descriptivos.
- **Clases latentes:** (a) el BVR de todos los modelos supera el umbral de independencia local de 10, es decir, hay dependencia entre variables que las clases no explican, sobre todo entre componentes; (b) el modelo de menor BIC alcanza su mejor log-verosimilitud en 1 de 20 arranques, así que puede no ser el máximo global; (c) el BIC sigue bajando en el límite del rango (7 clases) en los modelos con covariables; (d) los EM son propios (no hay `poLCA` ni `stepmix` instalados); el cálculo de parámetros y del BIC es el estándar, pero no se contrastó con otro programa; (e) el bootstrap empareja clases con asignación óptima y mide estabilidad en todos los contratos, no solo en los remuestreados.
- **Valor:** la distribución del residuo tiene colas más pesadas que la normal en los tres modelos (incluido el gamma, residuos cuantílicos con exceso de curtosis de 5,6); el gamma mixto de `lme4` estima la dispersión de forma aproximada (Laplace); el BIC en la escala del valor penaliza igual a los tres modelos por parámetro, sin contar el efecto aleatorio por entidad como parámetros individuales; la validación cruzada usa predicción de población y no premia el efecto aleatorio; Cook no está disponible para los modelos mixtos; una entidad con pocos contratos tiene un efecto aleatorio poco determinado.
- **Estacionalidad:** 72 meses; el Ljung-Box a 12 rezagos tiene poca potencia con ese tamaño y no se ajustó por los grados de libertad de cada modelo; los p de 0,02 a 0,04 de los modelos 2 y 3 son cercanos al umbral de 0,05; 2020 está atravesado por la pandemia y reportado aparte; el modelo 3 asume una tendencia lineal.
- **General:** los umbrales de «falla» son convencionales y se fijaron antes de ver los datos; con n = 4.992 el BIC favorece estructuras sencillas; la ubicación de las entidades es la sede, no el lugar de ejecución; el universo es el de los contratos clasificados `funerario` por TF-IDF (D84), con sus errores de clasificación (D93).
