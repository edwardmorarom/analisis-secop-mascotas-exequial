# Contraste INS–MinSalud sin denominador compartido (2023 y 2024)

Solo diagnóstico (D88): no cambia indicadores ni el panel. Generado por `python -m src.evaluacion.contraste_ins_minsalud`; semilla 2026, 2.000 remuestreos bootstrap de municipios.

## 1. Especies de los casos del evento 300

Los casos extraídos del INS incluyen todas las especies agresoras, no solo perros (Tabla 2 del informe 2025, p. 13):

| Especie | 2024 | 2025 |
|---|---|---|
| Perro | 84,23 % | 82,97 % |
| Gato | 14,27 % | 15,24 % |
| Silvestre | 0,85 % | 1,10 % |
| De producción | 0,65 % | 0,68 % |

El informe 2023 reporta perro 85,1 %, gato 13,5 % y silvestres 0,8 %.

## 2. Spearman por municipio

Agresiones por 100.000 habitantes (casos INS / población DANE del año) frente a perros por 1.000 habitantes (población de perros del PDF de MinSalud / población DANE del año). Se excluyen municipios sin dato de perros, con 0 perros o con 0 casos. Las filas marcadas son los municipios con alguna incidencia de `incidencias.csv` en ese año.

| Año | Conjunto | Municipios | Spearman | IC 95 % bootstrap | Marcados en el conjunto | Excluidos (sin dato o cero) |
|---|---|---|---|---|---|---|
| 2023 | todos | 1101 | 0.370 | 0.320 a 0.422 | 89 | 20 |
| 2023 | sin filas marcadas | 1012 | 0.372 | 0.321 a 0.421 | 0 | 20 |
| 2024 | todos | 1106 | 0.345 | 0.293 a 0.397 | 117 | 15 |
| 2024 | sin filas marcadas | 989 | 0.331 | 0.274 a 0.385 | 0 | 15 |

La población del INS frente a la de DANE: razón mediana 1,014 (2023) y 1,017 (2024).

## 3. Municipios de mayor residuo

Residuo = percentil de agresiones por 100.000 habitantes menos el esperado por una recta sobre el percentil de perros por 1.000 habitantes; se listan los 20 de mayor valor absoluto por año. Positivo: más agresiones de las que sugieren los perros; negativo: menos.

Municipios con incidencia en `incidencias.csv` entre los 20: 2023: 2 de 20; 2024: 0 de 20.

### 2023

| Código | Municipio | Departamento | Casos | Agresiones x100.000 | Perros x1.000 hab. | Residuo | Incidencia |
|---|---|---|---|---|---|---|---|
| 15022 | Almeida | Boyacá | 2 | 108.3 | 433.4 | -0.61 | no |
| 73275 | Flandes | Tolima | 251 | 866.4 | 85.3 | +0.61 | no |
| 25483 | Nariño | Cundinamarca | 2 | 82.1 | 268.1 | -0.59 | no |
| 15180 | Chiscas | Boyacá | 4 | 98.2 | 274.2 | -0.58 | no |
| 50245 | El Calvario | Meta | 2 | 105.8 | 283.6 | -0.58 | no |
| 15212 | Coper | Boyacá | 5 | 141.4 | 374.2 | -0.57 | no |
| 47605 | Remolino | Magdalena | 10 | 75.5 | 231.2 | -0.57 | cobertura_100 |
| 15106 | Briceño | Boyacá | 3 | 132.8 | 311.6 | -0.56 | no |
| 05321 | Guatapé | Antioquia | 79 | 843.3 | 107.2 | +0.56 | no |
| 52233 | Cumbitara | Nariño | 6 | 101.1 | 250.3 | -0.56 | no |
| 68682 | San Joaquín | Santander | 19 | 764.6 | 96.6 | +0.56 | cobertura_100 |
| 05667 | San Rafael | Antioquia | 131 | 771.4 | 98.7 | +0.56 | no |
| 15135 | Campohermoso | Boyacá | 3 | 94.4 | 233.9 | -0.55 | no |
| 86885 | Villagarzón | Putumayo | 167 | 660.9 | 61.2 | +0.55 | no |
| 25086 | Beltrán | Cundinamarca | 3 | 167.3 | 420.0 | -0.55 | no |
| 86219 | Colón | Putumayo | 49 | 856.5 | 116.2 | +0.55 | no |
| 44560 | Manaure | La Guajira | 23 | 24.2 | 185.6 | -0.54 | no |
| 25322 | Guasca | Cundinamarca | 149 | 866.5 | 118.7 | +0.54 | no |
| 76622 | Roldanillo | Valle del Cauca | 279 | 729.3 | 100.5 | +0.54 | no |
| 13442 | María La Baja | Bolívar | 47 | 96.4 | 217.3 | -0.54 | no |

### 2024

| Código | Municipio | Departamento | Casos | Agresiones x100.000 | Perros x1.000 hab. | Residuo | Incidencia |
|---|---|---|---|---|---|---|---|
| 73275 | Flandes | Tolima | 253 | 870.7 | 85.6 | +0.60 | no |
| 17446 | Marulanda | Caldas | 3 | 111.7 | 332.6 | -0.60 | no |
| 05321 | Guatapé | Antioquia | 105 | 1,103.2 | 106.3 | +0.59 | no |
| 76126 | Calima | Valledel Cauca | 163 | 849.2 | 95.8 | +0.58 | no |
| 19701 | Santa Rosa | Cauca | 8 | 150.2 | 742.3 | -0.58 | no |
| 25823 | Topaipí | Cundinamarca | 2 | 50.1 | 233.4 | -0.58 | no |
| 85136 | La Salina | Casanare | 1 | 65.9 | 231.9 | -0.57 | no |
| 05667 | San Rafael | Antioquia | 136 | 789.7 | 98.1 | +0.55 | no |
| 25736 | Sesquilé | Cundinamarca | 104 | 817.4 | 104.5 | +0.55 | no |
| 97666 | Taraira | Vaupés | 20 | 706.5 | 41.0 | +0.55 | no |
| 68264 | Encino | Santander | 2 | 69.0 | 216.4 | -0.55 | no |
| 86885 | Villagarzón | Putumayo | 183 | 715.5 | 61.3 | +0.55 | no |
| 27745 | Sipí | Chocó | 1 | 30.1 | 196.4 | -0.55 | no |
| 23168 | Chimá | Córdoba | 23 | 118.5 | 247.6 | -0.55 | no |
| 44560 | Manaure | La Guajira | 22 | 22.8 | 186.2 | -0.55 | no |
| 47551 | Pivijay | Magdalena | 47 | 116.3 | 226.5 | -0.54 | no |
| 15135 | Campohermoso | Boyacá | 4 | 125.5 | 236.0 | -0.54 | no |
| 15511 | Pachavita | Boyacá | 4 | 173.8 | 346.4 | -0.54 | no |
| 86760 | Santiago | Putumayo | 55 | 752.6 | 92.6 | +0.54 | no |
| 15550 | Pisba | Boyacá | 2 | 102.5 | 211.7 | -0.53 | no |
