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
