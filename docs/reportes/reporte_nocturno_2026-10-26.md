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
