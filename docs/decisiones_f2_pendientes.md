# Decisiones de F2 pendientes de pasar a `docs/decisiones.md`

`docs/decisiones.md` no estaba en el repositorio cuando se hizo esta extracción (no existe en el árbol de trabajo ni en el historial de git). Estas entradas siguen el formato del registro y usan una numeración provisional desde D29 (el registro tiene 28 decisiones). Hay que pegarlas en `decisiones.md` y ajustar los números.

Alcance: `minsalud_vacunacion_2019.pdf`, extraído con `python -m src.etl.extraer_minsalud --anio 2019` → `data/interim/minsalud_2019.parquet` y `minsalud_2019_departamentos.parquet`.

---

## D29. Extraer el PDF de 2019 con pdfplumber y usar camelot solo donde pdfplumber falla
- **Decisión:** las tablas de las páginas 4–35 se leen con pdfplumber. Una fila que pdfplumber no separa en columnas se recupera con camelot (`stream`, backend Ghostscript), según D25.
- **Por qué:** pdfplumber detecta una tabla de 13 columnas por página y entrega 1.173 de las 1.174 filas sin celdas no numéricas. La fila «NACIONAL 2019» sale con todo el texto en la primera celda; camelot `stream` la recupera completa (13 columnas, 49.549.275 de población DANE) y camelot `lattice` no la devuelve.
- **Descartado:** camelot para todo el PDF (innecesario); LLM (no hizo falta).
- **Sustento:** D25; prueba de las dos variantes de camelot sobre la página 35; `respaldo camelot: página 35, 1 fila` en la salida del script.
- **Estado:** vigente.

## D30. El departamento de cada municipio se asigna por el total que cierra su bloque, no por el nombre
- **Decisión:** el PDF lista los municipios de cada departamento seguidos de una fila de total. Una fila se acepta como total departamental si su nombre es un departamento de DIVIPOLA y la suma de la población DANE del bloque difiere de ella menos de 3 %. Todas las filas anteriores desde el total previo pertenecen a ese departamento.
- **Por qué:** 32 de 32 departamentos quedan reconocidos; la diferencia de población del bloque es 0 en 31 departamentos y 120 personas (0,0018 %) en Antioquia. Hay nombres que son a la vez departamento y municipio (BOLÍVAR, CÓRDOBA, NARIÑO, CALDAS, ARAUCA), de modo que el nombre solo no sirve.
- **Descartado:** asignar el departamento por nombre del municipio; usar la tabla de DIVIPOLA para asignarlo (los nombres del PDF no coinciden de forma fiable).
- **Sustento:** `asignar_bloques` en `src/etl/extraer_minsalud.py`; 32 filas `departamento_total`.
- **Estado:** vigente.

## D31. Seis distritos van como DTS aparte, fuera del total de su departamento
- **Decisión:** Barranquilla, Bogotá, Buenaventura, Cali, Cartagena y Santa Marta se tratan como `tipo = distrito`. Se detectan como el subconjunto de filas de distrito que hace cuadrar la población del bloque, y su código DIVIPOLA sale de una tabla explícita (08001, 11001, 76109, 76001, 13001, 47001).
- **Por qué:** estas filas aparecen mezcladas dentro de otros bloques y no suman en el total de su departamento: el bloque de Bolívar solo cierra si se excluyen Barranquilla y Bogotá; Caldas, si se excluye Buenaventura; Caquetá, si se excluye Cali; Casanare, si se excluye Cartagena; Santander, si se excluye Santa Marta. El PDF escribe «BARRABQUILLA»; se corrige con una tabla de equivalencias (el valor impreso se conserva en `municipio_pdf`).
- **Descartado:** sumarlas al departamento (rompe 5 totales); unirlas por nombre difuso.
- **Sustento:** prototipo de bloques; 6 filas `distrito`.
- **Estado:** vigente.

## D32. Las 20 localidades de Bogotá se guardan aparte y no cuentan como municipios
- **Decisión:** las filas sin población DANE (20, páginas 8–9, de Usaquén a Sumapaz) llevan `tipo = localidad` y `bloque = DISTRITO`. No se cruzan con DIVIPOLA.
- **Por qué:** suman exactamente la fila «BOGOTÁ» en las siete columnas aditivas que traen datos (población de perros 1.084.214, de gatos 126.606, de perros y gatos 1.210.820, vacunados DTS 380.342, particulares 410.097, perros vacunados 621.281, acumulado 790.439). Una de ellas, SAN CRISTÓBAL, repite el nombre de un municipio de Bolívar.
- **Descartado:** contarlas como municipios (inflaría el total en 1.084.214 perros y colisionaría con códigos de DIVIPOLA).
- **Sustento:** comparación localidades frente a fila Bogotá.
- **Estado:** vigente.

## D33. Cruce con DIVIPOLA por nombre dentro del departamento, en cuatro pasos
- **Decisión:** (1) nombre normalizado igual, único dentro del departamento: 1.039 filas; (2) tabla de equivalencias explícita (departamento + nombre del PDF → código): 16 filas; (3) aproximado con `token_set_ratio ≥ 90` y margen ≥ 5 sobre el segundo candidato, solo entre códigos aún libres: 59 filas, revisadas una por una; (4) distritos por tabla: 6. Las filas sin cruce quedan con `cod_divipola` nulo, sin inventar código.
- **Por qué:** cruzan 1.120 de 1.121 filas municipales y de distrito; 0 códigos repetidos. Sin cruce: Mapiripana (Guainía), que no aparece en `dane_divipola.csv`. DIVIPOLA sin fila en el PDF: Turbo (05837) y Nuevo Belén de Bajirá (27493).
- **Descartado:** fuzzy global sin restringir al departamento; validar el cruce con la población DANE (ver D34).
- **Sustento:** `cruzar_divipola`; la tabla `EQUIVALENCIAS_MUNICIPIO` está en el código.
- **Estado:** vigente. Los 59 aproximados y los 16 de la tabla deben revisarse una vez más con muestra manual (condición de F2).

## D34. La «Población DANE 2018» del PDF no se usa como llave ni para validar el cruce
- **Decisión:** se conserva `poblacion_dane` tal como se imprime, pero no se asume igual a las proyecciones DANE.
- **Por qué:** de 1.056 filas con cruce (versión previa del cruce), solo 1 coincide con la serie 2018–2042 del DANE; frente a la serie 2005–2017 (año 2017, 1.039 cruces exactos) la razón mediana es 1,017 con rango 0,32–3,36. Es otra base, no la serie que tenemos. Ejemplo: Leticia 42.280 en el PDF y 48.182 en la serie 2018.
- **Descartado:** corregir o reemplazar la cifra impresa.
- **Sustento:** comparación contra `dane_proyecciones_municipales_2018_2042.xlsx` y `_2005_2017.xlsx`.
- **Estado:** abierta. Falta decidir qué denominador usa el panel para «habitantes por perro» (el del PDF o el DANE de la serie vigente).

## D35. Los totales departamentales impresos se conservan y se comparan; no se corrigen los municipios
- **Decisión:** los totales del PDF van a `minsalud_2019_departamentos.parquet`, con suma de municipios, valor impreso y diferencia por columna. Los valores de los municipios quedan como se imprimen.
- **Por qué:** 8 de 32 departamentos cierran exactamente en todas las columnas; 24 difieren. Población DANE: diferencia máxima 0,0018 % (Antioquia, −120). Perros y gatos: hasta 0,2 % (Vaupés). Las diferencias grandes están en perros vacunados y acumulado: Cundinamarca −7.860 y −11.535 (3,0 % del acumulado), Guainía −912 (16,7 % de sus perros vacunados), Antioquia acumulado −8.236, Quindío −573, Cesar −361. A nivel nacional, la suma de municipios y distritos queda por debajo de «NACIONAL 2019» en 120 de población, 8.885 perros vacunados y 21.318 en el acumulado.
- **Descartado:** reescalar municipios para cerrar totales (inventaría datos).
- **Sustento:** `comparar_departamentos`; son incidencias del PDF para el agente de F6.
- **Estado:** vigente.

## D36. Celdas vacías son nulas y las coberturas se guardan como enteros impresos
- **Decisión:** una celda vacía (p. ej. ciudadanos venezolanos o revacunados en foco en municipios sin dato) queda nula, no cero. Las coberturas se guardan como el entero impreso, sin recalcular.
- **Por qué:** «0» y «sin dato» significan cosas distintas; la regla del CLAUDE.md es conservar el valor tal como viene.
- **Descartado:** rellenar con 0; recalcular coberturas desde los conteos (se compara después, en F3).
- **Sustento:** columnas `vacunados_venezolanos`, `revacunados_foco` y `cobertura_*` de `minsalud_2019.parquet`.
- **Estado:** vigente.

## D37. Solo 2019 está implementado; los demás años se revisan antes
- **Decisión:** `--anio` rechaza cualquier año distinto de 2019 hasta revisar el formato de ese PDF.
- **Por qué:** los formatos cambian entre años (CLAUDE.md) y el parser de 2019 depende de sus 13 columnas y de la estructura de bloques.
- **Descartado:** un parser genérico sin revisar cada año.
- **Sustento:** instrucción de empezar solo por 2019 y detenerse para revisión.
- **Estado:** vigente.
