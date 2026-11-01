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
| fuente y año | 5 | 148 | -25.689 | 52.639,3 | 460,3 | 51.674,9 | 0,84 | 2 | 6,8 | 173,9 | 7 | no evaluado | independencia local, identificabilidad |
| fuente y año | 6 | 179 | -25.435 | 52.394,8 | 215,9 | 51.228,5 | 0,87 | 1 | 3,9 | 156,9 | 8 | no evaluado | independencia local, identificabilidad |
| fuente y año | 7 | 210 | -25.195 | 52.179,0 | 0,0 | 50.810,7 | 0,86 | 1 | 3,6 | 36,5 | 5 | 0,70 | independencia local, identificabilidad |

- **ΔBIC entre modelos de igual número de clases (7):** sin covariables 959,9, fuente 27,9, fuente y año 0,0 (frente al menor BIC global).
- El BIC sigue bajando hasta 7 clases en los modelos 2 y 3, que es el límite superior del rango fijado en D97; en el modelo 1 el mínimo está en 6 clases (BIC 53.129,4) y 7 clases queda 9,6 por encima.
- **Independencia local:** el BVR máximo va de 36,5 a 535,2 y ningún modelo queda por debajo del umbral de 10; los 18 fallan este supuesto (el menor BVR máximo es el del modelo de fuente y año con 7 clases).
- **Identificabilidad:** 11 de 18 modelos repiten su mejor log-verosimilitud en al menos 3 de los 20 arranques; el de menor BIC la alcanza en 1 de 20, de modo que no se puede descartar un máximo local mejor.
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

## Análisis exploratorio (D98)

**Esta sección es exploratoria.** D98 se decidió después de ver los resultados de D97 (ningún modelo cumplió los supuestos en ninguna pregunta); los umbrales y modelos de D97 no se tocaron y sus resultados siguen arriba. Los hallazgos de esta sección deben confirmarse antes de apoyar una conclusión. Descripción de los datos, sin conclusiones de negocio.

### 1. Valor: regresión por cuantiles frente a los modelos de D97

Modelo principal: regresión por cuantiles en la **mediana** del log del valor constante de 2025, con las explicativas de D97 y bootstrap agrupado por entidad (500 remuestreos, semilla 2034, 912 entidades). Sensibilidad: el lineal mixto de D97 con errores robustos agrupados por entidad (CR1) y el gamma log mixto de D97. Los coeficientes de la mediana y del lineal mixto están en escala log del valor; los del gamma, en escala log de la media, y son comparables en signo y significancia, no en magnitud. Referencias: alcaldía y municipio; mínima cuantía; 2020; SECOP I.

| término | mediana (IC 95 % bootstrap por entidad) | lineal mixto, errores robustos (IC 95 %) | gamma log mixto (IC 95 % de Wald) | significativo (mediana / lineal / gamma) | cambia de signo | cambia de significancia |
|---|---|---|---|---|---|---|
| tipo_entidadgobernacion_departamento | 0,663 (0,238 a 1,013) | 0,916 (0,672 a 1,159) | 0,872 (0,633 a 1,111) | sí / sí / sí | no | no |
| tipo_entidadotra_entidad | 0,142 (-0,508 a 0,735) | -0,090 (-0,506 a 0,325) | -0,227 (-0,430 a -0,023) | no / no / sí | sí | sí |
| tipo_entidadotras | 0,782 (-0,535 a 3,679) | 0,303 (-0,875 a 1,480) | 0,273 (-0,190 a 0,737) | no / no / no | no | no |
| tipo_entidadsalud_hospital_ese | 0,234 (-0,406 a 1,492) | -0,265 (-0,820 a 0,290) | -0,314 (-0,603 a -0,026) | no / no / sí | sí | sí |
| tipo_entidadservicios_publicos_empresa | 0,370 (-1,022 a 1,689) | -0,220 (-1,056 a 0,616) | -0,446 (-0,847 a -0,045) | no / no / sí | sí | sí |
| modalidad_grupocontratacion_directa | -0,086 (-0,509 a 0,253) | 0,034 (-0,249 a 0,317) | 0,137 (0,056 a 0,219) | no / no / sí | sí | sí |
| modalidad_grupootras | 2,079 (-1,656 a 4,910) | 1,568 (0,618 a 2,518) | 1,613 (1,171 a 2,054) | no / sí / sí | no | sí |
| modalidad_gruporegimen_especial | -0,535 (-1,579 a 0,198) | 0,267 (-0,291 a 0,826) | 0,514 (0,287 a 0,742) | no / no / sí | sí | sí |
| modalidad_gruposeleccion_abreviada | 1,603 (1,384 a 1,824) | 1,187 (0,928 a 1,445) | 1,256 (1,156 a 1,356) | sí / sí / sí | no | no |
| fuentesecop2 | 0,477 (0,270 a 0,564) | 0,238 (0,151 a 0,325) | 0,231 (0,151 a 0,311) | sí / sí / sí | no | no |
| inhumacion_cremacion | 0,052 (-0,038 a 0,187) | 0,148 (0,042 a 0,254) | 0,052 (-0,004 a 0,107) | no / sí / no | no | sí |
| traslado | 0,064 (-0,081 a 0,311) | -0,006 (-0,139 a 0,126) | -0,026 (-0,120 a 0,067) | no / no / no | sí | no |
| ataudes_bienes | -0,003 (-0,116 a 0,126) | 0,003 (-0,091 a 0,096) | -0,043 (-0,102 a 0,017) | no / no / no | sí | no |
| plan_exequial | -0,332 (-0,550 a -0,085) | -0,088 (-0,223 a 0,047) | -0,109 (-0,209 a -0,008) | sí / no / sí | no | sí |
| operacion_cementerio | -0,013 (-0,673 a 0,830) | -0,560 (-1,208 a 0,089) | -0,327 (-0,509 a -0,145) | no / no / sí | no | sí |
| atencion_vulnerables_NN | 0,192 (-0,003 a 0,349) | 0,077 (-0,031 a 0,185) | 0,022 (-0,049 a 0,094) | no / no / no | no | no |
| anio2021 | -0,030 (-0,138 a 0,045) | -0,043 (-0,094 a 0,008) | -0,062 (-0,117 a -0,006) | no / no / sí | no | sí |
| anio2022 | -0,056 (-0,147 a 0,061) | 0,034 (-0,026 a 0,094) | -0,030 (-0,090 a 0,030) | no / no / no | sí | no |
| anio2023 | -0,128 (-0,223 a 0,006) | -0,061 (-0,161 a 0,039) | -0,095 (-0,156 a -0,033) | no / no / sí | no | sí |
| anio2024 | -0,116 (-0,217 a 0,000) | -0,002 (-0,066 a 0,061) | -0,054 (-0,119 a 0,012) | no / no / no | no | no |
| anio2025 | -0,016 (-0,085 a 0,125) | 0,060 (-0,002 a 0,122) | 0,033 (-0,034 a 0,101) | no / no / no | sí | no |

- **Cambian de signo** entre los tres estimadores puntuales: 9 de 21 coeficientes (tipo_entidadotra_entidad, tipo_entidadsalud_hospital_ese, tipo_entidadservicios_publicos_empresa, modalidad_grupocontratacion_directa, modalidad_gruporegimen_especial, traslado, ataudes_bienes, anio2022, anio2025).
- **Cambian de significancia** (al 5 %) entre los tres: 11 de 21 (tipo_entidadotra_entidad, tipo_entidadsalud_hospital_ese, tipo_entidadservicios_publicos_empresa, modalidad_grupocontratacion_directa, modalidad_grupootras, modalidad_gruporegimen_especial, inhumacion_cremacion, plan_exequial, operacion_cementerio, anio2021, anio2023).
- Significativos en los tres a la vez: 3; no significativos en ninguno: 7.

### 2. Tipología: sin variables redundantes y con `poLCA`

**Paso 1: residuos bivariados más altos (BVR) del modelo de menor BIC de D97** (fuente y año, 7 clases):

| posición | variable 1 | variable 2 | BVR |
|---|---|---|---|
| 1 | traslado | atencion_vulnerables_NN | 36,5 |
| 2 | inhumacion_cremacion | plan_exequial | 26,4 |
| 3 | tipo_contrato_hom | operacion_cementerio | 23,6 |
| 4 | tipo_entidad | traslado | 10,7 |
| 5 | tipo_entidad | plan_exequial | 10,3 |
| 6 | tipo_entidad | orden_nivel | 9,9 |
| 7 | tipo_entidad | modalidad_grupo | 8,9 |
| 8 | traslado | plan_exequial | 8,7 |
| 9 | modalidad_grupo | orden_nivel | 6,3 |
| 10 | tipo_contrato_hom | inhumacion_cremacion | 5,6 |
| 11 | traslado | ataudes_bienes | 5,2 |
| 12 | tipo_entidad | inhumacion_cremacion | 5,0 |

Y del de menor BIC sin covariables (6 clases):

| posición | variable 1 | variable 2 | BVR |
|---|---|---|---|
| 1 | ataudes_bienes | operacion_cementerio | 50,5 |
| 2 | traslado | atencion_vulnerables_NN | 31,8 |
| 3 | inhumacion_cremacion | plan_exequial | 29,6 |
| 4 | tipo_entidad | traslado | 11,4 |
| 5 | tipo_entidad | orden_nivel | 8,0 |
| 6 | tipo_contrato_hom | operacion_cementerio | 7,6 |
| 7 | orden_nivel | plan_exequial | 7,2 |
| 8 | tipo_entidad | atencion_vulnerables_NN | 6,8 |
| 9 | tipo_entidad | modalidad_grupo | 6,6 |
| 10 | traslado | ataudes_bienes | 6,6 |
| 11 | traslado | plan_exequial | 6,4 |
| 12 | orden_nivel | inhumacion_cremacion | 6,2 |

**Paso 2: variables que se quitan.** `cuartil_valor` se quita siempre (el valor se modela aparte). El par `tipo_contrato_hom` con `ataudes_bienes` está en la posición 14 del modelo de menor BIC de D97 (BVR 4,6), fuera de los 5 más altos; por la regla de D98, **`tipo_contrato_hom` se conserva**. Quedan 10 variables: tipo de entidad, grupo de modalidad, tipo de contrato homologado, territorial o nacional y los seis componentes.

**Paso 3: `poLCA` (versión 1.6.0.2), 100 arranques, 2 a 10 clases, tres modelos.** Cumplen el criterio (BVR máximo ≤ 10 y mejor ajuste en al menos 5 arranques): **0 de 27**. El BVR máximo más bajo alcanzado es 9,4 (sin covariables, 10 clases); 8 modelos repiten su mejor ajuste en al menos 5 arranques.

| covariables | clases | parámetros | BIC | ΔBIC | entropía relativa | arranques con el máximo (de 100) | clase más pequeña (%) | BVR máximo | pares con BVR > 10 | cumple (BVR ≤ 10 y ≥ 5 arranques) |
|---|---|---|---|---|---|---|---|---|---|---|
| sin covariables | 2 | 43 | 43.037,8 | 3.389,8 | 0,79 | 54 | 43,7 | 540,3 | 24 | no |
| sin covariables | 3 | 65 | 40.738,1 | 1.090,1 | 0,84 | 94 | 10,9 | 252,1 | 13 | no |
| sin covariables | 4 | 87 | 40.358,4 | 710,5 | 0,88 | 39 | 4,4 | 53,5 | 11 | no |
| sin covariables | 5 | 109 | 40.066,3 | 418,3 | 0,87 | 24 | 4,2 | 26,2 | 3 | no |
| sin covariables | 6 | 131 | 39.964,4 | 316,4 | 0,89 | 1 | 1,5 | 25,1 | 2 | no |
| sin covariables | 7 | 153 | 39.916,3 | 268,4 | 0,89 | 1 | 1,5 | 25,2 | 3 | no |
| sin covariables | 8 | 175 | 39.931,3 | 283,3 | 0,88 | 1 | 1,4 | 28,5 | 2 | no |
| sin covariables | 9 | 197 | 39.966,6 | 318,7 | 0,82 | 1 | 1,5 | 25,7 | 3 | no |
| sin covariables | 10 | 219 | 40.045,5 | 397,5 | 0,81 | 1 | 1,4 | 9,4 | 0 | no |
| fuente | 2 | 44 | 42.599,8 | 2.951,9 | 0,79 | 93 | 41,6 | 533,3 | 24 | no |
| fuente | 3 | 67 | 40.161,2 | 513,3 | 0,84 | 30 | 11,7 | 262,4 | 11 | no |
| fuente | 4 | 90 | 39.786,4 | 138,5 | 0,86 | 1 | 4,8 | 119,6 | 10 | no |
| fuente | 5 | 113 | 39.648,0 | 0,0 | 0,90 | 1 | 4,1 | 65,4 | 10 | no |
| fuente | 6 | 136 | 40.751,8 | 1.103,9 | 0,91 | 1 | 0,0 | 243,6 | 15 | no |
| fuente | 7 | 159 | 40.988,4 | 1.340,4 | 0,92 | 1 | 0,0 | 271,2 | 14 | no |
| fuente | 8 | 182 | 40.515,6 | 867,7 | 0,87 | 1 | 0,0 | 55,8 | 10 | no |
| fuente | 9 | 205 | 41.364,7 | 1.716,7 | 0,93 | 1 | 0,0 | 75,9 | 14 | no |
| fuente | 10 | 228 | 39.988,7 | 340,7 | 0,90 | 1 | 0,0 | 17,9 | 3 | no |
| fuente y año | 2 | 49 | 42.608,4 | 2.960,4 | 0,79 | 39 | 41,6 | 533,8 | 24 | no |
| fuente y año | 3 | 77 | 40.142,7 | 494,8 | 0,84 | 41 | 11,6 | 269,1 | 11 | no |
| fuente y año | 4 | 105 | 39.875,7 | 227,7 | 0,80 | 2 | 9,7 | 280,8 | 11 | no |
| fuente y año | 5 | 133 | 42.987,5 | 3.339,5 | 0,94 | 1 | 0,0 | 362,1 | 27 | no |
| fuente y año | 6 | 161 | 43.047,0 | 3.399,0 | 0,93 | 1 | 0,0 | 360,7 | 25 | no |
| fuente y año | 7 | 189 | 44.195,5 | 4.547,5 | 0,95 | 1 | 0,7 | 472,6 | 27 | no |
| fuente y año | 8 | 217 | 44.299,7 | 4.651,8 | 0,94 | 1 | 0,0 | 505,4 | 28 | no |
| fuente y año | 9 | 245 | 44.618,9 | 4.970,9 | 0,96 | 1 | 0,0 | 599,7 | 23 | no |
| fuente y año | 10 | 273 | 45.651,1 | 6.003,1 | 0,97 | 1 | 0,0 | 498,4 | 31 | no |

**Resultado: no hay tipología latente que cumpla independencia local.** Ninguno de los 27 modelos de `poLCA` cumple a la vez BVR máximo ≤ 10 y mejor ajuste en al menos 5 de 100 arranques. Matiz: los modelos con BVR máximo ≤ 10 son: sin covariables, 10 clases (BVR máximo 9,4, mejor ajuste en 1 de 100 arranques, ΔBIC 397,5); su mejor ajuste no se reproduce, de modo que no se distingue de un máximo local. En 10 modelos con covariables la mejor solución tiene una clase vacía (0,0 %): el ajuste con covariables no convergió a una solución útil (el BIC de esos modelos sube con el número de clases). Según D98, la tipología de clases latentes queda sin elegir y se deja el **ACM + HCPC solo como descripción**.

**ACM + HCPC (descriptivo).** Variables: las 10 de arriba. Las dos primeras dimensiones retienen 12,6 % y 9,2 % de la inercia (42,0 % las cinco primeras). HCPC sugiere 11 grupos. Estabilidad por bootstrap (200 remuestreos, semilla 2034; Jaccard de cada grupo frente a su mejor coincidencia, umbral de 0,60):

| grupo | contratos | % | Jaccard medio (bootstrap) | Jaccard percentil 5 | remuestreos en que se disuelve (Jaccard < 0,5, %) |
|---|---|---|---|---|---|
| 1 | 1278 | 25,6 | 0,96 | 0,81 | 0,0 |
| 2 | 280 | 5,6 | 0,87 | 0,15 | 8,0 |
| 3 | 253 | 5,1 | 0,87 | 0,07 | 9,5 |
| 4 | 362 | 7,3 | 0,91 | 0,70 | 0,0 |
| 5 | 2314 | 46,4 | 0,96 | 0,87 | 0,0 |
| 6 | 47 | 0,9 | 0,85 | 0,65 | 2,0 |
| 7 | 206 | 4,1 | 0,77 | 0,35 | 26,0 |
| 8 | 34 | 0,7 | 0,87 | 0,33 | 12,5 |
| 9 | 121 | 2,4 | 0,91 | 0,79 | 0,5 |
| 10 | 96 | 1,9 | 0,93 | 0,76 | 0,0 |
| 11 | 1 | 0,0 | 0,99 | 1,00 | 0,8 |

0 de 11 grupos tienen un Jaccard medio inferior a 0,60. Los dos grupos grandes (1 y 5, con 72,0 % de los contratos) son los más estables; el grupo 7 (206 contratos) se disuelve en 26 % de los remuestreos y los grupos 2, 3 y 8 tienen percentiles 5 de 0,07 a 0,33. El grupo 11 es un solo contrato y solo aparece en 118 de 200 remuestreos, así que su Jaccard no es informativo.

### 3. Estacionalidad: término autorregresivo e indicadora de julio a septiembre de 2020

Todos los modelos se ajustan a los mismos 71 meses (febrero de 2020 a diciembre de 2025), porque el término autorregresivo no existe en enero de 2020. Los modelos 1, 2 y 3 son los de D97 reajustados a esos 71 meses; 2b y 3b agregan `log(conteo del mes anterior + 1)` y una indicadora de julio, agosto y septiembre de 2020 (aproximación del pico de mortalidad por COVID-19, sin verificar con la serie mensual del INS; D98).

| modelo | parámetros | BIC (71 meses) | ΔBIC | Ljung-Box 6 (p) | Ljung-Box 12 (p) | asimetría RQ | exceso de curtosis RQ | supuestos que falla |
|---|---|---|---|---|---|---|---|---|
| 1 Poisson (mes y año) | 17 | 726,5 | 117,6 | 0,031 | 0,080 | -0,18 | 0,51 | sobredispersión |
| 2 binomial negativa (mes y año) | 18 | 645,0 | 36,2 | 0,122 | 0,271 | -0,30 | 0,39 | ninguno |
| 3 binomial negativa (armónicos y tendencia) | 7 | 613,0 | 4,1 | 0,043 | 0,177 | -0,16 | -0,65 | ninguno |
| 2b binomial negativa (mes, año, autorregresivo y COVID) | 20 | 640,6 | 31,7 | 0,169 | 0,353 | -0,17 | -0,14 | ninguno |
| 3b binomial negativa (armónicos, tendencia, autorregresivo y COVID) | 9 | 608,8 | 0,0 | 0,398 | 0,432 | -0,25 | -0,22 | ninguno |

- **Pasan todos los supuestos:** 2, 3, 2b, 3b. Aplicando la regla de BIC de D97 entre ellos, **queda 3b binomial negativa (armónicos, tendencia, autorregresivo y COVID)** (ΔBIC de 4,1 frente al siguiente, 3; mayor que 2, así que no entra la cláusula del más simple).
- **Sensibilidad del Ljung-Box a la muestra:** con los 72 meses de D97, los modelos 2 y 3 daban p = 0,020 y 0,037 a 12 rezagos (fallaban); con los 71 meses sin enero de 2020 dan p = 0,271 y 0,177 (pasan). Quitar un solo mes cambia la conclusión de autocorrelación en esos modelos, lo que indica que ese supuesto está cerca del umbral y que el resultado de D97 y el de aquí son frágiles.
- Errores estándar de Newey-West (Bartlett, rezago 3, T = 71) frente a los del modelo de verosimilitud en los coeficientes de 2b y 3b:

| modelo | término | estimador | EE del modelo | EE Newey-West | p del modelo | p Newey-West |
|---|---|---|---|---|---|---|
| 2b | autorregresivo log(conteo previo + 1) | 0,222 | 0,116 | 0,102 | 0,0566 | 0,0297 |
| 2b | indicadora jul–sep 2020 | 0,356 | 0,155 | 0,106 | 0,0221 | 0,0008 |
| 3b | seno 12 meses | 0,489 | 0,061 | 0,065 | 0,0000 | 0,0000 |
| 3b | coseno 12 meses | -0,054 | 0,059 | 0,056 | 0,3618 | 0,3394 |
| 3b | seno 6 meses | 0,060 | 0,043 | 0,038 | 0,1626 | 0,1130 |
| 3b | coseno 6 meses | -0,139 | 0,039 | 0,040 | 0,0004 | 0,0004 |
| 3b | tendencia (por mes) | -0,006 | 0,002 | 0,001 | 0,0001 | 0,0000 |
| 3b | autorregresivo log(conteo previo + 1) | 0,215 | 0,113 | 0,109 | 0,0576 | 0,0489 |
| 3b | indicadora jul–sep 2020 | 0,338 | 0,152 | 0,097 | 0,0256 | 0,0005 |

- La indicadora de julio a septiembre de 2020 y el término autorregresivo tienen p de Newey-West de 0,0005 a 0,0008 y de 0,030 a 0,049, respectivamente. Gráfico de las autocorrelaciones: `graficos/patrones/estacionalidad_d98_acf.png`.

### 4. Muertes COVID mensuales en lugar de la indicadora de julio a septiembre de 2020 (D99, exploratorio)

Fuente: conteo de fallecidos por mes de fecha de muerte del conjunto de casos positivos de COVID-19 del INS (datos.gov.co `gt2j-8ykr`), una consulta agregada guardada en `data/raw/covid/` con su SHA-256 en el manifiesto (D99). La serie tiene 184.393 fallecidos de marzo de 2020 a enero de 2024 (pico de 19.415 en 2021-06). Los 25 meses sin registro (enero y febrero de 2020 y desde febrero de 2024) son **faltantes, no ceros**: los modelos con términos de COVID se ajustan solo a los 47 meses con registro (marzo de 2020 a enero de 2024, contiguos), y los modelos 2 y 3 de D97 se muestran además con los 72 meses. El percentil 75 se calcula sobre los 47 meses con registro: 6.386 muertes; 12 meses lo superan: 2020-07, 2020-08, 2020-09, 2020-11, 2020-12, 2021-01, 2021-02, 2021-04, 2021-05, 2021-06, 2021-07, 2022-01. Correlación entre el log de las muertes y la indicadora del percentil 75: 0,68.

Modelos (binomial negativa): el 2 y el 3 de D97; 2b y 3b de D98 (autorregresivo e indicadora de julio a septiembre de 2020); 2c y 3c con las muertes (log + 1) y la indicadora del percentil 75 sin autorregresivo; 2d y 3d con autorregresivo y esos dos términos. Los ocho se comparan en los mismos meses; el BIC solo es comparable dentro de una muestra.

| muestra | modelo | parámetros | BIC | ΔBIC (en su muestra) | Ljung-Box 6 (p) | Ljung-Box 12 (p) | exceso de curtosis RQ | Wald de la parte estacional, p (Newey-West) | amplitud de 12 meses | falla |
|---|---|---|---|---|---|---|---|---|---|---|
| 72 meses (sin términos de COVID) | 2 mes y año | 18 | 656,4 | 32,5 | 0,019 | 0,020 | 0,13 | < 0,0001 |  | autocorrelación |
| 72 meses (sin términos de COVID) | 3 armónicos y tendencia | 7 | 624,0 | 0,0 | 0,011 | 0,037 | -0,74 | < 0,0001 | 0,56 | autocorrelación |
| meses con registro de COVID | 2 mes y año | 17 | 433,8 | 23,3 | 0,041 | 0,091 | 2,76 | < 0,0001 |  | ninguno |
| meses con registro de COVID | 3 armónicos y tendencia | 7 | 414,0 | 3,6 | 0,101 | 0,020 | -0,46 | < 0,0001 | 0,54 | autocorrelación |
| meses con registro de COVID | 2b mes, año, AR y jul–sep 2020 (D98) | 19 | 427,9 | 17,4 | 0,000 | 0,000 | 0,34 | < 0,0001 |  | autocorrelación |
| meses con registro de COVID | 3b armónicos, tendencia, AR y jul–sep 2020 (D98) | 9 | 415,7 | 5,2 | 0,053 | 0,010 | -0,71 | < 0,0001 | 0,45 | autocorrelación |
| meses con registro de COVID | 2c mes, año y COVID | 19 | 410,5 | 0,0 | 0,616 | 0,134 | -0,32 | < 0,0001 |  | ninguno |
| meses con registro de COVID | 3c armónicos, tendencia y COVID | 9 | 411,9 | 1,4 | 0,131 | 0,060 | -1,01 | < 0,0001 | 0,54 | ninguno |
| meses con registro de COVID | 2d mes, año, AR y COVID | 20 | 414,3 | 3,8 | 0,697 | 0,129 | -0,32 | < 0,0001 |  | ninguno |
| meses con registro de COVID | 3d armónicos, tendencia, AR y COVID | 10 | 414,0 | 3,5 | 0,183 | 0,086 | -1,13 | < 0,0001 | 0,46 | ninguno |

Coeficientes de los términos de COVID y del autorregresivo, con errores estándar de Newey-West:

| muestra | modelo | término | estimador | EE del modelo | EE Newey-West | p Newey-West |
|---|---|---|---|---|---|---|
| meses con registro de COVID | 2b | autorregresivo | 0,372 | 0,125 | 0,093 | 0,0001 |
| meses con registro de COVID | 2b | jul–sep 2020 | 0,185 | 0,143 | 0,075 | 0,0130 |
| meses con registro de COVID | 3b | autorregresivo | 0,266 | 0,144 | 0,114 | 0,0193 |
| meses con registro de COVID | 3b | jul–sep 2020 | 0,170 | 0,160 | 0,085 | 0,0440 |
| meses con registro de COVID | 2c | log(1 + muertes COVID del mes) | 0,152 | 0,020 | 0,022 | 0,0000 |
| meses con registro de COVID | 2c | mes sobre el percentil 75 | -0,146 | 0,064 | 0,067 | 0,0300 |
| meses con registro de COVID | 3c | log(1 + muertes COVID del mes) | 0,095 | 0,027 | 0,020 | 0,0000 |
| meses con registro de COVID | 3c | mes sobre el percentil 75 | -0,125 | 0,097 | 0,083 | 0,1317 |
| meses con registro de COVID | 2d | autorregresivo | -0,036 | 0,125 | 0,129 | 0,7817 |
| meses con registro de COVID | 2d | log(1 + muertes COVID del mes) | 0,158 | 0,028 | 0,035 | 0,0000 |
| meses con registro de COVID | 2d | mes sobre el percentil 75 | -0,148 | 0,064 | 0,070 | 0,0341 |
| meses con registro de COVID | 3d | autorregresivo | 0,187 | 0,138 | 0,108 | 0,0853 |
| meses con registro de COVID | 3d | log(1 + muertes COVID del mes) | 0,080 | 0,029 | 0,021 | 0,0001 |
| meses con registro de COVID | 3d | mes sobre el percentil 75 | -0,122 | 0,094 | 0,081 | 0,1314 |

- Con los 47 meses con registro, el Ljung-Box a 12 rezagos da p = 0,091 (modelo 2), 0,020 (3), 0,134 (2c), 0,060 (3c), 0,129 (2d) y 0,086 (3d); con los modelos de D98 con indicadora de julio a septiembre de 2020, 0,000 (2b) y 0,010 (3b). Pasan ambos supuestos: 2, 2c, 3c, 2d, 3d. Con los 72 meses, los modelos 2 y 3 sin COVID fallan (p = 0,020 y 0,037).
- **La señal estacional se mantiene** en todos los modelos: el contraste conjunto de la parte estacional con errores de Newey-West da p < 0,0001 en las 10 especificaciones y la amplitud del armónico de 12 meses queda entre 0,45 y 0,56.
- El log de las muertes queda asociado con más contratos en todos los modelos (coeficiente 0,08 a 0,16; p de Newey-West ≤ 0,0001). La indicadora del percentil 75 sale con signo negativo (-0,15 a -0,12) y solo es significativa en los modelos de mes y año; está correlacionada con el log de las muertes (0,68), de modo que sus coeficientes no se interpretan por separado. La asociación es descriptiva y no se interpreta como causal.
- El menor BIC entre los modelos con registro es el 2c (410,5); los que quedan a menos de 2 puntos: 3c.

### Limitaciones del análisis exploratorio

- Los tres análisis se decidieron después de ver los resultados de D97; son exploratorios y no sustituyen a los de D97.
- **Valor:** los intervalos de la mediana por bootstrap agrupado son anchos en las categorías con pocos contratos (otras entidades, otras modalidades, operación de cementerio); los de Wald del gamma son los más angostos porque son del modelo y no robustos; «cambia de signo» incluye coeficientes cercanos a cero, cuyo signo no es informativo; la regresión por cuantiles describe la mediana del log del valor y no la media, de modo que no es comparable en magnitud con el gamma.
- **Tipología:** `poLCA` con covariables no convergió a soluciones útiles a partir de 5 clases (clases vacías y BIC creciente), y sin covariables el único modelo con BVR ≤ 10 (10 clases) no reproduce su mejor ajuste; no se probó más de 100 arranques ni otro programa. Los mayores residuos bivariados están entre componentes (traslado con atención a vulnerables, inhumación con plan exequial, ataúdes con operación de cementerio), que `poLCA` no logra explicar con clases. El ACM + HCPC es descriptivo, sin modelo probabilístico.
- **Estacionalidad:** la indicadora de julio a septiembre de 2020 fue una aproximación y **fue reemplazada por la serie mensual del INS (D99, sección 4)**, con la que el modelo 3b ya no pasa el Ljung-Box; lo que sigue describe el análisis de D98 con 71 meses: el Ljung-Box de los modelos 2 y 3 cambia de conclusión al quitar enero de 2020 (con 72 meses fallaban, con 71 pasan), de modo que el supuesto está cerca del umbral y la elección del modelo 3b es frágil; con 71 observaciones los errores de Newey-West tienen poca precisión.
