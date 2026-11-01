# Reproducibilidad: cifras reportadas frente a cifras regeneradas (2026-11-01)

Se regeneró todo desde `data/processed` con los comandos documentados: `python -m src.modelos.mercado` (incluye el estimador principal, D93), `reevaluar_validacion` (D80), `evaluar_secop1_nuevos`, `robustez` y `robustez_revisada` (D71), `src.evaluacion.kappa` (D54, salida fuera de `docs/etiquetado`), `perfil_variables`, `patrones_base`, los scripts `patrones_*` de R y Python (D97) y los de D98 (`patrones_valor_cuantiles`, `patrones_valor_d98.R`, `patrones_polca.R`, `patrones_hcpc_bootstrap.R`, `patrones_estacionalidad_d98.R`), con los remuestreos completos (200 de bootstrap por modelo, 100 arranques de `poLCA`). Generado por `python -m src.modelos.tabla_reproducibilidad`; las cifras reportadas son las que citan las decisiones D54 y D71 a D98. Cifras monetarias en miles de millones de pesos de 2025.

## Resumen

- **117 de 127 cifras coinciden** (dentro de la precisión con que se reportaron) y **10 difieren**; las 10 diferencias tienen causa conocida (abajo).
- **Archivos regenerados frente a la copia previa** (comparación numérica, tolerancia 1e-9): `data/processed/resultados_secop` 42 de 43 CSV idénticos (difiere `sensibilidad_mixtos.csv`, que ahora incluye las 40 etiquetas de D91); CSV de `data/processed` 16 de 16 idénticos (`tabla_robustez.csv` solo difiere si se limitan los hilos, ver abajo); `resultados_secop/patrones` 29 de 33 idénticos (los otros cuatro difieren como máximo en 0,0044 en el modelo de clases latentes con covariables de fuente y año, por redondeo numérico de la optimización). Los remuestreos de bootstrap de D97 coinciden hasta el decimal 15.
- **Informes en `docs/resultados`:** `f4_mercado_publico.md`, `perfil_variables_secop.md`, `contraste_ins_minsalud.md`, `diagnostico_mixtos.md` y los gráficos del mercado se regeneran **idénticos byte a byte**. `coeficientes_tfidf.md`, `regla_servicios_profesionales.md` y `sensibilidad_mixtos.md` salen distintos porque se calcularon con las etiquetas de ese día (antes de V046 y de los lotes de D91); se conservan las versiones con las que se escribieron D90 y D92.

## Diferencias y su causa

| decisión | cifra | reportada | regenerada | diferencia | nota |
|---|---|---|---|---|---|
| D85 | TF-IDF con jerarquía (solo etiquetas humanas) | 230,7 | 230,6 | -0,052 | D96 pasó V046 a no_funerario: 230,65; D85 y D86 conservan 230,7 |
| D90 | caso C0 estimador | 244,5 | 245,8 | 1,276 | C0 y C1 son rangos para los 296 sin etiqueta; al regenerar entran las 40 etiquetas de D91 y los 296 pasan a 256 |
| D90 | caso C1 estimador | 260,2 | 260,1 | -0,075 | C0 y C1 son rangos para los 296 sin etiqueta; al regenerar entran las 40 etiquetas de D91 y los 296 pasan a 256 |
| D86 | contratos del mercado, jerarquía completa | 4.991,0 | 4.992,0 | 1,000 | D86, D89 y D93 citan 4.991 o 4.993; D96 lo dejó en 4.992 al pasar V046 a no_funerario |
| D89 | valor del mercado (jerarquía completa) | 230,7 | 230,6 | -0,052 | 230,65 redondea a 230,6 o 230,7 según la fuente de la cifra |
| D84 | contratos únicos con etiqueta humana | 542,0 | 732,0 | 190,000 | D84 se escribió con 400 + 60 + 30 + 2 + 50; D91 y D93 agregaron 40 + 150 |
| D86 | HHI nacional 2023 | 267,0 | 268,0 | 1,000 | D86 dice 267; la serie actual da 267,7 tras D96 |
| D86 | CR4 nacional 2023 | 26,5 | 26,6 | 0,100 | D96 cambió un contrato de 2023 |
| D92 | contratos del patrón con etiqueta humana funerario | 5,0 | 4,000 | -1,000 | V046 pasó a no_funerario (D92, 2026-10-29): hoy son 4 |
| D97 | arranques con el máximo, fuente y año con 5 clases | 3,000 | 2,000 | -1,000 | depende de los hilos y de la tolerancia: aparece 3 de 20 en la corrida original y 2 de 20 al regenerar con hilo único |

- **Efecto de V046 (D92, 2026-10-29):** pasar SSF-013 a `no_funerario` bajó el mercado de 4.993 a 4.992 contratos y de 230,7 a 230,6 (D96 lo anota en D93); D84, D85, D86 y D89 conservan las cifras del momento. También cambian el HHI y el CR4 de 2023 y el conteo de contratos del patrón de D92 con etiqueta `funerario` (5 a 4).
- **Etiquetas posteriores:** D84 cita 542 contratos con etiqueta humana (400, 60, 30, 2 y 50); los lotes de D91 y D93 suman 190 (40 y 150) y hoy son 732. El rango C0–C1 de D90 se calculó con 296 contratos humanitarios sin etiqueta; al regenerar quedan 256 y el rango es 245,8–260,1.
- **Hilos de XGBoost (D71):** la validación cruzada de XGBoost da F1 0,887 con los hilos por defecto (coincide con D71) y 0,890 si se fija `OMP_NUM_THREADS=1`; el resto de las cifras no depende de los hilos. El código no fija el número de hilos de la suma de gradientes; se documenta, no se corrige.
- **Arranques de clases latentes (D97):** el modelo de fuente y año con 5 clases repite su mejor log-verosimilitud en 3 de 20 arranques en la corrida original y en 2 de 20 al regenerar con hilo único, porque la tolerancia de 0,001 en la log-verosimilitud queda en el borde (la diferencia es de 0,001 en 52.639 de BIC). Ninguna conclusión de D97 cambia (ese modelo ya fallaba la independencia local).

## Código y pruebas

- No se encontró ningún error evidente de código. Se hizo un refactor sin cambio de comportamiento en `src/modelos/etiquetas_humanas.py` (`fusionar`, `aplicar_correccion_d92` y `corregir_validacion_d92` salen de `construir`, `lote` y `validacion_60`) para poder probar la jerarquía de D84 y la regla D92; las cifras regeneradas después del refactor coinciden con las anteriores.
- `tests/` (pytest, 24 pruebas): pesos N/n y reparto (`test_pesos.py`), jerarquía de etiquetas de D84 (`test_jerarquia_etiquetas.py`), estimador de diferencia con un caso de juguete calculado a mano (`test_estimador_diferencia.py`), guarda de Excel que no sobrescribe (`test_guarda_excel.py`) y regla D92 (`test_regla_d92.py`). Resultado: **24 pasan, 0 fallan** (`python -m pytest tests`).
- Revisión de las citas de D84 a D99 (`python -m src.modelos.verificar_decisiones`): 82 referencias a archivos y módulos y ningún hash de commit. Tres no se resuelven como archivo, sin que sea un error: `src.etl.anonimizar.anonimizar` (D91, es una función y su módulo existe), `/api/views/gt2j-8ykr.json` (D99, es una ruta de la API y no un archivo) y `desacuerdos_para_harold.xlsx` (D95, el archivo no está en `docs/etiquetado`; la guarda de `kappa` se activa solo si existe).

## Cifras que coinciden

| decisión | cifra | reportada | regenerada | diferencia |
|---|---|---|---|---|
| D93 | estimador principal TF-IDF | 254,0 | 254,0 | 0,025 |
| D93 | IC 95 % TF-IDF, límite inferior | 225,4 | 225,4 | -0,013 |
| D93 | IC 95 % TF-IDF, límite superior | 304,5 | 304,5 | -0,038 |
| D93 | estimador e5 | 221,9 | 221,9 | 0,035 |
| D93 | total del modelo sin corregir, TF-IDF | 262,9 | 262,9 | -0,014 |
| D85 | caso A (estimador con M214), TF-IDF | 198,4 | 198,4 | 0,028 |
| D85 | caso A, IC inferior | 79,2 | 79,2 | 0,012 |
| D85 | caso A, IC superior | 284,3 | 284,3 | -0,014 |
| D90 | caso B estimador | 243,9 | 243,9 | 0,010 |
| D96 | contratos del mercado (TF-IDF, jerarquía) | 4.992,0 | 4.992,0 | 0,000 |
| D96 | valor del mercado 2020–2025 | 230,6 | 230,6 | 0,048 |
| D96 | valor 2020 | 44,8 | 44,8 | -0,016 |
| D96 | valor 2021 | 41,9 | 41,9 | -0,027 |
| D96 | valor 2022 | 36,6 | 36,6 | -0,046 |
| D96 | valor 2023 | 34,2 | 34,2 | -0,004 |
| D96 | valor 2024 | 35,0 | 35,0 | 0,005 |
| D96 | valor 2025 | 38,2 | 38,2 | 0,036 |
| D91 | peso N/n de humanitarios, estrato A1 | 8,3 | 8,3 | 0,000 |
| D91 | peso N/n de humanitarios, estrato A2 | 4,600 | 4,600 | 0,000 |
| D91 | peso N/n del estrato D (150) | 175,6 | 175,6 | -0,020 |
| D91 | tamaño del marco del estrato D | 26.337 | 26.337 | 0,000 |
| D89 | mixtos, contratos | 111,0 | 111,0 | 0,000 |
| D89 | mixtos, valor | 157,4 | 157,4 | 0,026 |
| D93 | estrato D etiquetados | 208,0 | 208,0 | 0,000 |
| D93 | estrato D funerarios | 0,000 | 0,000 | 0,000 |
| D93 | cota de D (%) | 1,440 | 1,442 | 0,002 |
| D93 | contratos ocultos como máximo | 380,0 | 380,0 | 0,000 |
| D86 | HHI nacional 2020 | 240,0 | 240,0 | 0,000 |
| D86 | CR4 nacional 2020 | 24,1 | 24,1 | 0,000 |
| D86 | HHI nacional 2021 | 228,0 | 228,0 | 0,000 |
| D86 | CR4 nacional 2021 | 22,9 | 22,9 | 0,000 |
| D86 | HHI nacional 2022 | 292,0 | 292,0 | 0,000 |
| D86 | CR4 nacional 2022 | 25,2 | 25,2 | 0,000 |
| D86 | HHI nacional 2024 | 417,0 | 417,0 | 0,000 |
| D86 | CR4 nacional 2024 | 33,9 | 33,9 | 0,000 |
| D86 | HHI nacional 2025 | 651,0 | 651,0 | 0,000 |
| D86 | CR4 nacional 2025 | 33,3 | 33,3 | 0,000 |
| D86 | HHI departamental, mediana 2020 | 1.297,0 | 1.297,0 | 0,000 |
| D86 | departamentos con HHI > 2.500, 2020 | 4,000 | 4,000 | 0,000 |
| D86 | HHI departamental, mediana 2021 | 1.495,0 | 1.495,0 | 0,000 |
| D86 | departamentos con HHI > 2.500, 2021 | 6,0 | 6,0 | 0,000 |
| D86 | HHI departamental, mediana 2022 | 1.826,0 | 1.826,0 | 0,000 |
| D86 | departamentos con HHI > 2.500, 2022 | 4,000 | 4,000 | 0,000 |
| D86 | HHI departamental, mediana 2023 | 1.716,0 | 1.716,0 | 0,000 |
| D86 | departamentos con HHI > 2.500, 2023 | 5,0 | 5,0 | 0,000 |
| D86 | HHI departamental, mediana 2024 | 2.034,0 | 2.034,0 | 0,000 |
| D86 | departamentos con HHI > 2.500, 2024 | 7,0 | 7,0 | 0,000 |
| D86 | HHI departamental, mediana 2025 | 1.832,0 | 1.832,0 | 0,000 |
| D86 | departamentos con HHI > 2.500, 2025 | 9,0 | 9,0 | 0,000 |
| D80/D94 | F1 ponderado validación de 60, tfidf_logistica, original | 0,648 | 0,648 | 0,000 |
| D80/D94 | F1 ponderado validación de 60, tfidf_logistica, revisada | 0,970 | 0,970 | 0,000 |
| D80/D94 | F1 ponderado validación de 60, tfidf_logistica, revisada_d92 | 0,956 | 0,956 | -0,000 |
| D80/D94 | F1 ponderado validación de 60, e5_logistica, original | 0,596 | 0,596 | 0,000 |
| D80/D94 | F1 ponderado validación de 60, e5_logistica, revisada | 0,938 | 0,938 | -0,000 |
| D80/D94 | F1 ponderado validación de 60, e5_logistica, revisada_d92 | 0,952 | 0,952 | -0,000 |
| D80/D94 | F1 ponderado validación de 60, deepseek_flash, original | 0,606 | 0,606 | 0,000 |
| D80/D94 | F1 ponderado validación de 60, deepseek_flash, revisada | 0,950 | 0,950 | -0,000 |
| D80/D94 | F1 ponderado validación de 60, deepseek_flash, revisada_d92 | 0,963 | 0,963 | 0,000 |
| D94 | IC 95 % del F1 ponderado, tfidf_logistica, límite inferior | 0,908 | 0,908 | -0,000 |
| D94 | IC 95 % del F1 ponderado, tfidf_logistica, límite superior | 0,996 | 0,996 | -0,000 |
| D94 | IC 95 % del F1 ponderado, e5_logistica, límite inferior | 0,900 | 0,900 | 0,000 |
| D94 | IC 95 % del F1 ponderado, e5_logistica, límite superior | 0,996 | 0,996 | -0,000 |
| D94 | IC 95 % del F1 ponderado, deepseek_flash, límite inferior | 0,869 | 0,869 | -0,000 |
| D94 | IC 95 % del F1 ponderado, deepseek_flash, límite superior | 1,000 | 1,000 | 0,000 |
| D71 | F1 ponderado validación de 60, SVM, original | 0,662 | 0,662 | -0,000 |
| D71 | F1 ponderado validación de 60, SVM, revisada | 0,956 | 0,956 | -0,000 |
| D71 | F1 ponderado validación de 60, SVM, revisada_d92 | 0,942 | 0,942 | -0,000 |
| D71 | F1 ponderado validación de 60, XGBoost, original | 0,611 | 0,611 | -0,000 |
| D71 | F1 ponderado validación de 60, XGBoost, revisada | 0,955 | 0,955 | -0,000 |
| D71 | F1 ponderado validación de 60, XGBoost, revisada_d92 | 0,968 | 0,968 | 0,000 |
| D71 | F1 validación cruzada de 392, TF-IDF + regresión | 0,932 | 0,932 | 0,000 |
| D71 | F1 validación cruzada de 392, e5 | 0,946 | 0,946 | -0,000 |
| D71 | F1 validación cruzada de 392, DeepSeek | 0,979 | 0,979 | 0,000 |
| D71 | F1 validación cruzada de 392, SVM | 0,932 | 0,932 | 0,000 |
| D71 | F1 validación cruzada de 392, XGBoost | 0,887 | 0,887 | -0,000 |
| D54 | κ global de etiqueta (n = 400) | 0,683 | 0,683 | -0,000 |
| D86 | precisión TF-IDF en los 50 por valor | 0,900 | 0,900 | 0,000 |
| D86 | precisión por valor TF-IDF | 0,780 | 0,780 | 0,000 |
| D93 | F1 ponderado de TF-IDF en los 40 humanitarios | 0,976 | 0,976 | -0,000 |
| D92 | contratos con el patrón de servicios profesionales | 545,0 | 545,0 | 0,000 |
| D92 | los que TF-IDF clasifica funerario | 122,0 | 122,0 | 0,000 |
| D92 | sin etiqueta humana | 117,0 | 117,0 | 0,000 |
| D92 | valor sin etiqueta humana (miles de millones) | 3,900 | 3,924 | 0,024 |
| D96 | contratos con inhumacion_cremacion | 3.113,0 | 3.113,0 | 0,000 |
| D96 | contratos con traslado | 306,0 | 306,0 | 0,000 |
| D96 | contratos con ataudes_bienes | 1.674,0 | 1.674,0 | 0,000 |
| D96 | contratos con plan_exequial | 414,0 | 414,0 | 0,000 |
| D96 | contratos con operacion_cementerio | 61,0 | 61,0 | 0,000 |
| D96 | contratos con atencion_vulnerables_NN | 4.044,0 | 4.044,0 | 0,000 |
| D96 | contratos con ninguno_de_los_componentes | 170,0 | 170,0 | 0,000 |
| D96 | contratos de tipo de entidad alcaldia_municipio | 4.430,0 | 4.430,0 | 0,000 |
| D96 | contratos de tipo de entidad otra_entidad | 228,0 | 228,0 | 0,000 |
| D96 | contratos de tipo de entidad servicios_publicos_empresa | 119,0 | 119,0 | 0,000 |
| D96 | contratos de tipo de entidad gobernacion_departamento | 104,0 | 104,0 | 0,000 |
| D96 | contratos de tipo de entidad salud_hospital_ese | 85,0 | 85,0 | 0,000 |
| D96 | contratos de tipo de entidad otras | 26,0 | 26,0 | 0,000 |
| D97 | BIC del modelo de menor BIC (fuente y año, 7 clases) | 52.179 | 52.179 | -0,026 |
| D97 | BVR máximo, fuente y año con 7 clases | 36,5 | 36,5 | -0,011 |
| D97 | BVR máximo más bajo de los 18 modelos | 36,5 | 36,5 | -0,011 |
| D97 | Jaccard mínimo medio del bootstrap, modelo 3 con 7 clases | 0,700 | 0,699 | -0,001 |
| D97 | Jaccard mínimo medio del bootstrap, modelo 2 con 7 clases | 0,580 | 0,582 | 0,002 |
| D97 | Jaccard mínimo medio del bootstrap, modelo 1 con 6 clases | 0,760 | 0,759 | -0,001 |
| D97 | índice de Rand ajustado ACM + HCPC frente a la tipología de menor BIC | 0,520 | 0,520 | -0,000 |
| D97 | BIC del gamma log mixto (escala del valor) | 178.318 | 178.318 | 0,034 |
| D97 | ΔBIC del lineal mixto frente al gamma | 1.541,0 | 1.541,2 | 0,186 |
| D97 | exceso de curtosis de los residuos del gamma | 5,6 | 5,6 | 0,001 |
| D97 | BIC del modelo 3 de estacionalidad (72 meses) | 624,0 | 624,0 | -0,035 |
| D97 | Ljung-Box 12, modelo 2 (72 meses) | 0,020 | 0,020 | 0,000 |
| D98 | coeficientes que cambian de signo | 9,0 | 9,0 | 0,000 |
| D98 | coeficientes que cambian de significancia | 11,0 | 11,0 | 0,000 |
| D98 | significativos en los tres modelos | 3,000 | 3,000 | 0,000 |
| D98 | no significativos en ninguno | 7,0 | 7,0 | 0,000 |
| D98 | BVR máximo más bajo de los 27 modelos de poLCA | 9,4 | 9,4 | 0,039 |
| D98 | modelos de poLCA que cumplen BVR ≤ 10 y 5 arranques | 0,000 | 0,000 | 0,000 |
| D98 | grupos que sugiere HCPC | 11,0 | 11,0 | 0,000 |
| D98 | BIC del modelo 3b (71 meses) | 608,8 | 608,8 | 0,030 |
| D98 | Ljung-Box 12, modelo 3b | 0,432 | 0,432 | -0,000 |
