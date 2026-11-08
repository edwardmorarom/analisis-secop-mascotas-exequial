# Causas de defunción y contratación funeraria pública por departamento (D107)

> **Análisis exploratorio y ecológico (D107, propuesta pendiente de revisión de Edward).** No se interpreta ninguna asociación como causal; la unidad es el departamento (la entidad contratante y el residente fallecido pueden estar en departamentos distintos). Rama `causas-defuncion`, sin integrar a `main`.

## 1. Datos y verificación

Seis cuadros unificados de defunciones no fetales del DANE (cifras definitivas 2020 a 2025; la de 2025 se publicó el 24 de septiembre de 2026), Cuadro 5 (departamento de residencia × lista 6/67 de la OPS) y, para la COVID-19, Cuadro 16 (`U07`). Archivos en `data/raw/dane/eevv/` con URL, fecha, tamaño y SHA-256 en el manifiesto. El equivalente de cada grupo en la lista 6/67 y el tratamiento de la COVID-19 están en la enmienda de D107.

**Verificación de totales nacionales** (suma de los 33 departamentos más «Extranjero» y «Sin información» frente al Índice del DANE y a la fila `TOTAL` del Cuadro 5):

| Año | Total publicado (Índice) | Total nacional (Cuadro 5) | Suma de departamentos y no asignados | Suma de los siete grupos | Diferencia |
|---|---|---|---|---|---|
| 2020 | 300.853 | 300.853 | 300.853 | 300.853 | 0 |
| 2021 | 363.089 | 363.089 | 363.089 | 363.089 | 0 |
| 2022 | 287.251 | 287.251 | 287.251 | 287.251 | 0 |
| 2023 | 268.411 | 268.411 | 268.411 | 268.411 | 0 |
| 2024 | 275.778 | 275.778 | 275.778 | 275.778 | 0 |
| 2025 | 284.254 | 284.254 | 284.254 | 284.254 | 0 |

La diferencia es 0 en los seis años. **COVID-19** (EEVV: `U07` del Cuadro 16; INS: fallecidos por fecha de muerte en `data/raw/covid/`):

| Año | EEVV (U07, suma de departamentos) | INS (fallecidos) | INS − EEVV | Diferencia relativa |
|---|---|---|---|---|
| 2020 | 51.197 | 50.099 | -1.098 | -2,1 % |
| 2021 | 90.668 | 102.436 | 11.768 | 13,0 % |
| 2022 | 13.385 | 25.369 | 11.984 | 89,5 % |

El INS cuenta fallecidos con COVID-19 confirmado por fecha de muerte y las EEVV cuentan la causa certificada por residencia, de modo que no tienen por qué coincidir: el INS supera a las EEVV en 2021 y en 2022 (en 2020 la diferencia es de -2,1 %). Esta diferencia se reporta y no se corrige. De 2023 en adelante la COVID-19 no se observa en las EEVV por departamento (queda dentro de «demás causas»), mientras el INS registra 6.455 fallecidos en 2023.

**Cobertura de la COVID-19 por departamento.** `U07` aparece entre las diez primeras causas en 2020: 33 de 33 departamentos, 2021: 33 de 33 departamentos, 2022: 32 de 33 departamentos; los demás quedan en «demás causas» y la COVID-19 se toma como 0 en el panel. En 2023 a 2025 no es observable (se fija en 0 en el panel).

**Tasas por 100.000 habitantes** (mediana de los 33 departamentos, mínimo y máximo de los promedios anuales 2020–2025; COVID-19: 2020–2022):

| Causa | Mediana | Mínimo | Máximo |
|---|---|---|---|
| Agresiones (homicidios) | 25,7 | 7,6 | 57,8 |
| Accidentes de transporte | 15,9 | 1,9 | 34,3 |
| Otros accidentes y causas externas | 22,7 | 11,8 | 63,7 |
| COVID-19 | 83,4 | 19,7 | 143,8 |
| Sistema circulatorio | 155,7 | 43,7 | 253,3 |
| Neoplasias | 78,6 | 20,2 | 152,0 |
| Demás causas | 167,6 | 87,4 | 309,5 |

## 2. Transversal por departamento (Spearman, 33 departamentos)

Tasa promedio de cada causa 2020–2025 (COVID-19: 2020–2022) frente a contratos funerarios y valor, por 100.000 habitantes (promedio anual 2020–2025). Holm por causa (7) dentro de cada resultado. IC 95 % por transformación de Fisher (aproximado). La última columna es la sensibilidad con el promedio 2020–2024 (p de Holm).

**Contratos por 100.000**

| Causa | n | ρ | IC 95 % | p | p de Holm | p de Holm < 0,05 | Sin 2025: p de Holm |
|---|---|---|---|---|---|---|---|
| Agresiones (homicidios) | 33 | -0,12 | -0,46 a 0,26 | 0,513 | 1,000 | no | 0,995 (ρ = -0,12) |
| Accidentes de transporte | 33 | 0,12 | -0,26 a 0,46 | 0,514 | 1,000 | no | 0,995 (ρ = 0,12) |
| Otros accidentes y causas externas | 33 | 0,51 | 0,18 a 0,73 | 0,003 | 0,018 | sí | 0,021 (ρ = 0,50) |
| COVID-19 | 33 | -0,38 | -0,65 a -0,02 | 0,029 | 0,143 | no | 0,136 (ρ = -0,38) |
| Sistema circulatorio | 33 | -0,34 | -0,63 a 0,02 | 0,052 | 0,174 | no | 0,194 (ρ = -0,33) |
| Neoplasias | 33 | -0,42 | -0,68 a -0,06 | 0,016 | 0,097 | no | 0,110 (ρ = -0,41) |
| Demás causas | 33 | -0,35 | -0,63 a 0,01 | 0,044 | 0,174 | no | 0,156 (ρ = -0,36) |

**Valor por 100.000**

| Causa | n | ρ | IC 95 % | p | p de Holm | p de Holm < 0,05 | Sin 2025: p de Holm |
|---|---|---|---|---|---|---|---|
| Agresiones (homicidios) | 33 | -0,20 | -0,53 a 0,17 | 0,260 | 0,780 | no | 0,566 (ρ = -0,23) |
| Accidentes de transporte | 33 | -0,06 | -0,41 a 0,31 | 0,759 | 0,780 | no | 0,826 (ρ = -0,10) |
| Otros accidentes y causas externas | 33 | 0,19 | -0,18 a 0,52 | 0,285 | 0,780 | no | 0,826 (ρ = 0,15) |
| COVID-19 | 33 | -0,36 | -0,64 a 0,00 | 0,040 | 0,162 | no | 0,138 (ρ = -0,37) |
| Sistema circulatorio | 33 | -0,56 | -0,77 a -0,25 | < 0,001 | 0,005 | sí | 0,006 (ρ = -0,55) |
| Neoplasias | 33 | -0,53 | -0,75 a -0,21 | 0,001 | 0,009 | sí | 0,010 (ρ = -0,53) |
| Demás causas | 33 | -0,52 | -0,74 a -0,20 | 0,002 | 0,010 | sí | 0,018 (ρ = -0,49) |

## 3. Panel departamento × año (binomial negativa)

Contratos funerarios por departamento-año (n = 198: 33 departamentos × 6 años), offset log(población), efectos fijos de año, errores agrupados por departamento. Razón de tasas (IRR) **por cada duplicación de (1 + tasa)**: `exp(β·ln 2)`.

### 3.1 Modelo conjunto (B1)

Variables eliminadas por VIF ≥ 5 (en orden): Neoplasias (VIF 5,6). VIF finales: Agresiones (homicidios) 1,31, Accidentes de transporte 2,16, Otros accidentes y causas externas 1,12, COVID-19 1,08, Sistema circulatorio 3,77, Demás causas 2,55. α estimado = 0,222.

| Causa | IRR por duplicación | IC 95 % | p | p de Holm (entre las del modelo) |
|---|---|---|---|---|
| Agresiones (homicidios) | 0,88 | 0,71 a 1,10 | 0,258 | 0,515 |
| Accidentes de transporte | 1,53 | 1,10 a 2,12 | 0,011 | 0,053 |
| Otros accidentes y causas externas | 2,36 | 1,68 a 3,30 | < 0,001 | < 0,001 |
| COVID-19 | 0,78 | 0,64 a 0,95 | 0,016 | 0,062 |
| Sistema circulatorio | 0,64 | 0,40 a 1,03 | 0,067 | 0,202 |
| Demás causas | 0,85 | 0,39 a 1,83 | 0,672 | 0,672 |

### 3.2 Un modelo por causa (B2)

Una causa a la vez con efectos fijos de año; COVID-19 solo con 2020–2022 (n = 99). Holm entre las siete causas.

| Causa | IRR por duplicación | IC 95 % | p | p de Holm | n |
|---|---|---|---|---|---|
| Agresiones (homicidios) | 0,89 | 0,68 a 1,17 | 0,398 | 0,795 | 198 |
| Accidentes de transporte | 1,00 | 0,66 a 1,49 | 0,982 | 0,982 | 198 |
| Otros accidentes y causas externas | 2,06 | 1,30 a 3,25 | 0,002 | 0,014 | 198 |
| COVID-19 | 0,75 | 0,59 a 0,96 | 0,021 | 0,110 | 99 |
| Sistema circulatorio | 0,71 | 0,54 a 0,94 | 0,018 | 0,110 | 198 |
| Neoplasias | 0,70 | 0,49 a 0,99 | 0,043 | 0,170 | 198 |
| Demás causas | 0,66 | 0,36 a 1,23 | 0,192 | 0,575 | 198 |

**Sensibilidad** (IRR; p nominal), con la regla de D107: sin Bogotá D.C., sin San Andrés, sin 2020 y sin 2025 (en COVID-19, sin 2025 no aplica):

| Causa | Sin Bogotá | Sin San Andrés | Sin 2020 | Sin 2025 |
|---|---|---|---|---|
| Agresiones (homicidios) | 0,87 (p 0,273) | 0,91 (p 0,517) | 0,90 (p 0,477) | 0,88 (p 0,360) |
| Accidentes de transporte | 0,98 (p 0,908) | 1,01 (p 0,970) | 1,00 (p 0,994) | 1,00 (p 0,998) |
| Otros accidentes y causas externas | 1,95 (p 0,003) | 2,02 (p 0,003) | 1,99 (p 0,004) | 2,03 (p 0,001) |
| COVID-19 | 0,79 (p 0,039) | 0,75 (p 0,022) | 0,72 (p 0,003) | n. a. |
| Sistema circulatorio | 0,72 (p 0,023) | 0,72 (p 0,021) | 0,72 (p 0,028) | 0,73 (p 0,039) |
| Neoplasias | 0,73 (p 0,070) | 0,69 (p 0,041) | 0,70 (p 0,042) | 0,70 (p 0,052) |
| Demás causas | 0,65 (p 0,168) | 0,66 (p 0,183) | 0,66 (p 0,190) | 0,67 (p 0,246) |

### 3.3 Supuestos (estadístico, gl, p y decisión)

Sobredispersión: Cameron-Trivedi en el Poisson (t de la regresión auxiliar, gl, p; justifica la binomial negativa si p < 0,05) y χ² de Pearson/gl del Poisson (> 1,5 apoya la sobredispersión); dispersión residual del modelo binomial negativo (χ² de Pearson/gl ≤ 1,5); residuos cuantílicos aleatorizados (semilla 2035: |asimetría| ≤ 1 y |exceso de curtosis| ≤ 3); Cook (máximo ≤ 1); VIF < 5 (modelo conjunto).

| Modelo | Cameron-Trivedi (Poisson) | Pearson/gl Poisson | Sobredispersión (ambas) | Pearson/gl NB | Dispersión NB ≤ 1,5 | Asimetría / curtosis | Residuos | Cook máx. | Cook ≤ 1 | Cook > 4/n |
|---|---|---|---|---|---|---|---|---|---|---|
| B1 conjunto | t = 6,16, gl 197, p < 0,001 | 8,4 | sí | 1,15 | sí | 0,06 / -0,04 | sí | 0,29 | sí | 16 |
| B2 Agresiones (homicidios) | t = 7,87, gl 197, p < 0,001 | 16,3 | sí | 1,13 | sí | -0,06 / -0,29 | sí | 0,16 | sí | 15 |
| B2 Accidentes de transporte | t = 1,26, gl 197, p 0,208 | 27,8 | no | 1,19 | sí | 0,01 / -0,32 | sí | 0,23 | sí | 18 |
| B2 Otros accidentes y causas externas | t = 11,09, gl 197, p < 0,001 | 11,8 | sí | 1,24 | sí | 0,03 / -0,04 | sí | 0,16 | sí | 13 |
| B2 COVID-19 | t = 5,74, gl 98, p < 0,001 | 16,1 | sí | 1,15 | sí | -0,00 / 0,13 | sí | 0,76 | sí | 7 |
| B2 Sistema circulatorio | t = 9,61, gl 197, p < 0,001 | 15,8 | sí | 1,00 | sí | -0,13 / -0,41 | sí | 0,29 | sí | 16 |
| B2 Neoplasias | t = 7,65, gl 197, p < 0,001 | 14,3 | sí | 1,07 | sí | -0,04 / -0,29 | sí | 0,53 | sí | 16 |
| B2 Demás causas | t = 9,56, gl 197, p < 0,001 | 15,6 | sí | 1,20 | sí | 0,04 / 0,00 | sí | 0,94 | sí | 16 |

VIF del modelo conjunto: Agresiones (homicidios) 1,31, Accidentes de transporte 2,16, Otros accidentes y causas externas 1,12, COVID-19 1,08, Sistema circulatorio 3,77, Demás causas 2,55 (todos < 5 tras eliminar las variables indicadas).

### 3.4 Lectura según la regla de D107

Una asociación se reporta como resultado solo si es significativa tras Holm en B2, el modelo pasa los supuestos y conserva signo y significación nominal en las sensibilidades:

| Causa | Holm < 0,05 | Supuestos | Estable en las sensibilidades | Lectura |
|---|---|---|---|---|
| Agresiones (homicidios) | no | sí | no | no concluyente |
| Accidentes de transporte | no | no | no | no concluyente |
| Otros accidentes y causas externas | sí | sí | sí | **resultado** |
| COVID-19 | no | sí | sí | no concluyente |
| Sistema circulatorio | no | sí | sí | no concluyente |
| Neoplasias | no | sí | no | no concluyente |
| Demás causas | no | sí | no | no concluyente |

## 4. Por forma de compra (grupos de HCPC de D98)

Spearman entre la tasa promedio por causa (2020–2025; COVID-19: 2020–2022) y la participación de cada grupo en los contratos funerarios del departamento (contratos del grupo / contratos de los 8 grupos reportados), en los 31 departamentos con al menos 20 contratos. Grupo 1: alcaldías, prestación de servicios; Grupo 2: alcaldías, suministro con ataúdes (D99). Holm entre las 7 causas dentro de cada grupo.

**Grupo 1 (alcaldías: servicio)**

| Causa | n | ρ | IC 95 % | p | p de Holm | p de Holm < 0,05 |
|---|---|---|---|---|---|---|
| Agresiones (homicidios) | 31 | -0,02 | -0,39 a 0,36 | 0,909 | 0,909 | no |
| Accidentes de transporte | 31 | 0,49 | 0,14 a 0,73 | 0,005 | 0,037 | sí |
| Otros accidentes y causas externas | 31 | 0,16 | -0,23 a 0,50 | 0,388 | 0,777 | no |
| COVID-19 | 31 | 0,32 | -0,06 a 0,62 | 0,081 | 0,243 | no |
| Sistema circulatorio | 31 | 0,43 | 0,07 a 0,69 | 0,015 | 0,083 | no |
| Neoplasias | 31 | 0,40 | 0,04 a 0,68 | 0,024 | 0,097 | no |
| Demás causas | 31 | 0,44 | 0,08 a 0,70 | 0,014 | 0,083 | no |

**Grupo 2 (alcaldías: ataúdes)**

| Causa | n | ρ | IC 95 % | p | p de Holm | p de Holm < 0,05 |
|---|---|---|---|---|---|---|
| Agresiones (homicidios) | 31 | 0,33 | -0,05 a 0,62 | 0,072 | 0,504 | no |
| Accidentes de transporte | 31 | -0,11 | -0,46 a 0,28 | 0,567 | 1,000 | no |
| Otros accidentes y causas externas | 31 | -0,12 | -0,47 a 0,27 | 0,528 | 1,000 | no |
| COVID-19 | 31 | -0,26 | -0,58 a 0,13 | 0,159 | 0,953 | no |
| Sistema circulatorio | 31 | 0,02 | -0,36 a 0,39 | 0,918 | 1,000 | no |
| Neoplasias | 31 | -0,15 | -0,50 a 0,24 | 0,418 | 1,000 | no |
| Demás causas | 31 | -0,03 | -0,40 a 0,35 | 0,877 | 1,000 | no |

## 5. Gráfico

![Dispersión de homicidios y COVID-19 frente a contratos por 100.000](graficos/causas/dispersion_homicidios_covid_contratos.png)

Un punto por departamento. Izquierda: tasa de homicidios promedio 2020–2025 frente a contratos por 100.000 (promedio anual 2020–2025). Derecha: tasa de COVID-19 promedio 2020–2022 frente a contratos por 100.000 en esos tres años (el ρ del gráfico es descriptivo y difiere del transversal de la sección 2, que usa 2020–2025). Se rotulan los puntos extremos.

## 6. Conclusiones

- **Totales:** los totales nacionales de 2020 a 2025 coinciden exactamente con los del DANE (diferencia 0); la COVID-19 de las EEVV es menor que la del INS en 2021 y 2022.
- **Transversal:** tras Holm, 4 de 14 asociaciones son significativas: Otros accidentes y causas externas con contratos por 100.000 (ρ = 0,51, p de Holm 0,018); Sistema circulatorio con valor por 100.000 (ρ = -0,56, p de Holm 0,005); Neoplasias con valor por 100.000 (ρ = -0,53, p de Holm 0,009); Demás causas con valor por 100.000 (ρ = -0,52, p de Holm 0,010). Las asociaciones negativas con circulatorio, neoplasias y demás causas son compatibles con el efecto de la estructura de edad (tasas crudas) y no se interpretan.
- **Panel:** solo «Otros accidentes y causas externas» cumple la regla de D107 (IRR 2,06, IC 95 % 1,30 a 3,25, p de Holm 0,014; supuestos y sensibilidades superados): duplicar (1 + tasa) se asocia con una razón de tasas de contratos de 2,1. Las demás causas son **no concluyentes**. Homicidios no se asocian con la contratación funeraria (IRR 0,89, p 0,398).
- **Supuestos:** todos los modelos pasan dispersión residual, residuos cuantílicos y Cook, y el modelo conjunto cumple VIF < 5 tras eliminar neoplasias. Única excepción, en la sobredispersión: en el modelo de accidentes de transporte la prueba de Cameron-Trivedi no rechaza (p 0,21) aunque Pearson/gl del Poisson es 27,8; según la regla de D107 (ambas) no pasa, y esa causa no era significativa de todos modos.
- **Forma de compra:** 1 asociación(es) significativa(s) tras Holm: Grupo 1 con Accidentes de transporte (ρ = 0,49, p de Holm 0,037); las demás no superan la corrección. Con 31 departamentos y tasas crudas, es una pista y no un resultado.
- **Sobre la pregunta de partida:** la contratación funeraria pública no sigue la mortalidad violenta ni la COVID-19 de forma detectable en este diseño; la señal robusta está en «otros accidentes y causas externas» (que incluye suicidios y caídas), y debe leerse como asociación ecológica, sin causalidad.

## 7. Limitaciones

1. El contrato se ubica en la **sede de la entidad** y la defunción en la **residencia** del fallecido (D66, D67); la contratación de una capital puede atender a población de otros departamentos.
2. Es un análisis **ecológico**: los coeficientes describen departamentos, no personas ni causas (falacia ecológica). No se interpretan como causales.
3. Las tasas son **crudas**, sin estandarizar por edad: los departamentos con población más envejecida tienen tasas más altas de causas circulatorias, neoplasias y demás causas, y esas tasas se confunden con la estructura de edad y con la urbanización. Las proyecciones de población del DANE de 2020 en adelante se revisaron tras la pandemia.
4. **COVID-19:** no está separada en las listas 6/67 ni Colombia 105; solo se observa (`U07`, Cuadro 16) en 2020–2022 y en casi todos los departamentos. De 2023 en adelante queda dentro de «demás causas» y se fija en 0 en el panel; las defunciones por COVID-19 de los departamentos-año no observados también quedan en 0.
5. **Pocos departamentos** (33) para inferencia transversal: baja potencia; un resultado no significativo no es evidencia de ausencia de asociación. Con 31 departamentos en la comparación por forma de compra.
6. Los siete grupos de causa son excluyentes y sus tasas están correlacionadas (por eso el VIF eliminó a las neoplasias del modelo conjunto); los contratos de un mismo departamento y de una misma entidad no son independientes (por eso los errores agrupados y los valores p orientativos).
7. La contratación pública funeraria atiende sobre todo a población vulnerable y NN y a servicios de apoyo, no a la mortalidad total: no se espera proporcionalidad con las defunciones. «Otros accidentes y causas externas» incluye suicidios, caídas y eventos de intención no determinada.
8. Los departamentos de poca población (Guainía, Vaupés, Guaviare) tienen tasas de contratación altas por un denominador pequeño (pocos contratos); pesan mucho en las correlaciones de rango y en las razones de tasas, y los errores agrupados no corrigen eso por completo.
9. Los universos difieren levemente: `departamento_anual.csv` usa el mercado vigente (D66) y la participación de los grupos de HCPC usa los 4.992 contratos de D97 a D99 (D105).
