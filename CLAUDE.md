> Si trabajas en la rama agentes, lee primero docs/agente/ESPECIFICACION.md, src/agentes/CLAUDE.md y docs/decisiones_agente.md, y propón un plan antes de escribir código.

# CLAUDE.md — Mercado funerario (SECOP) y Previsión Exequial de Mascotas

Proyecto de consultoría USTA. Equipo: Edward Mora (código), Natalia Carrero y Harold Funeme (revisión, fuentes manuales). Plazo: 10 días hábiles desde el 20 oct 2026. Sistema operativo del equipo: Windows (PowerShell).

## Qué se construye

1. **Mercado público funerario.** Delimitar los contratos funerarios en SECOP 2020–2025 y caracterizar tamaño, evolución, distribución territorial, **patrones de compra** (tipo de entidad, tipo de servicio, modalidad, estacionalidad) y estructura de compradores y proveedores, con errores de clasificación medidos.
2. **Previsión exequial de mascotas.** Panel municipal 2014–2025 de perros y gatos (población estimada y vacunación, MinSalud), armonizado con DANE, contrastado con agresiones del INS, más oferta funeraria observable y disposición pública de animales muertos (SECOP).
3. **Agente (entregable del curso).** Orquestador + subagente de extracción + subagente de incidencias, con evaluación cuantitativa.

## Decisiones cerradas

- Mortalidad de mascotas: **vacío documentado**. No se estiman escenarios de defunciones. El piloto MSPS-OPS 2012 se cita como único antecedente.
- Sin derechos de petición ni redes sociales con datos personales. Solo fuentes públicas.
- Clasificación SECOP en tres clases: `funerario`, `no_funerario`, `mixto`. La referencia de validación es la revisión humana doble, nunca un LLM.
- Un solo repositorio. Ramas por línea de trabajo: `etl`, `modelos`, `agentes`.
- Agente con **LangGraph**; trazas y puntajes en **Langfuse** local (Docker). Modelo: **DeepSeek** por API (cliente `openai`). Ollama solo para pruebas locales.
- Google Trends: solo «cremación de mascotas» y «funeraria de mascotas». «Cementerio de mascotas» se excluye (contaminado por la película *Pet Sematary*). Trends se usa como variable descriptiva (interés detectable sí/no), no como mapa nacional: solo 9 y 11 departamentos tienen dato.
- Meta: la Biblioteca de Anuncios no informa alcance ni público de anuncios comerciales en Colombia. La capa es «presencia en Facebook + anuncios activos» (lado de la oferta), levantada a mano por Harold.
- Lado del consumidor: solo señales agregadas de visibilidad digital (búsquedas en Trends, seguidores, número de reseñas en Google, precios publicados). No miden compras; la mortalidad y el uso real de servicios siguen siendo vacío declarado.
- SECOP I 2020–2022 **incluido** (conjunto `f789-7hwg`): solo procesos con contrato firmado y estado Celebrado, Liquidado o Terminado sin Liquidar; una fila por `uid`.

## Estructura

```
config.yaml          rutas y parámetros
requirements.txt
.env                 DEEPSEEK_API_KEY, GOOGLE_MAPS_API_KEY, SOCRATA_APP_TOKEN, SEUDONIMO_SALT, LANGFUSE_*  (no se sube)
.gitignore           incluye data/ y .env
data/                no se sube
  raw/               crudos tal como se descargan + manifiesto.csv (solo lectura)
  interim/           tablas extraídas (Parquet)
  processed/         panel y bases finales (Parquet + CSV)
src/etl/             descargar_*, extraer_*, armonizar, validar
src/modelos/         clasificadores SECOP, indicadores, tipología
src/agentes/         grafo LangGraph, nodos, herramientas
src/evaluacion/      fallas sembradas, anclaje, consistencia, métricas
app/                 tablero Streamlit
logs/                trazas JSONL de respaldo
docs/                documento y anexos
```

## Crudos ya descargados a mano (no tocar)

```
data/raw/minsalud/   minsalud_vacunacion_{2014,2016,2017,2019,2023,2024,2025}.pdf
                     minsalud_piloto_dinamicas_2012.pdf
data/raw/ins/        ins_agresiones_{2023,2024,2025}.pdf
data/raw/dane/       dane_proyecciones_municipales_2005_2017.xlsx
                     dane_proyecciones_municipales_2018_2042.xlsx
                     dane_divipola.csv      (UTF-8, separador «,», 1.122 municipios, códigos con cero inicial)
                     dane_ipc_indices.xlsx  (IPC total, serie de empalme 2003–2026, base dic-2018 = 100; hoja IndicesIPC, encabezado en la fila 9, meses en filas y años en columnas)
data/raw/dane/mgn/   MGN_ADM_MPIO_GRAFICO.{shp,shx,dbf,prj,cpg,sbn,sbx,shp.xml} + dane_mgn2024_diccionario.xlsx
data/raw/unspsc/     unspsc_clasificador.csv (cp1252, separador «;», 3 líneas de nota antes del encabezado, 49.022 códigos)
                     unspsc_codigos_cce.pdf  (3 códigos nacionales; ninguno funerario)
data/raw/trends/     trends_{cremacion,funeraria}_mascotas_{subregion,tiempo}_20261020.csv
```

**Códigos UNSPSC funerarios** (en SECOP vienen como `V1.XXXXXXXX` en `codigo_de_categoria_principal`):
- Clase `851715` Servicios funerarios y asociados (familia `8517`; excluir la clase `851716`, hospicios).
- Familia `4813` Equipo y materiales funerarios (ataúdes, urnas, mortajas, lápidas).
- Clase `422621` Equipo y suministros funerarios.
- Clases `422615`–`422620` (autopsia, morgue, transporte de cadáveres, embalsamar): marcar como `forense`; revisar como posible `mixto`.

Agregar a la consulta de SECOP: `OR codigo_de_categoria_principal LIKE '%851715%' OR codigo_de_categoria_principal LIKE '%4813%' OR codigo_de_categoria_principal LIKE '%422621%'`.

Lo que descarga Claude Code: `data/raw/secop/`, `data/raw/camaras/`, `data/raw/places/`.

Lo que llena Harold a mano: `data/raw/meta_ads/facebook_prestadores_20261021.xlsx` (versión final pendiente). Una fila por prestador: nombre, tipo de fuente, enlace, ciudad sede, cobertura declarada, seguidores (número), servicios mencionados, dónde se verificaron, fecha de consulta, término de búsqueda, anuncios activos (sí/no), fecha de inicio del anuncio, precios publicados por servicio. Solo empresas.

## Convenciones

- Formatos: Parquet para tablas internas, CSV para compartir, JSONL para trazas y salidas de LLM.
- Llave de unión: `cod_divipola` (5 dígitos, **texto**, con cero inicial) + `anio`. Nunca unir por nombre de municipio. Leer DIVIPOLA con `dtype=str`.
- `data/raw` es de solo lectura. El manifiesto registra archivo, URL de origen, fecha, tamaño y SHA-256.
- Cada valor del panel conserva `fuente`, `anio_fuente` y `pagina` cuando viene de un PDF.
- LLM: temperatura 0; guardar instrucción, versión del modelo y respuesta de cada llamada.
- Semillas fijas para muestreos (`seed: 2026`).
- **Registro de decisiones.** Toda decisión de método (fuente, filtro, estructura de datos, modelo, parámetro, regla de etiquetado) se registra en `docs/decisiones.md` con **Decisión, Por qué** (con evidencia: cifras, archivo, commit), **Descartado, Sustento y Estado**, en el mismo commit que la implementa. Nunca se borra una decisión: se marca como reemplazada. Es el registro oficial; si este archivo y `decisiones.md` difieren, manda `decisiones.md`.
- **Control de versiones.** Al final de cada fase o sesión de trabajo se verifica `git status` y se hace push de la rama activa. `main` solo recibe fases cerradas, con `git merge --no-ff` y un mensaje que resume la fase y lista sus decisiones (D-números). Antes de subir se comprueba que no haya `data/`, `.env`, claves ni libros de etiquetado en el índice ni en el historial. **Rama `agentes` (D100):** el agente (F6–F7) se desarrolla en esa rama con su propio registro, `docs/decisiones_agente.md` (códigos A01, A02…), para no chocar con la numeración D de `decisiones.md`; `main` solo lo recibe por pull request revisado por Edward, y al integrarlo `decisiones.md` cita las A más importantes.
- **Nombres.** No usar nombres comerciales de servicios o empresas existentes; la línea se llama Previsión Exequial de Mascotas.
- Código limpio y con pocos comentarios.
- No leer archivos de datos completos en el contexto: usar muestras o resúmenes generados con código.
- No guardar datos personales: ni representantes legales, supervisores, ordenadores, cuentas bancarias, documentos de personas, ni contactos de las cámaras de comercio.
- No borrar archivos de datos ni hacer `git push --force` sin confirmación.

## Fuentes y notas de extracción

### MinSalud (PDF, municipal salvo 2025 departamental)
Extraer con pdfplumber → camelot → LLM. Validar contra el total nacional impreso. Los formatos cambian entre años: armonizar por DIVIPOLA. Si la serie completa no cierra al día 3, quedarse con 2019, 2023 y 2024.

### INS — agresiones por animales potencialmente transmisores de rabia (evento 300)
- **2024 (fuente principal municipal):** Anexo 1 departamental 2024 (casos, población, incidencia, muertes). Anexos 2–4: casos, población e incidencia **por municipio 2022, 2023 y 2024**, ordenados por departamento. El encabezado del anexo 4 está desordenado, pero los datos siguen casos–población–incidencia por año. Corregir «Valledel Cauca».
- **2025:** Figura 1 (tabla, p. 10): serie nacional 2018–2025. Anexo 2 (p. 48): incidencia por departamento y distrito 2018–2025. Anexos 3–5 (pp. 49–78): casos, población e incidencia por municipio 2025. Total procedente de Colombia 2025: 199.028.
- **2023:** solo para la especie agresora por departamento. Sus anexos municipales traen solo incidencia, con nombres partidos en dos líneas, abreviados («Sant. de Quilichao», «Carmen Apicalá») y las dos últimas páginas desarmadas.
- Unir municipios por coincidencia aproximada **dentro del mismo departamento** contra DIVIPOLA, con tabla de equivalencias; reportar los que no coincidan. Distritos (Barranquilla, Cartagena, Santa Marta, Buenaventura, Bogotá) vienen aparte.
- Microdatos del evento 300 (verificado 2026-10-22): el portal SIVIGILA los entrega solo con formulario. En datos.gov.co hay **conteos agregados** (evento × municipio × semana) para 2017 (`84d4-vfax`), 2018 (`xd2n-cu8j`), 2019 (`qvnt-2igj`) y 2021 (`fhc4-jjti`), descargados en `data/raw/ins/ins_sivigila_evento300_AAAA.jsonl`. Se usan solo para **validar** los PDF en 2019 y 2021 (no hay 2020 ni 2022–2025); los códigos de municipio vienen sin departamento, unir con `cod_dpto` + `cod_mun`.

### SECOP II (API Socrata, conjunto `jbjy-vk9h`, verificado)
Consulta de candidatos (paginar con `$limit`/`$offset`):

```sql
SELECT id_contrato, referencia_del_contrato, proceso_de_compra, urlproceso,
  nombre_entidad, nit_entidad, codigo_entidad, orden, sector, rama,
  departamento, ciudad, localizaci_n, direcci_n_de_ejecuci_n_del_contrato,
  objeto_del_contrato, descripcion_del_proceso, codigo_de_categoria_principal,
  tipo_de_contrato, modalidad_de_contratacion, estado_contrato,
  fecha_de_firma, fecha_de_inicio_del_contrato, fecha_de_fin_del_contrato,
  duraci_n_del_contrato, dias_adicionados,
  valor_del_contrato, valor_facturado, valor_pagado,
  origen_de_los_recursos, destino_gasto,
  codigo_proveedor, proveedor_adjudicado, tipodocproveedor, es_pyme,
  ultima_actualizacion
WHERE fecha_de_firma BETWEEN '2020-01-01T00:00:00' AND '2025-12-31T23:59:59'
  AND ( upper(objeto_del_contrato) LIKE '%FUNERA%' OR upper(objeto_del_contrato) LIKE '%EXEQU%'
     OR upper(objeto_del_contrato) LIKE '%INHUMA%' OR upper(objeto_del_contrato) LIKE '%CREMACI%'
     OR upper(objeto_del_contrato) LIKE '%CAD_VER%' OR upper(objeto_del_contrato) LIKE '%SEPELIO%'
     OR upper(objeto_del_contrato) LIKE '%SEPULT%' OR upper(objeto_del_contrato) LIKE '%OSARIO%'
     OR upper(objeto_del_contrato) LIKE '%CEMENTERIO%' OR upper(objeto_del_contrato) LIKE '%NECR%'
     OR upper(objeto_del_contrato) LIKE '%ANIMALES MUERTOS%' OR upper(objeto_del_contrato) LIKE '%ZOONOSIS%'
     OR upper(descripcion_del_proceso) LIKE '%FUNERA%' OR upper(descripcion_del_proceso) LIKE '%EXEQU%'
     OR upper(descripcion_del_proceso) LIKE '%INHUMA%' OR upper(descripcion_del_proceso) LIKE '%CREMACI%'
     OR upper(descripcion_del_proceso) LIKE '%ANIMALES MUERTOS%' )
```

- Agregar la condición por códigos UNSPSC funerarios una vez identificados en el clasificador (no inventarlos).
- **Filtro afinado (2026-10-22).** Los crudos conservan la consulta original (19.306 filas SECOP II; 15.484 uid SECOP I) y no se vuelven a descargar. En interim (`src/etl/senales_secop.py`) cada señal es una columna booleana: `OSARIO` con límite de palabra (excluye ROSARIO: 5.943 → 53 en SECOP II) y `ZOONOSIS` solo junto a animales muertos, cadáver, disposición final, incinera, recolección de animales o sepult (10.060 → 20); esas filas llevan `posible_disposicion_animales`. `CEMENTERIO`, `NECR` y `CAD_VER` quedan como señales pendientes de decisión (mezclan obras, necropsias y servicios funerarios).
- SECOP I: columnas distintas (`detalle_del_objeto_a_contratar`, `objeto_del_contrato_a_la`, `id_clase`/`id_familia` sin prefijo `V1.`, `cuantia_contrato`). El crudo ya viene con una fila por `uid` (primera fila en orden de `uid`): se verificó que los 245 `uid` repetidos (420 filas sobrantes) no difieren en `cuantia_contrato`, `valor_contrato_con_adiciones` ni `fecha_de_firma_del_contrato` (`src/etl/verificar_uid_secop1.py`). Cruce con SECOP II por NIT + valor + fecha: sin coincidencias exactas; los 10 pares con fecha ±30 días (Yumbo, Unidad Ejecutora de Saneamiento del Valle, La Samaritana) **no se eliminan**: probablemente son contratos distintos de apoyo a la gestión con el mismo valor.
- Muestra aparte de ~100 contratos aleatorios **que no cumplan** el filtro (no recuperados), estratificada por año.
- Si se incluye SECOP I, misma lógica sobre su conjunto en datos.gov.co.

### Cámaras de Comercio (API Socrata: `gwqv-sqvs` Ibagué, `yufs-urdt` Arauca, `pevq-v2xz` Villavicencio)
Filtrar CIIU 9603 en la consulta. Guardar solo NIT, razón social, códigos CIIU, municipio, estado de la matrícula y fecha. Solo para validar la cobertura de Places. Villavicencio no trae NIT. En personas naturales el NIT (cédula) no se guarda, y la razón social queda solo en `data/raw`; en interim y processed se reemplaza por un seudónimo `PN-…` (HMAC con `SEUDONIMO_SALT`) y nunca se usa en salidas (`src/etl/procesar_camaras.py`).

### Google Places (Text Search New)
- Solo campos Pro: nombre, dirección, ubicación, tipos. Nada de reseñas, calificación ni sitio web (tarifa Enterprise).
- Cuota diaria `SearchTextRequest per day` = 150. Prueba con 10 municipios dentro de esa cuota. Para la corrida completa (~2.200 llamadas) Edward sube la cuota a 2.500 ese día y la baja después. Gratis hasta 5.000 llamadas/mes.
- Error `RESOURCE_EXHAUSTED` / 429 = cuota agotada, no reintentar en bucle.
- **Segunda pasada, solo para prestadores ya identificados** (Places + Facebook + Cámaras, unos 50–150): pedir `rating` y `userRatingCount` (tarifa Enterprise, 1.000 llamadas gratis/mes; no pasar de 200). **Nunca** pedir ni guardar el texto de las reseñas ni datos de quienes reseñan.

### Prestadores en Facebook (archivo de Harold)
- Separar «servicios mencionados» en columnas sí/no: `cremacion_individual`, `cremacion_colectiva`, `entierro`, `compostaje`, `recogida`.
- La ciudad sede recibe `cod_divipola` (ubicación en el mapa). La cobertura declarada se descompone en una tabla aparte prestador × municipio atendido.
- Unir con Places por nombre normalizado + municipio para no contar dos veces el mismo prestador. Conservar la fuente de cada registro (`places`, `facebook`, `camara`) y su nivel de evidencia: registro formal > sitio web verificado > solo red social.

## Fases y condiciones para avanzar

| Fase | Salida | Condición |
|---|---|---|
| F0 Preparación | repo, entorno, `.gitignore`, claves, Langfuse | claves y Docker funcionando |
| F1 Adquisición | descargas por API + manifiesto de todo `data/raw` | todo archivo con procedencia |
| F2 Extracción | `interim/minsalud_AAAA.parquet`, `interim/ins_*.parquet` | totales cuadran con los PDF; muestra manual coincide |
| F3 Armonización | panel municipal + `incidencias.csv` | validaciones deterministas aprobadas |
| F4 SECOP | contratos clasificados + métricas + patrones de compra | κ entre revisores y F1 con intervalos |
| F5 Capas complementarias | Places, Trends, Biblioteca de Anuncios, Cámaras | fuente, fecha y nivel de evidencia por registro |
| F6 Agente | grafo LangGraph + trazas | no se salta validaciones |
| F7 Evaluación | informe de evaluación | umbrales (abajo) |
| F8 Análisis | indicadores, mapas, tipología | cada cifra rastreable |
| F9 Entrega | documento Word, tablero, README | revisión del equipo |

## Estado de las fases (2026-11-01)

| Fase | Estado |
|---|---|
| F0 Preparación | repo, entorno y claves listos; Langfuse y Docker sin verificar en este registro |
| F1 Adquisición | cerrada (D28); integrada en `main` |
| F2 Extracción | cerrada (D28): MinSalud 2014–2024 (D44–D53); integrada en `main` |
| F3 Armonización | cerrada (D64, D65: INS 2022–2025, panel de agresiones, `incidencias.csv`); integrada en `main` |
| F4 SECOP | cerrada (D55–D99; cierre en `docs/resultados/cierre_f4.md`); integrada en `main` con el merge `4d48d28` y la etiqueta `f4-cerrada` |
| F5 Capas complementarias | pendiente |
| F6–F7 Agente y evaluación | en la rama `agentes` (D100; contrato en `docs/agente/ESPECIFICACION.md` de esa rama) |
| F8–F9 | pendientes |

## Análisis SECOP

**Clasificadores:** regla léxica + UNSPSC (línea base); TF-IDF + regresión logística (principal); `intfloat/multilingual-e5-base` + regresión logística; DeepSeek con 6–8 ejemplos (preetiquetado). Muestra de ~400 candidatos + ~100 no recuperados. Precisión, sensibilidad y F1 de `funerario` con intervalos bootstrap; diagrama de calibración.

**Caracterización (objetivo específico 2):**
- Número y valor por año, en pesos corrientes y **constantes** (IPC DANE, base del último año).
- Valor por departamento y municipio y **por cada 100.000 habitantes** (DANE). Distinguir ubicación de la entidad y dirección de ejecución.
- **Patrones de compra:** por tipo de entidad (`orden`, `sector`, `rama`), por tipo de servicio (subclasificación del objeto: inhumación de NN o población vulnerable, planes exequiales colectivos, traslado de cadáveres, cremación, disposición de animales), por modalidad (participación de la contratación directa en el valor) y por mes de firma.
- Sensibilidad: totales con y sin contratos `mixto`.

**Libro de códigos del etiquetado.** Tres clases (`funerario`, `no_funerario`, `mixto`) más la marca `forense` (columna aparte, no es cuarta clase). `CEMENTERIO`, `NECR` y `CAD_VER` sin otra señal no se clasifican por regla: quedan como candidatas en el estrato C y las decide la revisión humana con estos criterios:
- Cementerio con **operación o administración** (inhumación, exhumación, bóvedas, concesión) = `funerario`.
- Cementerio con obras civiles, mantenimiento físico, estudios y diseños = `no_funerario`.
- `NECR` o `CAD_VER` sin `FUNERA` ni `INHUMA` = `forense`: se reporta aparte y **queda fuera del tamaño de mercado**.
- Contratación de **personal administrativo o de apoyo a una dependencia funeraria** (supervisión, PQRS, correspondencia, apoyo financiero o jurídico) = `no_funerario`: no compra servicios funerarios.
- **Regla de coherencia:** si `forense = 1`, la etiqueta debe ser `no_funerario`, salvo componente funerario claro (p. ej. inhumación de cuerpos no identificados), que va como `mixto`. `forense = 1` con `funerario` es un error de etiquetado y la validación (`src/evaluacion/kappa.py`) lo exporta como desacuerdo.
- **Texto de objetos:** toda salida (pantalla, archivo, documento) que muestre texto de objetos o descripciones pasa antes por `src.etl.anonimizar.anonimizar`. `data/raw` conserva el original; interim y processed llevan el texto censurado.

**Muestra de etiquetado (400, semilla 2026).** Estratos y asignación: A1 palabra y UNSPSC 60, A2 solo palabra 90, A3 solo UNSPSC 60, B posible disposición de animales 23, C cementerio 45, C NECR 25, C CAD_VER 30, C mixtas y OSARIO 17, D sin señal 50; proporcional por fuente y año. La tabla maestra `data/processed/muestra_secop_maestra.*` guarda `peso` = N/n del estrato (suma 34.790); las métricas se calculan **ponderadas**. El archivo de etiquetado (`muestra_secop_etiquetado.csv`) va sin estrato, sin señales ni peso, sin proveedores, y con datos de pacientes omitidos (`src/modelos/muestra_secop.py`).

**Proveedores (objetivo específico 3):** participación por `codigo_proveedor`, HHI, CR4, locales frente a nacionales; K-means solo si es estable.

## Indicadores de mascotas

- Habitantes por perro (DANE / MinSalud), contrastado con 1,7–11,4 (Moran et al., 2022) y con 2,7–7,9 del piloto colombiano 2012.
- Cambio interanual de la población estimada (saltos > ±50 % → incidencia).
- Coberturas exactamente en 100 %.
- Agresiones por cada 1.000 perros (INS / MinSalud), 2022–2025; en 2023, también solo agresiones por perros.
- Prestadores por cada 100.000 animales; contratos de disposición pública; interés detectable en Trends (sí/no).
- Señales del consumidor por prestador (descriptivas): seguidores, número de reseñas, calificación promedio, precios publicados. Mercado potencial aproximado = perros estimados × tasa de mortalidad de referencia NO se calcula (decisión: mortalidad como vacío); los precios solo describen la oferta.

## Agente

```
orquestador → extraccion → validar (código) ─falla y <3 intentos→ extraccion
                                       └─pasa→ incidencias → revision_humana (interrupt) → cargar
```

- Herramientas = funciones de `src/etl` y `src/modelos`: `extraer_pdf`, `validar`, `consultar`, `comparar_fuentes`, `correr_modelo`, `registrar_incidencia`.
- Reglas en el grafo: máximo 3 reintentos, sin carga si falla la validación, tope de costo por corrida, el agente no edita `data/raw`.
- Todo diagnóstico devuelve: `cod_divipola`, `anio`, `valor_citado`, `archivo`, `pagina`, `conclusion`.
- Langfuse: `config={"callbacks": [CallbackHandler()]}` al invocar el grafo. Exportar el diagrama del grafo para el documento.

## Evaluación del agente (F7)

- **Fallas sembradas** sobre una copia del panel: 20 duplicados, 15 dígitos cambiados, 10 municipios borrados, 10 coberturas forzadas al 100 %, 5 saltos falsos. Sensibilidad y precisión con intervalo de Wilson.
- **Anclaje:** `verificar_anclaje()` comprueba que el valor citado exista en el archivo, año y página indicados.
- **Consistencia:** cada incidencia real se corre 3 veces; si no coinciden, confianza baja.
- **Revisión humana:** todos los de confianza baja (Harold) y 60 aleatorios de confianza alta (Natalia). κ de Cohen; si 0 errores en 60, error < 5 % (regla del tres).
- **Umbrales fijados antes:** detección ≥ 90 %, falsas alarmas ≤ 10 %, κ ≥ 0,70, anclaje 100 %.

## Comandos (PowerShell)

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
docker compose up -d                       # en la carpeta de Langfuse
python -m src.etl.manifiesto
python -m src.etl.descargar_secop
python -m src.etl.extraer_minsalud --anio 2019
python -m src.etl.extraer_ins --anio 2024
python -m src.etl.validar
python -m src.agentes.grafo --tarea incidencias
python -m src.evaluacion.fallas_sembradas
streamlit run app/tablero.py
```
