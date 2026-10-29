# Diagnóstico: servicios profesionales o de apoyo a la gestión con término funerario (D92)

Solo diagnóstico, sin cambiar etiquetas. Generado por `python -m src.modelos.regla_servicios_profesionales`. Valores en miles de millones de pesos de 2025.

Patrón: objeto con «servicios profesionales», «servicios personales», «apoyo a la gestión» o «apoyar la gestión» **y** una raíz funeraria (FUNERA, EXEQU, INHUMA, CREMACI, SEPELIO), sobre los 39.870 contratos candidatos de SECOP I y II.

- Contratos con el patrón: 545 (valor 20,652).
- De ellos, los que TF-IDF clasifica `funerario` (predicción del modelo, antes de la jerarquía de etiquetas): **122**, valor **4,025**.
- Con etiqueta humana: 5 (funerario 5) ; por origen: muestra_400 4, validacion_60_revisada 1.
- Sin etiqueta humana: 117 (valor 3,924).

## 10 ejemplos (mayor valor; objeto anonimizado y recortado a 240 caracteres)

| fuente | anio | valor | etiqueta_humana | objeto_anon |
|---|---|---|---|---|
| secop2 | 2022 | 0,222 | sin etiqueta | PRESTACIÓN DE SERVICIOS DE APOYO A LA GESTIÓN EN LA FILIACIÓN A UN PLAN EXEQUIAL PARA PERSONAS MAYORES DE 60 AÑOS O DE 55 AÑOS EN EXTREMA VULNERABILIDAD |
| secop2 | 2022 | 0,178 | sin etiqueta | SSF-022 Prestar los servicios profesionales especializados a la Subdirección de Servicios Funerarios y Alumbrado Público en temas de arquitectura y patrimonio cultural inmueble; relacionados con la prestación de los servicios funerarios en  |
| secop2 | 2023 | 0,127 | sin etiqueta | SSF-026 Prestar los servicios profesionales especializados a la Subdirección de Servicios Funerarios y Alumbrado Público en el componente sanitario; relacionados con la prestación de los servicios funerarios en los Cementerios de propiedad  |
| secop2 | 2022 | 0,119 | sin etiqueta | SSF-011 Prestar los servicios profesionales desde el componente comercial; social y comunitario para gestionar las relaciones con los grupos de interés de los servicios funerarios en los cementerios de propiedad del distrito |
| secop2 | 2022 | 0,118 | sin etiqueta | SSF-024 Prestar los servicios profesionales especializados a la Subdirección de Servicios Funerarios y Alumbrado Público en el componente ambiental; relacionados con la prestación de los servicios funerarios en los Cementerios de propiedad  |
| secop2 | 2021 | 0,113 | sin etiqueta | SSF-007 Prestar los servicios profesionales especializados a la Subdirección de Servicios Funerarios y Alumbrado Público en el componente ambiental; relacionados con la prestación de los servicios funerarios en los Cementerios de propiedad  |
| secop2 | 2021 | 0,112 | sin etiqueta | SSF-005 Prestar los servicios profesionales especializados a la Subdirección de Servicios Funerarios y Alumbrado Público en temas de arquitectura y patrimonio cultural inmueble; relacionados con la prestación de los servicios funerarios en  |
| secop2 | 2025 | 0,101 | sin etiqueta | SSF-006 Prestar los servicios profesionales a la Subdirección de Servicios Funerarios y Alumbrado Público; de seguimiento y control al componente técnico y operativo de la prestación de los servicios funerarios en los equipamientos propieda |
| secop2 | 2022 | 0,094 | sin etiqueta | SSF-007 Prestar los servicios profesionales en la Subdirección de Servicios Funerarios y Alumbrado Público; para realizar el acompañamiento jurídico a los beneficiarios y usuarios de los servicios funerarios en los cementerios propiedad del |
| secop2 | 2020 | 0,089 | sin etiqueta | Prestar los servicios profesionales especializados a la Subdirección de Servicios Funerarios y Alumbrado Público en temas ambientales y sanitarios; relacionados con la prestación de los servicios funerarios en los Cementerios de propiedad d |
