# Instrucciones para trabajar en `src/agentes` (rama `agentes`)

Claude Code carga este archivo al trabajar en esta carpeta. Se aplica además del `CLAUDE.md` de la raíz.

## Antes de escribir código

1. Lee, en este orden: `docs/agente/ESPECIFICACION.md`, el `CLAUDE.md` de la raíz y `docs/decisiones_agente.md`.
2. Lee `docs/agente/HOJA_DE_RUTA.md`: **sigue la hoja de ruta; no empieces un hito sin aprobación del anterior.**
3. Propón el plan del hito y espera la aprobación de la persona que te lo pide antes de escribir código. Al terminar el hito, pide revisión a Edward (punto de control) antes de pasar al siguiente.

## Reglas

- **Decisiones.** Toda decisión de método (herramienta, filtro, umbral, estructura, modelo, parámetro, regla) va a `docs/decisiones_agente.md` con el mismo formato de `decisiones.md`: **Decisión, Por qué** (con evidencia: cifras, archivo, commit), **Descartado, Sustento y Estado**, y **en el mismo commit que la implementa**. Los códigos son A01, A02… Nunca se borra una decisión: se marca como reemplazada.
- **Umbrales.** Se registran antes de evaluar. Cambiarlos después de ver resultados exige una enmienda registrada.
- **Commits.** Formato de D28: `tipo(alcance): resumen`, con Qué, Por qué, Fuentes, Validación y Fase. Tipos: `feat`, `fix`, `docs`, `test`, `chore`.
- **Lo que no se toca.** `data/raw`, `src/etl`, `src/modelos`, las ramas `etl`, `modelos` y `main`. Si necesitas un cambio en `src/etl` o en los datos, **no lo hagas**: anótalo en `docs/agente/solicitudes.md` (fecha, qué se necesita, por qué, evidencia) para Edward.
- **Herramientas.** Se importan las funciones de `src/etl`; no se copian ni se reescriben.
- **Grafo.** Las reglas de la sección 4 de la especificación (reintentos, sin carga si falla la validación, tope de costo, citas obligatorias, no escribir en `data/raw`) se implementan en el grafo y se prueban; no se delegan al prompt.
- **LLM.** Temperatura 0; guardar instrucción, versión del modelo y respuesta de cada llamada.
- **Datos.** Usar muestras o resúmenes generados con código; no leer archivos de datos completos en el contexto. No guardar datos personales.
- **Llaves.** `cod_divipola` es texto de 5 dígitos con cero inicial (leer con `dtype=str`); nunca unir por nombre de municipio.
- **Claves.** Nunca pegues claves en el chat ni las escribas en archivos versionados; viven en `.env`.
- **Cierre de sesión.** Corre `pytest`, verifica `git status` (sin `data/`, `.env`, claves ni trazas con datos) y haz **push de la rama `agentes`** al terminar cada sesión.
- **Integración.** No hagas merge a `main`: el agente entra por pull request revisado por Edward (D100).
