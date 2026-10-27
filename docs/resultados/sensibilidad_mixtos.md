# Sensibilidad del mercado a los contratos mixtos (diagnóstico)

Solo diagnóstico: no se registra ninguna decisión ni se cambia el estimador. Generado por `python -m src.modelos.sensibilidad_mixtos`. Valores en miles de millones de pesos de 2025 salvo que se indique.

## 1. Ayuda humanitaria con componente funerario en todo el marco

Marco: los 39.870 contratos candidatos de SECOP I y II, 2020–2025. Criterio: el objeto (sin tildes, en mayúsculas) contiene «asistencia(s) funeraria(s)», «gasto(s) funerario(s)» o «auxilio(s) funerario(s)» **y** alguno de «humanitari-», «víctimas», «justicia transicional», «vulnerable» o «COVID».

**317 contratos, 175,0 miles de millones.** Como son más de 80, **no se exportó** `mixtos_humanitarios.xlsx`.

### Por estrato de la muestra

| grupo | contratos | valor_mm |
|---|---|---|
| A1_palabra_y_unspsc | 256 | 9,1 |
| A2_solo_palabra | 61 | 166,0 |

### Por origen de la etiqueta humana (NaN = sin revisión humana)

| grupo | contratos | valor_mm |
|---|---|---|
| adicionales_d81 | 1 | 9,0 |
| muestra_400 | 10 | 3,8 |
| top_valor | 10 | 146,5 |
| sin etiqueta | 296 | 15,7 |

### Por predicción de TF-IDF (sin jerarquía de etiquetas)

| grupo | contratos | valor_mm |
|---|---|---|
| funerario | 282 | 22,2 |
| mixto | 12 | 146,7 |
| no_funerario | 23 | 6,1 |

### Por etiqueta humana

| grupo | contratos | valor_mm |
|---|---|---|
| funerario | 7 | 2,0 |
| mixto | 12 | 153,7 |
| no_funerario | 2 | 3,6 |
| sin etiqueta | 296 | 15,7 |

### Por fuente

| grupo | contratos | valor_mm |
|---|---|---|
| secop1 | 206 | 140,7 |
| secop2 | 111 | 34,3 |

### Por año

| grupo | contratos | valor_mm |
|---|---|---|
| 2020 | 58 | 137,3 |
| 2021 | 48 | 4,6 |
| 2022 | 49 | 4,4 |
| 2023 | 53 | 5,2 |
| 2024 | 47 | 4,6 |
| 2025 | 62 | 18,9 |

Con etiqueta humana: 21 contratos (en la muestra de 400: 10; en la revisión censal por valor: 10; en D81: 1). Sin etiqueta humana: 296.

## 2. Estimador de diferencia (TF-IDF, sin mixto)

El caso A reproduce el estimador publicado (D85). En B, M214 sale del marco y de la muestra (N y n de su estrato bajan en uno). En C, los 317 contratos salen de la muestra y del marco muestral y se corrigen exactamente como censo: con la etiqueta humana donde existe y, en los 296 sin etiqueta, con el supuesto indicado (C0 no funerario; C1 funerario). C0 y C1 son los dos extremos posibles; la etiqueta real de esos 296 la pondrá la revisión. M214 es uno de los 317, por lo que en C queda como censal con su etiqueta `mixto`.

| caso | total_sin_corregir_mm | estimador_mm | ic95_bajo_mm | ic95_alto_mm | correccion_censo_mm | correccion_muestra_400_mm |
|---|---|---|---|---|---|---|
| A. Con M214 (estimador publicado, D85) | 262,9 | 198,4 | 79,2 | 284,3 | -29,9 | -34,6 |
| B. Sin M214 (se saca del marco y de la muestra) | 259,9 | 243,9 | 210,2 | 293,6 | -29,9 | 13,9 |
| C0. Humanitarios como estrato censal; sin etiqueta humana se supone no funerario (mixto) | 262,9 | 244,5 | 215,2 | 292,8 | -43,0 | 24,6 |
| C1. Humanitarios como estrato censal; sin etiqueta humana se supone funerario | 262,9 | 260,2 | 230,9 | 308,5 | -27,2 | 24,6 |

## 3. Componente «traslado» activado sin servicio funerario

`incluye_traslado` usa la expresión `TRASLADO|MANEJO DE (CADÁVERES|CUERPOS)|TRANSPORTE DE (CADÁVER|CUERPO|RESTOS|DIFUNTO)|RECOLECCIÓN DE (CADÁVER|CUERPO)`. Aquí se cuentan los contratos donde se activó solo por la palabra «traslado» (o «traslado y transporte» de otra cosa): sin una expresión de cadáver, cuerpo, restos, difunto u occiso cerca de «traslado/transporte/recolección/levantamiento» y sin las raíces FUNERA, INHUMA, SEPELIO, EXEQU, SEPULT, EXHUMA, FUNEBRE, CREMACI, CADAVER, OCCISO ni CEMENTERIO en el objeto.

- Contratos con `incluye_traslado` en el marco: 613. Solo por traslado sin servicio funerario: **136** (3,9 miles de millones); de ellos, 40 mencionan emergencia, urgencia, ambulancia, paciente o referencia.
- Entre los contratos que TF-IDF (con la jerarquía de etiquetas) marca `funerario`: 304 tienen traslado, de los cuales **5** lo tienen solo por esa vía; con `mixto` incluido, 319 y 5.
- Clase de TF-IDF de los 136: no_funerario 131, funerario 5.

Los 5 que TF-IDF marca `funerario` sí tienen componente funerario (cofres o servicios mortuorios) que la raíz de servicio no recoge; el traslado va junto a bienes funerarios.

### 10 ejemplos (los 5 que TF-IDF marca funerario y los 5 de mayor valor entre el resto; objeto anonimizado y recortado a 260 caracteres)

| fuente | anio | clase | valor_mm | objeto_anon |
|---|---|---|---|---|
| secop1 | 2020 | funerario | 0,032 | PRESTACIÓN DE SERVICIOS MORTUORIOS; PARA LA ACTIVACIÓN DE PROTOCOLOS; PROCESOS DE DESINFECCIÓN; EMBALAJE DEL CUERPO; TRASLADO Y DISPOSICIÓN FINAL PARA CASOS O POSIBLES CASOS CON COVID-19 EN LA POBLACIÓN VULNERABLE DEL MUNICIPIO DE SAN SEBASTIAN DE BUENAVISTA M |
| secop2 | 2021 | funerario | 0,014 | SUMINISTRAR COFRES MORTUORIOS Y TRASLADOS DENTRO Y FUERA DEL DEPARTAMENTO PARA LA POBLACION VICTIMA DEL CONFLICTO ARMADO EN EL DEPARTAMENTO DEL CAQUETA. |
| secop2 | 2022 | funerario | 0,013 | SUMINISTRAR COFRES MORTUORIOS Y TRASLADOS DENTRO Y FUERA DEL DEPARTAMENTO PARA LA POBLACION VICTIMA DEL CONFLICTO ARMADO EN EL DEPARTAMENTO DEL CAQUETA. |
| secop2 | 2023 | funerario | 0,011 | SUMINISTRAR COFRES MORTUORIOS Y TRASLADOS DENTRO Y FUERA DEL DEPARTAMENTO PARA LA POBLACION VICTIMA DEL CONFLICTO ARMADO EN EL DEPARTAMENTO DE CAQUETA |
| secop2 | 2024 | funerario | 0,011 | SUMINISTRAR COFRES MORTUORIOS Y TRASLADOS DENTRO Y FUERA DEL DEPARTAMENTO PARA LA POBLACION VICTIMA DEL CONFLICTO ARMADO EN EL DEPARTAMENTO DE CAQUETA. |
| secop2 | 2025 | no_funerario | 0,588 | El contratista se compromete con el Municipio de Pasto - Secretaria de Gobierno a entregar un (1) vehículo con adecuación y transformación de carrocería especial tipo NECROMOVIL; matrícula y registro; SOAT; mantenimientos hasta los 50.000k/m y traslado hasta l |
| secop1 | 2021 | no_funerario | 0,289 | ADQUISICIÓN Y DOTACIÓN DE AMBULANCIA TIPO TRANSPORTE ASISTENCIAL BÁSICO (TAB) PARA EL TRASLADO DE PACIENTES DE LA EMPRESA SOCIAL DEL ESTADO NUESTRA SEÑORA DEL ROSARIO DEL MUNICIPIO DE PISBA - BOYACÁ. |
| secop1 | 2022 | no_funerario | 0,247 | PRESTACION DE SERVICIOS PUBLICO DE TRANSPORTE ESPECIAL CON VEHÍCULOS TIPO CAMIONETA 4 X 4 INCLUIDOS SUMINISTROS DE COMBUSTIBLE; MANTENIMIENTO PREVENTIVO Y CORRECTIVO Y CONDUCTOR PARA EL TRASLADO DEL PERSONAL TÉCNICO Y ADMINISTRATIVO DEL CONVENIO N°. 00174-2021 |
| secop2 | 2025 | no_funerario | 0,174 | CONTRATAR EL SERVICIO DE TRANSPORTE TERRESTRE AUTOMOTOR ESPECIAL PARA REALIZAR EN CÚCUTA; SU ÁREA METROPOLITANA Y DENTRO DEL TERRITORIO DEL DEPARTAMENTO; EL TRASLADO DE FUNCIONARIOS; CONTRATISTAS; EQUIPOS; INSUMOS Y OTROS BIENES NECESARIOS PARA GARANTIZAR LAS  |
| secop1 | 2020 | no_funerario | 0,172 | REALIZR BAJO SU PROPIA AUTONOMIA Y RESPONSABILIDAD EL PROCESO ASISTENCIAL EL PROCESO DE CAMILLEROS O TRASLADO INTERNO DE PACIENTES EN LAS DISTINTAS AREAS DE LA E.S.E. HOSPITAL ROSARIO PUMAREJO DE LOPEZ; DE ACUERDO CON LA OFERTA Y DEMANDA DEL SERVICIO; LOS CUAL |
