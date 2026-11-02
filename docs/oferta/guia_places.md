# Guía de revisión de lugares de Google Places (F5)

Versión 1 · 2026-11-02 · Revisan: Edward y Harold, cada quien por separado · Decisión de origen: D102.

## 1. Qué se hace

La corrida de Google Places encontró 255 lugares únicos con los términos «cremación de mascotas» y «funeraria de mascotas». Muchos no son prestadores de mascotas: hay funerarias de personas, veterinarias, tiendas y oficinas. Cada revisor clasifica los 255 en su propia copia del libro de Excel (`places_revision_edward.xlsx` y `places_revision_harold.xlsx`), **sin consultar al otro**. Después se calcula el acuerdo (κ de Cohen) y se resuelven los desacuerdos.

Columnas que se llenan: `clase`, `verificado_en` y `nota`. Las demás son de lectura.

## 2. Criterio central: se etiqueta por lo que el negocio ofrece

La clase depende de **lo que el negocio ofrece al público**, no de su nombre ni del tipo que Google le asignó. Los tipos de Google fallan: hay lugares llamados «Funeraria de mascotas» con tipo `cemetery`, y otros con tipo `pet_care` que son funerarias de personas.

**Servicios funerarios de mascotas** (cuentan): cremación individual o colectiva, entierro o inhumación en cementerio o jardín de mascotas, compostaje de cuerpos de animales y recogida del cuerpo para esos servicios. Si el negocio ofrece y cobra el servicio, cuenta aunque lo ejecute un tercero.

**No cuentan por sí solos:** vender alimento, accesorios, urnas o joyas conmemorativas, peluquería, hotel o guardería canina, atención clínica veterinaria, y dar el teléfono de otro negocio sin ofrecer el servicio.

## 3. Las cuatro clases

| Clase | Cuándo se usa |
|---|---|
| `prestador_mascotas` | Ofrece servicios funerarios de mascotas (sección 2) y no es una funeraria o cementerio de personas. |
| `mixto` | Funeraria o cementerio **de personas** que además ofrece servicios funerarios de mascotas (plan, servicio o sección explícita). |
| `no_prestador` | No ofrece servicios funerarios de mascotas: funeraria o cementerio solo de personas, veterinaria sin ese servicio, tienda, oficina, iglesia, entidad pública, etc. |
| `no_determinable` | Tras revisar las fuentes de la sección 4 no se puede saber qué ofrece el negocio (ficha sin descripción, sin sitio ni red social, nombre ambiguo). No se adivina: se usa esta clase. |

## 4. Cómo verificar y qué anotar

Revise en este orden y deténgase cuando pueda decidir:

1. **Nombre y tipos** del libro → `solo_nombre`.
2. **Ficha de Google Maps** (descripción, categorías, servicios, fotos del local) → `google_maps`.
3. **Sitio web** del negocio → `sitio_web`.
4. **Red social** del negocio (Facebook o Instagram) → `red_social`.

En `verificado_en` anote la fuente que **decidió** la etiqueta. Si dos fuentes se contradicen, manda la más formal: sitio web antes que red social. En `nota` escriba una frase corta con el motivo (por ejemplo: «cremación individual según su sitio web»).

**No se guardan:** reseñas ni su texto, nombres de personas (dueños, empleados, clientes), teléfonos ni correos. Si la ficha muestra un dato personal, no lo copie.

## 5. Casos frontera

| Caso | Qué hacer |
|---|---|
| Veterinaria que ofrece cremación | `prestador_mascotas`: la cremación es un servicio funerario aunque el negocio sea veterinario. Si no ofrece el servicio, o solo remite a otro negocio, `no_prestador`. |
| Funeraria de personas con plan o servicio para mascotas | `mixto`. Si no menciona mascotas en lo que ofrece, `no_prestador`, aunque el nombre del lugar diga «mascotas». |
| Cementerio de personas | `no_prestador`. Si tiene una sección o servicio de mascotas explícito, `mixto`. |
| Oficina o sede administrativa de una empresa de previsión | Se etiqueta por lo que **ofrece la empresa**, no por la oficina: solo mascotas → `prestador_mascotas`; personas y mascotas → `mixto`; solo personas → `no_prestador`. Escriba «oficina» en `nota`. |
| Hotel, guardería, tienda, venta de compost de residuos orgánicos | `no_prestador`, salvo que preste un servicio funerario de mascotas. |
| Mismo negocio con varias fichas o sedes | Etiquete cada fila por separado; los duplicados se resuelven después. |
| Negocio cerrado | Etiquete por lo que ofrecía y escriba «cerrado» en `nota`. |

## 6. Ronda de calibración

Las **25 primeras filas** de ambos libros llevan `ronda = calibracion`. Cada revisor las etiqueta y las entrega primero. Con ellas se calcula el κ de Cohen, se listan los desacuerdos y se ajusta esta guía. **No se continúa con las 230 restantes** hasta que el equipo comunique la guía ajustada.

## 7. Ejemplos de esta corrida

Son ilustrativos: se eligieron por lo que dicen el nombre y la ficha, y ninguno está entre las 25 filas de calibración. Cada revisor verifica por su cuenta antes de etiquetar.

| Clase | Lugar | Municipio | Por qué |
|---|---|---|---|
| `prestador_mascotas` | Funeraria de mascotas y Cremación Pet · TRAFUNPET Medellín | Bello | Ofrece cremación de mascotas y no es una funeraria de personas. |
| `prestador_mascotas` | Pleia · Pet Memorial Garden Funeraria Mascotas | San Vicente Ferrer | Jardín memorial y funeraria dedicados a mascotas. |
| `mixto` | Funeraria San Gabriel Envigado · Funeraria para Mascotas | Envigado | Funeraria de personas que anuncia también servicio para mascotas. |
| `mixto` | Funeraria San Gabriel Itagüí · Sala de Velación · Funeraria para Mascotas | Itagüí | Misma empresa en otra sede: sala de velación de personas y servicio para mascotas. |
| `no_prestador` | Cementerio Jardines de la Asunción | Cómbita | Cementerio de personas; verifique que no tenga sección de mascotas. |
| `no_prestador` | Funeraria La Valvanera | Chía | Funeraria de personas; verifique que no ofrezca plan para mascotas. |
| `no_determinable` | Grupo Recordar | Tunja | Nombre genérico, sin tipo principal y con tipos genéricos: la ficha no dice qué ofrece. |
| `no_determinable` | siempre a tu lado | Santiago de Cali | Tipo de hotel y cuidado de mascotas con nombre ambiguo: puede ser guardería o despedida; decida solo si las fuentes lo aclaran. |

## 8. Dudas

Si un caso no encaja, anótelo en `nota`, etiquete según el criterio de la sección 2 y avise al equipo: los casos nuevos se agregan a la sección 5 en la ronda de calibración.
