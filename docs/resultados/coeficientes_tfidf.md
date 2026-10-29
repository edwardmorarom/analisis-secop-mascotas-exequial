# Coeficientes del modelo TF-IDF (auditabilidad)

Solo reporte. Generado por `python -m src.modelos.coeficientes_tfidf`. Modelo: TF-IDF (unigramas y bigramas, `min_df` 2, tf sublineal) con regresión logística multinomial (D56), ajustado con **todas las etiquetas humanas vigentes** (732 contratos: no_funerario 462, funerario 245, mixto 25); C elegido por validación cruzada de 3 pliegues: 100,00. Vocabulario: 4208 términos. Los coeficientes son los de la clase `funerario` frente a las otras dos clases; un coeficiente positivo sube la probabilidad de `funerario`. Los textos incluyen el código UNSPSC como palabra (`UNSPSC`).

## 20 términos con mayor coeficiente a favor de `funerario`

| término | coeficiente |
|---|---|
| funerarios | 4,768 |
| servicios funerarios | 4,385 |
| poblacion | 4,216 |
| personas | 3,784 |
| vulnerable | 3,534 |
| la poblacion | 3,284 |
| poblacion vulnerable | 3,115 |
| funebres | 2,943 |
| exequiales | 2,870 |
| funerarios para | 2,720 |
| victimas | 2,667 |
| unspsc 85171500 | 2,646 |
| 85171500 | 2,646 |
| del distrito | 2,479 |
| exequial | 2,447 |
| funcionarios | 2,444 |
| cofres | 2,274 |
| auxilio | 2,252 |
| distrito | 2,201 |
| proteccion | 2,145 |

## 20 términos con mayor coeficiente en contra

| término | coeficiente |
|---|---|
| necropsias | -2,809 |
| rosario | -2,727 |
| construccion | -2,391 |
| del cementerio | -2,240 |
| materiales | -2,195 |
| actividades | -2,102 |
| gestion | -2,069 |
| del rosario | -2,036 |
| construccion de | -1,972 |
| cementerio | -1,940 |
| unspsc 93131501 | -1,937 |
| 93131501 | -1,937 |
| apoyo | -1,830 |
| la gestion | -1,801 |
| publico en | -1,792 |
| salud | -1,777 |
| servicios profesionales | -1,753 |
| de apoyo | -1,707 |
| profesionales | -1,675 |
| participacion unspsc | -1,645 |

## Tres contratos de ejemplo

Contratos sin etiqueta humana (el modelo no los vio al ajustarse). Se eligen los más cercanos a probabilidad 0,97, 0,03 y 0,50. La contribución de un término es su valor TF-IDF por su coeficiente; se listan las cinco mayores a favor y las cinco mayores en contra. Objeto anonimizado y recortado a 300 caracteres.

### probabilidad alta de funerario: probabilidad de `funerario` 0,970

- Fuente y año: secop1, 2022.
- Texto: PRESTACION DE SERVICIOS DE INHUMACION INTEGRAL DE CADAVERES COMO ESTRATEGIA DE APOYO A LAS PERSONAS ADULTAS MAYORES; DE BAJOS RECURSOS ECONOMICOS DEL MUNICIPIO DE SANTANDER DE QUILICHAO; CAUCA. | RESTACION DE SERVICIOS DE INHUMACION INTEGRAL DE CADAVERES COMO ESTRATEGIA DE APOYO A LAS PERSONAS ADULT
- Términos que más aportaron a favor: personas (0,504), mayores (0,321), las personas (0,290), recursos (0,276), economicos (0,248).
- Términos que más aportaron en contra: de apoyo (-0,191), apoyo (-0,180), como (-0,102), santander (-0,074), de (-0,056).

### probabilidad baja: probabilidad de `funerario` 0,030

- Fuente y año: secop2, 2021.
- Texto: PRESTACION DE SERVICIOS DE APOYO A LA GESTION PARA EL DESARROLLO DE ACTIVIDADES COMO SEPULTURERO EN EL CEMENTERIO CENTRAL DEL MUNICIPIO DE VILLAVICENCIO | UNSPSC 80111701
- Términos que más aportaron a favor: sepulturero (0,526), del municipio (0,160), para el (0,115), de servicios (0,112), prestacion (0,111).
- Términos que más aportaron en contra: actividades (-0,283), cementerio (-0,279), gestion (-0,251), la gestion (-0,232), de apoyo (-0,210).

### caso intermedio: probabilidad de `funerario` 0,499

- Fuente y año: secop2, 2020.
- Texto: CONTRATAR LA PRESTACION DE SERVICIOS DE MANEJO Y DISPOSICION FINAL DE CADAVERES COMO MEDIDA DE MITIGACION CAUSADA POR EL COVID 19 EN EL DISTRITO DE CARTAGENA. | UNSPSC 85171500
- Términos que más aportaron a favor: unspsc 85171500 (0,412), 85171500 (0,412), distrito (0,391), 19 (0,136), final (0,132).
- Términos que más aportaron en contra: como (-0,102), disposicion (-0,096), la (-0,079), el (-0,076), manejo (-0,073).
