# Especificación del agente (F6) y su evaluación (F7)

Contrato que debe seguir cualquier persona o IA que trabaje en la rama `agentes`. Si algo de este documento choca con lo que parece conveniente, no se ajusta por cuenta propia: se registra una enmienda en `docs/decisiones_agente.md` (A-números) y se avisa a Edward. Las decisiones de origen son D25, D26, D27 y D100 de `docs/decisiones.md`; los umbrales y la arquitectura quedan fijados en A01 y el tope de costo en A02.

## 1. Intención

El agente automatiza lo que en F2 y F3 se hizo a mano y con supervisión:

1. extraer los PDF de MinSalud (vacunación antirrábica) y del INS (agresiones por animales potencialmente transmisores de rabia);
2. validar lo extraído contra los totales impresos en los mismos PDF y con las identidades de las tablas;
3. diagnosticar las incidencias del panel con evidencia verificable (municipio, año, valor, archivo y página).

**El agente no decide el método ni corrige datos por su cuenta: propone, y un humano aprueba.** Nada se carga a `data/processed` sin pasar por la validación en código y por la revisión humana.

## 2. Alcance

**Entradas** (lectura):

| Entrada | Contenido |
|---|---|
| `data/processed/incidencias.csv` | 1.721 incidencias marcadas por reglas deterministas (`cod_divipola`, `anio`, `regla`, `valor_citado`, `archivo`, `pagina`, `conclusion`). Reglas: `cobertura_100` (1.221), `dif_poblacion` (344), `identidad_tabla_no_cierra` (60), `salto_poblacion` (50), `habitantes_por_perro_fuera_de_rango` (32), `total_departamental_no_cierra` (8), `total_ins_no_cierra` (5), `municipio_sin_codigo` (1) |
| `data/processed/panel_minsalud_municipal.parquet` | panel municipal 2014–2025 de MinSalud |
| `data/processed/panel_agresiones.parquet` | agresiones del INS por municipio, 2022–2025 |
| `data/raw/minsalud/*.pdf`, `data/raw/ins/*.pdf` | PDF de origen (solo lectura) |

También se usan `data/raw/dane` (DIVIPOLA y proyecciones) y los conteos del SIVIGILA en `data/raw/ins` para validar.

**Salida:** diagnósticos propuestos (JSONL en `logs/`), tablas de revisión humana y, solo tras la aprobación, la carga a `data/processed` con la misma estructura que ya tiene el panel.

**Fuera de alcance:** SECOP, el mercado público y todo lo de `src/modelos` (F4 está cerrada, etiqueta `f4-cerrada`), las capas de Places, Trends, Meta y Cámaras.

## 3. Arquitectura (D25, D26)

```
orquestador → extraccion → validar (código, sin LLM) ─falla y < 3 intentos→ extraccion
                                       └─ pasa → incidencias → revision_humana (interrupt) → cargar
```

- Grafo en **LangGraph** (`src/agentes/grafo.py`). Un grafo explícito obliga a pasar por la validación; el agente no puede saltársela.
- **Extracción en cascada (D25):** `pdfplumber` → `camelot` (con Ghostscript) → LLM como último recurso. Cada resultado se valida contra los totales impresos.
- **Validación en código:** funciones deterministas, sin LLM, que comprueban totales, identidades de las tablas, duplicados, llaves (`cod_divipola` de 5 dígitos como texto con cero inicial) y coincidencia con DIVIPOLA.
- **Incidencias (diagnóstico):** el LLM propone una explicación de cada incidencia a partir de la evidencia que le entregan las herramientas; nunca de memoria.
- **Revisión humana:** `interrupt` de LangGraph antes de cargar; la persona aprueba, rechaza o corrige.
- **Herramientas = los scripts que ya existen en `src/etl`, que se importan y no se reescriben:** `extraer_minsalud` (y las variantes de 2014, 2016 y 2017), `extraer_ins`, `panel_minsalud`, `panel_agresiones`, `detectar_imputacion`, `incidencias`, `revisar_cruces`, `comun` y `manifiesto`. Si falta una función, se envuelve en `src/agentes/herramientas.py`; si hay que cambiar `src/etl`, se pide en `docs/agente/solicitudes.md`.
- Herramientas expuestas al grafo (nombres): `descargar`, `extraer_pdf`, `validar`, `consultar`, `comparar_fuentes`, `registrar_incidencia`.

## 4. Reglas que impone el grafo (no el prompt)

1. **Máximo 3 reintentos** de extracción por documento (`agente.max_reintentos` de `config.yaml`).
2. **No se carga nada si la validación falla.** La arista `validar → cargar` no existe; solo se llega a `cargar` tras `revision_humana` aprobada.
3. **Tope de costo por corrida:** `agente.tope_costo_usd` de `config.yaml` (por defecto 2 USD, A02). Al superarlo, el grafo se detiene y deja constancia.
4. **Cada diagnóstico cita** `cod_divipola`, `anio`, `valor_citado`, `archivo`, `pagina` y `conclusion`. Un diagnóstico sin estos campos se rechaza antes de llegar a la revisión humana.
5. **El agente no escribe en `data/raw`, no modifica `src/etl` ni `src/modelos`.** Solo escribe en `data/interim`, `data/processed` (tras aprobación), `logs/` y en las rutas de salida propias.
6. **Temperatura 0**, y se guardan la instrucción, la versión del modelo y la respuesta de cada llamada.
7. **Sin datos personales** en entradas, salidas ni trazas.

## 5. Modelo y trazas

- **DeepSeek** por API con el cliente `openai` (`llm.base_url`, `llm.modelo` de `config.yaml`); `DEEPSEEK_API_KEY` en `.env`. Ollama solo para pruebas locales.
- **Langfuse** local con Docker; al invocar el grafo: `config={"callbacks": [CallbackHandler()]}`. Los puntajes de la evaluación se cargan en Langfuse.
- **Respaldo:** trazas JSONL en `logs/*.jsonl` (no se versionan; si tienen datos, no se suben).
- Exportar el diagrama del grafo para el documento final.

## 6. Evaluación F7 (D27)

Los umbrales se fijan **antes de construir** y están en `config.yaml` (`evaluacion.umbrales`):

| Medida | Umbral |
|---|---|
| Detección (sensibilidad) | ≥ 90 % |
| Falsas alarmas | ≤ 10 % |
| κ de Cohen entre agente y revisión humana | ≥ 0,70 |
| Anclaje | 100 % |

**Fallas sembradas.** Una copia del panel con **60 fallas** conocidas (semilla 2026): 20 duplicados, 15 dígitos cambiados, 10 municipios borrados, 10 coberturas forzadas al 100 % y 5 saltos falsos. Se mide cuántas detecta el agente y cuántas alarmas son falsas, con **intervalos de Wilson**. Código en `src/evaluacion/fallas_sembradas.py`.

**Anclaje.** `verificar_anclaje()` (`src/evaluacion/anclaje.py`) comprueba por código que el `valor_citado` exista en el `archivo`, el año y la `pagina` indicados. Debe dar 100 %.

**Consistencia.** Cada incidencia real se corre **3 veces**; si los resultados no coinciden, la confianza es baja.

**Revisión humana.** Todos los casos de confianza baja (Harold) y **60 al azar de confianza alta** (Natalia, semilla 2026). κ de Cohen entre el agente y la revisión; si hay 0 errores en 60, el error es menor que 5 % (regla del tres).

## 7. Definición de terminado

**F6 está terminada cuando:**

- [ ] el grafo corre de extremo a extremo con `python -m src.agentes.grafo --tarea incidencias`;
- [ ] las reglas de la sección 4 están en el grafo y cada una tiene una prueba que falla si se quita;
- [ ] no existe ninguna ruta de `validar` a `cargar` que no pase por `revision_humana`;
- [ ] el tope de costo detiene una corrida simulada;
- [ ] cada diagnóstico tiene los seis campos y pasa `verificar_anclaje()`;
- [ ] las trazas llegan a Langfuse y a `logs/*.jsonl`, con instrucción, modelo y respuesta;
- [ ] el diagrama del grafo está exportado a `docs/agente/`;
- [ ] `pytest` pasa y `git status` está limpio (sin `data/`, `.env`, claves ni trazas con datos en el índice);
- [ ] cada decisión de método está en `docs/decisiones_agente.md`, en el mismo commit que la implementa.

**F7 está terminada cuando:**

- [ ] los umbrales están registrados en `decisiones_agente.md` con fecha anterior a la primera evaluación;
- [ ] la copia del panel con las 60 fallas sembradas existe y es reproducible (semilla 2026);
- [ ] detección ≥ 90 % y falsas alarmas ≤ 10 %, con intervalos de Wilson;
- [ ] anclaje de 100 %;
- [ ] consistencia entre 3 corridas medida y los casos de confianza baja listados;
- [ ] revisión humana hecha (todos los de confianza baja y 60 al azar de confianza alta), con κ ≥ 0,70 y la regla del tres;
- [ ] los puntajes están en Langfuse;
- [ ] hay un informe de evaluación en `docs/agente/` con cada cifra rastreable a su archivo y decisión;
- [ ] si algún umbral no se cumple, se informa tal cual y no se cambia el umbral.

## 8. Lo que no se hace

- Cambiar los umbrales después de ver resultados **sin registrar una enmienda** en `decisiones_agente.md` (y, aun así, no para que "pase").
- Usar SECOP, el mercado público o cualquier dato de `src/modelos`.
- Subir `data/`, `.env`, claves, trazas con datos, ni libros de etiquetado al repositorio; pegar claves en el chat.
- Escribir en `data/raw` o modificar `src/etl`, `src/modelos` o las ramas `etl` y `modelos`.
- Hacer merge a `main`: el agente entra por pull request revisado por Edward (D100).
- Que el LLM decida si un dato se corrige o se carga: eso lo hace una persona.
