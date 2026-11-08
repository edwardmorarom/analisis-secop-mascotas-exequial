# Perfil de mortalidad por grupo del clustering (D108)

> Descriptivo, sin pruebas de hipótesis ni valores p. Propuesta pendiente de revisión de Edward (D108; alcance de D107 cambiado en D107c). Rama `causas-defuncion`, sin integrar a `main`.

A cada uno de los 4.992 contratos con grupo HCPC (D97 a D99) se le asigna la **tasa de defunción estandarizada por edad** (método directo, población estándar Colombia 2020, por 100.000 habitantes) del departamento de la **entidad contratante** y el año de firma, para las siete causas de D107. Cada celda es **mediana (p25 a p75)** sobre contratos: cada contrato pesa una vez, de modo que los departamentos con más contratos pesan más. G1 a G8 son los grupos reportados en D98 y D105 (4.910 contratos); el total incluye los 82 contratos de grupos no reportados. 7 contratos sin código de departamento no reciben tasa.

**Lectura.** Las tasas describen la mortalidad de la población del departamento donde está la entidad, no la de los fallecidos atendidos por el contrato (D107, limitaciones: sede frente a residencia, falacia ecológica). **COVID-19:** solo hay dato en 2020–2022 y en los departamentos-año donde `U07` está entre las diez primeras causas, y es tasa **cruda** (el Cuadro 16 no trae edad); «demás causas» incluye la COVID-19 de 2020 a 2022.

## Tasa por 100.000 habitantes: mediana (p25 a p75)

| Grupo | Contratos | Departamentos | Agresiones (homicidios) | Accidentes de transporte | Otras causas externas (no homicidio ni transporte) | COVID-19 | Sistema circulatorio | Neoplasias | Demás causas |
|---|---|---|---|---|---|---|---|---|---|
| Grupo 1 | 2.314 | 32 | 24,4 (16,9 a 32,2) | 16,6 (14,3 a 19,2) | 22,9 (18,5 a 25,2) | 86,5 (33,1 a 154,7) | 171,3 (158,2 a 189,4) | 94,9 (84,2 a 105,4) | 213,1 (188,4 a 274,5) |
| Grupo 2 | 1.278 | 29 | 27,1 (20,0 a 34,5) | 16,1 (13,3 a 17,7) | 22,9 (17,8 a 26,5) | 86,5 (33,1 a 119,5) | 165,9 (155,4 a 186,4) | 84,5 (78,9 a 93,6) | 215,1 (177,5 a 289,1) |
| Grupo 3 | 362 | 30 | 25,5 (19,4 a 33,1) | 15,2 (13,0 a 17,7) | 23,0 (18,4 a 25,3) | 86,6 (41,0 a 128,4) | 170,2 (155,3 a 191,6) | 93,5 (79,3 a 106,1) | 222,1 (198,7 a 302,0) |
| Grupo 4 | 280 | 26 | 29,9 (20,0 a 43,8) | 16,4 (13,7 a 18,3) | 22,2 (18,8 a 27,2) | 69,4 (25,1 a 125,8) | 162,7 (145,3 a 186,4) | 82,6 (78,7 a 90,3) | 195,3 (170,2 a 252,2) |
| Grupo 5 | 253 | 27 | 24,4 (17,6 a 33,4) | 16,6 (13,8 a 20,2) | 19,1 (16,6 a 23,7) | 88,2 (25,0 a 125,6) | 171,3 (155,3 a 190,4) | 89,7 (79,0 a 99,7) | 211,2 (182,7 a 289,1) |
| Grupo 6 | 206 | 21 | 25,1 (15,0 a 41,2) | 15,5 (13,0 a 17,7) | 21,0 (17,4 a 24,6) | 101,8 (44,4 a 159,0) | 172,0 (155,8 a 183,2) | 101,7 (97,1 a 108,1) | 213,1 (189,5 a 297,0) |
| Grupo 7 | 121 | 11 | 14,5 (13,8 a 15,1) | 9,6 (9,6 a 13,8) | 15,6 (15,0 a 17,9) | 125,6 (32,3 a 176,1) | 147,3 (137,3 a 168,2) | 105,7 (104,3 a 108,1) | 196,5 (174,5 a 296,5) |
| Grupo 8 | 96 | 18 | 28,9 (21,8 a 48,3) | 16,6 (14,0 a 17,7) | 19,1 (18,0 a 23,6) | 101,8 (59,4 a 148,1) | 176,9 (168,2 a 191,0) | 99,6 (89,6 a 105,1) | 249,2 (205,2 a 351,2) |
| Total | 4.992 | 33 | 25,5 (18,5 a 34,0) | 16,1 (13,6 a 18,5) | 22,9 (18,0 a 25,3) | 86,6 (33,1 a 136,4) | 169,1 (155,7 a 189,3) | 89,7 (81,2 a 104,8) | 213,3 (183,2 a 289,1) |

## Contratos y departamentos con tasa de COVID-19

| Grupo | Contratos con tasa | Contratos del grupo | Departamentos con tasa |
|---|---|---|---|
| Grupo 1 | 1.244 | 2.314 | 32 |
| Grupo 2 | 786 | 1.278 | 29 |
| Grupo 3 | 228 | 362 | 29 |
| Grupo 4 | 155 | 280 | 24 |
| Grupo 5 | 128 | 253 | 26 |
| Grupo 6 | 115 | 206 | 18 |
| Grupo 7 | 57 | 121 | 10 |
| Grupo 8 | 71 | 96 | 16 |
| Total | 2.838 | 4.992 | 33 |

Las demás causas tienen tasa en todos los contratos con departamento (contratos con tasa = contratos del grupo menos los sin departamento). El detalle por causa (contratos y departamentos con tasa, mediana, p25 y p75) está en `docs/resultados/mortalidad_por_grupo.csv`.
