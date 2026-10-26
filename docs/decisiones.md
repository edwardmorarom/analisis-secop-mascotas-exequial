# Registro de decisiones

Cada decisión del proyecto queda aquí con su sustento. Formato:

- **Decisión:** qué se hizo.
- **Por qué:** la razón, con evidencia propia (cifras, archivos, commits) cuando existe.
- **Descartado:** alternativas consideradas y por qué no.
- **Sustento:** referencia bibliográfica, norma o documento técnico.
- **Estado:** vigente, propuesta (pendiente de validar) o reemplazada (indicar por cuál).

Las decisiones no se borran: si cambian, se marca la anterior como reemplazada y se agrega una nueva.

---

## A. Alcance y fuentes

### D01. Vista nacional, solo fuentes públicas
- **Decisión:** el análisis cubre todo el país y usa solo datos públicos descargables.
- **Por qué:** el proyecto dura dos semanas; un derecho de petición tarda hasta 15 días hábiles en responderse (Ley 1755 de 2015) y no garantiza respuesta a tiempo. Las fuentes públicas permiten que cualquiera reproduzca los resultados.
- **Descartado:** derechos de petición a MinSalud, INS y alcaldías; redes sociales con datos personales.
- **Sustento:** Ley 1755 de 2015; Ley 1581 de 2012.
- **Estado:** vigente.

### D02. SECOP II 2020–2025 más SECOP I 2020–2022
- **Decisión:** se usan los dos sistemas de contratación pública.
- **Por qué:** entre 2020 y 2022 las entidades migraron de SECOP I a SECOP II. En 2020, SECOP I tiene 6.313 candidatos (un contrato por `uid`, solo firmados) y SECOP II solo 1.123; con el filtro afinado (D17), 2.069 frente a 345. Sin SECOP I, 2020 quedaría subrepresentado más de cinco veces y la serie mostraría un crecimiento falso.
- **Descartado:** solo SECOP II (sesgo de migración).
- **Sustento:** conteos previos de F1 (commit 46aa476); Colombia Compra Eficiente, conjuntos `jbjy-vk9h` y `f789-7hwg`.
- **Estado:** vigente en lo de usar los dos sistemas; el supuesto de que la migración a SECOP II terminó en 2022 (SECOP I solo hasta 2022) queda **reemplazado por D73**: SECOP I sigue teniendo contratos en 2023–2025.

### D03. Descarga por API con paginación y token
- **Decisión:** se descarga con la API SoQL de Socrata, paginando, con `SOCRATA_APP_TOKEN`.
- **Por qué:** la exportación JSON del portal se trunca en 1.000 filas. Sin token, las consultas con muchos `LIKE` agotaban el tiempo de espera. Reproducibilidad: el 25 de octubre de 2026 (vista modificada a las 05:45 UTC) la API de `jbjy-vk9h` devuelve `count(*)` = 1.000, aunque el 22 de octubre entregó 19.306 candidatos; los demás conjuntos usados están completos (SECOP I 6.471.634 filas; INS y cámaras con sus conteos). El análisis usa el crudo del 22 de octubre (`data/raw/secop/secop2_candidatos_2020_2025.jsonl`, 38.759.174 bytes, SHA-256 `1b75a79ba5fc3c727d79a8dd704b438db7e351a23eebbe83e847ecc490859756`, verificado el 25 de octubre contra el manifiesto) y no se vuelve a descargar. El 28 de octubre se repite solo el conteo (`python -m src.etl.verificar_secop2_count`, que lo registra en `logs/secop2_count.jsonl`).
- **Descartado:** exportar a mano desde datos.gov.co (no reproducible y truncado).
- **Sustento:** documentación de la API de Socrata (SODA).
- **Estado:** vigente.

### D04. Datos de mascotas: vacunación antirrábica de MinSalud
- **Decisión:** la población de perros y gatos por municipio sale de los informes de vacunación antirrábica de MinSalud (2014, 2016, 2017, 2019, 2023 y 2024 municipales; 2025 departamental).
- **Por qué:** es la única serie histórica con cobertura municipal nacional. La Encuesta Multipropósito no tiene cobertura municipal nacional ni serie larga.
- **Descartado:** Encuesta Multipropósito; censos municipales aislados.
- **Sustento:** MinSalud (s. f.-a a g); piloto MSPS-OPS (2012) como referencia de método.
- **Estado:** vigente.

### D05. Agresiones del INS como contraste
- **Decisión:** se usan los informes del evento 300 (agresiones por animales potencialmente transmisores de rabia) del INS en PDF, más los conjuntos agregados de datos.gov.co para 2017 (`84d4-vfax`), 2018 (`xd2n-cu8j`), 2019 (`qvnt-2igj`) y 2021 (`fhc4-jjti`).
- **Por qué:** sirven para comprobar que las cifras de MinSalud son creíbles (agresiones por cada 1.000 perros). Los conjuntos de datos.gov.co validan los totales nacionales del propio PDF del INS: coinciden exactamente con la Figura 1 del informe 2025 (p. 10) en 2018 (136.746), 2019 (141.156) y 2021 (124.760). No validan los PDF de MinSalud, que traen vacunación y no agresiones. Los microdatos individuales exigen un formulario de solicitud (ver D01).
- **Descartado:** microdatos de SIVIGILA.
- **Sustento:** INS, informes del evento 300; reporte de F1.
- **Estado:** vigente.

### D06. Oferta funeraria de mascotas desde varias fuentes
- **Decisión:** la oferta se mide con Google Places, Facebook (levantamiento manual de Harold) y cámaras de comercio con CIIU 9603 (Ibagué, Arauca y Villavicencio, las que publican datos abiertos).
- **Por qué:** ninguna fuente sola cubre la oferta. Places mide presencia física, Facebook mide presencia digital y las cámaras miden la formalidad.
- **Descartado:** RUES completo (sin acceso masivo gratuito).
- **Sustento:** conjuntos de las cámaras en datos.gov.co; Places API (New).
- **Estado:** vigente.

### D07. Google Places: Text Search Pro, sin texto de reseñas
- **Decisión:** se usa Text Search Pro, con una segunda pasada solo para `rating` y `userRatingCount` (tope de 200) y con la cuota diaria limitada.
- **Por qué:** 5.000 llamadas gratuitas al mes alcanzan para el levantamiento nacional. El texto de las reseñas contiene datos personales y no hace falta para los indicadores.
- **Descartado:** la versión Enterprise (costo); descargar reseñas.
- **Sustento:** precios de Places API (New); Ley 1581 de 2012.
- **Estado:** vigente.

### D08. Google Trends limitado
- **Decisión:** se consultan solo «cremación de mascotas» y «funeraria de mascotas», como variable descriptiva (interés detectable: sí o no).
- **Por qué:** «cementerio de mascotas» está contaminado por la película *Pet Sematary*. Solo 9 y 11 departamentos tienen datos, así que no sirve como mapa nacional.
- **Descartado:** pytrends (descontinuado); usar Trends como indicador continuo.
- **Sustento:** consultas exploratorias en Google Trends.
- **Estado:** vigente.

### D09. Meta: presencia y anuncios activos
- **Decisión:** de Facebook solo se registra presencia, seguidores y anuncios activos con fecha de inicio, desde el lado de la oferta.
- **Por qué:** la Biblioteca de Anuncios de Meta no informa alcance ni público de los anuncios comerciales en Colombia, solo de los políticos.
- **Descartado:** medir audiencia o demanda desde Meta.
- **Sustento:** documentación de la Biblioteca de Anuncios de Meta.
- **Estado:** vigente.

### D10. No se estima el mercado potencial en pesos
- **Decisión:** no se calcula «perros × tasa de mortalidad × precio».
- **Por qué:** no hay tasas de mortalidad de mascotas para Colombia. Usar tablas de otro país (Reino Unido) introduciría un supuesto que no se puede validar. Los precios publicados solo describen la oferta.
- **Descartado:** tablas de vida de perros del Reino Unido.
- **Sustento:** revisión del estado del arte (sección de mascotas).
- **Estado:** vigente.

---

## B. Estructura y tratamiento de datos

### D11. Tres capas: raw, interim y processed
- **Decisión:** `data/raw` guarda lo descargado tal cual y nunca se modifica. `data/interim` guarda lo limpiado. `data/processed` guarda las tablas finales de análisis.
- **Por qué:** si un error aparece después, siempre se puede reconstruir desde el crudo. El manifiesto SHA-256 prueba que el crudo no cambió.
- **Descartado:** limpiar sobre los archivos originales.
- **Sustento:** prácticas de reproducibilidad (estructura tipo Cookiecutter Data Science).
- **Estado:** vigente.

### D12. Formatos: JSONL, Parquet y Excel
- **Decisión:** el crudo de las API va en JSONL; interim y processed, en Parquet; Excel o CSV solo para lo que lee o llena una persona.
- **Por qué:** JSONL conserva la respuesta de la API sin perder campos. Parquet guarda los tipos de dato (no pierde ceros iniciales ni fechas) y comprime. Excel con listas desplegables evita errores de tipeo y de tildes en el etiquetado.
- **Descartado:** CSV para todo (pierde tipos y daña las tildes al abrirlo en Excel).
- **Sustento:** documentación de Apache Parquet.
- **Estado:** vigente.

### D13. DIVIPOLA como llave, en texto
- **Decisión:** todos los cruces por municipio usan el código DIVIPOLA de 5 dígitos como texto.
- **Por qué:** los nombres de municipios se repiten y se escriben distinto entre fuentes. Como número, el código pierde el cero inicial (05001 pasa a 5001) y el cruce falla.
- **Descartado:** cruzar por nombre.
- **Sustento:** DANE, DIVIPOLA.
- **Estado:** vigente.

### D14. Pesos constantes y valores por habitante
- **Decisión:** los valores se expresan en pesos constantes con el IPC del DANE (serie de empalme) y por cada 100.000 habitantes con las proyecciones post-COVID del DANE.
- **Por qué:** sin deflactar, el crecimiento por inflación se confunde con crecimiento real. Sin dividir por población, los municipios grandes siempre aparecen arriba.
- **Descartado:** pesos corrientes únicamente; proyecciones anteriores al censo de 2018.
- **Sustento:** DANE, IPC y proyecciones de población.
- **Estado:** vigente.

### D15. Protección de datos personales
- **Decisión:** se eliminan los nombres, documentos, teléfonos, correos e historias clínicas que aparecen en texto libre (`src/etl/anonimizar.py`). Las personas naturales (proveedores, contratistas, comerciantes de las cámaras) se reemplazan por un seudónimo HMAC con sal. Las personas jurídicas conservan nombre y NIT.
- **Por qué:** Ley 1581 de 2012. Se encontraron 30 filas con datos personales, entre ellas nombres de pacientes con diagnóstico. El seudónimo es el mismo en todas las fuentes, para poder contar a un proveedor una sola vez en la concentración del mercado sin exponer su nombre. Las empresas necesitan su NIT para calcular HHI y CR4.
- **Descartado:** borrar a los proveedores personas naturales (distorsiona la concentración); seudónimo sin sal (se puede revertir con un diccionario).
- **Sustento:** Ley 1581 de 2012; reporte de anonimización (commit 05d1137).
- **Estado:** vigente e implementada en `data/interim` (`src/etl/seudonimo.py`, `src/etl/contratistas_secop1.py`, `src/etl/senales_secop.py`). Persona natural en SECOP I = tipo de identificación distinto de «Nit de Persona Jurídica» (11.804 de 15.484 contratos, 5.707 seudónimos distintos), con el número de documento como identificador (se usa solo en memoria para calcular el seudónimo y no se guarda). Persona natural en SECOP II = `tipodocproveedor` distinto de «NIT» (16.232 de 19.306 contratos, 7.328 seudónimos), con `codigo_proveedor` como identificador. El nombre y el documento se reemplazan por el seudónimo (HMAC-SHA256 con `SEUDONIMO_SALT`, 12 caracteres); las personas jurídicas conservan nombre y NIT (3.680 contratos en SECOP I y 3.074 en SECOP II). `data/raw` conserva el original (D11). Cámaras de comercio: 59 personas naturales con razón social seudonimizada, NIT omitido en 21 de Ibagué y 17 de Arauca, y Villavicencio sin NIT. **Limitaciones:** (1) los seudónimos de personas naturales no se unen entre SECOP I y SECOP II (documento en una fuente y `codigo_proveedor` en la otra) ni con las cámaras, así que la concentración (HHI, CR4) de personas naturales se calcula por fuente y puede contar dos veces a una misma persona; (2) en SECOP II un proveedor con «NIT» puede ser una persona natural y conserva su nombre; (3) el documento se normaliza a dígitos, de modo que la cédula y el NIT de una misma persona natural pueden producir seudónimos distintos en SECOP I; (4) 107 nombres de SECOP I aparecen como persona natural en unos contratos y como persona jurídica en otros (empresas unipersonales), y en estos últimos el nombre se conserva por ser persona jurídica.

---

## C. Delimitación de contratos SECOP

### D16. Candidatos por palabras clave y UNSPSC
- **Decisión:** un contrato es candidato si su texto contiene una palabra clave funeraria o tiene códigos UNSPSC 851715 (servicios funerarios), 4813 (ataúdes, urnas, lápidas) o 422621.
- **Por qué:** el código UNSPSC por sí solo es incompleto (aporta 173 contratos de 19.307 en SECOP II), porque las entidades lo diligencian mal o de forma genérica. El texto captura casi todo.
- **Descartado:** filtrar solo por UNSPSC.
- **Sustento:** clasificador UNSPSC de Colombia Compra Eficiente; conteos de F1.
- **Estado:** vigente.

### D17. Ajuste del filtro: OSARIO y ZOONOSIS
- **Decisión:** OSARIO se busca con límite de palabra. ZOONOSIS solo cuenta si va junto a términos de disposición de animales muertos.
- **Por qué:** OSARIO coincidía con «ROSARIO» (5.943 filas, que bajan a 53 con el ajuste). ZOONOSIS traía contratos de salud pública (10.060 filas, que bajan a 20). Juntas eran el 82,6 % de las filas candidatas de SECOP II (15.941 de 19.306 tienen solo una de esas dos señales). Las 23 filas que quedan con ZOONOSIS junto a disposición o con «animales muertos» (21 de SECOP II y 2 de SECOP I) se marcan como posible disposición de animales para la parte de mascotas.
- **Descartado:** quitar ZOONOSIS por completo (se perdería la disposición pública de animales).
- **Sustento:** commit 3f016a7; revisión de 10 objetos al azar.
- **Estado:** vigente.

### D18. Deduplicación de SECOP I por uid
- **Decisión:** se conserva una fila por `uid`.
- **Por qué:** SECOP I repite contratos por rubro presupuestal. Se verificaron los 245 uid repetidos y ninguno difiere en valor ni en fecha de firma.
- **Descartado:** volver a descargar con un criterio explícito (innecesario, según la verificación).
- **Sustento:** commit 587ce35.
- **Estado:** vigente.

### D19. No se eliminan los cruces SECOP I y II por fecha cercana
- **Decisión:** los 10 pares con mismo NIT y valor y fecha a menos de 30 días se conservan.
- **Por qué:** no hay coincidencias exactas por NIT, valor y fecha (0), y los 10 pares con fecha cercana son 3 casos. Los de Yumbo (8 pares) y de la Unidad Ejecutora de Saneamiento del Valle son, probablemente, contratos de apoyo a la gestión que se firman con varias personas por el mismo valor. El de La Samaritana tiene el mismo objeto en ambos sistemas con 7 días de diferencia y podría ser el mismo contrato registrado dos veces. Una regla automática borraría contratos reales. Además, ninguno es funerario.
- **Descartado:** regla de NIT + valor + ±30 días.
- **Sustento:** revisión manual de los pares (Yumbo, Unidad Ejecutora de Saneamiento del Valle, La Samaritana).
- **Estado:** vigente.

---

## D. Etiquetado

### D20. Tres clases y una marca forense
- **Decisión:** cada contrato se etiqueta como `funerario`, `no_funerario` o `mixto`, y por separado lleva `forense` (0 o 1). Si `forense = 1`, la etiqueta no puede ser `funerario`.
- **Por qué:** `mixto` permite reportar el mercado con y sin contratos mezclados (análisis de sensibilidad). Forense va como marca y no como cuarta clase para no fragmentar las clases y mantener estable el κ. Además, el gasto forense se reporta aparte y no se suma al mercado funerario.
- **Descartado:** clasificación binaria; forense como cuarta clase.
- **Estado:** vigente.

### D21. Reglas del libro de códigos
- **Decisión:**
  1. Se etiqueta según **lo que se compra**, no según el lugar donde se usa.
  2. Servicios funerarios directos y bienes funerarios (ataúdes, cajas mortuorias, urnas, lápidas) → `funerario`.
  3. Planes o pólizas de previsión exequial, incluidos los de bienestar para funcionarios → `funerario`. El subtipo se separa después por reglas, no a mano.
  4. Operación o arrendamiento de espacios del cementerio para inhumar → `funerario`.
  5. Obras, construcción, mantenimiento físico, estudios y diseños, aunque sean en cementerios o edificios funerarios → `no_funerario`.
  6. Personal administrativo o de apoyo (supervisión, PQRS, correspondencia, aseo, cafetería, vigilancia, custodia) de una dependencia funeraria o un cementerio → `no_funerario`.
  7. Sepulturero junto con otras tareas no funerarias → `mixto`.
  8. Que un contrato diga «NN» o «víctimas» no lo vuelve forense. Es forense si compra necropsia, toma de muestras, certificación de defunción, identificación o búsqueda de personas.
  9. Bolsas para cadáveres e insumos para manejar cuerpos en hospitales → manejo sanitario: `no_funerario`.
  10. Póliza de vida grupo con auxilio funerario → `no_funerario`: es una indemnización, no un servicio funerario (distinta del plan exequial de la regla 3).
  11. Custodia y conservación de cuerpos NN o no reclamados → `funerario`. Es distinta de la custodia del cementerio como lugar (regla 6), que es `no_funerario`.
  12. Infraestructura de salas de necropsia o de Medicina Legal → `forense = 1`. Una morgue sin necropsia → `forense = 0`.
  13. Todo trabajo de búsqueda, identificación o información sobre personas desaparecidas, fosas o SIRDEC → `forense = 1` (es la regla final para el Registro de Fosas y SIRDEC; la etiqueta sigue siendo `no_funerario` si solo es trabajo de datos). Con ella, M112 pasa de 0 a 1 en `etiquetas_finales.parquet`; las otras seis filas de fosas, SIRDEC y desaparecidos ya tenían 1.
- **Por qué:** cada regla salió de un caso real de la muestra en el que la guía era ambigua. Si no se fijan por escrito, dos revisores etiquetan distinto y el κ baja por falta de criterio, no por dificultad real.
- **Estado:** vigente. Las reglas 8, 10–13 quedaron cerradas con la revisión final de Edward (D54); la regla 13 completa la 8 en lo relativo a búsqueda de personas. El etiquetado de los 400 casos terminó y no se re-etiqueta: `docs/etiquetado/guia_etiquetado.docx` se actualizó con D20 y D21 completas como documentación del criterio usado.

### D22. Muestra de 400, estratificada y con pesos
- **Decisión:** 400 contratos en estratos (A1 60, A2 90, A3 60, B 23, C cementerio 45, C NECR 25, C CAD_VER 30, C mixtas y OSARIO 17, D 50), con el peso N/n de cada estrato, más 100 no recuperados por la consulta original.
- **Por qué:** una muestra aleatoria simple sería casi toda ruido. Los estratos aseguran casos de cada tipo de señal. Los pesos corrigen que los estratos estén sobrerrepresentados; sin ellos, la precisión estimada saldría inflada. El estrato D y los no recuperados miden lo que el filtro deja escapar (sensibilidad).
- **Descartado:** muestra aleatoria simple; muestra sin pesos.
- **Sustento:** Cochran (1977), muestreo estratificado.
- **Estado:** vigente.

### D23. Etiquetado doble y ciego, con calibración
- **Decisión:** dos revisores etiquetan por separado, sin ver estrato, señales ni peso. Las primeras 40 filas son de calibración. El acuerdo se mide con κ de Cohen (umbral de 0,70) y Harold desempata sin saber quién marcó qué.
- **Por qué:** el κ demuestra que la definición es reproducible y no depende de una sola persona. La calibración detecta temprano las reglas que faltan. El desempate ciego evita sesgos hacia un revisor. La referencia de validación es humana, nunca un LLM, para no evaluar al modelo contra sí mismo.
- **Sustento:** Cohen (1960).
- **Estado:** vigente. El desempate de Harold no fue ciego (D54). Para sostener el ciego, los libros de etiquetado y sus derivados (desacuerdos, κ) no se versionan hasta que el equipo lo indique (`.gitignore`); ninguna versión ya commiteada tiene etiquetas (verificado en los commits a92f09d y 3d40ac5). El archivo de desacuerdos de Harold muestra las etiquetas como A y B al azar; la clave queda fuera de `docs/`, en `data/processed/`.

---

## E. Modelos

### D24. Clasificadores comparados
- **Decisión:** se comparan cuatro métodos con las mismas etiquetas: (1) reglas por palabras clave y UNSPSC como línea base; (2) TF-IDF + regresión logística como modelo principal; (3) embeddings `multilingual-e5-base` + regresión logística; (4) DeepSeek con 6 a 8 ejemplos. Se evalúan con validación cruzada y se reportan precisión, sensibilidad y F1 ponderados por estrato, con intervalos bootstrap.
- **Por qué:** con 400 casos, un modelo simple e interpretable rinde bien y sus coeficientes muestran qué palabras deciden la clase. Los embeddings prueban si entender sinónimos mejora el resultado. El LLM prueba si un modelo sin entrenamiento iguala a los entrenados. La línea base dice si los modelos agregan algo.
- **Descartado:** ajuste fino de un transformer (400 casos son pocos y sería costoso para dos semanas).
- **Sustento:** estado del arte, sección de mercado público.
- **Estado:** vigente.

### D25. Extracción de PDF en cascada
- **Decisión:** pdfplumber, luego camelot con Ghostscript y, como último recurso, un LLM.
- **Por qué:** se ordena de más a menos determinista y de menor a mayor costo. Cada resultado se valida contra los totales impresos en el PDF.
- **Descartado:** LLM directo (no determinista, con costo y riesgo de inventar cifras).
- **Estado:** vigente.

---

## F. Agente y evaluación

### D26. Agente con LangGraph, Langfuse y DeepSeek
- **Decisión:** el grafo tiene un orquestador, un nodo de extracción, una validación en código, un nodo de incidencias y una revisión humana con `interrupt` antes de cargar. Las trazas van a Langfuse local y el modelo es DeepSeek.
- **Por qué:** un grafo explícito obliga a pasar por la validación (el agente no puede saltársela). La revisión humana evita cargar datos erróneos. Langfuse registra cada paso para evaluar. DeepSeek tiene un costo bajo por token.
- **Descartado:** un agente libre sin grafo; arquitectura multiagente más compleja.
- **Sustento:** Yao et al. (2023); documentación de LangGraph y Langfuse.
- **Estado:** vigente.

### D27. Evaluación con fallas sembradas
- **Decisión:** se insertan errores conocidos en una copia del panel (20 duplicados, 15 dígitos cambiados, 10 municipios borrados, 10 coberturas forzadas al 100 %, 5 saltos falsos) y se mide cuántos detecta el agente, con intervalos de Wilson. Además: verificación de anclaje, consistencia entre 3 corridas y revisión humana con regla del tres.
- **Por qué:** con errores reales no se sabe cuántos hay, así que no se puede medir la sensibilidad. Con errores sembrados, sí.
- **Sustento:** Wilson (1927); Hanley y Lippman-Hand (1983); Wang et al. (2023).
- **Estado:** vigente.

---

## G. Organización

### D28. Repositorio, ramas y commits
- **Decisión:** un solo repositorio privado con ramas `etl`, `modelos` y `agentes`. Commits en el formato `tipo(alcance): resumen`, con Qué, Por qué, Fuentes, Validación y Fase. Nunca se versionan `data/` ni `.env`.
- **Por qué:** cada cambio queda rastreable hasta su fuente y su validación. Los datos son pesados o tienen datos personales; el `.env` tiene claves.
- **Estado:** vigente.

---

## H. Extracción de PDF (F2)

### D29. Los indicadores de densidad de mascotas solo se interpretan en municipios `posible_medido`
- **Decisión:** para cada municipio y distrito se calcula la razón de habitantes por animal (`razon_hab_perro` y `razon_hab_gato` = «Población DANE» del PDF / población de perros o de gatos) y se clasifica cómo se obtuvo la población de animales. Es `imputado` si es la población DANE 2018 dividida por una razón entera (perros 1–9, gatos 1–25), que es el procedimiento del instructivo para los municipios sin metodología propia; es `posible_medido` si no lo es. La clasificación es por especie (`metodo_estimacion_perro`, `metodo_estimacion_gato`) y `metodo_estimacion` la resume: `imputado` (ambas imputadas), `posible_medido` (ninguna imputada) o `parcial` (una sí y una no). Los indicadores de densidad (habitantes por perro o por gato, animales por cada 100.000 habitantes y derivados) solo se interpretan donde la especie correspondiente es `posible_medido`. `razon_entera_perro` y `razon_entera_gato` guardan la razón que reproduce el dato, para auditar.
- **Regla de «razón entera»:** existe un entero R (1–9 en perros, 1–25 en gatos) tal que `round(DANE / R)` es igual a la población de animales, con tolerancia de ±1 animal.
- **Marca de cobertura:** `cobertura_100 = 1` cuando la cobertura de perros y gatos impresa es exactamente 100; `cobertura_perros_100` hace lo mismo para la cobertura de perros.
- **Por qué:** el instructivo (págs. 2–3) dice que, sin metodología propia, la población de perros 2019 es DANE 2018 sobre la razón perro:humano de 2018, topada en 9 y bajada un dígito en el tramo 9–7, y la de gatos es DANE 2018 sobre la razón gato:humano, topada en 25 y bajada un dígito en el tramo 25–11. Esa cifra refleja la población humana, no una medición de animales. Evidencia en 1.121 municipios y distritos: 597 reproducen la población de perros con una razón entera (232 con R = 9) y 784 la de gatos (408 con R = 25, el tope); en los demás la razón no es entera (hasta 43,3 habitantes por perro, y 93 municipios superan 9,05, algo que el procedimiento impide). Combinado: 513 `imputado`, 253 `posible_medido` y 355 `parcial`; en 271 municipios solo los gatos son imputados y en 84 solo los perros. Para perros, la cuenta pasa de 567 (tolerancia 0) a 597 (±1) y solo a 604 con ±2 (meseta); con ±1 el falso positivo estimado es 0,9 % en perros y 7,4 % en gatos (simulación con la población DANE perturbada hasta 15 %). Sobre la cobertura: 178 municipios tienen cobertura de perros y gatos exactamente 100 y 102 la de perros; el PDF explica que donde hubo focos de rabia se revacunó a más animales que la población estimada y la cobertura se ajustó a 100 (100 de los 178 tienen acumulado igual a la población y 81 tienen más vacunados por la DTS que población), de modo que un 100 puede ser un tope y no una medición. Otros 20 municipios imprimen una cobertura mayor de 100 y no se marcan (`cobertura_100 = 0`).
- **Descartado:** tratar la población de animales como medida en todos los municipios; un único `metodo_estimacion` sin separar especies (oculta 355 municipios mixtos); exigir razón exacta con tolerancia 0 (deja como medidos unos 30 perros imputados por redondeo).
- **Sustento:** MinSalud (2019), instructivo de los informes bimestrales de vacunación antirrábica, págs. 2–3; `agregar_estimacion` en `src/etl/extraer_minsalud.py`.
- **Estado:** reemplazada por D40 en la regla de detección (se elimina la categoría `parcial` y la tolerancia de ±1 animal pasa a la columna `reproducible_*`). Se mantienen `cobertura_100` y `cobertura_perros_100`. Limitación original: en gatos, con ±1, hasta uno de cada catorce municipios con población medida podía quedar como `imputado` por coincidencia numérica.

### D30. Extraer el PDF de 2019 con pdfplumber y usar camelot solo donde pdfplumber falla
- **Decisión:** las tablas de las páginas 4–35 se leen con pdfplumber. Una fila que pdfplumber no separa en columnas se recupera con camelot (`stream`, backend Ghostscript), según D25.
- **Por qué:** pdfplumber detecta una tabla de 13 columnas por página y entrega 1.173 de las 1.174 filas sin celdas no numéricas. La fila «NACIONAL 2019» sale con todo el texto en la primera celda; camelot `stream` la recupera completa (13 columnas, 49.549.275 de población DANE) y camelot `lattice` no la devuelve.
- **Descartado:** camelot para todo el PDF (innecesario); LLM (no hizo falta).
- **Sustento:** D25; prueba de las dos variantes de camelot sobre la página 35; `respaldo camelot: página 35, 1 fila` en la salida del script.
- **Estado:** vigente.

### D31. El departamento de cada municipio se asigna por el total que cierra su bloque, no por el nombre
- **Decisión:** el PDF lista los municipios de cada departamento seguidos de una fila de total. Una fila se acepta como total departamental si su nombre es un departamento de DIVIPOLA y la suma de la población DANE del bloque difiere de ella menos de 3 %. Todas las filas anteriores desde el total previo pertenecen a ese departamento.
- **Por qué:** 32 de 32 departamentos quedan reconocidos; la diferencia de población del bloque es 0 en 31 departamentos y 120 personas (0,0018 %) en Antioquia. Hay nombres que son a la vez departamento y municipio (BOLÍVAR, CÓRDOBA, NARIÑO, CALDAS, ARAUCA), de modo que el nombre solo no sirve.
- **Descartado:** asignar el departamento por nombre del municipio; usar la tabla de DIVIPOLA para asignarlo (los nombres del PDF no coinciden de forma fiable).
- **Sustento:** `asignar_bloques` en `src/etl/extraer_minsalud.py`; 32 filas `departamento_total`.
- **Estado:** vigente.

### D32. Seis distritos van como DTS aparte, fuera del total de su departamento
- **Decisión:** Barranquilla, Bogotá, Buenaventura, Cali, Cartagena y Santa Marta se tratan como `tipo = distrito`. Se detectan como el subconjunto de filas de distrito que hace cuadrar la población del bloque, y su código DIVIPOLA sale de una tabla explícita (08001, 11001, 76109, 76001, 13001, 47001).
- **Por qué:** estas filas aparecen mezcladas dentro de otros bloques y no suman en el total de su departamento: el bloque de Bolívar solo cierra si se excluyen Barranquilla y Bogotá; Caldas, si se excluye Buenaventura; Caquetá, si se excluye Cali; Casanare, si se excluye Cartagena; Santander, si se excluye Santa Marta. El PDF escribe «BARRABQUILLA»; se corrige con una tabla de equivalencias (el valor impreso se conserva en `municipio_pdf`).
- **Descartado:** sumarlas al departamento (rompe 5 totales); unirlas por nombre difuso.
- **Sustento:** prototipo de bloques; 6 filas `distrito`.
- **Estado:** vigente.

### D33. Las 20 localidades de Bogotá se guardan aparte y no cuentan como municipios
- **Decisión:** las filas sin población DANE (20, páginas 8–9, de Usaquén a Sumapaz) llevan `tipo = localidad` y `bloque = DISTRITO`. No se cruzan con DIVIPOLA.
- **Por qué:** suman exactamente la fila «BOGOTÁ» en las siete columnas aditivas que traen datos (población de perros 1.084.214, de gatos 126.606, de perros y gatos 1.210.820, vacunados DTS 380.342, particulares 410.097, perros vacunados 621.281, acumulado 790.439). Una de ellas, SAN CRISTÓBAL, repite el nombre de un municipio de Bolívar.
- **Descartado:** contarlas como municipios (inflaría el total en 1.084.214 perros y colisionaría con códigos de DIVIPOLA).
- **Sustento:** comparación localidades frente a fila Bogotá.
- **Estado:** vigente.

### D34. Cruce con DIVIPOLA por nombre dentro del departamento, en cuatro pasos
- **Decisión:** (1) nombre normalizado igual, único dentro del departamento: 1.039 filas; (2) tabla de equivalencias explícita (departamento + nombre del PDF → código): 16 filas; (3) aproximado con `token_set_ratio ≥ 90` y margen ≥ 5 sobre el segundo candidato, solo entre códigos aún libres: 59 filas, revisadas una por una; (4) distritos por tabla: 6. Las filas sin cruce quedan con `cod_divipola` nulo, sin inventar código.
- **Por qué:** cruzan 1.120 de 1.121 filas municipales y de distrito; 0 códigos repetidos. Sin cruce: Mapiripana (Guainía), que no aparece en `dane_divipola.csv`. DIVIPOLA sin fila en el PDF: Turbo (05837) y Nuevo Belén de Bajirá (27493).
- **Descartado:** fuzzy global sin restringir al departamento; validar el cruce con la población DANE (ver D35).
- **Sustento:** `cruzar_divipola`; la tabla `EQUIVALENCIAS_MUNICIPIO` está en el código.
- **Estado:** vigente. Revisión manual (Edward, 2026-10-25): de los 59 cruces aproximados se revisaron 20, elegidos al azar con semilla 2026 (`src/etl/revisar_cruces.py`), y los 20 son correctos. Con 0 errores en 20, el límite superior del error de los aproximados es 1 − 0,05^(1/20) = 13,9 % con 95 % de confianza. Los 39 restantes no se revisaron a mano. Los 16 de la tabla de equivalencias son reglas explícitas y no entraron en la muestra.

### D35. La «Población DANE 2018» del PDF no se usa como llave ni para validar el cruce
- **Decisión:** se conserva la cifra del PDF tal como se imprime (hoy `pob_pdf`, ver D41), pero no se asume igual a las proyecciones DANE.
- **Por qué:** de 1.056 filas con cruce (versión previa del cruce), solo 1 coincide con la serie 2018–2042 del DANE; frente a la serie 2005–2017 (año 2017, 1.039 cruces exactos) la razón mediana es 1,017 con rango 0,32–3,36. Es otra base, no la serie que tenemos. Ejemplo: Leticia 42.280 en el PDF y 48.182 en la serie 2018.
- **Descartado:** corregir o reemplazar la cifra impresa.
- **Sustento:** comparación contra `dane_proyecciones_municipales_2018_2042.xlsx` y `_2005_2017.xlsx`.
- **Estado:** resuelta por D41 (el denominador de los indicadores es `pob_dane`; la cifra del PDF se conserva como `pob_pdf`).

### D36. Los totales departamentales impresos se conservan y se comparan; no se corrigen los municipios
- **Decisión:** los totales del PDF van a `minsalud_2019_departamentos.parquet`, con suma de municipios, valor impreso y diferencia por columna. Los valores de los municipios quedan como se imprimen.
- **Por qué:** 8 de 32 departamentos cierran exactamente en todas las columnas; 24 difieren. Población DANE: diferencia máxima 0,0018 % (Antioquia, −120). Perros y gatos: hasta 0,2 % (Vaupés). Las diferencias grandes están en perros vacunados y acumulado: Cundinamarca −7.860 y −11.535 (3,0 % del acumulado), Guainía −912 (16,7 % de sus perros vacunados), Antioquia acumulado −8.236, Quindío −573, Cesar −361. A nivel nacional, la suma de municipios y distritos queda por debajo de «NACIONAL 2019» en 120 de población, 8.885 perros vacunados y 21.318 en el acumulado.
- **Descartado:** reescalar municipios para cerrar totales (inventaría datos).
- **Sustento:** `comparar_departamentos`; es la validación contra los totales impresos que exige D25. Las diferencias son incidencias del propio PDF para el agente de F6, no errores de extracción: los municipios se leyeron tal como están impresos.
- **Estado:** vigente.

### D37. Celdas vacías son nulas y las coberturas se guardan como enteros impresos
- **Decisión:** una celda vacía (p. ej. ciudadanos venezolanos o revacunados en foco en municipios sin dato) queda nula, no cero. Las coberturas se guardan como el entero impreso, sin recalcular.
- **Por qué:** «0» y «sin dato» significan cosas distintas; la regla del CLAUDE.md es conservar el valor tal como viene.
- **Descartado:** rellenar con 0; recalcular coberturas desde los conteos (se compara después, en F3).
- **Sustento:** columnas `vacunados_venezolanos`, `revacunados_foco` y `cobertura_*` de `minsalud_2019.parquet`.
- **Estado:** vigente.

### D38. Solo 2019 está implementado; los demás años se revisan antes
- **Decisión:** `--anio` rechaza cualquier año distinto de 2019 hasta revisar el formato de ese PDF.
- **Por qué:** los formatos cambian entre años (CLAUDE.md) y el parser de 2019 depende de sus 13 columnas y de la estructura de bloques.
- **Descartado:** un parser genérico sin revisar cada año.
- **Sustento:** instrucción de empezar solo por 2019 y detenerse para revisión.
- **Estado:** reemplazada por D44 (se implementaron 2023 y 2024). Los demás años (2014, 2016, 2017) siguen sin extraerse hasta revisar su formato.

### D39. Las páginas 34 y 35 no repiten filas; se deja una guarda contra duplicados
- **Decisión:** el extractor elimina filas idénticas en nombre y valores, sin importar la página, y reporta cuántas elimina.
- **Por qué:** se esperaba que la página 35 repitiera filas de la 34. No es así: la 34 tiene 39 filas, la 35 tiene 8 (continúan Vaupés y Vichada y traen el total nacional) y 0 son idénticas; tampoco hay filas duplicadas en las 1.174 ni municipios con el mismo nombre dentro de un departamento. La guarda elimina 0 filas.
- **Descartado:** eliminar duplicados por nombre solo (hay nombres repetidos legítimos, como SAN CRISTÓBAL en Bogotá y en Bolívar).
- **Sustento:** `quitar_duplicados` en `src/etl/extraer_minsalud.py`.
- **Estado:** vigente.

### D40. Los indicadores de densidad de mascotas solo se interpretan en municipios `posible_medido`
- **Decisión:** `metodo_estimacion` es `imputado` si `razon_hab_perro` (`pob_pdf` / población de perros) está a menos de 0,05 de un entero entre 1 y 9, y `posible_medido` si no. El mismo criterio con enteros de 1 a 25 se aplica a los gatos en `metodo_estimacion_gato`. Los indicadores de densidad (habitantes por perro o por gato, animales por cada 100.000 habitantes y derivados) solo se interpretan en municipios `posible_medido`, y se calculan con `pob_dane` (D41), no con `pob_pdf`. `razon_hab_perro` y `razon_hab_gato` usan `pob_pdf` y sirven solo para detectar la imputación. `razon_entera_*` guarda el entero detectado y `reproducible_*` indica si `round(pob_pdf / R)` reproduce la población de animales con ±1 animal.
- **Por qué:** el instructivo del PDF (págs. 2–3) dice que, sin metodología propia, la población de perros es la población DANE 2018 dividida por una razón entera topada en 9 (con un dígito menos entre 1:9 y 1:7), y la de gatos, dividida por una razón entera topada en 25 (con un dígito menos entre 1:25 y 1:11). Esa cifra reproduce la población humana, no mide animales. En 1.121 municipios y distritos: 632 quedan `imputado` y 489 `posible_medido`. Distribución de la razón entera de perros: 9 → 236, 8 → 107, 7 → 72, 6 → 110, 5 → 39, 4 → 32, 3 → 29, 2 → 6, 1 → 1. En gatos, 396 están en el tope de 25 y el resto se reparte entre 5 y 24.
- **Limitaciones:** la regla de 0,05 es más laxa que reproducir el dato: de los 632 perros `imputado`, 597 se reproducen exactamente (±1 animal) y 35 solo están cerca de un entero; por azar, un 10 % de los municipios medidos caería a menos de 0,05 de un entero (unos 41 esperados), de modo que esos 35 son probablemente coincidencias. En gatos, 761 de 770 se reproducen. Además, 11 municipios (perros) y 19 (gatos) quedan cerca de un entero por encima del tope y se tratan como `posible_medido`. `metodo_estimacion` sigue la regla de perros: 246 municipios imputan los gatos pero no los perros y 108 al revés, así que la densidad de gatos debe leerse con `metodo_estimacion_gato`.
- **Descartado:** exigir que la razón se reproduzca exactamente (se conserva como `reproducible_*`); la categoría `parcial` de D29.
- **Sustento:** MinSalud (2019), instructivo de los informes bimestrales de vacunación antirrábica, págs. 2–3; `agregar_estimacion` en `src/etl/extraer_minsalud.py`.
- **Estado:** reemplazada por D43 en el criterio de detección (regla de «menos de 0,05 de un entero»). Se mantienen la interpretación de la densidad solo en `posible_medido`, los topes por especie y `metodo_estimacion` según la regla de perros.

### D41. Población: `pob_pdf` solo detecta imputaciones; los indicadores usan `pob_dane`
- **Decisión:** la cifra «Población DANE 2018» del PDF se conserva como `pob_pdf` (antes `poblacion_dane`) y solo se usa para detectar imputaciones. Los indicadores usan `pob_dane`, la proyección municipal del DANE 2018–2042 (actualización del 30 de julio de 2025) para el año del informe (2019). `dif_poblacion = 1` si `pob_pdf / pob_dane` está fuera de 0,8–1,25.
- **Por qué:** D35 mostró que la cifra del PDF no reproduce las series DANE disponibles. Con la proyección vigente, 344 de 1.120 municipios y distritos (30,7 %) quedan fuera del rango (153 por debajo de 0,8 y 191 por encima de 1,25); el cociente tiene mediana 1,00, percentiles 5 y 95 de 0,67 y 1,59, y extremos de 0,29 y 3,22. Mapiripana no tiene `pob_dane` porque no tiene código DIVIPOLA. La imputación del PDF se hizo sobre su propia cifra, por eso hay que conservarla.
- **Descartado:** usar `pob_pdf` como denominador (casi un tercio difiere más de 20–25 %); reemplazar `pob_pdf` por `pob_dane` (se perdería la detección de imputaciones).
- **Sustento:** D14; DANE (2025), proyecciones municipales 2018–2042; `cargar_pob_dane` en `src/etl/extraer_minsalud.py`.
- **Estado:** vigente. Cierra D35.

---

## I. Decisiones registradas después de implementarse

### D42. SECOP I: solo procesos con contrato firmado y ejecutado
- **Decisión:** de SECOP I se conservan los procesos con `fecha_de_firma_del_contrato` no vacía y estado Celebrado, Liquidado o Terminado sin Liquidar. Se excluyen Convocado y Adjudicado.
- **Por qué:** con el filtro de contenido de F1, los estados son Celebrado (11.006 filas), Liquidado (4.631), Terminado sin Liquidar (267), Adjudicado (2) y Convocado (3). Los dos últimos no tienen contrato ejecutado. Quedan 15.904 filas y 15.484 `uid` (D18).
- **Descartado:** conservar todos los estados (incluiría procesos sin contrato).
- **Sustento:** `src/etl/descargar_secop1.py` (commit 9cdcdcf); conteo de estados de F1.
- **Estado:** vigente.

### D43. `imputado` es que la población de animales se reproduce con una razón entera (±1 animal)
- **Decisión:** `metodo_estimacion_perro` y `metodo_estimacion_gato` son `imputado` si `reproducible_perro` o `reproducible_gato` vale 1, y `posible_medido` si vale 0. `reproducible_*` es 1 cuando existe un entero R (1–9 en perros, 1–25 en gatos) tal que `round(pob_pdf / R)` reproduce la población de animales con ±1 animal; `razon_entera_*` guarda ese R. Ahora se calcula para todos los municipios y distritos. `metodo_estimacion` sigue la regla de perros. La regla de «menos de 0,05 de un entero» de D40 queda reemplazada.
- **Por qué:** la regla de 0,05 marcaba como `imputado` a 35 perros que no se reproducen con ±1 animal; por azar se esperaban unos 41 entre los medidos. Con la reproducibilidad hay 597 perros `imputado` y 524 `posible_medido` (1.121 municipios y distritos), y 784 gatos `imputado` y 337 `posible_medido`. En gatos, 23 municipios pasan de medidos a imputados (con pocos animales, el redondeo aleja la razón de un entero por más de 0,05) y 9 pasan de imputados a medidos. Razón entera de perros: 9 → 232, 8 → 105, 7 → 70, 6 → 103, 5 → 35, 4 → 22, 3 → 23, 2 → 6, 1 → 1. En gatos, 408 están en el tope de 25. Las combinaciones siguen siendo mixtas: 271 municipios imputan solo los gatos y 84 solo los perros, así que la densidad de gatos se lee con `metodo_estimacion_gato`.
- **Limitación:** una razón entera puede reproducir el dato por coincidencia, sobre todo con pocos animales. La simulación de D29 (población DANE perturbada hasta 15 %) estimó un falso positivo de 0,9 % en perros y 7,4 % en gatos con esta tolerancia.
- **Descartado:** la regla de 0,05 de D40; exigir reproducción exacta (deja como medidos unos 30 perros imputados por redondeo).
- **Sustento:** MinSalud (2019), instructivo de los informes bimestrales de vacunación antirrábica, págs. 2–3; `razon_reproducible` en `src/etl/extraer_minsalud.py`.
- **Estado:** vigente. Reemplaza a D40 en el criterio de detección.

### D44. Formato anual de 2023 y 2024 y extracción en tres capas
- **Decisión:** los PDF de 2023 (16 páginas) y 2024 (18) traen una tabla de 14 columnas por página (municipio y 13 cifras) con el formato propio: miles con punto, porcentajes con coma y signo %, y «(ANM)» en las áreas no municipalizadas. Se leen con pdfplumber y cada fila se valida por formato y por las identidades de la tabla (población de perros + gatos = total, con ±1 de redondeo; vacunados DTS + particulares = total, exacto). Si falla el formato o la identidad, la fila se lee de nuevo con camelot (`stream` y luego `lattice`) y se prefiere la lectura que cumple las identidades; si ninguna las cumple, se conserva la de pdfplumber con `identidad_ok = 0`. Un control de completitud con la capa de texto agrega las filas que la tabla omitió. Los totales departamentales se detectan como en D31, con la población de perros y gatos como control (no hay columna DANE); las 20 localidades de Bogotá se identifican por suma contra la fila BOGOTÁ, y «SANTIAGO DE CALI» se trata como el distrito de Cali.
- **Por qué:** 2023 sale con 1.174 filas (1.115 municipios, 6 distritos, 20 localidades, 32 totales departamentales y 1 nacional): 1.173 por pdfplumber y 1 por camelot (TAME, p. 2), todas con `identidad_ok = 1`. 2024 sale con la misma composición: 1.077 por pdfplumber, 96 por camelot (filas con celdas fusionadas por texto desalineado, sobre todo en las filas con asterisco, que camelot `stream` separó bien) y 1 por texto: SANTUARIO (Risaralda, p. 14), que está en la página pero la tabla de pdfplumber la omitía. Hay 21 filas de 2024 con `identidad_ok = 0` (19 localidades de Bogotá, Bogotá y el total nacional): pdfplumber y camelot leen lo mismo, así que la inconsistencia es del PDF (gatos vacunados DTS + particulares ≠ total de gatos). La capa de texto da 1.174 filas en cada año, igual que lo extraído. Cruce con DIVIPOLA en ambos años: 1.121 de 1.121 (exacto 1.108, distritos 6, tabla de equivalencias 4, aproximado 3), sin códigos repetidos; solo Nuevo Belén de Bajirá queda sin fila. Totales: las diez columnas de vacunación suman exacto en todos los departamentos y a nivel nacional, en ambos años; la población difiere por redondeo (hasta 7 animales por departamento en 2024). Cierran exactos 14 departamentos de 32 en 2023 y 4 en 2024. Excepción en 2023: Bolívar suma 2.877 gatos más que su total impreso (4,8 %), diferencia que se arrastra al nacional (+2.880 gatos).
- **Descartado:** exigir que la población sume exacto (el PDF redondea: 54 filas de 2023 difieren en 1); descartar las filas con identidad rota (se perderían 21 filas reales de 2024); reutilizar el extractor de 2019 (otras columnas, otro formato numérico y localidades sin columna DANE).
- **Sustento:** D25; `extraer_anual`, `completar_desde_texto` y `procesar_anual` en `src/etl/extraer_minsalud.py`.
- **Estado:** vigente.

### D45. El asterisco de 2024 se guarda como `ajuste_cobertura = 1`
- **Decisión:** el asterisco del nombre se guarda como `ajuste_cobertura = 1` y se quita del nombre para el cruce con DIVIPOLA. `cobertura_100 = 1` cuando la cobertura de perros y gatos impresa es exactamente 100,0.
- **Por qué:** la nota del PDF de 2024 dice que, en los municipios con asterisco y cobertura mayor de 100 %, la estimación de población se ajustó al 100 %. Hay 341 municipios y distritos con asterisco (379 filas con los totales): 332 tienen la cobertura de perros o la de gatos exactamente en 100 (111 en ambas), 9 no tienen ninguna en 100, y entre los 780 sin asterisco solo 4 tienen alguna en 100. No hay coberturas mayores de 100. Por eso un 100 de 2024 puede ser un tope y no una medición, y en esos municipios la población de animales no es la estimada. En 2023 hay 1 asterisco, 92 municipios con cobertura de perros y gatos en 100 y ninguna cobertura mayor de 100.
- **Descartado:** ignorar el asterisco (mezclaría topes con mediciones).
- **Sustento:** nota al pie del PDF de 2024 (p. 18); `procesar_anual` en `src/etl/extraer_minsalud.py`.
- **Estado:** vigente.

### D46. La imputación de la población de animales no es detectable en 2023 ni en 2024
- **Decisión:** en 2023 y 2024, `metodo_estimacion = no_detectable` para todos los municipios y distritos. Los indicadores de densidad (`hab_por_perro`, `hab_por_gato`) usan `pob_dane` del año del informe (D41) y llevan esa advertencia; D40 y D43 no se pueden aplicar a estos años.
- **Por qué:** estos PDF no traen columna de población DANE ni instructivo, así que se probó con la proyección DANE 2018–2042 de 2018, 2019, 2022 y del año del informe: porcentaje de municipios cuya población de perros se reproduce como DANE / R, con R entero de 1 a 9 y ±1 animal. Control positivo, 2019 con la cifra impresa del PDF: 53,3 % (20,7 % exactamente en R = 9); con cualquier base DANE de 2019: 1,2–1,3 %. Informe 2023: 1,5 % (DANE 2018), 1,1 % (2019), 0,4 % (2022), 1,0 % (2023). Informe 2024: 0,8 %, 0,9 %, 1,0 % y 1,1 %. El pico en R = 9 es de 0–0,2 % en todos los casos. En gatos el porcentaje es 4,8–6,8 %, igual al azar (7,4 % estimado en D29). Como observación, la población de perros de 2024 es la de 2023 multiplicada por unos 1,008 (mediana 1,008, rango intercuartílico 1,003–1,012; 45,9 % de los municipios a ±1 %; en gatos, 36,0 %), mientras que entre 2019 y 2023 no hay relación (5,2 % a ±1 %). Puede ser otro mecanismo de proyección, no identificado.
- **Descartado:** probar un solo año de base; suponer que 2023 y 2024 conservan el método de 2019.
- **Sustento:** `src/etl/detectar_imputacion.py`; D40, D41, D43.
- **Estado:** vigente. Limitación: en 2023 y 2024 no hay forma de separar `imputado` de `posible_medido`, así que sus densidades no son comparables en interpretación con las de 2019.

### D47. Indicador principal del panel: perros vacunados por 1.000 habitantes; la densidad solo con 2019
- **Decisión:** todos los años extraídos entran al panel municipal (`data/processed/panel_minsalud_municipal.parquet`, llave `cod_divipola` + `anio`) con su `metodo_estimacion` (2019: `imputado` o `posible_medido`; 2023 y 2024: `no_detectable`). La medida principal de evolución es `vacunados_perros_x1000hab = perros vacunados / pob_dane × 1.000`, calculada para todos los años con la población DANE del año del informe. La densidad (`hab_por_perro`) se analiza solo con 2019 y `metodo_estimacion = posible_medido` (columna `densidad_analizable = 1`; 524 municipios).
- **Por qué:** los perros vacunados son conteos del programa, no estimaciones; la población de animales de 2023 y 2024 no permite separar imputación de medición (D46) y la de 2019 imputada no mide animales (D43). Resultado actual: 1.120 unidades con indicador en 2019 (Mapiripana sin código) y 1.121 en 2023 y 2024; mediana de 120,8, 113,2 y 108,4 por 1.000 habitantes.
- **Descartado:** usar la densidad de 2023 y 2024 como serie; usar la población de animales del PDF como denominador.
- **Sustento:** `src/etl/panel_minsalud.py`; D41, D43, D46.
- **Estado:** vigente. Limitación: el denominador es la población total DANE, no la de perros; compara municipios, no mide cobertura. El panel agrega `vacunados_perros_gatos_x1000hab` para todos los años (2014, 2016, 2017, 2019, 2023 y 2024), porque 2016 y 2017 solo informan vacunados de perros y gatos juntos (D50, D52); en 2019 se usa el acumulado de perros y gatos vacunados (5.573.573 en municipios y distritos; 5.594.891 el total nacional impreso), cuya razón con la población total coincide con la cobertura impresa en los 1.121 casos (±1 punto). El indicador de perros existe en 2014, 2019, 2023 y 2024.

### D48. La población de perros de 2024 es una proyección de la de 2023
- **Decisión:** el cambio de la población de animales entre 2023 y 2024 no se interpreta como crecimiento. No se usa para variaciones interanuales de población de perros o gatos.
- **Por qué:** la población de perros de 2024 es la de 2023 multiplicada por ~1,008 (mediana 1,008; rango intercuartílico 1,003–1,012; 45,9 % de los municipios a ±1 %; en gatos, 36,0 %), mientras que entre 2019 y 2023 no hay relación (5,2 % a ±1 %), ver D46.
- **Descartado:** tratar la población de 2024 como una medición independiente.
- **Sustento:** `src/etl/detectar_imputacion.py`.
- **Estado:** vigente.

### D49. Las inconsistencias del PDF se marcan, no se excluyen; Bogotá es una sola unidad
- **Decisión:** el panel conserva todas las filas y agrega `marca_inconsistencia` con: `identidad_tabla_no_cierra` (fila de 2024 cuyas identidades fallan), `ajuste_cobertura_asterisco` (D45) y `total_departamental_no_cierra:<columna>` (la suma municipal difiere del total impreso del departamento en más de 0,5 %). La unidad municipal de Bogotá es la fila de la ciudad (11001, `tipo = distrito`); las 20 localidades quedan solo como detalle en `data/processed/minsalud_localidades_bogota.parquet` (60 filas: 20 por año). Bolívar 2023 se conserva con su marca.
- **Por qué:** excluir perdería filas reales (D44). Marcas actuales: 2023, 45 municipios de Bolívar (+2.877 gatos sobre el total impreso) y 1 con asterisco; 2024, 341 con asterisco, uno de ellos (Bogotá) también con identidad rota; 2019, Antioquia y Quindío (acumulado), Cundinamarca (perros vacunados −7.860, 2,8 %) y Guainía (−912, 16,7 %).
- **Descartado:** excluir las filas marcadas; contar las localidades como municipios (D33).
- **Sustento:** `marcas_departamento` y `armonizar` en `src/etl/panel_minsalud.py`; D33, D36, D44, D45.
- **Estado:** vigente.

### D50. Extracción de 2017: formato de cinco cifras por línea, vacunados de perros y gatos juntos
- **Decisión:** el PDF de 2017 (24 páginas) trae por municipio solo cinco cifras: población de perros, de gatos, total, perros y gatos vacunados y cobertura acumulada (porcentaje entero). No hay columna de población DANE, ni vacunados de perros por separado, ni nombre de departamento por fila: el departamento aparece en la fila «Total <departamento>» que cierra cada bloque. Se leen las líneas con la capa de texto de pdfplumber (cada línea es nombre + 4 o 5 números; coma decimal o punto de miles) y el departamento de cada municipio se asigna por la fila de total que lo sigue. Barranquilla, Bogotá (con sus 20 localidades, por suma), Cartagena, Santa Marta y Buenaventura son filas de distrito fuera de los bloques; Cali queda dentro del bloque Valle del Cauca y se marca como distrito. Cuatro filas de Cesar (Agustín Codazzi, La Jagua de Ibirico, La Paz, Manaure) traen solo cuatro números: el último es el número de vacunados (suman 55 contra 56 del total de Cesar) y su cobertura queda nula. `metodo_estimacion = no_detectable`. Para el panel, 2017 aporta `vacunados_perros_gatos_x1000hab` y no `vacunados_perros_x1000hab`.
- **Por qué:** se leen 1.173 filas: 1.114 municipios, 6 distritos, 20 localidades, 32 totales departamentales y 1 nacional, sin líneas descartadas. Cruce con DIVIPOLA: 1.119 de 1.120 filas municipales y de distrito (exacto 1.031, aproximado 61, tabla de equivalencias 21 —siete nuevas, resueltas por eliminación dentro del departamento: San Andrés de Cuerquia, San Pedro de los Milagros, San Pedro de Urabá, Hato Corozal, El Carmen de Atrato, Carmen del Darién, Mitú—, distritos 6). Sin cruce: «INIRIDA RURAL» (Guainía), que parece una división de Inírida que DIVIPOLA no tiene. DIVIPOLA sin fila: La Victoria y Puerto Alegría (Amazonas) y Nuevo Belén de Bajirá. De 15 cruces aproximados al azar (semilla 2026), los 15 son correctos. Totales: los vacunados cierran exacto en los 32 departamentos salvo Cesar (−1); los perros difieren hasta 6 por redondeo; los gatos suman 7.275 más que el total impreso de Antioquia (4,2 %) y 251 más en Amazonas; el total nacional impreso (perros 5.206.617, gatos 1.630.828, perros y gatos 6.844.687, vacunados 5.047.601) coincide con la suma municipal en perros (+26) y vacunados (−1), y en gatos queda 7.549 por debajo. La columna «total» no es la suma de perros y gatos en 30 filas (`identidad_ok = 0`; Caldas suma 33.465 más que su total impreso en esa columna). Seis municipios traen población de gatos con decimales. Imputación: no hay población DANE impresa, así que no aplica D43; con DANE de 2017, 2018, 2019 y 2022 solo el 0,4–1,0 % de los municipios reproduce su población de perros como DANE / R (R entero), igual al azar (D46). Hay 5 municipios o distritos y 22 filas de total con asterisco en el nombre (cobertura de los 5 municipios: 62 a 102) cuyo significado el PDF no explica; se guarda como `asterisco` y no se interpreta. La cobertura supera 100 en 2 municipios (máximo 102): este año no se topa a 100.
- **Descartado:** reutilizar el extractor anual de 2023 y 2024 (otras columnas, sin porcentajes con símbolo %); inferir `vacunados_perros` repartiendo entre perros y gatos; descartar las 30 filas con identidad rota.
- **Sustento:** `src/etl/extraer_minsalud_2017.py`; `cargar_pob_dane` ahora lee también las proyecciones 2005–2017; D43, D46.
- **Estado:** vigente. Limitación: el PDF dice «vacunados en el semestre» y «cobertura acumulada»; el periodo exacto de los vacunados no está claro, así que no es comparable sin reserva con los años siguientes.

### D51. Extracción de 2014: tabla con departamento por fila y asteriscos de ajuste y de focos de rabia
- **Decisión:** el PDF de 2014 (33 páginas) trae por fila departamento, municipio y nueve cifras: censo de perros, de gatos, total, perros vacunados, gatos vacunados, cobertura de perros, de gatos, total vacunados y cobertura total (porcentajes con coma decimal y `#¡DIV/0!` donde la población es 0). Se leen con las líneas de texto de pdfplumber y las coordenadas de los caracteres: el departamento ocupa la columna izquierda (x < 58) y el municipio hasta x = 208. Dos casos se resuelven aparte: en Norte de Santander el nombre del departamento se desborda sobre la columna del municipio (se separa por la altura del texto) y en las 38 filas de Tolima el texto de la población de gatos está dañado (`1 .422`), así que se deriva como total − perros y se marca con `poblacion_gatos_derivada = 1`. San Andrés y Providencia tienen el nombre de las dos filas mezclado con el del departamento: se asignan por orden y tamaño (Providencia es la menor). Un asterisco en el nombre es `ajuste_cobertura = 1` y dos asteriscos son `foco_rabia = 1` (focos de rabia y revacunación), según la nota de la p. 32. `metodo_estimacion = no_detectable`. No hay filas de total departamental ni nacional, ni localidades de Bogotá.
- **Por qué:** se leen 1.123 filas: 1.117 municipios y 6 distritos (Barranquilla, Bogotá, Buenaventura, Cali, Cartagena y Santa Marta). Cruce con DIVIPOLA: 1.122 de 1.123, y los 1.122 códigos de DIVIPOLA quedan usados (exacto 1.070, aproximado 34, tabla de equivalencias 12 —siete nuevas por eliminación dentro del departamento: Gama, San Juan de Rioseco, Cuaspud Carlosama, El Carmen de Norte de Santander, Villa Caro, Riofrío y Belén de Bajirá, que en 2014 es Nuevo Belén de Bajirá—, distritos 6); sin cruce «Inidira rural» (Guainía), la misma división de Inírida que 2017. De 15 cruces aproximados al azar (semilla 2026), los 15 son correctos. Calidad interna: las 1.123 filas cumplen perros + gatos = total y vacunados de perros + gatos = total vacunados; 8 filas tienen población 0 (cobertura nula). No hay totales impresos para cuadrar, así que no hay comparación departamental ni nacional. La tabla de la p. 33 (286, 74, 89 y 673 municipios por banda de cobertura) no se reproduce con ninguna de las tres coberturas (cobertura total: 295, 88, 107 y 633; perros: 304, 92, 96 y 631): se registra sin explicación. Asteriscos: 218 filas con un asterisco, de las cuales 215 tienen la cobertura de perros o la de gatos exactamente en 100 (hay 25 filas sin asterisco con alguna en 100); 17 filas con dos asteriscos (focos de rabia). Las coberturas no se topan: 53 municipios superan 100 en perros, 159 en gatos y 19 en el total. Imputación: sin población DANE impresa no aplica D43; con DANE de 2014, 2018, 2019 y 2022 solo el 0,4–1,3 % de los municipios reproduce su población de perros como DANE / R (azar, D46).
- **Descartado:** el extractor de 2017 (otro orden de columnas); extraer las tablas con camelot (columnas desplazadas por celdas combinadas); borrar las 38 filas de Tolima.
- **Sustento:** `src/etl/extraer_minsalud_2014.py`; D44–D46, D50.
- **Estado:** vigente. Limitación: la población de gatos de Tolima es derivada, y la tabla de bandas del PDF no se reproduce.

### D52. Extracción de 2016: departamento asignado por orden y conteo, con validación del cruce
- **Decisión:** el PDF de 2016 (34 páginas) trae por municipio seis cifras (población de perros, de gatos, total, perros y gatos vacunados, cobertura acumulada y «stock de vacuna») y no tiene el departamento por fila: su nombre está en una celda combinada tan alta que el texto cae fuera de la página. El departamento se asigna por orden: los bloques salen en orden alfabético (Amazonas, Antioquia, Arauca, Atlántico, Barranquilla, Bogotá, Bolívar, Boyacá, Buenaventura, …, Vichada; 37 bloques con cinco distritos que van solos) y una programación dinámica corta la lista de filas en esos bloques contiguos maximizando los nombres que coinciden con los municipios del departamento asignado en DIVIPOLA (exacto, razón ≥ 90 o nombre contenido, más la tabla de equivalencias). El criterio de abandono fijado antes era: más del 1 % de nombres sin cruce dentro de su departamento, o «Total País» que no cuadre. Las 20 localidades de Bogotá van seguidas y no hay fila de la ciudad: se construye sumándolas (`fila_derivada = 1`). El «Nr» del stock se lee como nulo. `metodo_estimacion = no_detectable`.
- **Por qué:** se leen 1.132 filas (sin «Total País»): 1.106 municipios, 6 distritos, 20 localidades y la fila de Bogotá derivada. Los tamaños de bloque coinciden con los de 2014 (Antioquia 125, Boyacá 123, Cundinamarca 116, Santander 87, Nariño 64, Norte de Santander 40, Chocó 30, Córdoba 30, Guainía 9, …; Amazonas 2, solo Leticia y Puerto Nariño). Cruce con DIVIPOLA dentro del departamento asignado: 1.112 de 1.113 filas municipales y de distrito, es decir 1 sin cruce (0,09 %, «Inírida rural», la misma división de 2014 y 2017), bajo el 1 % de abandono (exacto 1.009, aproximado 78, tabla de equivalencias 19, distritos 6). Solo 12 nombres no coinciden en la etapa de segmentación (1,1 %: abreviaturas como «S.Rosa de Osos» o «Yondo (Casabe)»), pero todos cruzan después. De 15 cruces aproximados al azar (semilla 2026), los 15 son correctos. «Total País» impreso: la suma municipal da exacto los perros y gatos vacunados (4.321.895) y difiere por redondeo en la población (perros +13, gatos +6, total +19). DIVIPOLA sin fila: Nuevo Belén de Bajirá y los nueve municipios no municipalizados de Amazonas (el PDF no los trae). Calidad interna: 29 filas con perros + gatos distinto del total; 498 sin stock; la cobertura impresa coincide con vacunados / población total en las 1.112 filas (±1 punto); 1 municipio supera 100. Algunos nombres pierden su primera letra («l Carmen de Chucuri») porque la columna de nombres se corta en x = 100; no afecta al cruce. Imputación: sin población DANE impresa no aplica D43; con DANE 2016, 2018, 2019 y 2022, 0,8–1,2 % de perros reproducibles (azar, D46).
- **Descartado:** asignar por la etiqueta del departamento (no está en la página); extraer con camelot (celda combinada); abandonar 2016.
- **Sustento:** `src/etl/extraer_minsalud_2016.py`; D34, D44–D51.
- **Estado:** vigente. Limitación: el departamento no es una lectura sino una inferencia validada por el cruce; si dos departamentos vecinos intercambiaran un municipio con el mismo nombre no se detectaría.

### D53. 2017 entra al panel con `periodo_incierto = 1`
- **Decisión:** las filas de 2017 llevan `periodo_incierto = 1` en el panel; los demás años, 0. Se usan con esa advertencia.
- **Por qué:** el PDF de 2017 dice «perros y gatos vacunados en semestre» y «cobertura acumulada». Evidencia de que es una cifra anual: el total nacional de perros y gatos vacunados es 5.047.601, entre el de 2016 (4.321.895, «enero a diciembre») y el de 2019 (5.594.891), y no la mitad de ellos; la cobertura nacional impresa es 74 % frente a 67 % en 2016 y 2019; el archivo se actualizó el 15 de marzo de 2018, como el de 2016 (26 de marzo de 2017), que cierra el año anterior. La serie nacional completa de vacunados de perros y gatos es 4,32 millones (2016), 5,05 (2017), 5,59 (2019), 5,81 (2023) y 5,63 (2024). Sigue sin ser una confirmación del periodo.
- **Descartado:** excluir 2017; tratarlo como semestral.
- **Sustento:** `src/etl/panel_minsalud.py`; D50.
- **Estado:** vigente.

### D54. Resultado del etiquetado: κ, desempate de Harold y etiquetas finales
- **Decisión:** la etiqueta final de cada contrato es la de la revisión de Edward si el caso está en la hoja «Revisar» (38 casos) y, si no, la propuesta de Harold con D21 aplicada. Se guardan en `data/processed/etiquetas_finales.parquet` (400 filas: etiqueta, forense, origen, etiquetas de Edward y Natalia, subestrato y peso). El umbral de κ (0,70) no se cambia. El κ de `forense` no se reporta.
- **Por qué:** κ de etiqueta entre Edward y Natalia (n = 400): **0,683 global**, que **no cumple el umbral de 0,70 fijado antes**; es «sustancial» según Landis y Koch (1977, 0,61–0,80). La calibración (40 filas) dio 0,812 y la ronda principal (360) 0,668, porque las reglas de D21 se definieron durante el etiquetado y no llegaron a la guía de Natalia. Los 68 desacuerdos de etiqueta (83,0 % de acuerdo) se concentran en la frontera con `no_funerario`: en 42 Edward puso `funerario` o `mixto` y Natalia `no_funerario`, y en 57 hay desacuerdo en cualquier sentido entre esa frontera. Por estrato: A 0,548, B 0,000, C 0,232 (D es una sola clase, sin κ); los κ de 0,000 de A1, B y C cad_ver vienen de prevalencia extrema (casi todos los casos en una clase). El κ de `forense` no se calcula: Natalia marcó `forense = 1` en los 150 contratos que etiquetó `funerario` (error sistemático de comprensión; Edward lo hizo en 2 de 158). Es una limitación del etiquetado. El desempate de Harold **no fue ciego** (veía qué marcó cada revisor) y cubrió las **400 filas** (`decision_harold`: 143 funerario, 240 no_funerario, 17 mixto; su `forense` se dedujo del texto, y en 59 filas sin dato se completó con 0 salvo en «Revisar»). Edward revisó **38 casos** aplicando D21: confirmó las 38 propuestas (0 cambios sobre ellas; 2 etiquetas distintas de la decisión de Harold, además de los cambios de `forense`). Verificaciones: las propuestas coinciden con `decision_harold` en las 362 filas fuera de «Revisar» (etiqueta y `forense`; 45 filas sin `forense` de Harold quedan en 0); las 38 filas de «Revisar» tienen `revisado = sí`; ningún `funerario` con `forense = 1`. Tabla final etiqueta × forense: funerario 143 / 0; mixto 13 / 2; no_funerario 195 / 47 (total 351 con forense 0 y 49 con forense 1).
- **Descartado:** bajar el umbral a 0,60 después de ver el resultado; re-etiquetar a Natalia; calcular un κ de `forense` con una marca inválida; usar las fórmulas del libro de revisión (se leyeron los valores).
- **Sustento:** `src/evaluacion/kappa.py`, `src/evaluacion/etiquetas_finales.py`; Landis y Koch (1977); D21, D23.
- **Estado:** vigente. Limitaciones: el κ global no alcanza el umbral; el desempate no fue ciego; el `forense` de Natalia no es utilizable. Los libros de etiquetado siguen sin versionarse.

### D55. Diseño de la comparación de clasificadores y línea base de reglas
- **Decisión:** los cuatro métodos de D24 se evalúan sobre las 400 etiquetas finales (D54) con las mismas particiones: validación cruzada de 5 pliegues estratificada por subestrato y etiqueta (celdas con menos de 5 casos se agrupan; semilla 2026). Las métricas son precisión, sensibilidad y F1 de `funerario` ponderados por el peso N/n de cada estrato (D22), con intervalo bootstrap percentil del 95 % (2.000 remuestreos dentro de cada estrato, que conserva el diseño). `mixto` cuenta como no `funerario` en estas métricas y se reporta aparte. Los modelos entrenados usan solo el texto del contrato (objeto, descripción y código UNSPSC), nunca las señales ni el estrato, que son función del filtro. La línea base de reglas marca `funerario` si hay alguna señal núcleo (FUNERA, EXEQU, INHUMA, CREMACI, SEPELIO, SEPULT o UNSPSC funerario) y `no_funerario` en otro caso, y se evalúa sobre los 400 sin entrenamiento.
- **Por qué:** el estrato D (50 casos, peso 528) representa el 76 % de los 34.790 contratos y no tiene ningún positivo, de modo que un solo falso positivo allí cambia mucho la precisión ponderada; por eso el intervalo se remuestrea por estrato. Resultado de las reglas: precisión 0,770 (IC 0,729–0,811), sensibilidad 1,000, F1 0,870 (IC 0,843–0,896), exactitud ponderada 0,961; de los 210 casos con señal núcleo, 143 son `funerario`, 8 `mixto` y 59 `no_funerario`.
- **Descartado:** validación cruzada sin estratificar (los estratos de 23 a 60 casos quedarían sin representación en algunos pliegues); métricas sin ponderar (sobrerrepresentan a los candidatos); usar el estrato o las señales como variables (fuga: el estrato se define con ellas).
- **Sustento:** `src/modelos/datos_clasificacion.py`, `src/evaluacion/metricas_ponderadas.py`, `src/modelos/linea_base_reglas.py`; D22, D24, D54.
- **Estado:** vigente. Limitación: la sensibilidad de las reglas es 1,000 por construcción de la muestra (todos los `funerario` están en estratos con señal) y no mide los funerarios que el filtro no recupera; eso lo cubre la muestra de no recuperados.

### D56. TF-IDF con regresión logística: modelo principal
- **Decisión:** texto del contrato (objeto, descripción si difiere, código UNSPSC) vectorizado con TF-IDF (unigramas y bigramas, sin tildes, minúsculas, `sublinear_tf`, `min_df = 2`) y regresión logística multinomial de tres clases con la regularización C elegida por validación cruzada interna de 3 pliegues dentro de cada pliegue de entrenamiento (rejilla de 0,1 a 1.000). Se entrena sin pesos muestrales y sin balanceo de clases; la variante balanceada se evalúa solo como contraste.
- **Por qué:** con las particiones de D55, `funerario`: precisión **0,942** (IC 0,908–0,972), sensibilidad **0,919** (IC 0,873–0,962), F1 **0,931** (IC 0,901–0,957), exactitud ponderada 0,981, frente a las reglas (precisión 0,770, F1 0,870): el modelo recorta los falsos positivos a costa de perder algo de sensibilidad (1,000 → 0,919). La variante balanceada es indistinguible (precisión 0,938, sensibilidad 0,930, F1 0,934; IC solapados). De los 15 `mixto`, 6 se predicen `mixto` y 5 `funerario`. Palabras que empujan hacia `funerario`: «servicios funerarios», «exequial(es)», «fúnebres», «población vulnerable»; hacia `no_funerario`: «necropsias», «construcción», «del cementerio», «bóvedas para», «laboratorio», «servicios profesionales». C llegó al borde de la rejilla (1.000): casi no hay regularización preferida.
- **Descartado:** entrenar con los pesos N/n (el estrato D, con 50 casos de peso 528, dominaría el ajuste); elegir la variante por F1 (la diferencia está dentro del ruido).
- **Sustento:** `src/modelos/tfidf_logistica.py`, `src/modelos/comparar.py`; D24, D55.
- **Estado:** vigente. Limitación: el IC es sobre una sola partición de 5 pliegues; la sensibilidad no mide los funerarios que el filtro nunca recupera.

### D57. Embeddings `multilingual-e5-base` con regresión logística
- **Decisión:** cada texto (el mismo de D56) se convierte en un vector con `intfloat/multilingual-e5-base` (prefijo `query: `, máximo 256 tokens, vectores normalizados, sin ajuste fino) y se clasifica con la misma regresión logística de tres clases y la misma validación cruzada de D55. Los vectores de la muestra se guardan en `data/processed/embeddings_e5_muestra.npy`.
- **Por qué:** `funerario`: precisión **0,939** (IC 0,899–0,972), sensibilidad **0,954** (IC 0,920–0,982), F1 **0,946** (IC 0,921–0,969), exactitud ponderada 0,982. Frente a TF-IDF (F1 0,931; IC 0,901–0,957) la diferencia es de 0,015 y los intervalos se solapan: no hay evidencia de que entender sinónimos mejore la clasificación con 400 casos, aunque la sensibilidad sube de 0,919 a 0,954 con la misma precisión. De los 15 `mixto`, 5 se predicen `mixto` y 3 `funerario`.
- **Descartado:** ajuste fino del transformer (D24); texto sin el prefijo `query: ` (el modelo lo exige).
- **Sustento:** `src/modelos/embeddings_logistica.py`; Wang et al. (2024), multilingual-e5; D24, D55.
- **Estado:** vigente. Limitación: sin diferencia estadística clara frente a TF-IDF; la elección del modelo final se decide con la tabla completa, incluido DeepSeek.

### D58. DeepSeek con ocho ejemplos: diseño y presupuesto (sin llamadas todavía)
- **Decisión:** el clasificador de DeepSeek recibe una instrucción con D20, D21 y las reglas 10 a 13, ocho ejemplos de la muestra (3 `funerario`, 2 `no_funerario`, 2 `mixto` y 1 `no_funerario` con `forense = 1`; casos de hasta 260 caracteres elegidos con la semilla 2026: M011, M012, M055, M172, M190, M218, M257 y M337) y el texto del contrato, y responde un JSON `{"etiqueta", "forense"}` con temperatura 0. Los ocho ejemplos se excluyen de la evaluación, que se hace sobre los 392 restantes; los demás modelos se reportan también sobre esos 392 para compararlos. Solo se envía el texto ya censurado de interim (D15). Cada llamada guarda instrucción, versión del modelo y respuesta en `logs/` (CLAUDE.md). No se llama a la API hasta que se apruebe el presupuesto.
- **Por qué (presupuesto, tarifas del modelo `deepseek-flash` según una guía secundaria de junio de 2026: 0,30 USD por millón de tokens de entrada sin caché, 0,006 con caché, 1,20 de salida, tarifa pico):** evaluación en la muestra, 392 llamadas, unos 0,72–0,96 millones de tokens de entrada: **0,02–0,03 USD con caché, 0,23–0,30 USD sin caché**. Clasificar los 34.790 contratos: 34.790 llamadas, 38,8–51,7 millones de tokens de entrada (prefijo de 1.000–1.400 tokens más un texto de 369 caracteres de media): **2,0–2,4 USD con caché y 12,5–16,4 USD sin caché**. Los tokens se estiman por caracteres (3,0 a 4,0 por token) porque no hay tokenizador local. El tope de costo del agente en `config.yaml` es 2,0 USD.
- **Descartado:** enviar texto sin censurar; usar las etiquetas de los demás modelos como ejemplos.
- **Sustento:** `src/modelos/deepseek_clasificador.py`; D15, D24, D26.
- **Estado:** cerrado por D60 (se ejecutó la evaluación de 392 llamadas; la corrida completa se decide con D62). Aviso: `config.yaml` dice `deepseek-chat`, nombre que la documentación actual de DeepSeek ya no lista (ahora `deepseek-flash` y `deepseek-v4-pro`, y los nombres retirados se redirigen a Flash); las tarifas de arriba son de una fuente secundaria porque la página oficial de precios no pudo leerse y deben confirmarse antes de gastar.

### D59. Regla de selección del clasificador final, fijada antes de evaluar DeepSeek
- **Decisión:** TF-IDF con regresión logística (modelo principal de D24) clasifica los 34.790 contratos, salvo que otro modelo lo supere en el F1 de `funerario` con intervalos bootstrap que no se solapan, es decir, que el límite inferior del IC del 95 % del otro modelo sea mayor que el límite superior del de TF-IDF, calculados sobre los mismos casos (para DeepSeek, los 392 que no son ejemplos). Si los intervalos se solapan, gana el más simple y auditable (orden: reglas, TF-IDF, e5, DeepSeek). Si gana más de uno, se elige el de mayor F1. Si el ganador es DeepSeek, la corrida de los 34.790 (2,0–2,4 USD con caché según D58) supera el tope de 2,0 USD de `config.yaml`: no se ejecuta ni se sube el tope sin aprobación expresa. e5 se corre además sobre los 34.790 como análisis de sensibilidad del tamaño de mercado, con el modelo elegido como cifra principal.
- **Por qué:** fijar el criterio antes de ver el resultado de DeepSeek evita elegir el modelo por el número que salga. A la fecha de esta regla se conocen solo las reglas (F1 0,870; IC 0,843–0,896), TF-IDF (0,931; IC 0,901–0,957) y e5 (0,946; IC 0,921–0,969): e5 solapa con TF-IDF y por tanto no lo desplaza; DeepSeek aún no se evaluó. Con 400 casos, intervalos solapados significan que la diferencia no se distingue del ruido, y entonces pesan la interpretabilidad (los coeficientes de TF-IDF se auditan) y el costo.
- **Descartado:** elegir el de mayor F1 puntual; usar umbrales de F1 propios del modelo; subir el tope de costo para acomodar a DeepSeek.
- **Sustento:** D24, D55–D58; el commit de esta regla es anterior a cualquier llamada de evaluación a DeepSeek.
- **Estado:** vigente.

### D60. Resultado de DeepSeek en la muestra y aplicación de la regla D59
- **Decisión:** según D59, DeepSeek (`deepseek-flash`, ocho ejemplos, sin razonamiento) supera a TF-IDF: su límite inferior del IC del F1 de `funerario` (0,964) es mayor que el límite superior de TF-IDF (0,959). Por la misma regla, la corrida de los 34.790 con DeepSeek no se ejecuta sin aprobación expresa (su costo real estimado supera el tope de 2,0 USD) y el tope no se sube. Mientras tanto se clasifican los 34.790 con TF-IDF y con e5 (local, sin costo) para tener la cifra de referencia y la sensibilidad.
- **Por qué:** 392 casos (los 400 menos los 8 ejemplos), `funerario` ponderado, IC 95 %: reglas precisión 0,771, sensibilidad 1,000, F1 0,870 (0,843–0,894); TF-IDF 0,941 / 0,923 / 0,932 (0,904–0,959); e5 0,938 / 0,953 / 0,946 (0,919–0,968); **DeepSeek 0,985 (0,966–1,000) / 0,973 (0,951–0,991) / 0,979 (0,964–0,991)**; exactitud ponderada 0,964, 0,983, 0,983 y 0,991. Matriz de DeepSeek: de 140 `funerario`, 134 aciertos, 2 `mixto`, 4 `no_funerario`; de 13 `mixto`, 9 aciertos; de 239 `no_funerario`, 236 aciertos. Marca `forense`: acuerdo 97,4 % (3 forenses no detectados y 7 falsos). Las 392 respuestas fueron JSON válido, sin errores, con la versión `deepseek-flash`. Costo real: **0,038 USD** (526.464 tokens de entrada con caché, 88.085 sin caché, 7.299 de salida; el 85,7 % de la entrada salió de la caché), frente a 0,02–0,03 USD estimados con caché: un 28 % por encima del extremo alto, porque el prefijo real fue de 1.455 tokens y no de 1.023–1.364. Con ese costo por llamada, los 34.790 costarían unos 3,4 USD. Corrida de 04:23 UTC de un lunes, fuera de las franjas pico 01–04 y 06–10.
- **Descartado:** subir el tope de 2,0 USD; ejecutar la corrida completa antes de la aprobación.
- **Sustento:** `src/modelos/deepseek_clasificador.py`, `logs/deepseek_evaluacion.jsonl` (no se versiona); D58, D59.
- **Estado:** vigente. Advertencia de validez: la instrucción de DeepSeek recoge las reglas de D21 y las reglas 10 a 13, que se formularon mirando casos de esta misma muestra, y los ocho ejemplos salen de ella; el F1 de DeepSeek es, por tanto, optimista respecto de contratos nuevos. TF-IDF y e5 no ven reglas, solo texto. La regla D59 se aplicó tal como se fijó, sin ajustes.

### D61. Clasificación de los 34.790 contratos con TF-IDF y e5 (DeepSeek pendiente)
- **Decisión:** los 34.790 contratos (15.484 de SECOP I y 19.306 de SECOP II) se clasifican con TF-IDF (modelo de referencia hasta que se apruebe la corrida de DeepSeek, D60) y con e5 (sensibilidad), entrenados con las 400 etiquetas finales. En los 400 casos de la muestra se usa la predicción fuera de pliegue, no la ajustada con todos los datos, para evitar fuga. El valor es el valor inicial del contrato (`cuantia_contrato` en SECOP I, `valor_del_contrato` en SECOP II), en pesos corrientes; el ajuste con IPC y el tratamiento de valores atípicos quedan para F8. La salida es `data/processed/clasificacion_universo.parquet` (no se versiona).
- **Por qué:** **TF-IDF:** `funerario` 3.732 contratos (10,7 %) y 189,6 miles de millones de pesos (8,4 % del valor); `mixto` 89 y 107,8; `no_funerario` 30.969 y 1.954,3. **e5:** `funerario` 3.639 y 166,7; `mixto` 114 y 117,7; `no_funerario` 31.037 y 1.967,4. El tamaño de mercado funerario es, entonces, 166,7–189,6 miles de millones (7,4–8,4 % del valor candidato), y con `mixto` incluido, 274,4–297,4. Entre los dos modelos cambian de clase **546 contratos (1,57 %)**, con 76,0 miles de millones: 280 `funerario` de TF-IDF son `no_funerario` para e5 (42,7), 193 al revés (20,1), 41 `no_funerario` → `mixto` (11,1), 22 `mixto` → `no_funerario`, 8 `funerario` → `mixto` y 2 `mixto` → `funerario`. Solo 31 de los 546 están en la muestra etiquetada. Los cambios son casos frontera de D21: servicios profesionales o diseños en dependencias funerarias y cementerios (TF-IDF los lleva a `funerario`, e5 a `no_funerario`), pólizas de seguros de entidades con probabilidad baja (0,5–0,8) en ambos, y compra de cofres o bóvedas (e5 los ve funerarios o no según el texto). Ningún contrato individual domina: el mayor `funerario` pesa 4,7 % (TF-IDF) y 3,9 % (e5) del valor de su clase.
- **Descartado:** reemplazar por la etiqueta humana en los 400 casos (mezclaría dos fuentes y falsearía la comparación entre modelos); presentar una sola cifra de mercado antes de elegir modelo.
- **Sustento:** `src/modelos/clasificar_todos.py`; D55–D60.
- **Estado:** vigente como cifra preliminar. Por la regla D59 el modelo elegido es DeepSeek; mientras no se apruebe su corrida (unos 3,4 USD, por encima del tope de 2,0 USD) se reporta el rango TF-IDF–e5. Los embeddings de los 34.790 textos tardaron más de 2 horas de CPU.

### D62. Validación externa de 60 contratos y regla para aprobar la corrida completa de DeepSeek
- **Decisión:** se etiquetan 60 contratos al azar de los 34.790 que no están en los 400, repartidos por subestrato en proporción a la asignación original (semilla 2027), con el mismo formato y listas desplegables del etiquetado, sin estrato, señales ni predicciones, en `docs/etiquetado/validacion_edward.xlsx` (no se versiona). Los ids son V001–V060 y el peso de cada subestrato es N/n con N los contratos del estrato que no están en los 400. Cuando Edward lo entregue etiquetado, se evaluarán DeepSeek, TF-IDF y e5 en esos 60 con las mismas métricas ponderadas e intervalos bootstrap de D55 antes de cualquier corrida. **Regla fijada ahora, antes de ver ese resultado:** si DeepSeek mantiene el F1 de `funerario` más alto de los tres en los 60 sin que su intervalo quede por debajo del de TF-IDF (límite superior de DeepSeek menor que el límite inferior de TF-IDF), se aprueba la corrida completa de los 34.790 con un tope de 5 USD; si no, se reporta el rango TF-IDF–e5 como tamaño de mercado. El tope de 5 USD vale solo para esa corrida y no cambia el `tope_costo_usd` de `config.yaml`.
- **Por qué:** la advertencia de validez de D60: la instrucción de DeepSeek y sus ocho ejemplos se formularon con casos de las 400 etiquetas, así que su F1 de 0,979 en ellas es optimista, y la selección por D59 se hizo sobre esos mismos casos. Los 60 contratos son nuevos para los tres modelos (TF-IDF y e5 se ajustan con las 400, y DeepSeek solo vio ocho). Reparto: A1 9, A2 14, A3 10, C cad_ver 5, C cementerio 7, C mixtas y OSARIO 3, C necr 4 y D 8 (60 en total). B (animales) no tiene contratos disponibles: sus 23 ya están en los 400. Pesos de 27 a 3.293; el estrato D pesa el 77 % de los 34.390 contratos disponibles y solo tiene 8 casos. 27 contratos son de SECOP I y 33 de SECOP II. Número de decisión: el encargo pedía D61, pero D61 ya existe (clasificación de los 34.790 con TF-IDF y e5), así que esta es D62.
- **Descartado:** reutilizar las 400 para decidir (es el conjunto sobre el que se diseñó la instrucción); aprobar la corrida por la sola diferencia de D60; mostrar predicciones al revisor.
- **Sustento:** `src/modelos/validacion_externa.py`; D55, D58–D61.
- **Estado:** vigente. Limitaciones: con 60 casos los intervalos son anchos y, como el criterio de «por debajo» solo se incumple si DeepSeek queda claramente peor, en la práctica la regla se reduce a que DeepSeek tenga el F1 puntual más alto; el estrato D, con ocho casos y casi todo el peso, hace que un solo falso positivo mueva mucho la precisión ponderada. Al evaluar los 60 se reportan además, para cada modelo, las métricas sin ponderar (con su intervalo) y la matriz de confusión de tres clases, para que un solo caso del estrato D no domine la lectura; la regla de aprobación no cambia y se aplica sobre las métricas ponderadas, como se fijó (`src/modelos/evaluar_validacion.py`).

### D63. Resultado de la validación externa: la regla D62 no aprueba la corrida de DeepSeek
- **Decisión:** aplicada tal como se escribió, la regla de D62 no se cumple: DeepSeek no tiene el F1 de `funerario` más alto en los 60 (lo tiene TF-IDF). No se programa la corrida de los 34.790 con DeepSeek. `clase_final` es la de TF-IDF y el tamaño de mercado se reporta como rango TF-IDF–e5.
- **Por qué:** 60 contratos (28 `funerario`, 32 `no_funerario`, 0 `mixto` según Edward). F1 ponderado: **TF-IDF 0,648** (IC 0,389–0,970), e5 0,596 (0,352–0,916), DeepSeek 0,606 (0,357–0,943); precisión 0,973, 0,969 y 0,970; sensibilidad 0,486, 0,430 y 0,441. Sin ponderar: TF-IDF F1 0,863 (0,766–0,947), e5 0,766 (0,652–0,873), DeepSeek 0,840 (0,727–0,930); sensibilidad 0,786, 0,643 y 0,750. Matrices (humano en filas): TF-IDF 22 funerarios acertados, 6 perdidos y 1 falso positivo; e5 18, 1 `mixto`, 9 perdidos y 1 falso positivo; DeepSeek 21, 1 `mixto`, 6 perdidos y 2 falsos positivos (uno `funerario`, uno `mixto`). La sensibilidad ponderada baja a 0,43–0,49 por un solo caso: V006 (mantenimiento de estructuras metálicas y vallas, estrato D, peso 3.293, el 46 % del peso de los funerarios), que Edward etiquetó `funerario` y que los tres modelos dejan como `no_funerario`. Como sensibilidad del resultado, sin V006 el F1 ponderado es 0,931 (TF-IDF), 0,870 (e5) y 0,882 (DeepSeek): TF-IDF sigue siendo el más alto, de modo que la decisión no depende de ese caso. El F1 de TF-IDF sin V006 (0,931) coincide con el de la validación cruzada de las 400 (0,932). Costo real de las 60 llamadas a DeepSeek: **0,0057 USD** (80.384 tokens de entrada con caché, 13.072 sin caché, 1.116 de salida), ejecutadas en hora pico por autorización expresa para estas 60.
- **Descartado:** reinterpretar la regla después de ver el resultado; corregir las etiquetas de Edward por mi cuenta.
- **Sustento:** `src/modelos/evaluar_validacion.py`, `data/processed/tabla_validacion_60.csv` y `predicciones_validacion_60.parquet` (no se versionan); D59, D60, D62.
- **Estado:** vigente. Alerta para Edward (revisión de etiquetas): al leer los errores aparecen siete casos de la validación cuya etiqueta no sigue D21 tal como está escrita: V006 y V054 (bomberos) como `funerario` sin componente funerario; V057 (construcción de bóvedas, regla 5), V027 (limpieza y aseo del cementerio, regla 6), V015 (asistencia administrativa de la Subdirección de Servicios Funerarios, regla 6) y V046 (acompañamiento psicológico en esa Subdirección) como `funerario` donde las reglas dicen `no_funerario`; y V030 (arrendamiento de bóvedas y osarios para inhumar, regla 4) como `no_funerario` donde la regla dice `funerario`. No se corrigió nada: el resultado de arriba usa las etiquetas tal como se entregaron. Seguimiento (2026-10-26): Edward pidió revisar esos siete casos en `docs/revision_f4/revision_7_etiquetas.xlsx` (objeto, descripción, etiqueta actual y la regla posiblemente incumplida, sin predicciones de los modelos). Cuando devuelva el archivo, `python -m src.modelos.reevaluar_validacion` recalcula la validación con las etiquetas revisadas y reporta las dos versiones usando las predicciones ya guardadas (sin nuevas llamadas a DeepSeek). La decisión de D63 no se reabre: solo se registrará aquí si el resultado de la regla D62 cambia o no.

### D64. Extracción municipal de agresiones del INS (APTR 2022–2025)
- **Decisión:** se extraen los municipios del informe INS 2024 (Anexos 2 a 4, pp. 33–54: casos, población e incidencia 2022, 2023 y 2024) y del informe 2025 (Anexos 3 a 5, pp. 49–80: casos, población DANE e incidencia 2025) con las líneas de texto de pdfplumber, sin camelot ni LLM (la capa de texto bastó, D25). El informe 2024 trae filas partidas de tres maneras (nombre en dos líneas, incidencia en línea aparte y cifras en una línea con el nombre debajo), que se reconstruyen por posición; la incidencia 2023 de 11 municipios falta en el PDF y queda nula (se recalcula). El departamento sale del nombre de la entidad territorial (al inicio de la fila en 2024 y al final en 2025, el más largo que coincida con DIVIPOLA: «Valle del Cauca» y «Norte de Santander» antes que «Cauca» y «Santander»). El cruce usa `cruzar_divipola` (D34) dentro del departamento. Salida: `data/interim/ins_agresiones_municipal.parquet` (una fila por municipio y año, con archivo, página, método de cruce y la incidencia impresa y la recalculada). El informe 2023 solo se usa para la especie agresora por departamento y no se extrajo aquí.
- **Por qué:** 2024: 1.122 municipios (1.115 por nombre exacto, 6 distritos y 1 sin código: Mapiripana (CD), Guainía, que DIVIPOLA no tiene y cuya población es 0); 2025: 1.109 (1.094 exactos, 5 aproximados —Mariquita, San Andrés de Sotavento, San Vicente, Cúcuta y Tumaco, los cinco correctos—, 4 por la tabla de equivalencias y 6 distritos). Validación 2024 contra la tabla departamental del Anexo 1 (casos 2024): 37 de 39 entidades cuadran exacto; Chocó suma 3 casos menos (320 frente a 323) y el nacional 180.016 frente a 180.019 (−3, probablemente Nuevo Belén de Bajirá, que no está en los anexos). Totales de casos: 2022 150.014, 2023 174.064, 2024 180.016. Validación 2025: la suma municipal es **199.028**, igual al total impreso; la incidencia recalculada por entidad territorial (casos / población municipal × 100.000) coincide con la del Anexo 2 en 35 de 38 entidades (diferencia menor de 0,01 %) y difiere en Amazonas (+1,8 %), Chocó (+10,6 %) y Guainía (+11,1 %), porque el informe 2025 no lista 13 municipios y áreas no municipalizadas: seis de Chocó (Bagadó, Bojayá, Lloró, Medio San Juan, Río Iró y Sipí), Güicán (Boyacá), La Victoria y Puerto Alegría (Amazonas) y Puerto Colombia, Cacahual, Pana Pana y Morichal (Guainía). Como los casos suman exacto el nacional y la incidencia departamental implica una población mayor, esas entidades casi seguro tuvieron cero casos y no se listaron; no se les inventa una fila.
- **Descartado:** camelot (las filas partidas se resuelven por texto); imputar cero a los 13 no listados (es una inferencia, no una lectura); usar la incidencia impresa en vez de recalcularla.
- **Sustento:** `src/etl/extraer_ins.py`; `data/processed/ins_validacion_2024.csv` y `ins_validacion_2025.csv`; D25, D34.
- **Estado:** vigente. Limitación: los 13 municipios ausentes de 2025 quedan sin dato (no cero) en el panel.

### D65. Panel de agresiones por 1.000 perros e `incidencias.csv` (cierre de F3)
- **Decisión:** `data/processed/panel_agresiones.parquet` une las agresiones del INS (D64) con el panel de MinSalud por `cod_divipola` + `anio`. `agresiones_x1000_perros = casos / población de perros del PDF × 1.000`. MinSalud no tiene municipios en 2022 ni 2025, así que esos años usan la población de perros de 2023 y 2024 respectivamente, marcados con `denominador_otro_anio = 1`. Cada fila lleva `poblacion_perros_imputacion` (el `metodo_estimacion` del panel: `no_detectable` en 2023 y 2024, D46) para no leer el indicador como una densidad medida, y `agresiones_x1000_vacunados` como alternativa con conteos (D47). `data/processed/incidencias.csv` reúne, con `cod_divipola`, `anio`, valor citado, archivo y página, los casos que las reglas del CLAUDE.md señalan: duplicados, saltos de la población de perros mayores de ±50 % entre años consecutivos, coberturas exactamente en 100, `dif_poblacion` (D41), habitantes por perro fuera de 1,7–11,4 solo en `posible_medido`, identidades de la tabla que no cierran y totales (de MinSalud y del INS) que no cierran; los totales departamentales van con el código del departamento y «000». Todas las incidencias se marcan y ninguna fila se excluye (D49).
- **Por qué:** mediana de agresiones por 1.000 perros: 19,4 (2022, 1.121 municipios), 23,5 (2023), 24,6 (2024) y 27,4 (2025, 1.108 con dato de perros); ningún municipio supera 1.000 por 1.000 perros. `incidencias.csv` tiene 1.721 filas: cobertura en 100, 1.221 (2014: 224, 2016: 276, 2017: 340, 2019: 178, 2023: 92, 2024: 111); `dif_poblacion`, 344 (2019); saltos de población, 50 (2017: 39, 2024: 11); identidad de tabla, 60 (2016: 29, 2017: 30, 2024: 1); habitantes por perro fuera de rango, 32 (2019, `posible_medido`); totales departamentales de MinSalud que no cierran, 8; totales del INS, 5; un municipio sin código (Mapiripana); duplicados, 0.
- **Descartado:** dejar sin indicador 2022 y 2025 (se pierden dos de los cuatro años del INS); excluir las filas con incidencia; calcular la incidencia por 1.000 perros con la población DANE.
- **Sustento:** `src/etl/panel_agresiones.py`, `src/etl/incidencias.py`; D41, D43, D46, D47, D49, D64.
- **Estado:** vigente (Edward aceptó usar la población de perros de otro año en 2022 y 2025, 2026-10-26). La especie agresora de 2023 (solo perros) no se extrajo: queda para una fase posterior.

### D66. Ubicación de la entidad compradora: cruce con DIVIPOLA (propuesta)
- **Decisión:** cada contrato se ubica por el departamento y el municipio de la entidad compradora (`departamento_entidad`/`municipio_entidad` en SECOP I y `departamento`/`ciudad` en SECOP II), no por el lugar de ejecución, con el cruce de D34 (nombre normalizado dentro del departamento, tabla de equivalencias, aproximado con puntaje ≥ 90 y margen ≥ 5, distritos por tabla). El cruce se hace sobre pares únicos de (departamento, nombre normalizado) para que dos escrituras del mismo municipio («Villa del Rosario» y «Villa Del Rosario») no se disputen el mismo código, y se agrega una tabla de 10 alias manuales (Cúcuta → San José de Cúcuta, El Líbano → Líbano, El Espinal → Espinal, El Guamo → Guamo, Villa Garzón/Villa Amazónica → Villa Garzón, San Miguel de Mocoa → Mocoa, Valle del Guamuez/La Hormiga → Valle del Guamuez, Santa Rosa de Lima → Santa Rosa, San Miguel (La Dorada) → San Miguel, Distrito Capital → Bogotá). El departamento se toma del nombre del departamento aunque el municipio no cruce.
- **Por qué:** de los 34.790 contratos, 33.060 (95,0 %) tienen código de municipio (exacto 26.412, distritos 6.415, aproximado 214, tabla de equivalencias 19) y 34.694 (99,7 %) tienen departamento. Quedan sin municipio 1.730: 1.706 con la entidad registrada en «No Definido» y 24 de otros nombres (Guayabal en Tolima, El Peñol en Antioquia, Villa Garzón/Villa Amazónica y Mariquita, entre otros). Entre los 3.732 contratos `funerario` de TF-IDF, 3.583 (96,0 %) tienen municipio y 3.725 (99,8 %) departamento. Los 22 cruces aproximados distintos están en `docs/revision_f4/cruces_secop.xlsx` (20 al azar, semilla 2026, con lista desplegable sí/no) para su revisión.
- **Descartado:** ubicar por el municipio de ejecución (viene en texto libre, con direcciones); eliminar los contratos con ubicación «No Definido» (se conservan en las cifras nacionales y por año).
- **Sustento:** `src/modelos/mercado_base.py`, `data/processed/resultados_secop/tasa_cruce_ubicacion.csv`; D34.
- **Estado:** vigente (confirmada por Edward, 2026-10-26). Revisión manual de los cruces aproximados: de los 20 revisados, los 20 son correctos; con 0 errores en 20, el límite superior del error es 1 − 0,05^(1/20) = 13,9 % con 95 % de confianza. Los 2 pares aproximados restantes no se revisaron a mano. Limitación: ubicar por la sede de la entidad concentra en pocos municipios lo que compran entidades nacionales o departamentales (por ejemplo Villa del Rosario y Cúcuta reúnen más de 6.700 contratos).

### D67. Deflactor y base de las series de valor
- **Decisión:** los valores se expresan en pesos corrientes y en pesos constantes de 2025: valor × (promedio mensual del índice IPC total de 2025) / (índice del mes de firma), con la serie de empalme del DANE (base diciembre de 2018 = 100). El valor de cada contrato es su valor inicial (`cuantia_contrato` en SECOP I y `valor_del_contrato` en SECOP II), sin adiciones. Los indicadores por 100.000 habitantes usan la población DANE del año de firma, municipal o sumada por departamento; el resumen es el promedio de los años con contratos. El escenario principal es `funerario` según TF-IDF (`clase_final`, D63); las sensibilidades son TF-IDF con `mixto`, e5 y e5 con `mixto`.
- **Por qué:** el índice promedio de 2025 es 150,17 y el de enero de 2020, 104,24 (factor 1,44). Series de `funerario` (TF-IDF): 2020, 1.066 contratos y 48,6 miles de millones de pesos de 2025; 2021, 973 y 54,2; 2022, 805 y 36,5; 2023, 240 y 21,0; 2024, 295 y 24,0; 2025, 353 y 45,8; total 3.732 contratos y 230,1 miles de millones (189,6 en pesos corrientes). Sensibilidad (valor constante, 2020–2025): TF-IDF con `mixto` 3.821 contratos y 380,5; e5 3.639 y 202,8; e5 con `mixto` 3.753 y 365,9. La caída de 2022 a 2023 (de 805 a 240 contratos) coincide con el fin de SECOP I (2020–2022, D02): no es una caída del mercado sino un cambio de fuente, y la serie debe leerse por fuente (`serie_anual_fuente.csv`).
- **Descartado:** deflactar con el IPC anual (pierde la variación dentro del año); incluir las adiciones al valor (D14 las trata aparte).
- **Sustento:** `src/modelos/mercado_base.py`, `src/modelos/mercado.py`, tablas en `data/processed/resultados_secop/`; D14, D63.
- **Estado:** vigente (confirmada por Edward, 2026-10-26). Todas las cifras se recalculan con `python -m src.modelos.mercado`.
- **Sensibilidad con adiciones:** solo SECOP I informa el valor con adiciones (`valor_contrato_con_adiciones`); SECOP II trae únicamente los días adicionados, sin valor. Para los 2.396 contratos `funerario` de SECOP I (2020–2022, TF-IDF), el valor constante de 2025 pasa de 62,45 a 65,12 miles de millones al incluir adiciones (+4,3 %): +4,9 % en 2020 (27,00 → 28,31), +4,5 % en 2021 (20,13 → 21,04) y +2,9 % en 2022 (15,33 → 15,77); 207 contratos tienen adiciones. Tabla: `sensibilidad_adiciones_secop1.csv`. La serie principal sigue usando el valor inicial.

### D68. Patrones de compra: agrupaciones y reglas (borrador)
- **Decisión:** como borrador sin conclusiones, los contratos `funerario` del escenario principal se describen por (a) tipo de entidad, con reglas sobre el nombre de la entidad (salud/hospital/ESE, alcaldía o municipio, gobernación o departamento, empresa de servicios públicos, educación, seguridad y justicia, otra), además del orden de cada fuente y el sector de SECOP II; (b) modalidad agrupada (contratación directa, régimen especial, mínima cuantía, selección abreviada o subasta, licitación o concurso), con la participación de la contratación directa en el valor por año y fuente; (c) mes de firma; y (d) subtipo de servicio con reglas sobre el objeto, en este orden de prioridad: disposición de animales, cremación, plan o póliza exequial, traslado de cadáveres, cofres y bienes, inhumación de NN o población vulnerable, operación de cementerio y otro. Se dejan 40 contratos con su subtipo en `docs/revision_f4/subtipos.xlsx` (5 por subtipo, semilla 2026, con lista desplegable) para que Edward los valide.
- **Por qué (cifras del borrador):** tipo de entidad: alcaldías y municipios 85,3 % de los contratos y 54,4 % del valor. Modalidad: mínima cuantía 76,1 % de los contratos y 32,8 % del valor; contratación directa 13,3 % y 12,2 %; selección abreviada 5,9 % y 29,5 %; licitación o concurso 0,2 % y 16,2 %. Participación de la contratación directa en el valor: entre 3,8 % y 25,1 % según año y fuente, de 7,0 % en SECOP II 2025. Subtipo: inhumación de NN o vulnerables 60,0 % de los contratos y 43,6 % del valor; plan o póliza exequial 12,1 % y 5,6 %; cremación 4,1 % y 5,0 %; traslado 4,0 % y 1,9 %; cofres y bienes 3,5 % y 1,3 %; operación de cementerio 1,6 % y 9,5 %; disposición de animales 2 contratos; otro 14,8 % y 32,9 %. El orden de prioridad decide los casos que cumplen varias reglas (un contrato de cofres para población vulnerable queda en inhumación de vulnerables), y «vulnerable» incluye adultos mayores, víctimas y personas en vulnerabilidad.
- **Descartado:** presentar conclusiones sobre estos patrones antes de validar los subtipos; clasificar el subtipo con el modelo (no hay etiquetas de subtipo).
- **Sustento:** `src/modelos/mercado_patrones.py`, tablas `borrador_*.csv`; D21, D67.
- **Estado:** versión 1 reemplazada por la versión 2 (abajo) en lo que respecta a los subtipos (d); lo demás (tipo de entidad, modalidad y mes de firma) sigue como propuesta, requiere confirmación de Edward.
- **Versión 1, resultado de la validación (2026-10-26):** Edward revisó los 40 contratos de `docs/revision_f4/subtipos.xlsx`: las reglas del subtipo único acertaron 24 de 40 (60 %). Las causas: un solo subtipo obliga a elegir entre componentes que conviven en el mismo contrato (por ejemplo, traslado y cremación, o ataúdes y servicio funerario), el orden de prioridad decide arbitrariamente, y «servicios exequiales» se confundía con plan exequial.

**Versión 2 (vigente en el borrador, 2026-10-26): indicadores no excluyentes por componente.**
- **Decisión:** en lugar de un subtipo con prioridad, cada contrato `funerario` lleva siete indicadores booleanos que pueden coincidir: `incluye_inhumacion_cremacion` (inhumación, exhumación, cremación, sepelio o servicio funerario o exequial directo), `incluye_traslado` (traslado o manejo de cadáveres), `incluye_ataudes_bienes` (cofres, ataúdes, urnas, lápidas, cajas mortuorias, carrozas, cenizarios), `incluye_plan_exequial` (solo con plan, póliza, auxilio funerario o exequial, afiliación o seguro; «servicios exequiales» por sí solo es servicio directo y no plan), `incluye_operacion_cementerio` (cementerio, bóveda, osario, nicho o sepulturero junto con administración, operación, arriendo, concesión, mantenimiento o adquisición, con «osario» como palabra completa para no confundirlo con «Rosario»), `incluye_disposicion_animales` y `incluye_atencion_vulnerables_NN` (NN, no identificados o no reclamados, vulnerabilidad, pobreza, víctimas, adultos mayores; no se activa si es disposición de animales). El informe reporta, para cada componente, el porcentaje de contratos y de valor que lo incluye (los porcentajes no suman 100) y el 4,1 % de contratos que no incluye ninguno.
- **Por qué (resultados, 3.732 contratos):** incluye inhumación o cremación 62,3 % de los contratos y 69,8 % del valor; atención a vulnerables o NN, 77,1 % y 55,0 %; ataúdes y bienes, 30,8 % y 16,1 %; plan exequial, 8,9 % y 4,8 %; traslado, 6,6 % y 3,9 %; operación de cementerio, 1,6 % y 8,6 %; disposición de animales, 2 contratos; ninguno, 4,1 % y 6,6 %. Acierto contra los 40 de Edward, con la verdad por componente derivada de su subtipo único y las filas 10 y 16 (pasan de plan exequial a inhumación de vulnerables) y 31 (pasa de plan exequial a otro) corregidas con la definición nueva: sensibilidad 1,00 en inhumación o cremación (11 de 11), traslado (5), ataúdes y bienes (8), plan exequial (5), animales (1) y vulnerables o NN (11), y 0,75 en operación de cementerio (3 de 4); acierto de 0,98 en plan exequial, operación de cementerio y animales, 0,90 en traslado, 0,88 en ataúdes, 0,68 en inhumación o cremación y 0,57 en vulnerables o NN. **La medición es optimista: las reglas se ajustaron con esos mismos casos.** Además, Edward marcó un solo subtipo por contrato, de modo que la sensibilidad es confiable y la precisión (0,39 a 1,00) es un mínimo: un componente presente que no era el marcado cuenta como falso positivo. Dos filas de su revisión parecen inconsistentes entre sí (6 y 14, con el mismo texto de cuidado veterinario de animales, una como `otro` y otra como disposición de animales; 35 y 38, gastos de operación de un hospital, una como operación de cementerio y otra como `otro`).
- **Descartado:** conservar el subtipo único con prioridad (60 % de acierto); medir la precisión de los componentes como si el subtipo único agotara los componentes del contrato.
- **Sustento:** `src/modelos/mercado_patrones.py` (`COMPONENTES`, `acierto_indicadores`); `componentes.csv`, `componentes_anual.csv` y `acierto_indicadores.csv` en `data/processed/resultados_secop/`.
- **Estado:** propuesta, requiere confirmación de Edward (definición de los componentes). Recomendación: validar los componentes con una muestra nueva de contratos no vistos y con marcas no excluyentes.

### D69. Proveedores: identificador y concentración (borrador)
- **Decisión:** el proveedor se identifica por el NIT en SECOP I (personas jurídicas), por el código de proveedor en SECOP II y por el seudónimo de D15 en las personas naturales. La participación se mide en valor constante; el HHI es la suma de los cuadrados de las participaciones en porcentaje (0 a 10.000) y el CR4 la suma de las cuatro mayores. Se calculan por año a nivel nacional y por departamento de la entidad (2020–2025 agrupado, y se describe la distribución con los departamentos de 5 o más proveedores).
- **Por qué:** HHI nacional por año: 290 (2020), 470, 294, 676, 742 y 1.120 (2025); CR4 de 28,4 % a 60,6 %, es decir, mercado poco concentrado que sube, en parte porque en 2023–2025 solo queda SECOP II y hay menos contratos. Por departamento (31 con 5 o más proveedores): percentiles 10, 25, 50, 75 y 90 de 633, 918, 1.328, 1.941 y 2.778; 4 superan 2.500. El 41,4 % de los contratos tiene un proveedor persona natural. Los cinco proveedores de mayor valor reúnen el 25,0 % del valor.
- **Descartado:** unir proveedores entre SECOP I y II (D15: no hay identificador común para las personas naturales ni código común para las jurídicas); medir la concentración por número de contratos como cifra principal.
- **Sustento:** `src/modelos/mercado_patrones.py`; D15, D67.
- **Estado:** propuesta, requiere confirmación de Edward. Limitación: en 2020–2022 un mismo proveedor puede figurar en las dos fuentes con identificadores distintos, lo que subestima la concentración de esos años.

### D70. Cobertura de SECOP I después de 2022: conteo sin descarga
- **Decisión:** no se descarga nada de SECOP I posterior a 2022 hasta que Edward lo apruebe. Se contó en `f789-7hwg`, con la misma consulta de D16 y los estados de D42 (Celebrado, Liquidado y Terminado sin Liquidar), la fecha de firma en 2023, 2024 y 2025. La advertencia de cobertura queda en el informe del mercado público y D69 sigue como propuesta.
- **Por qué:** contratos candidatos firmados en SECOP I (filas, sin quitar `uid` repetidos): **1.914 en 2023, 1.841 en 2024 y 1.647 en 2025**, todos por encima del umbral de 50 fijado para avisar. Para comparar, en 2020–2022 la misma consulta dio 15.484 `uid` (unos 5.200 al año) y SECOP I tiene 337.246, 288.737 y 267.441 contratos firmados en esos tres años sin ningún filtro. Si la proporción de funerarios entre candidatos fuera la de 2020–2022 (2.396 de 15.484, 15,5 %), SECOP I aportaría del orden de 300, 285 y 255 contratos funerarios en 2023, 2024 y 2025, frente a los 240, 295 y 353 de SECOP II; es una estimación gruesa, no una medición. Consecuencia: la serie de 2023–2025 (D67) está incompleta, la caída de 2022 a 2023 es en buena parte un efecto de cobertura y el aumento del HHI (D69) puede serlo también, porque faltan contratos de SECOP I de entidades pequeñas. Los conteos y su fecha están en `logs/secop1_cobertura_2023_2025.jsonl` (consulta del 2026-10-26, entre las 13:10 y las 13:17).
- **Descartado:** descargar sin aviso (la regla era avisar si algún año superaba 50); suponer que SECOP I termina en 2022 (D02 lo fijó como límite de migración, no como límite del conjunto).
- **Sustento:** `src/etl/descargar_secop1.py` (consulta y estados); D02, D16, D42, D67, D69.
- **Estado:** pendiente de decisión de Edward: ¿extender SECOP I a 2023–2025 (unas 5.400 filas candidatas más, con el mismo procedimiento de D42 y D18)?

### D71. Análisis de robustez: SVM lineal y XGBoost sobre TF-IDF (sensibilidad)
- **Decisión:** como análisis de sensibilidad, sin cambiar D59 ni D63, se entrenan una SVM lineal (`LinearSVC`, C elegido entre 0,1 y 100 con validación cruzada interna de 3 pliegues) y un XGBoost (300 árboles, profundidad 4, tasa 0,1, `subsample` 0,8, `colsample_bytree` 0,5, semilla 2026, sin ajuste de hiperparámetros) con las mismas características TF-IDF (D56), los mismos 5 pliegues de D55 y el ajuste con las 400 etiquetas para los 60 de validación externa. Se reportan junto a los cuatro modelos de D24 en `data/processed/tabla_robustez.csv`, con las mismas métricas ponderadas e intervalos bootstrap. Las etiquetas de la validación externa son las entregadas originalmente (la revisión de las siete etiquetas de D63 sigue pendiente).
- **Por qué:** F1 de `funerario` (IC 95 %). **Validación cruzada, 392 casos:** reglas 0,870 (0,843–0,894); TF-IDF con regresión logística 0,932 (0,904–0,959); e5 0,946 (0,919–0,968); DeepSeek 0,979 (0,964–0,991); **SVM lineal 0,932 (0,903–0,959)**, con precisión 0,941 y sensibilidad 0,923, idénticas a las de la regresión logística; **XGBoost 0,887 (0,846–0,922)**, con precisión 0,934 y sensibilidad 0,844. **Validación externa, 60 casos, ponderado:** reglas 0,609 (0,380–0,892); TF-IDF 0,648 (0,389–0,970); e5 0,596 (0,352–0,916); DeepSeek 0,606 (0,357–0,943); **SVM lineal 0,662 (0,398–0,977)**; **XGBoost 0,611 (0,363–0,930)**. **Sin ponderar:** 0,754, 0,863, 0,766, 0,840, **0,885 (0,792–0,963)** y **0,792 (0,682–0,893)**. Los intervalos de la validación externa se solapan por completo entre todos los modelos. Lectura: los dos modelos lineales sobre TF-IDF son equivalentes en validación cruzada (0,932 y 0,932) y la SVM queda apenas por encima en la validación externa, sin diferencia distinguible del ruido; XGBoost rinde menos que ambos (pierde sensibilidad: 19 de 28 funerarios en la validación externa frente a 22 y 23). Ninguno cumple la condición de D59 para desplazar a TF-IDF (límite inferior mayor que el límite superior de TF-IDF, 0,959 en validación cruzada). La conclusión de D59 y D63 no cambia: la clasificación sigue siendo TF-IDF con regresión logística, y la robustez muestra que el resultado no depende de esa elección concreta de clasificador lineal.
- **Descartado:** reabrir D59 o D63 con estos resultados; ajustar los hiperparámetros de XGBoost mirando la validación externa (se dejaron fijos para no sobreajustar con 400 casos); calibrar probabilidades de la SVM (solo se usa la clase predicha).
- **Sustento:** `src/modelos/robustez.py`, `data/processed/tabla_robustez.csv` (no se versiona); `xgboost` 3.4.1 agregado a `requirements.txt`; D55, D56, D59, D63.
- **Estado:** vigente como análisis de sensibilidad. Limitación: con 60 casos de validación y un solo caso de peso 3.293 (V006), las diferencias entre modelos no son distinguibles; las predicciones de la SVM y de XGBoost en la validación cruzada quedan en `predicciones_cv_svm_lineal.parquet` y `predicciones_cv_xgboost.parquet`.

### D72. Contraste con la Encuesta Multipropósito 2021: existencia de microdatos y propuesta (sin descarga)
- **Decisión:** se verificó que existen microdatos públicos de la Encuesta Multipropósito Bogotá–Cundinamarca 2021 (DANE) y que la encuesta incluye una pregunta de tenencia de mascotas por hogar. No se descargó ningún microdato; solo se leyó la página del catálogo y el boletín técnico. Se propone cómo compararla con la población de perros de MinSalud, pendiente de que Edward autorice descargar el diccionario de datos y los capítulos necesarios.
- **Por qué (hallazgos):** (1) Catálogo: `microdatos.dane.gov.co/index.php/catalog/743`, operación DANE-DIMPE-EM-2021; 14 archivos comprimidos por capítulo (A a M, con M1 y M2) publicados en 2022, 107.119 hogares y 292.281 personas, recolección de abril a noviembre de 2021; cobertura de Bogotá (cabecera, centros poblados y rural disperso, con sus localidades), Soacha, Chía, Cota, Funza, La Calera, Mosquera y Sopó, y solo la cabecera de Facatativá, Zipaquirá, Fusagasugá, Madrid, Cajicá, Sibaté, El Rosal, Tocancipá, Tabio, Tenjo, Bojacá, Gachancipá, Subachoque y Zipacón. Licencia: la página habla de microdatos anonimizados de uso público gratuitos; exige citar al DANE y prohíbe redistribuirlos sin autorización; no confirma si pide registro. (2) La pregunta existe: el boletín técnico (sección 1.3.3, pp. 19–20) dice que se indagó al jefe o cónyuge del hogar por la tenencia de mascotas («perro, gato u otro»), entendida como cualquier animal de compañía que viva permanentemente en la misma vivienda; publica el 40,2 % de los hogares con mascota en la cabecera de Bogotá, entre 34,8 % (Fontibón) y 45,5 % (Antonio Nariño) por localidad, y entre 30,4 % y 59,7 % en las cabeceras municipales (Cota 59,7 %, Tabio 51,9 %, Zipacón 50,4 %; 14 de 21 con al menos 40 %). (3) Sin verificar: el capítulo y el nombre de la variable (el listado de capítulos del formulario no trae uno de mascotas), si separa perros de gatos, si pregunta cuántos animales y cuál es el factor de expansión. Eso lo dicen el diccionario (ZIP de 118 KB) y la estructura de la base (PDF de 488 KB) del mismo catálogo.
- **Propuesta de comparación:** (a) con el diccionario, localizar la variable, la unidad (hogar), el factor de expansión y las llaves geográficas (localidad y municipio). (b) Hogares con perro por unidad = suma de los factores de expansión de los hogares con perro; si hay conteo de animales, perros = suma de factor × número de perros; si solo hay indicador sí/no, esa suma es una **cota inferior** de la población de perros (al menos un perro por hogar). (c) Comparar con MinSalud en las unidades comunes: Bogotá (11001) y sus 20 localidades (tabla `minsalud_localidades_bogota.parquet`), Soacha, Chía, Cota, Funza, La Calera, Mosquera y Sopó, y las 14 cabeceras, teniendo en cuenta que MinSalud es municipal completo y la EM solo cubre la cabecera en 14 de ellos; para esos, comparar solo municipios sin población rural relevante o ajustar con la proporción de cabecera del DANE. (d) Años: MinSalud tiene 2019 (imputada salvo `posible_medido`), 2023 y 2024 (`no_detectable`) pero no 2021: comparar con ambos extremos y con la interpolación logarítmica a 2021, marcada. (e) Indicadores: razón MinSalud / cota inferior de la EM (debe ser mayor o igual a 1; menor de 1 indica subestimación de MinSalud), habitantes por perro de la EM frente a `hab_por_perro` de MinSalud (con el techo de 9 de la imputación, D43) y correlación de rangos entre hogares con perro de la EM y población de perros de MinSalud entre las unidades. (f) Intervalos: usar los errores de muestreo de la EM (declarados en la ficha metodológica) para decir si una razón es distinguible de 1.
- **Descartado:** descargar ahora los 14 capítulos (sin confirmar antes la variable en el diccionario); usar el 40,2 % de hogares con mascota como proxy directo de perros (mezcla gatos y otros y no da la población); comparar con departamentos fuera de Bogotá–Cundinamarca (la EM no los cubre).
- **Sustento:** catálogo `microdatos.dane.gov.co/index.php/catalog/743` y su boletín técnico (`Boletin_EM_2021.pdf`); D43, D46, D47.
- **Estado:** propuesta, requiere confirmación de Edward para descargar el diccionario y los capítulos. Limitación: la comparación cubre unos 22 municipios de una sola región urbana, con años que no coinciden.

### D73. SECOP I se extiende a 2023–2025 (reemplaza el supuesto de D02)
- **Decisión:** se descargan los contratos candidatos de SECOP I (`f789-7hwg`) firmados entre el 1 de enero de 2023 y el 31 de diciembre de 2025, con el mismo procedimiento de 2020–2022: consulta de D16, estados de D42 (Celebrado, Liquidado y Terminado sin Liquidar), una fila por `uid` (D18), señales y estratos de D17, anonimización de D15 y seudónimos de personas naturales con la misma sal. El crudo queda en `data/raw/secop/secop1_candidatos_2023_2025.jsonl` (registrado en el manifiesto); el de 2020–2022 no se toca. `python -m src.etl.descargar_secop1 descargar --desde 2023 --hasta 2025` y `python -m src.etl.contratistas_secop1 --desde 2023 --hasta 2025` parametrizan el periodo, y las señales leen todos los crudos de SECOP I. El supuesto de D02 de que la migración a SECOP II terminó en 2022 queda reemplazado: la migración no terminó.
- **Por qué (evidencia):** el conteo de D70 (2026-10-26) dio 1.914, 1.841 y 1.647 contratos candidatos de SECOP I en 2023, 2024 y 2025, frente a unos 5.200 al año en 2020–2022; esos años tienen además 337.246, 288.737 y 267.441 contratos firmados en SECOP I sin filtro. La descarga trajo 5.402 filas, igual a la suma de los conteos, y 5.080 `uid` únicos (1.794 en 2023, 1.737 en 2024 y 1.549 en 2025). Estratos de los nuevos: núcleo 1.324, pendientes 1.140 y sin señal 2.616; el 71 % de los contratistas son personas naturales (3.611 seudónimos, 1.865 distintos). Las 15.484 filas de 2020–2022 de `secop1_senales` y las 19.306 de SECOP II quedan idénticas. El universo pasa de 34.790 a 39.870 contratos.
- **Descartado:** dejar SECOP I en 2020–2022 (la serie 2023–2025 quedaba incompleta); reentrenar los clasificadores con los contratos nuevos (se aplican los ya entrenados, D74).
- **Sustento:** `src/etl/descargar_secop1.py`, `src/etl/contratistas_secop1.py`, `src/etl/senales_secop.py`; D02, D15, D16, D17, D18, D42, D70.
- **Estado:** vigente. Limitación (D74): ni la muestra de 400 ni la validación de 60 incluyen contratos de SECOP I de 2023–2025.
