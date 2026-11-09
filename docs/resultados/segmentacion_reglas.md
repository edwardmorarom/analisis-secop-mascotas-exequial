# Segmentación por reglas del mercado funerario: quién compra × qué compra (D109)

> Propuesta pendiente de revisión de Edward (D109). Rama `segmentacion-reglas`, sin integrar a `main`. Respuesta descriptiva principal; el HCPC de D98 es comprobación (P5). Los valores p son **orientativos**: los contratos de una misma entidad no son independientes (ICC 0,52, D97); la incertidumbre principal es el bootstrap por entidad.

Universo: mercado vigente de **4.985 contratos `funerario`** (D105), 913 entidades, valor total 229,6 mil millones de pesos de 2025.

**Reglas.** *Comprador:* según `tipo_entidad` y `orden_nivel`. *Objeto* (primera regla que se cumple): plan exequial → Plan exequial; ataúdes o bienes sin inhumación o cremación → Ataúdes y bienes; traslado → Traslado; inhumación o cremación → Servicio de inhumación; si no, Otro. *Segmento* = Comprador × Objeto; los segmentos con menos del 1 % de los contratos van juntos en «Otros segmentos» (16 segmentos: Gobernación · Ataúdes y bienes; Gobernación · Otro; Gobernación · Plan exequial; Gobernación · Traslado; Hospital · Otro; Hospital · Plan exequial; Hospital · Servicio de inhumación; Hospital · Traslado; Nacional · Otro; Nacional · Plan exequial; Nacional · Servicio de inhumación; Otra · Ataúdes y bienes; Otra · Otro; Otra · Traslado; Servicios públicos · Otro; Servicios públicos · Plan exequial).

## 1. Descripción

IC 95 % por bootstrap por entidad (2.000 réplicas, semilla 2026, percentiles).

### Por Comprador

| Categoría | Contratos | % contratos (IC 95 %) | % valor (IC 95 %) | Mediana, millones de 2025 (IC 95 %) | p25 | p75 |
|---|---|---|---|---|---|---|
| Alcaldía | 4.423 | 88,7 (84,5 a 92,1) | 63,2 (46,7 a 81,9) | 21,5 (20,5 a 24,0) | 11,5 | 34,8 |
| Gobernación | 104 | 2,1 (1,2 a 3,1) | 3,9 (1,9 a 6,7) | 61,6 (32,5 a 87,2) | 27,3 | 112,1 |
| Hospital | 85 | 1,7 (1,1 a 2,5) | 1,6 (0,6 a 3,4) | 16,2 (9,9 a 25,7) | 7,3 | 33,1 |
| Servicios públicos | 119 | 2,4 (0,3 a 6,0) | 2,7 (0,1 a 8,2) | 33,5 (4,0 a 36,8) | 13,8 | 55,8 |
| Nacional | 66 | 1,3 (0,5 a 2,3) | 13,8 (0,9 a 33,8) | 33,2 (18,8 a 126,5) | 16,1 | 118,1 |
| Otra | 188 | 3,8 (2,3 a 5,6) | 14,8 (3,2 a 28,0) | 13,8 (7,3 a 88,6) | 6,0 | 127,5 |

### Por Segmento

| Categoría | Contratos | % contratos (IC 95 %) | % valor (IC 95 %) | Mediana, millones de 2025 (IC 95 %) | p25 | p75 |
|---|---|---|---|---|---|---|
| Alcaldía · Servicio de inhumación | 2.566 | 51,5 (47,9 a 55,1) | 42,3 (30,9 a 55,4) | 23,0 (21,0 a 26,1) | 12,5 | 35,7 |
| Alcaldía · Ataúdes y bienes | 968 | 19,4 (17,2 a 21,9) | 9,4 (6,8 a 12,8) | 19,3 (16,5 a 21,5) | 10,3 | 32,8 |
| Alcaldía · Otro | 424 | 8,5 (6,9 a 10,3) | 6,2 (4,3 a 8,7) | 24,1 (19,8 a 28,5) | 11,4 | 35,0 |
| Alcaldía · Plan exequial | 257 | 5,2 (3,9 a 6,5) | 2,4 (1,5 a 3,6) | 17,2 (13,6 a 21,8) | 9,2 | 30,0 |
| Otros segmentos | 257 | 5,2 (3,8 a 6,6) | 18,8 (5,2 a 37,7) | 25,7 (17,0 a 42,2) | 10,0 | 71,5 |
| Alcaldía · Traslado | 208 | 4,2 (3,3 a 5,2) | 2,9 (1,9 a 4,5) | 25,4 (20,3 a 31,4) | 12,7 | 35,6 |
| Otra · Plan exequial | 101 | 2,0 (1,1 a 3,2) | 2,1 (0,2 a 5,1) | 8,4 (4,4 a 20,1) | 4,3 | 20,1 |
| Servicios públicos · Servicio de inhumación | 89 | 1,8 (0,0 a 5,1) | 2,0 (0,0 a 6,1) | 34,7 (2,4 a 42,4) | 20,1 | 57,4 |
| Otra · Servicio de inhumación | 59 | 1,2 (0,4 a 2,1) | 12,3 (1,5 a 25,1) | 166,6 (37,1 a 912,0) | 60,2 | 691,1 |
| Gobernación · Servicio de inhumación | 56 | 1,1 (0,5 a 1,9) | 1,7 (0,6 a 3,3) | 57,0 (20,4 a 97,5) | 24,5 | 108,3 |

### Independencia Comprador × Objeto

| Versión | χ² | gl | p (orientativo) | V de Cramér | Celdas con esperada < 5 |
|---|---|---|---|---|---|
| Comprador × Objeto (6 compradores) | 756,1 | 20 | < 0,001 | 0,195 | 10,0 % |

El Comprador y el Objeto no son independientes (V 0,195); esto describe que la segmentación recoge dos ejes asociados, y es una medida de asociación, no un umbral de la decisión.

## 2. Validación

### P1. Diferencias en variables que no definen los segmentos

| Prueba | Estadístico, gl | p (orientativo) | Tamaño del efecto | Umbral | Se sostiene |
|---|---|---|---|---|---|
| Comprador: log del valor (Kruskal-Wallis) | H = 123,6, gl 5, n = 4.978 | < 0,001 | ε² = 0,025 (débil) | ε² ≥ 0,06 | no |
| Comprador: departamento (χ², 33 → 8 departamentos tras Cochran) | χ² = 447,9, gl 35, n = 4.978 | < 0,001 (permutación) | V = 0,134 | V ≥ 0,20 | no |
| Segmento: log del valor (Kruskal-Wallis) | H = 271,6, gl 9, n = 4.978 | < 0,001 | ε² = 0,055 (moderado) | ε² ≥ 0,06 | no |
| Segmento: departamento (χ², 33 → 8 departamentos tras Cochran) | χ² = 810,4, gl 63, n = 4.978 | < 0,001 (permutación) | V = 0,152 | V ≥ 0,20 | no |

Dunn con Holm sobre el log del valor: Comprador 10 de 15 pares difieren (p ajustado < 0,05); Segmento 35 de 45 pares difieren (p ajustado < 0,05). Detalle en los CSV.

**Proveedores por Comprador** (HHI y CR4 sobre el valor, sin umbral):

| Comprador | Contratos con proveedor y valor | Proveedores | HHI | CR4 |
|---|---|---|---|---|
| Alcaldía | 4.419 | 1.234 | 55 | 9,2 % |
| Gobernación | 104 | 50 | 529 | 35,0 % |
| Hospital | 84 | 43 | 1.222 | 49,4 % |
| Nacional | 64 | 24 | 2.656 | 94,8 % |
| Otra | 188 | 57 | 1.317 | 63,5 % |
| Servicios públicos | 119 | 71 | 445 | 31,8 % |
| Todos | 4.978 | 1.376 | 168 | 20,3 % |

### P2. Orden de las reglas

Con las 24 permutaciones del orden de prioridad, como máximo cambian de segmento **7,3 %** de los contratos y el cambio máximo del % del valor por segmento es **2,98 puntos** (umbral ≤ 2). **Se sostiene: no.**

### P3. Estabilidad frente a contratos grandes

Los IC del bootstrap por entidad están en las tablas de la sección 1. Sensibilidad sin el 1 % de contratos de mayor valor (50 contratos): orden de los Compradores por % del valor.

| Comprador | % valor (base) | Posición | % valor (sin 1 % mayor) | Posición |
|---|---|---|---|---|
| Alcaldía | 63,2 | 1 | 80,6 | 1 |
| Otra | 14,8 | 2 | 6,1 | 2 |
| Nacional | 13,8 | 3 | 2,0 | 6 |
| Gobernación | 3,9 | 4 | 5,5 | 3 |
| Servicios públicos | 2,7 | 5 | 3,6 | 4 |
| Hospital | 1,6 | 6 | 2,2 | 5 |

**Se sostiene (el orden no cambia): no.**

### P4. Plataforma y periodo

V de Cramér fuente × Segmento = 0,372 (χ² = 690,0, gl 9, n = 4.985, p < 0,001, orientativo).

Tres segmentos con más contratos por plataforma: secop1: Alcaldía · Servicio de inhumación, Alcaldía · Ataúdes y bienes, Alcaldía · Otro; secop2: Alcaldía · Servicio de inhumación, Otros segmentos, Alcaldía · Otro. **Se sostiene (mismo conjunto de tres): no.** Lectura complementaria, que no cambia la decisión: «Otros segmentos» es una bolsa de segmentos pequeños y no un segmento; sin ella, los tres con más contratos son secop1: Alcaldía · Servicio de inhumación, Alcaldía · Ataúdes y bienes, Alcaldía · Otro; secop2: Alcaldía · Servicio de inhumación, Alcaldía · Otro, Alcaldía · Ataúdes y bienes (mismo conjunto: sí).

**Segmento por plataforma y periodo** (contratos, % de contratos, % del valor y mediana en millones de 2025):

| Subgrupo | Segmento | Contratos | % contratos | % valor | Mediana |
|---|---|---|---|---|---|
| secop1 | Alcaldía · Servicio de inhumación | 1.908 | 52,2 | 57,4 | 21,4 |
| secop1 | Alcaldía · Ataúdes y bienes | 876 | 24,0 | 18,9 | 18,1 |
| secop1 | Alcaldía · Otro | 302 | 8,3 | 8,7 | 21,2 |
| secop1 | Alcaldía · Plan exequial | 217 | 5,9 | 4,3 | 16,7 |
| secop1 | Alcaldía · Traslado | 166 | 4,5 | 4,3 | 21,4 |
| secop1 | Otros segmentos | 110 | 3,0 | 5,1 | 18,7 |
| secop1 | Otra · Plan exequial | 41 | 1,1 | 0,3 | 5,1 |
| secop1 | Gobernación · Servicio de inhumación | 17 | 0,5 | 0,6 | 25,0 |
| secop1 | Otra · Servicio de inhumación | 10 | 0,3 | 0,1 | 10,4 |
| secop1 | Servicios públicos · Servicio de inhumación | 7 | 0,2 | 0,1 | 4,0 |
| secop2 | Alcaldía · Servicio de inhumación | 658 | 49,4 | 31,5 | 32,6 |
| secop2 | Otros segmentos | 147 | 11,0 | 28,6 | 33,6 |
| secop2 | Alcaldía · Otro | 122 | 9,2 | 4,5 | 30,5 |
| secop2 | Alcaldía · Ataúdes y bienes | 92 | 6,9 | 2,7 | 28,3 |
| secop2 | Servicios públicos · Servicio de inhumación | 82 | 6,2 | 3,2 | 35,3 |
| secop2 | Otra · Plan exequial | 60 | 4,5 | 3,3 | 10,0 |
| secop2 | Otra · Servicio de inhumación | 49 | 3,7 | 20,9 | 280,5 |
| secop2 | Alcaldía · Traslado | 42 | 3,2 | 1,9 | 35,7 |
| secop2 | Alcaldía · Plan exequial | 40 | 3,0 | 1,0 | 26,8 |
| secop2 | Gobernación · Servicio de inhumación | 39 | 2,9 | 2,4 | 76,9 |
| 2020–2022 | Alcaldía · Servicio de inhumación | 1.406 | 49,5 | 42,3 | 22,4 |
| 2020–2022 | Alcaldía · Ataúdes y bienes | 594 | 20,9 | 10,7 | 19,8 |
| 2020–2022 | Alcaldía · Otro | 223 | 7,8 | 6,4 | 21,5 |
| 2020–2022 | Otros segmentos | 164 | 5,8 | 17,5 | 23,4 |
| 2020–2022 | Alcaldía · Plan exequial | 152 | 5,3 | 2,5 | 17,5 |
| 2020–2022 | Alcaldía · Traslado | 140 | 4,9 | 3,7 | 21,9 |
| 2020–2022 | Otra · Plan exequial | 63 | 2,2 | 1,7 | 7,7 |
| 2020–2022 | Servicios públicos · Servicio de inhumación | 36 | 1,3 | 1,5 | 40,4 |
| 2020–2022 | Otra · Servicio de inhumación | 35 | 1,2 | 12,0 | 139,5 |
| 2020–2022 | Gobernación · Servicio de inhumación | 30 | 1,1 | 1,7 | 59,1 |
| 2023–2025 | Alcaldía · Servicio de inhumación | 1.160 | 54,2 | 42,2 | 24,4 |
| 2023–2025 | Alcaldía · Ataúdes y bienes | 374 | 17,5 | 8,0 | 18,1 |
| 2023–2025 | Alcaldía · Otro | 201 | 9,4 | 6,1 | 27,4 |
| 2023–2025 | Alcaldía · Plan exequial | 105 | 4,9 | 2,2 | 16,8 |
| 2023–2025 | Otros segmentos | 93 | 4,3 | 20,4 | 33,0 |
| 2023–2025 | Alcaldía · Traslado | 68 | 3,2 | 2,0 | 31,8 |
| 2023–2025 | Servicios públicos · Servicio de inhumación | 53 | 2,5 | 2,5 | 33,2 |
| 2023–2025 | Otra · Plan exequial | 38 | 1,8 | 2,5 | 11,0 |
| 2023–2025 | Gobernación · Servicio de inhumación | 26 | 1,2 | 1,6 | 53,2 |
| 2023–2025 | Otra · Servicio de inhumación | 24 | 1,1 | 12,6 | 279,9 |

**Comprador por plataforma y periodo** (contratos, % de contratos, % del valor y mediana en millones de 2025):

| Subgrupo | Comprador | Contratos | % contratos | % valor | Mediana |
|---|---|---|---|---|---|
| secop1 | Alcaldía | 3.469 | 94,9 | 93,7 | 20,5 |
| secop1 | Otra | 65 | 1,8 | 0,6 | 6,6 |
| secop1 | Hospital | 61 | 1,7 | 2,9 | 13,5 |
| secop1 | Gobernación | 32 | 0,9 | 2,1 | 38,9 |
| secop1 | Servicios públicos | 23 | 0,6 | 0,6 | 10,7 |
| secop1 | Nacional | 4 | 0,1 | 0,1 | 31,9 |
| secop2 | Alcaldía | 954 | 71,7 | 41,6 | 31,5 |
| secop2 | Otra | 123 | 9,2 | 24,8 | 85,7 |
| secop2 | Servicios públicos | 96 | 7,2 | 4,3 | 35,3 |
| secop2 | Gobernación | 72 | 5,4 | 5,2 | 66,6 |
| secop2 | Nacional | 62 | 4,7 | 23,5 | 33,4 |
| secop2 | Hospital | 24 | 1,8 | 0,7 | 17,6 |
| 2020–2022 | Alcaldía | 2.515 | 88,5 | 65,6 | 21,3 |
| 2020–2022 | Otra | 114 | 4,0 | 14,0 | 9,9 |
| 2020–2022 | Hospital | 66 | 2,3 | 2,4 | 13,9 |
| 2020–2022 | Servicios públicos | 58 | 2,0 | 2,7 | 34,5 |
| 2020–2022 | Gobernación | 57 | 2,0 | 3,8 | 68,2 |
| 2020–2022 | Nacional | 33 | 1,2 | 11,5 | 33,1 |
| 2023–2025 | Alcaldía | 1.908 | 89,1 | 60,4 | 22,4 |
| 2023–2025 | Otra | 74 | 3,5 | 15,6 | 37,6 |
| 2023–2025 | Servicios públicos | 61 | 2,8 | 2,8 | 32,4 |
| 2023–2025 | Gobernación | 47 | 2,2 | 3,9 | 56,3 |
| 2023–2025 | Nacional | 33 | 1,5 | 16,5 | 33,2 |
| 2023–2025 | Hospital | 19 | 0,9 | 0,6 | 20,1 |

### P5. Concordancia con el HCPC de D98 (4.992 contratos)

ARI entre Segmento y los 8 grupos de D98 (no reportados = una categoría) = **0,440** (n = 4.992). Sin umbral: por debajo de 0,5 los dos métodos no coinciden como particiones.

| Segmento | Grupo 1 | Grupo 2 | Grupo 3 | Grupo 4 | Grupo 5 | Grupo 6 | Grupo 7 | Grupo 8 | No reportado |
|---|---|---|---|---|---|---|---|---|---|
| Alcaldía · Ataúdes y bienes | 1 | 762 | 36 | 156 | 13 | 0 | 0 | 0 | 0 |
| Alcaldía · Otro | 249 | 117 | 0 | 12 | 24 | 6 | 6 | 5 | 12 |
| Alcaldía · Plan exequial | 118 | 54 | 29 | 35 | 8 | 13 | 0 | 0 | 0 |
| Alcaldía · Servicio de inhumación | 1930 | 342 | 0 | 70 | 174 | 12 | 0 | 9 | 29 |
| Alcaldía · Traslado | 0 | 0 | 202 | 1 | 4 | 0 | 0 | 0 | 1 |
| Gobernación · Servicio de inhumación | 0 | 0 | 54 | 0 | 2 | 0 | 0 | 0 | 0 |
| Otra · Plan exequial | 0 | 0 | 0 | 0 | 0 | 99 | 0 | 0 | 2 |
| Otra · Servicio de inhumación | 16 | 0 | 0 | 0 | 25 | 10 | 0 | 0 | 8 |
| Otros segmentos | 0 | 3 | 41 | 6 | 3 | 66 | 27 | 82 | 29 |
| Servicios públicos · Servicio de inhumación | 0 | 0 | 0 | 0 | 0 | 0 | 88 | 0 | 1 |

## 3. Lo que no se sostiene

- P1, Comprador: valor: no alcanza el umbral.
- P1, Comprador: departamento: no alcanza el umbral.
- P1, Segmento: valor: no alcanza el umbral.
- P1, Segmento: departamento: no alcanza el umbral.
- P2: el cambio máximo del % del valor por segmento es 2,98 puntos (> 2).
- P3: el orden de los Compradores por % del valor cambia al quitar el 1 % de contratos de mayor valor.
- P4: los tres segmentos con más contratos no son los mismos en SECOP I y SECOP II.

ESTADO: TERMINADO — 2026-11-08 23:59 — pruebas: 64 pasan
