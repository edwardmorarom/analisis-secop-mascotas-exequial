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
- **Por qué:** entre 2020 y 2022 las entidades migraron de SECOP I a SECOP II. En 2020, SECOP I tiene unos 6.400 candidatos y SECOP II solo 1.123. Sin SECOP I, 2020 quedaría subrepresentado más de cinco veces y la serie mostraría un crecimiento falso.
- **Descartado:** solo SECOP II (sesgo de migración).
- **Sustento:** conteos previos de F1 (commit 46aa476); Colombia Compra Eficiente, conjuntos `jbjy-vk9h` y `f789-7hwg`.
- **Estado:** vigente.

### D03. Descarga por API con paginación y token
- **Decisión:** se descarga con la API SoQL de Socrata, paginando, con `SOCRATA_APP_TOKEN`.
- **Por qué:** la exportación JSON del portal se trunca en 1.000 filas. Sin token, las consultas con muchos `LIKE` agotaban el tiempo de espera.
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
- **Por qué:** sirven para comprobar que las cifras de MinSalud son creíbles (agresiones por cada 1.000 perros). Los conjuntos de 2019 permiten validar con el mismo año los PDF de MinSalud. Los microdatos individuales exigen un formulario de solicitud (ver D01).
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
- **Estado:** vigente.

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
- **Por qué:** OSARIO coincidía con «ROSARIO» (5.943 filas, que bajan a 53 con el ajuste). ZOONOSIS traía contratos de salud pública (10.060 filas, que bajan a 20). Juntas eran el 82 % del ruido. Las 23 filas restantes de ZOONOSIS se marcan como posible disposición de animales para la parte de mascotas.
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
- **Por qué:** son contratos de apoyo a la gestión que los municipios firman con varias personas por el mismo valor. Una regla automática borraría contratos reales. Además, ninguno es funerario.
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
- **Por qué:** cada regla salió de un caso real de la muestra en el que la guía era ambigua. Si no se fijan por escrito, dos revisores etiquetan distinto y el κ baja por falta de criterio, no por dificultad real.
- **Estado:** vigente. La regla de búsqueda de personas (8) y la de infraestructura de Medicina Legal con `forense = 1` quedan como propuesta hasta la revisión de Harold.

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
- **Estado:** vigente.

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

### D29. Extraer el PDF de 2019 con pdfplumber y usar camelot solo donde pdfplumber falla
- **Decisión:** las tablas de las páginas 4–35 se leen con pdfplumber. Una fila que pdfplumber no separa en columnas se recupera con camelot (`stream`, backend Ghostscript), según D25.
- **Por qué:** pdfplumber detecta una tabla de 13 columnas por página y entrega 1.173 de las 1.174 filas sin celdas no numéricas. La fila «NACIONAL 2019» sale con todo el texto en la primera celda; camelot `stream` la recupera completa (13 columnas, 49.549.275 de población DANE) y camelot `lattice` no la devuelve.
- **Descartado:** camelot para todo el PDF (innecesario); LLM (no hizo falta).
- **Sustento:** D25; prueba de las dos variantes de camelot sobre la página 35; `respaldo camelot: página 35, 1 fila` en la salida del script.
- **Estado:** vigente.

### D30. El departamento de cada municipio se asigna por el total que cierra su bloque, no por el nombre
- **Decisión:** el PDF lista los municipios de cada departamento seguidos de una fila de total. Una fila se acepta como total departamental si su nombre es un departamento de DIVIPOLA y la suma de la población DANE del bloque difiere de ella menos de 3 %. Todas las filas anteriores desde el total previo pertenecen a ese departamento.
- **Por qué:** 32 de 32 departamentos quedan reconocidos; la diferencia de población del bloque es 0 en 31 departamentos y 120 personas (0,0018 %) en Antioquia. Hay nombres que son a la vez departamento y municipio (BOLÍVAR, CÓRDOBA, NARIÑO, CALDAS, ARAUCA), de modo que el nombre solo no sirve.
- **Descartado:** asignar el departamento por nombre del municipio; usar la tabla de DIVIPOLA para asignarlo (los nombres del PDF no coinciden de forma fiable).
- **Sustento:** `asignar_bloques` en `src/etl/extraer_minsalud.py`; 32 filas `departamento_total`.
- **Estado:** vigente.

### D31. Seis distritos van como DTS aparte, fuera del total de su departamento
- **Decisión:** Barranquilla, Bogotá, Buenaventura, Cali, Cartagena y Santa Marta se tratan como `tipo = distrito`. Se detectan como el subconjunto de filas de distrito que hace cuadrar la población del bloque, y su código DIVIPOLA sale de una tabla explícita (08001, 11001, 76109, 76001, 13001, 47001).
- **Por qué:** estas filas aparecen mezcladas dentro de otros bloques y no suman en el total de su departamento: el bloque de Bolívar solo cierra si se excluyen Barranquilla y Bogotá; Caldas, si se excluye Buenaventura; Caquetá, si se excluye Cali; Casanare, si se excluye Cartagena; Santander, si se excluye Santa Marta. El PDF escribe «BARRABQUILLA»; se corrige con una tabla de equivalencias (el valor impreso se conserva en `municipio_pdf`).
- **Descartado:** sumarlas al departamento (rompe 5 totales); unirlas por nombre difuso.
- **Sustento:** prototipo de bloques; 6 filas `distrito`.
- **Estado:** vigente.

### D32. Las 20 localidades de Bogotá se guardan aparte y no cuentan como municipios
- **Decisión:** las filas sin población DANE (20, páginas 8–9, de Usaquén a Sumapaz) llevan `tipo = localidad` y `bloque = DISTRITO`. No se cruzan con DIVIPOLA.
- **Por qué:** suman exactamente la fila «BOGOTÁ» en las siete columnas aditivas que traen datos (población de perros 1.084.214, de gatos 126.606, de perros y gatos 1.210.820, vacunados DTS 380.342, particulares 410.097, perros vacunados 621.281, acumulado 790.439). Una de ellas, SAN CRISTÓBAL, repite el nombre de un municipio de Bolívar.
- **Descartado:** contarlas como municipios (inflaría el total en 1.084.214 perros y colisionaría con códigos de DIVIPOLA).
- **Sustento:** comparación localidades frente a fila Bogotá.
- **Estado:** vigente.

### D33. Cruce con DIVIPOLA por nombre dentro del departamento, en cuatro pasos
- **Decisión:** (1) nombre normalizado igual, único dentro del departamento: 1.039 filas; (2) tabla de equivalencias explícita (departamento + nombre del PDF → código): 16 filas; (3) aproximado con `token_set_ratio ≥ 90` y margen ≥ 5 sobre el segundo candidato, solo entre códigos aún libres: 59 filas, revisadas una por una; (4) distritos por tabla: 6. Las filas sin cruce quedan con `cod_divipola` nulo, sin inventar código.
- **Por qué:** cruzan 1.120 de 1.121 filas municipales y de distrito; 0 códigos repetidos. Sin cruce: Mapiripana (Guainía), que no aparece en `dane_divipola.csv`. DIVIPOLA sin fila en el PDF: Turbo (05837) y Nuevo Belén de Bajirá (27493).
- **Descartado:** fuzzy global sin restringir al departamento; validar el cruce con la población DANE (ver D34).
- **Sustento:** `cruzar_divipola`; la tabla `EQUIVALENCIAS_MUNICIPIO` está en el código.
- **Estado:** vigente. Los 59 aproximados y los 16 de la tabla deben revisarse una vez más con muestra manual (condición de F2).

### D34. La «Población DANE 2018» del PDF no se usa como llave ni para validar el cruce
- **Decisión:** se conserva `poblacion_dane` tal como se imprime, pero no se asume igual a las proyecciones DANE.
- **Por qué:** de 1.056 filas con cruce (versión previa del cruce), solo 1 coincide con la serie 2018–2042 del DANE; frente a la serie 2005–2017 (año 2017, 1.039 cruces exactos) la razón mediana es 1,017 con rango 0,32–3,36. Es otra base, no la serie que tenemos. Ejemplo: Leticia 42.280 en el PDF y 48.182 en la serie 2018.
- **Descartado:** corregir o reemplazar la cifra impresa.
- **Sustento:** comparación contra `dane_proyecciones_municipales_2018_2042.xlsx` y `_2005_2017.xlsx`.
- **Estado:** abierta. Afecta a D14: falta decidir qué denominador usa el panel para «habitantes por perro» (la cifra del PDF o la proyección DANE de la serie vigente).

### D35. Los totales departamentales impresos se conservan y se comparan; no se corrigen los municipios
- **Decisión:** los totales del PDF van a `minsalud_2019_departamentos.parquet`, con suma de municipios, valor impreso y diferencia por columna. Los valores de los municipios quedan como se imprimen.
- **Por qué:** 8 de 32 departamentos cierran exactamente en todas las columnas; 24 difieren. Población DANE: diferencia máxima 0,0018 % (Antioquia, −120). Perros y gatos: hasta 0,2 % (Vaupés). Las diferencias grandes están en perros vacunados y acumulado: Cundinamarca −7.860 y −11.535 (3,0 % del acumulado), Guainía −912 (16,7 % de sus perros vacunados), Antioquia acumulado −8.236, Quindío −573, Cesar −361. A nivel nacional, la suma de municipios y distritos queda por debajo de «NACIONAL 2019» en 120 de población, 8.885 perros vacunados y 21.318 en el acumulado.
- **Descartado:** reescalar municipios para cerrar totales (inventaría datos).
- **Sustento:** `comparar_departamentos`; es la validación contra los totales impresos que exige D25. Las diferencias son incidencias del propio PDF para el agente de F6, no errores de extracción: los municipios se leyeron tal como están impresos.
- **Estado:** vigente.

### D36. Celdas vacías son nulas y las coberturas se guardan como enteros impresos
- **Decisión:** una celda vacía (p. ej. ciudadanos venezolanos o revacunados en foco en municipios sin dato) queda nula, no cero. Las coberturas se guardan como el entero impreso, sin recalcular.
- **Por qué:** «0» y «sin dato» significan cosas distintas; la regla del CLAUDE.md es conservar el valor tal como viene.
- **Descartado:** rellenar con 0; recalcular coberturas desde los conteos (se compara después, en F3).
- **Sustento:** columnas `vacunados_venezolanos`, `revacunados_foco` y `cobertura_*` de `minsalud_2019.parquet`.
- **Estado:** vigente.

### D37. Solo 2019 está implementado; los demás años se revisan antes
- **Decisión:** `--anio` rechaza cualquier año distinto de 2019 hasta revisar el formato de ese PDF.
- **Por qué:** los formatos cambian entre años (CLAUDE.md) y el parser de 2019 depende de sus 13 columnas y de la estructura de bloques.
- **Descartado:** un parser genérico sin revisar cada año.
- **Sustento:** instrucción de empezar solo por 2019 y detenerse para revisión.
- **Estado:** vigente.
