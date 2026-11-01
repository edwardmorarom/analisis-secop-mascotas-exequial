# Cierre de F4: mercado público funerario (SECOP 2020–2025)

Documento de una sola lectura para el informe final. Cada cifra lleva la decisión que la fija (`docs/decisiones.md`) y el archivo de donde sale (`data/processed/`, sin versionar). Las cifras de este documento se generan con `src/modelos/cierre_f4.py` a partir de los CSV de resultados y una prueba (`tests/test_cierre_f4.py`) verifica que coinciden. Valores monetarios en miles de millones de pesos de 2025. La rama `modelos` no está integrada en `main`: D99 fue aprobada por Edward el 2026-11-01 y no queda ninguna decisión de F4 abierta; falta solo el merge (ver «Decisiones pendientes»).

## 1. Cobertura y universo

| Cifra | Valor | Decisión | Archivo |
|---|---|---|---|
| Candidatos SECOP I y II, 2020–2025 | 39.870 | D73 (34.790 + 5.080 de SECOP I 2023–2025) | `data/interim/*_senales.parquet` |
| SECOP II (conjunto `jbjy-vk9h`) | 19.306 | D16, D17 | `data/raw/secop/` |
| SECOP I 2020–2022 (conjunto `f789-7hwg`, solo Celebrado, Liquidado, Terminado sin Liquidar; una fila por `uid`) | 15.484 | D42, D18 | `data/raw/secop/` |
| SECOP I 2023–2025 | 5.080 | D73 | `data/raw/secop/secop1_candidatos_2023_2025.jsonl` |
| No recuperados por la consulta (muestra de 100) | 0 funerarios de 100 (cota superior de 3 %) | D22 (nota del 2026-10-31) | `no_recuperados_100_maestra.parquet` |

Los candidatos son contratos que cumplen la consulta léxica o de códigos UNSPSC, no contratos funerarios. Los 100 no recuperados no tienen pesos y no corrigen el total: son evidencia de que la consulta no deja escapar funerarios de forma apreciable, no una medida del total.

## 2. Clasificación

Tres clases (`funerario`, `no_funerario`, `mixto`) más la marca `forense` (D20, D21). La referencia es la revisión humana doble; nunca un LLM. **Modelo elegido: TF-IDF con regresión logística** (D56, D59, D94).

| Cifra | Valor | Decisión | Archivo |
|---|---|---|---|
| F1 de `funerario`, validación cruzada de 392 casos: reglas / TF-IDF / e5 / DeepSeek | 0,870 / 0,932 (0,904–0,959) / 0,946 / 0,979 | D55, D60 | `tabla_comparativa_392.csv` |
| Validación externa de 60 contratos, F1 ponderado, TF-IDF / DeepSeek: etiquetas originales | 0,648 / 0,606 | D63 | `tabla_validacion_60_revisada.csv` |
| Ídem con las siete etiquetas revisadas | 0,970 / 0,950 | D80 | `tabla_validacion_60_revisada.csv` |
| Ídem con la regla D92 (V046 pasa a `no_funerario`) | 0,956 (0,908–0,996) / 0,963 (0,869–1,000) | D92, D94 | `tabla_validacion_60_revisada.csv` |
| Lote de 30 contratos de SECOP I 2023–2025: TF-IDF y e5 coinciden con la etiqueta humana | 30 de 30 (error máximo de 18,1 % por grupo con 95 % de confianza) | D80 | `evaluacion_secop1_nuevos.csv` |
| Acuerdo entre revisores (κ de Cohen, 400 contratos) | 0,683 (umbral fijado de 0,70: no se cumple) | D54 | `etiquetas_finales.parquet` |

**Por qué no otros modelos.** DeepSeek tuvo el F1 más alto en la validación cruzada (su instrucción y sus ocho ejemplos se formularon con esos mismos casos, de modo que la cifra es optimista) y, por la regla D59, solo desplaza a TF-IDF si su intervalo queda por encima del de TF-IDF; en la validación externa los intervalos se solapan en las tres versiones de etiquetas, así que gana el modelo más simple y auditable (D63, D94). Edward decidió no ejecutar la corrida completa de DeepSeek (D94); la regla de aprobación de D62, reducida al F1 puntual, es inestable con 60 casos (el orden cambia entre versiones de etiquetas por un solo contrato). e5 y la SVM y XGBoost de D71 no superan a TF-IDF. La etiqueta humana manda sobre la del modelo (D84).

## 3. Mercado

| Cifra | Valor | Decisión | Archivo |
|---|---|---|---|
| **Estimación principal** (estimador de diferencia por estratos, solo `funerario`), TF-IDF | **254,0** (IC 95 %: 225,4 a 304,5) | D93, D85, D89 | `estimador_principal.csv` |
| Misma estimación con e5 (sensibilidad) | 221,9 (215,4 a 228,2) | D93 | `estimador_principal.csv` |
| Caso A: estimador de D85 sin los lotes posteriores | 198,4 (79,2 a 284,3) | D85 | `estimador_diferencia.csv` |
| Total del modelo sin corregir (TF-IDF) | 262,9 | D93 | `estimador_principal.csv` |
| **Suma con etiquetas** (jerarquía completa de D84, sin `mixto`) | 230,6 en 4.992 contratos | D84, D89, D92, D96 | `mercado_con_y_sin_revision.csv` |
| `mixto`, aparte (fuera de la cifra principal) | 111 contratos, 157,4 | D89 | `mixtos_aparte.csv` |
| Cota del estrato D (sin señal): funerarios en los etiquetados | 0 de 208; proporción < 1,44 % (regla del tres), como máximo 381 contratos ocultos | D93 | `cota_estrato_d.csv` |

La estimación principal es mayor que la suma con etiquetas porque estima también los funerarios no revisados del universo (la suma con etiquetas es la parte que la revisión humana y el modelo ya clasifican). Los `mixto` y los contratos `forense` quedan fuera del tamaño de mercado (D21, D89). El total es una cota inferior respecto de los funerarios que la consulta original no recupera, que no se pueden cuantificar (D22).

**Serie anual** (TF-IDF, jerarquía completa, sin `mixto`; pesos constantes de 2025; D86, D67; `serie_anual.csv`):

| Año | Contratos | Valor corriente | Valor constante de 2025 |
|---|---|---|---|
| 2020 | 1.066 | 31,4 | 44,8 |
| 2021 | 973 | 30,3 | 41,9 |
| 2022 | 809 | 28,9 | 36,6 |
| 2023 | 765 | 30,4 | 34,2 |
| 2024 | 690 | 33,4 | 35,0 |
| 2025 | 689 | 38,2 | 38,2 |

## 4. Territorio y concentración

Valor por departamento (ubicación de la entidad compradora, cruce con DIVIPOLA, D66; `departamento_resumen.csv`): 4.985 de 4.992 contratos tienen departamento. Mayores valores: Bogotá, D.C. 58,3 (150 contratos); Antioquia 17,5 (446 contratos); Valle Del Cauca 16,3 (320 contratos); Bolívar 11,9 (213 contratos); Nariño 10,6 (416 contratos). La tasa por 100.000 habitantes (DANE, D66) se publica en el mismo archivo y en `municipio_resumen.csv`.

Concentración de proveedores (`proveedores_hhi_cr4_anual.csv`, `proveedores_hhi_departamento_resumen_anual.csv`; D69, D77):

| Año | Proveedores | HHI nacional | CR4 nacional (%) | HHI departamental, mediana | Departamentos con HHI > 2.500 |
|---|---|---|---|---|---|
| 2020 | 604 | 240 | 24,1 | 1.297 | 4 |
| 2021 | 532 | 228 | 22,9 | 1.495 | 6 |
| 2022 | 477 | 292 | 25,2 | 1.826 | 4 |
| 2023 | 471 | 268 | 26,6 | 1.716 | 5 |
| 2024 | 425 | 417 | 33,9 | 2.034 | 7 |
| 2025 | 438 | 651 | 33,3 | 1.832 | 9 |

El HHI nacional es bajo (menos de 700) y sube desde 2022; la mediana departamental es de 1.297 a 2.034, es decir, los mercados departamentales están bastante más concentrados que el nacional (D86, D77). D69 sigue marcada como propuesta.

## 5. Patrones de compra

Todo lo de esta sección es **exploratorio** (D98 se decidió después de ver D97) y D99 (aprobada por Edward el 2026-11-01) fija qué se reporta. Universo: 4.992 contratos `funerario` (D84). Informe: `docs/resultados/patrones_compra.md`.

**Valor** (log del valor constante de 2025; solo se reportan los tres efectos significativos en los tres modelos: regresión por cuantiles en la mediana, lineal mixto y gamma mixto; D99):

| Efecto | Mediana (cuantiles) | Lineal mixto | Gamma mixto |
|---|---|---|---|
| Selección abreviada frente a mínima cuantía | 1,603 | 1,187 | 1,256 |
| Gobernación o departamento frente a alcaldía o municipio | 0,663 | 0,916 | 0,872 |
| Fuente SECOP II frente a SECOP I | 0,477 | 0,238 | 0,231 |

Los otros 18 coeficientes son no concluyentes. Archivos: `valor_d98_cuantiles.csv`, `valor_d98_lmm_gamma.csv`. La regresión usa 4.985 contratos (se excluyen 7 con valor 0, D99).

**Tipología.** No hay tipología latente que cumpla independencia local: ninguno de los 18 modelos de D97 (residuo bivariado máximo de 36,5 a 535) ni de los 27 de `poLCA` de D98 (mínimo 9,4) cumple a la vez BVR ≤ 10 y mejor ajuste en al menos 5 de 100 arranques (0 cumplen; `lca_comparacion.csv`, `polca_comparacion.csv`). Como descripción se reportan los grupos de ACM + HCPC con Jaccard medio ≥ 0,75 y al menos 1 % de los contratos (criterio de la enmienda de D99): 8 de 11, con 4.910 contratos (98,4 %): grupo 1 (1.278, Jaccard 0,96); grupo 2 (280, Jaccard 0,87); grupo 3 (253, Jaccard 0,87); grupo 4 (362, Jaccard 0,91); grupo 5 (2.314, Jaccard 0,96); grupo 7 (206, Jaccard 0,77); grupo 9 (121, Jaccard 0,91); grupo 10 (96, Jaccard 0,93). Sus categorías características (prueba v) están en `patrones_compra.md` y `hcpc_d98_vtest.csv`; no se les da interpretación de negocio.

**Estacionalidad: resultado en cuanto a los meses de mayor contratación; la forma exacta del modelo es una limitación (D99, ajuste de Edward).** Modelos de binomial negativa sobre el conteo mensual de contratos firmados. Con la serie de fallecidos de COVID-19 del INS filtrada por estado «Fallecido» (`gt2j-8ykr`, 143.125 fallecidos de marzo de 2020 a enero de 2024; sin filtrar eran 184.393; los 25 meses sin registro son faltantes, no ceros): la señal estacional se mantiene en todos los modelos (Wald con Newey-West p < 0,0001; amplitud de 12 meses de 0,43 a 0,55); pasan los supuestos los modelos 2, 2c, 2e; el de menor BIC entre ellos es el 2e (420,1). **Resultado:** los meses de mayor contratación del año son febrero, marzo y abril, con ambas series (Wald con Newey-West p < 0,0001 en las 12 especificaciones con la serie filtrada). **Limitación:** el 2e y el 2c empatan en BIC y los modelos con armónicos no pasan el Ljung-Box. La serie filtrada es coherente con la cifra oficial (OPS, Informe de situación 293, 14 de marzo de 2023: 142.639 muertes al 8 de marzo de 2023; la serie suma 142.651 hasta febrero de 2023). Archivos: `estacionalidad_covid_modelos.csv`, `perfil_mensual_2e.csv`; decisiones D97, D98, D99.

## 6. Tratamiento de faltantes

| Qué faltaba | Qué se hizo | Decisión |
|---|---|---|
| Contratos con valor 0 (valor no positivo) | 7 contratos: excluidos de la regresión del log del valor; incluidos en los totales (suman 0) | D99 (enmienda) |
| `forense` de Harold sin dato en 59 filas | Se completó con 0 (imputación); no afecta el mercado; todo conteo de `forense = 1` es un mínimo | D54 (nota) |
| Meses sin registro de muertes por COVID (enero y febrero de 2020; desde febrero de 2024) | Faltantes, no ceros: los modelos con COVID se ajustan a los 47 meses con registro | D99 (enmienda) |
| Contratos con ubicación «No Definido» o sin municipio | Se conservan en las cifras nacionales y por año; sin departamento quedan 7 contratos del mercado | D66 |
| Población de perros de MinSalud sin municipios en 2022 y 2025 | El denominador de las agresiones del INS usa la población de otro año (2023 y 2024), marcado con `denominador_otro_anio = 1` | D65, D88 |
| Población de animales de MinSalud reproducible con una razón entera (imputada) | Se detecta y se marca (`imputado`/`posible_medido`: 597 y 524 en perros; 784 y 337 en gatos), no se excluye; los indicadores de densidad solo se interpretan en `posible_medido` | D43, D49, D29 |
| Contratos no recuperados por la consulta | Sin pesos ni corrección del total; 0 funerarios en 100 etiquetados | D22 |
| Etiqueta humana ausente en la mayoría de los contratos | Se aplica el modelo; la etiqueta humana manda donde existe (jerarquía); estimador de diferencia para la corrección | D84, D93 |

## 7. Limitaciones

- El κ entre revisores (0,683) no alcanza el umbral fijado de 0,70; el desempate de Harold no fue ciego y el `forense` de Natalia no es utilizable (D54).
- El intervalo de la estimación principal (225,4 a 304,5) es ancho: depende del estrato D (sin señal), donde se etiquetó una muestra pequeña, y de los 50 contratos de mayor valor revisados uno por uno (D90, D93).
- La validación externa tiene 60 casos y un estrato D con casi todo el peso; el F1 puntual cambia con una sola etiqueta (D94).
- DeepSeek no se evaluó sobre el universo (D94); su F1 en la muestra es optimista (D60).
- El total es una cota inferior respecto de lo que la consulta no recupera (D22) y excluye `mixto` y `forense` (D89).
- La ubicación es la de la entidad compradora, no la de ejecución (D66); las entidades nacionales con sede en Bogotá se ubican en Bogotá aunque el servicio se ejecute en otro lugar.
- SECOP I y SECOP II no son equivalentes (SECOP I solo con contrato firmado y estado de ejecución, D42); el efecto de la fuente aparece como uno de los tres efectos robustos de valor.
- Los patrones de compra son exploratorios; ninguna tipología latente cumple los supuestos; de la estacionalidad se reportan los meses de mayor contratación, pero la forma exacta del modelo es una limitación (empate de BIC entre 2e y 2c; los modelos con armónicos no pasan el Ljung-Box).
- La cifra de XGBoost de D71 depende del número de hilos (0,887 original; 0,890 reproducible con un hilo).
- Mortalidad de mascotas: vacío documentado; no se estiman escenarios de defunciones (decisión cerrada).

## 8. Decisiones pendientes de Edward

- Ninguna decisión de F4 queda abierta: D99 aprobada (2026-11-01); D68, D69, D74, D83, D95 y D96 resueltas (2026-11-01); el mes de firma se usa sin validación humana porque es la fecha original de SECOP (D68).
- Integrar `modelos` en `main` con `git merge --no-ff` y un mensaje que resuma la fase y liste sus decisiones (D55–D99).
