# Reporte nocturno, 26 de octubre de 2026

Estado: en curso. Se actualiza al cerrar cada paso.

## Preparación
- `.claude/settings.local.json` creado con permisos para python del `.venv`, pip, schtasks y git (status, add, commit, push, log, diff, checkout). No se versiona.
- Hora de la máquina: Bogotá (UTC−5). Inicio 02:04.

## Paso 1 · Validación externa (rama modelos): terminado
- DeepSeek, TF-IDF y e5 evaluados en los 60 contratos de `validacion_edward.xlsx`.
- F1 ponderado de `funerario`: TF-IDF 0,648 (IC 0,389–0,970), e5 0,596 (0,352–0,916), DeepSeek 0,606 (0,357–0,943). Sin ponderar: 0,863, 0,766 y 0,840.
- Regla de D62: DeepSeek no tiene el F1 más alto, por lo que **no se aprueba la corrida completa**. `clase_final` = TF-IDF; se reporta el rango TF-IDF–e5.
- Costo real de DeepSeek en la validación: 0,0057 USD (60 llamadas, hora pico autorizada).
- Alerta: siete etiquetas de la validación no siguen D21 (V006, V054, V057, V027, V015, V046, V030); ver D63. V006 pesa el 46 % del peso de los funerarios y explica la sensibilidad ponderada baja. Con o sin V006, TF-IDF queda primero.
- Decisión: D63.

## Paso 2 · Programar la corrida de DeepSeek: no aplica
- D62 no aprobó la corrida (D63). No se creó `correr_deepseek_universo.py` ni se programó nada con schtasks. `clase_final` = TF-IDF.

## Paso 4 · Cerrar F3 (rama etl): terminado
- INS: 2024 (casos, población e incidencia 2022–2024) y 2025, extraídos con texto de pdfplumber (D64). 2024: 1.122 municipios; 2025: 1.109. Cruce con DIVIPOLA: exacto salvo 5 aproximados y 4 por tabla (2025); único sin código, Mapiripana (CD).
- Validación: 2024 cuadra con la tabla departamental salvo Chocó (−3) y el nacional (−3). 2025: suma municipal 199.028 = total impreso; la incidencia por entidad coincide en 35 de 38 (las otras tres tienen municipios no listados).
- Panel de agresiones (D65): mediana de agresiones por 1.000 perros 19,4 (2022), 23,5 (2023), 24,6 (2024), 27,4 (2025). 2022 y 2025 usan la población de perros de 2023 y 2024 (marcado; propuesta).
- `data/processed/incidencias.csv`: 1.721 filas (cobertura en 100: 1.221; dif_poblacion: 344; saltos de población: 50; identidad de tabla: 60; habitantes por perro fuera de rango: 32; totales que no cierran: 13).
- Decisiones: D64 y D65 (están en la rama `etl`; en `modelos` las decisiones siguen desde D66 para no repetir números). Rama `etl` subida a origin.
- Nota para el merge futuro: `docs/decisiones.md` tiene D55–D63 en `modelos` y D64–D65 en `etl`; al unir las ramas habrá un conflicto de texto al final del archivo, fácil de resolver conservando todo.

## Paso 3 · Mercado público (rama modelos): terminado como borrador
- Comando único: `python -m src.modelos.mercado` (recalcula universo, cruce, tablas, patrones, gráficos e informe desde `clase_final`, hoy TF-IDF). Informe: `docs/resultados/f4_mercado_publico.md`; 5 gráficos en `docs/resultados/graficos/`; tablas en `data/processed/resultados_secop/` (no se versionan).
- Cruce de ubicación (D66): 95,0 % de los contratos con municipio DIVIPOLA y 99,7 % con departamento (1.706 con la entidad en «No Definido»). 22 cruces aproximados; 20 en `docs/revision_f4/cruces_secop.xlsx`.
- Mercado funerario (TF-IDF, pesos de 2025, D67): 3.732 contratos y 230,1 miles de millones (189,6 corrientes). Por año: 48,6 (2020), 54,2, 36,5, 21,0, 24,0 y 45,8 (2025). La caída 2022→2023 es el fin de SECOP I; en SECOP II el número de contratos sube cada año (84 → 353). Sensibilidad: TF-IDF con mixto 380,5; e5 202,8; e5 con mixto 365,9.
- Por 100.000 habitantes lideran departamentos pequeños (Guainía 593 millones por 100.000 hab. al año, Vaupés, Amazonas); Bogotá reúne 126 contratos y 45,7 mm.
- Borrador (D68, D69): alcaldías 85 % de los contratos y 54 % del valor; mínima cuantía 76 % de los contratos y 33 % del valor; inhumación de NN o vulnerables 60 % de los contratos y 44 % del valor; HHI nacional de 290 (2020) a 1.120 (2025); 4 de 31 departamentos con HHI mayor de 2.500. 40 contratos para validar en `docs/revision_f4/subtipos.xlsx`.
- Cierre: CLAUDE.md con el estado de las fases; `modelos` y `etl` subidas a origin. No se hizo ningún merge a main.

## Cierre

**Costo real de DeepSeek en la validación:** 0,0057 USD (60 llamadas; 80.384 tokens de entrada con caché, 13.072 sin caché, 1.116 de salida). En total, con la evaluación de 392 casos (0,038 USD), el gasto de DeepSeek es de unos 0,044 USD.

**¿Quedó programada la corrida de DeepSeek?** No. D62 no la aprobó (D63); no se usó `schtasks` ni se creó `correr_deepseek_universo.py`.

**Decisiones tomadas sin ti (todas «propuesta, requiere confirmación de Edward»):**
- D65: en 2022 y 2025 la población de perros es la de 2023 y 2024 (marcado con `denominador_otro_anio`).
- D66: 10 alias manuales de municipios, ubicación por sede de la entidad y cruces aproximados.
- D67: pesos constantes de 2025 con el promedio del IPC de 2025 y valor inicial sin adiciones; `clase_final` = TF-IDF solo vive en `universo_mercado.parquet` (no se agregó a `clasificacion_universo.parquet`).
- D68: grupos de modalidad, reglas de tipo de entidad y reglas y prioridad de subtipos.
- D69: identificador de proveedor y medidas de concentración.
- Numeración: el pedido decía D61 para la validación externa, pero D61 ya existía; quedó como D62.
- Orden de ramas: las decisiones D64 y D65 están en `etl` y D55–D63 y D66–D69 en `modelos`; al unirlas habrá un conflicto de texto al final de `docs/decisiones.md`.

**Lo que falló:** nada falló tres veces. Hubo errores de escritura de scripts (escapes de saltos de línea) y de lógica (homónimos en el cruce, nombres partidos en el INS), todos corregidos. No fue posible leer la página oficial de precios de DeepSeek; las tarifas usadas son de una fuente secundaria (D58).

**Qué revisar al despertar (en este orden):**
1. D63: siete etiquetas de `validacion_edward.xlsx` que parecen no seguir D21 (V006, V054, V057, V027, V015, V046, V030). V006 pesa 3.293 y explica la sensibilidad ponderada baja. Decide si se corrigen; la regla de D62 ya quedó aplicada con las etiquetas tal como las entregaste.
2. `docs/revision_f4/cruces_secop.xlsx`: 20 cruces aproximados, columna «correcto».
3. `docs/revision_f4/subtipos.xlsx`: 40 contratos, columna «subtipo_correcto».
4. D65: ¿usar la población de perros de otro año en 2022 y 2025?
5. D66–D69: confirmar o corregir (alias, base de precios, grupos y reglas).
6. Decidir cuándo integrar `etl` y `modelos` en `main` y cómo resolver el conflicto de `docs/decisiones.md`.
7. Pendientes anteriores: parcheo del Excel de Edward en Excel cerrado, conteo de SECOP II el 28-oct (`python -m src.etl.verificar_secop2_count`).
