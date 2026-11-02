# Hoja de ruta del agente (F6 y F7)

La secuencia que sigue el equipo, en hitos pequeños. **No empieces un hito sin la aprobación del anterior.** El contrato de qué se construye y cómo se evalúa está en `ESPECIFICACION.md`; las decisiones, en `docs/decisiones_agente.md`.

## Cómo se trabaja cada hito

1. Propón el plan del hito (archivos, funciones, pruebas) y espera el visto bueno antes de escribir código.
2. Implementa con sus pruebas. Toda decisión de método va a `docs/decisiones_agente.md` (A05, A06…), **en el mismo commit** que la implementa.
3. Al terminar: `pytest` en verde, `git status` limpio (sin `data/`, `.env`, claves ni trazas con datos) y `git push` de `agentes`.
4. **Punto de control: pedir revisión a Edward.** Envía el hash del último commit, la salida de `pytest` y las decisiones nuevas. Edward aprueba por escrito (mensaje o comentario en el pull request); anota la aprobación en la tabla de avance, al final de este archivo, en el commit siguiente.
5. Recién entonces empieza el hito siguiente. Si algo bloquea, no lo saltes: anótalo en `docs/agente/solicitudes.md` y avisa.

Formato de commit: `tipo(alcance): resumen`, con Qué, Por qué, Fuentes, Validación y Fase (D28).

## H1. Entorno verificado

- **Entregable:** entorno reproducible en cada máquina del equipo: `.venv` con `pip install -r requirements.txt`, Docker Desktop con WSL2 comprobado, Langfuse 3.225.15 en marcha (A04), `.env` completo y paquete de datos verificado. Script `python -m src.agentes.traza_prueba` que envía una traza mínima a Langfuse.
- **Pruebas que lo verifican:** `pytest` en verde; `python -m src.agentes.verificar_paquete` termina con `faltantes: 0 | con otra huella: 0`; `http://localhost:3000/api/public/health` responde; `traza_prueba` imprime el identificador de la traza y la traza aparece en la interfaz de Langfuse; `python -c "import langfuse; print(langfuse.__version__)"` muestra una versión 4.x. Una prueba (`tests/test_entorno.py`) comprueba que la versión instalada de `langfuse` es 4.x.
- **Commit esperado:** `chore(agentes): entorno verificado y traza de prueba` (script, prueba y, si hace falta, ajustes menores a `LEEME_EQUIPO.md`).
- **Punto de control:** pedir revisión a Edward con la captura de la traza de prueba en Langfuse (sin claves visibles).

## H2. Herramientas envueltas desde `src/etl`, sin LLM

- **Entregable:** `src/agentes/herramientas.py` con las funciones `extraer_pdf`, `validar`, `consultar`, `comparar_fuentes` y `registrar_incidencia`, que **importan** las funciones de `src/etl` (no las reescriben). Cada una devuelve estructuras simples (diccionarios) con los campos de cita: `cod_divipola`, `anio`, `valor_citado`, `archivo`, `pagina`, `conclusion`.
- **Pruebas:** `tests/test_herramientas.py`, con un PDF y una fila reales del paquete como casos y datos sintéticos para los bordes: llave `cod_divipola` como texto de 5 dígitos con cero inicial; `validar` rechaza un total que no cierra; `consultar` no escribe nada; ninguna herramienta escribe en `data/raw` (prueba que lo comprueba); `registrar_incidencia` escribe solo en `logs/` o `data/interim`.
- **Commit esperado:** `feat(agentes): herramientas envueltas desde src/etl`.
- **Punto de control:** pedir revisión a Edward con la lista de funciones de `src/etl` que se envolvieron y cualquier cambio que necesitarían en `src/etl` (va a `solicitudes.md`, no se hace).

## H3. Grafo completo sin LLM

- **Entregable:** `src/agentes/grafo.py` en LangGraph con orquestador → extracción → validar → incidencias → revisión humana (`interrupt`) → cargar, usando un **diagnóstico simulado** (función determinista) en lugar del LLM. `python -m src.agentes.grafo --tarea incidencias` corre de extremo a extremo con el simulado.
- **Pruebas** (`tests/test_grafo_reglas.py`): una prueba por regla de la sección 4 de la especificación, y cada una **debe fallar si se quita la regla** (comprobarlo quitándola a propósito una vez y anotarlo en el commit):
  1. máximo 3 reintentos de extracción por documento (`agente.max_reintentos`);
  2. no existe arista de `validar` a `cargar`; solo se llega a `cargar` tras `revision_humana` aprobada (la prueba inspecciona las aristas del grafo compilado);
  3. el `interrupt` se activa antes de cargar y una revisión rechazada no carga;
  4. el tope de costo (`agente.tope_costo_usd`, A02) detiene una corrida simulada y deja constancia;
  5. un diagnóstico sin los seis campos de cita se rechaza antes de la revisión humana;
  6. el agente no escribe en `data/raw`.
- **Commit esperado:** `feat(agentes): grafo LangGraph con reglas y diagnóstico simulado`.
- **Punto de control:** pedir revisión a Edward con el resultado de las pruebas y la confirmación de que cada una falla al quitar su regla.

## H4. Nodo de diagnóstico con DeepSeek sobre 20 incidencias

- **Entregable:** el nodo de incidencias con DeepSeek (cliente `openai`, temperatura 0), que recibe la evidencia de las herramientas y devuelve el diagnóstico con una categoría de A03. Guarda instrucción, versión del modelo y respuesta de cada llamada. Corrida sobre **20 incidencias** de `data/processed/incidencias.csv` elegidas con semilla 2026 (`numpy.random.default_rng(2026)` sobre las filas ordenadas).
- **Pruebas:** `verificar_anclaje()` (`src/evaluacion/anclaje.py`) sobre los 20 diagnósticos: impresos en el PDF verificados en el archivo, año y página; derivados recalculados desde los impresos citados (A03); todos con los seis campos y una categoría válida. Informe breve con el costo real de la corrida (debe ser menor que el tope de 2 USD) y el número de llamadas.
- **Commit esperado:** `feat(agentes): diagnóstico con DeepSeek y anclaje sobre 20 incidencias`.
- **Punto de control:** pedir revisión a Edward con los 20 diagnósticos (sin datos personales), el porcentaje de anclaje y el costo. No se avanza si el anclaje no es 100 % en los impresos.

## H5. Trazas completas, diagrama y F6 terminada

- **Entregable:** cada corrida deja su traza completa en Langfuse (`CallbackHandler`) y en `logs/*.jsonl` (instrucción, modelo, respuesta, costo); diagrama del grafo exportado a `docs/agente/` (imagen y fuente); lista de verificación de F6 de la sección 7 de la especificación marcada con evidencia; **pull request en borrador** de `agentes` hacia `main`.
- **Pruebas:** una corrida real produce una traza en Langfuse con las llamadas al modelo y los nodos; el JSONL contiene los tres campos exigidos; el diagrama se regenera con un comando; `pytest` en verde y `git status` limpio.
- **Commit esperado:** `feat(agentes): trazas completas, diagrama del grafo y cierre de F6`.
- **Punto de control:** pedir revisión a Edward sobre el pull request en borrador. **F6 se da por terminada solo con su aprobación.** No se integra a `main` en este hito.

## H6. Generador de las 60 fallas sembradas

- **Entregable:** `src/evaluacion/fallas_sembradas.py`, que parte de una **copia** del panel y siembra 60 fallas conocidas con semilla 2026: 20 duplicados, 15 dígitos cambiados, 10 municipios borrados, 10 coberturas forzadas al 100 % y 5 saltos falsos. Guarda la copia sembrada y la tabla de verdad (cuál falla, en qué `cod_divipola` y `anio`).
- **Pruebas:** `tests/test_fallas_sembradas.py`: dos ejecuciones producen archivos idénticos (misma huella SHA-256); los conteos por tipo son exactamente 20, 15, 10, 10 y 5; ninguna falla toca el panel original ni `data/raw`; cada falla de la tabla de verdad se puede localizar en la copia.
- **Commit esperado:** `feat(evaluacion): generador reproducible de 60 fallas sembradas`.
- **Punto de control:** pedir revisión a Edward con las dos huellas iguales y la tabla de verdad.

## H7. Corrida de evaluación, consistencia y libros de revisión humana

- **Entregable:** corrida del agente sobre la copia sembrada y sobre las incidencias reales: detección y falsas alarmas con intervalos de Wilson (definición de A03: las alarmas sobre incidencias reales se reportan aparte); anclaje; **consistencia** (cada incidencia real corrida 3 veces; si no coinciden, confianza baja); **libros de revisión humana a ciegas**: todos los casos de confianza baja (Harold) y 60 al azar de confianza alta (Natalia, semilla 2026), con las cinco categorías de A03. Los libros no se versionan.
- **Pruebas:** el cálculo de Wilson y del κ de Cohen tiene pruebas con valores conocidos; la consistencia marca confianza baja cuando dos corridas difieren; los libros no contienen la categoría del agente. Los umbrales son los de A01 y **no se cambian** al ver resultados.
- **Commit esperado:** `feat(evaluacion): corrida de evaluación, consistencia y libros de revisión humana`.
- **Punto de control:** pedir revisión a Edward antes de entregar los libros a quienes revisan, y de nuevo con los resultados y el κ cuando vuelvan etiquetados.

## H8. Informe de evaluación y pull request final

- **Entregable:** informe de evaluación en `docs/agente/` con cada cifra rastreable a su archivo y decisión (detección, falsas alarmas, anclaje, consistencia, κ, regla del tres si aplica, costo); si algún umbral no se cumple, se informa tal cual. Puntajes cargados en Langfuse. Pull request final (ya no en borrador) de `agentes` hacia `main`.
- **Pruebas:** lista de verificación de F7 de la sección 7 de la especificación marcada con evidencia; `pytest` en verde; las cifras del informe se regeneran con un comando.
- **Commit esperado:** `docs(agentes): informe de evaluación de F7`.
- **Punto de control:** pedir revisión a Edward. **Solo Edward integra a `main`** (D100), con `git merge --no-ff` y un mensaje que lista las A importantes.

## Tabla de avance

| Hito | Estado | Último commit | Aprobado por Edward (fecha) |
|---|---|---|---|
| H1 Entorno verificado | pendiente | | |
| H2 Herramientas sin LLM | pendiente | | |
| H3 Grafo sin LLM | pendiente | | |
| H4 Diagnóstico con DeepSeek | pendiente | | |
| H5 Trazas, diagrama y F6 | pendiente | | |
| H6 Fallas sembradas | pendiente | | |
| H7 Evaluación y libros | pendiente | | |
| H8 Informe y PR final | pendiente | | |
