# Cómo contrata el Estado los servicios funerarios: muestreo y clustering en SECOP, 2020–2025

Estudio del Pregrado en Estadística de la Universidad Santo Tomás (Bogotá), presentado en el Statistical DataPulse 2026 (11 y 12 de noviembre de 2026).

**Equipo:** Edward Mora (edwardmora@usantotomas.edu.co), Natalia Carrero (nataliacarrero@usantotomas.edu.co) y Harold Funeme (haroldfuneme@usantotomas.edu.co).

Aquí están el código, las decisiones de método, los libros de etiquetado, las revisiones y los resultados del estudio.

> **Sobre el historial.** El proyecto empezó con dos líneas: la contratación funeraria del Estado en SECOP y un estudio del mercado de previsión exequial de mascotas. La segunda se dejó de lado para concentrarnos en SECOP, que es lo que se presenta aquí. Por eso el historial, algunas ramas y algunos archivos corresponden a esa línea y no forman parte de los resultados: los módulos de MinSalud, INS, cámaras de comercio y EM 2021 en `src/etl/`, `src/agentes/` y las decisiones D04–D10, D25–D27, D29–D41, D43–D53, D64, D65, D72, D75, D76, D87, D88 y D100.

- **Referencias y fuentes de datos:** [`BIBLIOGRAFIA.md`](BIBLIOGRAFIA.md), y la versión diseñada a la que lleva el código del póster y de la presentación: [canva.link/knpzwi9a2n4q4f3](https://canva.link/knpzwi9a2n4q4f3)
- **Póster, presentación y guía metodológica:** [`entregables/`](entregables/)
- **Registro de decisiones:** [`docs/decisiones.md`](docs/decisiones.md)

## Resultados principales

| Resultado | Cifra | Dónde se sustenta |
|---|---|---|
| Candidatos en SECOP I y II | 39.870 | `docs/resultados/cierre_f4.md`, D73 |
| Proporción funeraria entre los candidatos (muestra estratificada de 400) | 10,5 % (IC 95 %: 10,0–11,1) | D79 |
| Acuerdo entre revisores (κ de Cohen) | 0,683, bajo el umbral fijado de 0,70 | D54 |
| F1 ponderado del clasificador TF-IDF en la validación externa | 0,956 (IC 95 %: 0,908–0,996) | D92, D94 |
| Valor del mercado, estimador de diferencia | 254,0 mil millones de pesos de 2025 (IC 95 %: 225,4–304,5) | D93 |
| Contratos funerarios clasificados | 4.985 | D84, D105 |
| Contrato promedio, 2020 → 2025 | 42 → 55 millones; dentro de SECOP I, 28 → 27, y dentro de SECOP II, 203 → 82 | `docs/resultados/f4_mercado_publico.md` |
| Contratos firmados por alcaldías | 88,7 % | `docs/resultados/f4_mercado_publico.md` |
| Contratos firmados de febrero a abril | 43 % | `docs/resultados/patrones_compra.md`, perfil mensual |
| Grupos estables de HCPC (Jaccard medio ≥ 0,75) | 8 | D99 |

El contrato promedio sube por composición: SECOP II, donde los contratos son más grandes, pasó del 8 % al 51 % de los contratos (paradoja de Simpson). Ningún modelo de clases latentes cumplió la independencia local (D97, D98), así que los grupos del ACM y el HCPC son descriptivos.

## Entregables (`entregables/`)

| Archivo | Contenido |
|---|---|
| `presentacion_secop.html` | Presentación de 33 láminas: 32 de exposición y una con los códigos de las referencias y del repositorio. Se abre en el navegador, sin conexión. Las gráficas de las láminas 20, 21 y 22 muestran sus valores al pasar el cursor y permiten filtrar las series desde la leyenda. |
| `poster/poster_secop_funerario.pdf` | Póster de 90 × 120 cm. La fuente LaTeX y las gráficas en TikZ (`figs_tikz/`) están en la misma carpeta. |
| `guia_metodologica.html` y `.pdf` | Guía de lectura: qué significa cada indicador, cómo se infiere, qué supuestos se verificaron y qué se descartó. |

## Evidencia del proceso

### Etiquetado (`docs/etiquetado/`)

| Archivo | Contenido |
|---|---|
| `guia_etiquetado.docx` | Libro de códigos que siguieron los revisores. |
| `etiquetado_edward.xlsx`, `etiquetado_natalia.xlsx` | Etiquetado doble y ciego de la muestra de 400 contratos (κ de D54). |
| `etiquetado_harold.xlsx` | Desempate de los desacuerdos por un tercer revisor. |
| `etiquetado_final.xlsx` | Etiquetas finales y revisión de cada desacuerdo. |
| `validacion_edward.xlsx` | Validación externa de 60 contratos. |

### Revisiones (`docs/revision_f4/`)

Cada libro es una revisión humana registrada en una decisión de `docs/decisiones.md`: los 50 contratos de mayor valor, los 150 del estrato D, los 40 humanitarios, los 100 no recuperados por la búsqueda, los 30 de SECOP I 2023–2025, las siete etiquetas revisadas, el grupo 5 y las variables derivadas.

### Método y resultados

| Archivo | Contenido |
|---|---|
| `docs/decisiones.md` | Cada decisión con su razón, lo descartado, el sustento y el estado. Las reglas de cada análisis se registraron antes de correrlo. |
| `docs/resultados/cierre_f4.md` | Cierre del mercado público: cada cifra con su decisión y su archivo de origen. |
| `docs/resultados/f4_mercado_publico.md` | Tamaño, evolución, territorio, modalidades y concentración de proveedores. |
| `docs/resultados/patrones_compra.md` | Clases latentes, modelos del valor, estacionalidad y COVID-19. |
| `docs/resultados/grupos_hcpc.md` | Los 8 grupos estables y sus categorías características. |
| `docs/resultados/mortalidad_por_grupo.md` | Perfil descriptivo de mortalidad por grupo (D108). |
| `docs/resultados/causas_defuncion.md` | Causas de defunción por departamento; los modelos se retiraron en D107c. |
| `docs/resultados/coeficientes_tfidf.md` | Coeficientes del clasificador, para auditar qué palabras pesan. |
| `docs/resultados/sensibilidad_mixtos.md` | Cuánto cambia el mercado según cómo se traten los contratos mixtos. |
| `docs/resultados/perfil_variables_secop.md` | Perfil de las variables de los contratos funerarios. |
| `docs/resultados/regla_servicios_profesionales.md` | Contratos de servicios profesionales con término funerario (D92). |
| `docs/resultados/graficos/` | Gráficos de diagnóstico y de resultados. |
| `docs/resultados/resumen_*.md`, `reproducibilidad_2026-11-01.md` | Resúmenes de sesión y la tabla de reproducibilidad del 1 de noviembre. El historial completo está en los commits. |
| `docs/resultados/validacion_deepseek.md` | Validación ampliada de DeepSeek frente a TF-IDF con 343 contratos etiquetados fuera de la muestra (D110). |

### Código

| Carpeta | Contenido |
|---|---|
| `src/etl/` | Descarga de SECOP I y II, DANE e INS; anonimización (D15) y manifiesto con SHA-256. |
| `src/evaluacion/` | Diseño muestral, plantillas de etiquetado, κ y métricas ponderadas. |
| `src/modelos/` | Clasificadores, estimador de diferencia, modelos del valor y de la estacionalidad (Python y R), clases latentes, ACM, HCPC y validación de los grupos. |
| `tests/` | Pruebas con `pytest`. |

## Lo que no está en el repositorio

- **Datos (`data/`).** Son públicos y se descargan con `src/etl/` desde Datos Abiertos Colombia y el DANE (ver [`BIBLIOGRAFIA.md`](BIBLIOGRAFIA.md), sección 9). Cada descarga queda en un manifiesto con su URL, fecha y SHA-256.
- **Claves (`.env`).** `.env.example` muestra qué variables hacen falta.
- **Datos personales.** Los nombres, documentos y teléfonos que aparecen en texto libre se eliminan, y las personas naturales se reemplazan por un seudónimo (D15, Ley 1581 de 2012). Los libros de etiquetado y de revisión se publican con el texto ya anonimizado.

## Reproducir

```bash
python -m venv .venv
.venv\Scripts\activate     # en Windows; en Linux o macOS: source .venv/bin/activate
pip install -r requirements.lock.txt
cp .env.example .env        # completar las claves
python -m pytest
python -m src.modelos.cierre_f4
```

Los modelos de `src/modelos/*.R` necesitan R 4.6 con `FactoMineR`, `poLCA`, `lme4`, `MASS`, `car` y `cluster`. Las semillas están fijas (`seed: 2026` en `config.yaml`; 2034 en los bootstrap de D98).
