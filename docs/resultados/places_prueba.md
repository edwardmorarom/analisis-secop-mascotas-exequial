# Prueba de Google Places (D101): diagnóstico, sin decisiones

Prueba del 2026-11-01 con 10 municipios (semilla 2026). Crudo: `data/raw/places/places_prueba_20261101.jsonl` (con huella en el manifiesto).

## 1. Llamadas y resultados

- Llamadas gastadas: **30** de 150 al día (30 búsquedas de una página: 10 municipios × 3 términos; ninguna llenó 20 resultados, así que no hubo páginas adicionales).

- Resultados devueltos: **47**; lugares únicos por `place_id`: **29**; recuperados por más de un término: 12.

- Únicos que caen **fuera del municipio buscado** (punto en polígono del MGN): **0**; sin municipio (fuera de todo polígono): 0.

- Nombres con aspecto de persona natural (reemplazados por seudónimo `PN-…`): 0.

### Por término

| termino | resultados | unicos |
|---|---|---|
| cementerio de mascotas | 22 | 22 |
| cremación de mascotas | 12 | 12 |
| funeraria de mascotas | 13 | 13 |

### Por municipio buscado

| cod_busqueda | resultados | unicos | municipio |
|---|---|---|---|
| 05147 | 2 | 1 | CAREPA |
| 08638 | 1 | 1 | SABANALARGA |
| 50001 | 4 | 2 | VILLAVICENCIO |
| 50568 | 1 | 1 | PUERTO GAITÁN |
| 68001 | 20 | 15 | BUCARAMANGA |
| 73001 | 19 | 9 | IBAGUÉ |

## 2. Tipos de Google (sobre lugares únicos)

### Todos los tipos

| tipo | lugares_con_el_tipo |
|---|---|
| point_of_interest | 29 |
| establishment | 29 |
| service | 20 |
| cemetery | 14 |
| pet_care | 11 |
| funeral_home | 5 |
| health | 3 |
| store | 3 |
| hospital | 2 |
| veterinary_care | 2 |
| pet_store | 2 |
| association_or_organization | 1 |
| medical_clinic | 1 |
| supermarket | 1 |
| farm | 1 |
| grocery_store | 1 |
| food_store | 1 |
| supplier | 1 |
| food | 1 |
| corporate_office | 1 |
| pharmacy | 1 |
| pet_boarding_service | 1 |

### Tipo principal

| tipo_principal | lugares |
|---|---|
| cemetery | 9 |
| pet_care | 7 |
| funeral_home | 4 |
| (sin tipo principal) | 3 |
| hospital | 2 |
| point_of_interest | 1 |
| pet_store | 1 |
| corporate_office | 1 |
| veterinary_care | 1 |

## 3. 15 ejemplos (azar con semilla 2026, solo empresas)

| nombre | tipo_principal | tipos | municipio |
|---|---|---|---|
| MascoPlus EPS | hospital | hospital, association_or_organization, health, service | BUCARAMANGA |
| Funeraria Los Olivos Bucaramanga | funeral_home | funeral_home, cemetery, service, point_of_interest | BUCARAMANGA |
| Cementerio Católico Arquidiocesano de Bucaramanga | cemetery | cemetery, service, point_of_interest, establishment | BUCARAMANGA |
| Memorar Pet - Funeraria para mascotas | pet_care | pet_care, point_of_interest, establishment | BUCARAMANGA |
| MOMO - Oficinas | cemetery | cemetery, service, point_of_interest, establishment | BUCARAMANGA |
| Jardín la Mariposa | cemetery | cemetery, point_of_interest, service, establishment | IBAGUÉ |
| FUNERARIA DE MASCOTAS AF 24/7 / IBAGUE | funeral_home | funeral_home, point_of_interest, service, establishment | IBAGUÉ |
| cielo azul mascotas | pet_care | cemetery, pet_care, point_of_interest, service | IBAGUÉ |
| Funeraria Para Mascotas Huellitas | point_of_interest | point_of_interest, establishment | VILLAVICENCIO |
| Concentrados Espartaco S.A. | pet_store | pet_store, supermarket, pet_care, farm | BUCARAMANGA |
| Previsan Ltda. | funeral_home | funeral_home, service, point_of_interest, establishment | BUCARAMANGA |
| Club de mascotas Momo | corporate_office | corporate_office, point_of_interest, establishment | BUCARAMANGA |
| Funeraria para Mascotas en Ibagué - Sergemas Ibagué | pet_care | pet_care, point_of_interest, establishment | IBAGUÉ |
| Funeraria Lagos del Cacique | funeral_home | funeral_home, service, point_of_interest, establishment | BUCARAMANGA |
| Parque del Cementerio | - | point_of_interest, establishment | SABANALARGA |

## 4. Cruce con las cámaras de comercio (Ibagué 73001 y Villavicencio 50001)

Las cámaras traen CIIU 9603 (pompas fúnebres: servicios funerarios humanos), mientras que la prueba busca términos de mascotas: el cruce mide solapamiento de nombres, no cobertura. Comparables = personas jurídicas con nombre no genérico (se excluyen de la comparación las palabras funeraria, mascotas, exequial, etc.). Similitud = `token_set_ratio` de rapidfuzz contra los lugares de Places del mismo municipio.

| camara | registros | activas | personas_naturales | comparables | con_similitud_85 | con_similitud_70_84 |
|---|---|---|---|---|---|---|
| ibague | 75 | 74 | 18 | 57 | 0 | 2 |
| villavicencio | 19 | 17 | 3 | 16 | 0 | 0 |

### Pares con similitud ≥ 70 (revisión a mano)

| camara | mejor_similitud | razon_social | lugar_places |
|---|---|---|---|
| ibague | 75.0 | GEP IBAGUE | Funeraria para Mascotas en Ibagué - Sergemas Ibagué |
| ibague | 70.6 | PARQUE CEMENTERIO JARDINES LA MILAGROSA | Jardín la Mariposa |

- Lugares de Places en esos dos municipios por tipo principal: {'cemetery': 6, 'pet_care': 2, 'funeral_home': 1, 'point_of_interest': 1, '-': 1}.
