# Guía de revisión de lugares de Google Places (F5)

Versión 2 · 2026-11-02 (v1 reemplazada tras la primera ronda de calibración) · Revisan: Edward y Harold, cada quien por separado · Decisión de origen: D102.

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
| `no_determinable` | **Solo después de revisar al menos dos fuentes** de la sección 4 (además del nombre) sin poder saber qué ofrece el negocio (ficha sin descripción, sin sitio ni red social, nombre ambiguo). Las fuentes revisadas se anotan en `nota`. No se usa por no haber mirado. |

## 4. Cómo verificar y qué anotar

**Regla de verificación (v2).** El nombre y los tipos **bastan solo** si el nombre dice explícitamente funeraria, crematorio o cementerio **de mascotas** (por ejemplo «Funeraria de mascotas», «Crematorio de mascotas»). En cualquier otro caso es **obligatorio** revisar la ficha de Google Maps o el sitio web **antes** de decidir. Un nombre que solo sugiere mascotas («Mascopaz», «Pets») o un nombre de funeraria sin más **no basta**.

Revise en este orden y deténgase cuando pueda decidir:

1. **Nombre y tipos** del libro → `solo_nombre`.
2. **Ficha de Google Maps** (descripción, categorías, servicios, fotos del local) → `google_maps`.
3. **Sitio web** del negocio → `sitio_web`.
4. **Red social** del negocio (Facebook o Instagram) → `red_social`.

En `verificado_en` anote la fuente que **decidió** la etiqueta; `solo_nombre` solo es válido cuando se aplica la regla de verificación de arriba. Si dos fuentes se contradicen, manda la más formal: sitio web antes que red social. En `nota` escriba una frase corta con el motivo (por ejemplo: «cremación individual según su sitio web»).

**No se guardan:** reseñas ni su texto, nombres de personas (dueños, empleados, clientes), teléfonos ni correos. Si la ficha muestra un dato personal, no lo copie.

## 5. Casos frontera

| Caso | Qué hacer |
|---|---|
| Veterinaria que ofrece cremación | `prestador_mascotas`: la cremación es un servicio funerario aunque el negocio sea veterinario. Si no ofrece el servicio, o solo remite a otro negocio, `no_prestador`. |
| Funeraria de personas con plan o servicio para mascotas | **Toda funeraria o cementerio de personas se verifica**; nunca se decide por el nombre ni por el tipo. Con servicio o plan para mascotas verificado → `mixto`. Verificado sin servicio para mascotas → `no_prestador`, aunque el nombre del lugar diga «mascotas». Si tras dos fuentes no se sabe → `no_determinable`. |
| Cementerio de personas | Se verifica igual que la funeraria: sección o servicio de mascotas explícito → `mixto`; verificado sin ese servicio → `no_prestador`. |
| Oficina o sede administrativa de una empresa de previsión | Se etiqueta por lo que **ofrece la empresa**, no por la oficina: solo mascotas → `prestador_mascotas`; personas y mascotas → `mixto`; solo personas → `no_prestador`. Escriba «oficina» en `nota`. |
| Hotel, guardería, tienda, venta de compost de residuos orgánicos | `no_prestador`, salvo que preste un servicio funerario de mascotas. |
| Cadena con varias sedes o fichas | Se decide **a nivel de empresa**, con la **misma clase en todas las sedes**. Si el sitio de la empresa muestra el servicio para mascotas, todas las sedes son `mixto` (o `prestador_mascotas`); no se separan por lo que diga la ficha de cada sede. Anote «cadena» en `nota`. |
| Negocio cerrado | Etiquete por lo que ofrecía y escriba «cerrado» en `nota`. |

## 6. Rondas de calibración

- **Ronda 1 (`calibracion`, 25 filas, guía v1).** κ de Cohen = 0,064 sobre 25 pares (acuerdo 0,20). Los desacuerdos vinieron de decidir solo por el nombre (Edward infirió la clase; Harold marcó `no_determinable`) sin verificar. Esta guía v2 corrige eso. Las etiquetas de la ronda 1 no se modifican.
- **Ronda 2 (`calibracion_2`, 25 filas elegidas al azar entre las 230 sin etiquetar, semilla 2027, las mismas en ambos libros).** Cada revisor las etiqueta **con la guía v2**, sin consultar al otro, y las entrega. Se calcula el κ (umbral de referencia 0,70). **No se continúa con las 205 restantes** hasta que el equipo lo comunique.

## 7. Ejemplos de esta corrida

Los dos primeros bloques son ilustrativos (se eligieron por lo que dicen el nombre y la ficha; cada revisor verifica por su cuenta). Los tres últimos (`L018`, `L023`, `L011`) son filas de la ronda 1 **resueltas con verificación**, que muestran cómo se aplica la v2.

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

| Resuelto | Lugar | Municipio | Cómo se decide |
|---|---|---|---|
| `mixto` (`L018`) | La Aurora Funerales y Capillas | Manizales | Por el nombre es una funeraria de personas. Su sitio ofrece servicios exequiales humanos y un plan de mascotas con cremación → `mixto`. Anotar «sitio web» en `verificado_en`. |
| `prestador_mascotas` (`L023`) | Garritas De AMOR - Funeraria de mascotas | Neiva | El nombre dice explícitamente «Funeraria de mascotas»: basta `solo_nombre`, aunque el tipo de Google sea `cemetery`. |
| `prestador_mascotas` (`L011`) | Ambiental Pets | Dosquebradas | El nombre es ambiguo y el tipo `pet_care` no aclara. En su sitio web (sección de servicios) ofrece cremación y traslado de mascotas → `prestador_mascotas`, `verificado_en = sitio_web`. |

## 8. Dudas

Si un caso no encaja, anótelo en `nota`, etiquete según el criterio de la sección 2 y avise al equipo: los casos nuevos se agregan a la sección 5 en la ronda de calibración.

## 9. Qué cuenta como mixto

**PENDIENTE DE CONFIRMACIÓN DE EDWARD.** Las notas de `calibracion_2` están vacías, así que esta definición se dedujo de sus **etiquetas** y de la fuente que anotó en `verificado_en` (D103). No es una regla aprobada.

**Lo observado (`calibracion_2` y filas ya etiquetadas del libro final).**
- De unas 112 filas (agrupadas por palabras del nombre y tipos de Google, sin revisión una a una) cuyo nombre o tipo es de funeraria, capilla, sala de velación, cementerio, parque cementerio o crematorio y que no dicen «mascotas», Edward etiquetó **102 `mixto`**, 9 `prestador_mascotas` y 1 `no_prestador`.
- En `calibracion_2`, 11 de 11 lugares de ese tipo son `mixto`, verificados en Google Maps (7) o en el sitio web (4). En 10 de ellos la segunda revisora, con la misma fuente, no encontró servicio de mascotas y puso `no_prestador`.

**Definición operativa deducida.** Es `mixto` el negocio que cumple **las dos** condiciones:
1. Es funeraria, capilla o sala de velación, cementerio o parque cementerio, o crematorio **de personas** (lo confirma la ficha de Google Maps o el sitio web).
2. Tras revisar esa fuente, **no se descarta** que atienda mascotas: la ficha o el sitio no dicen que solo atiende personas, y ofrece cremación, inhumación o un servicio funerario general que podría extenderse a animales.

**Conflicto con la regla de la sección 5.** La regla escrita dice que una funeraria de personas **verificada sin servicio de mascotas** es `no_prestador`; la definición deducida pone `mixto` salvo evidencia en contra. Son criterios distintos y cambian la oferta que se reporta (D103: con y sin `mixto`). Edward debe elegir una:

- **A. Evidencia explícita (regla actual).** `mixto` solo si la fuente menciona mascotas; si no, `no_prestador`.
- **B. Sin evidencia en contra (deducida).** `mixto` si es funeraria o cementerio de personas con cremación o servicio funerario general y la fuente no excluye a las mascotas.

Con cualquiera de las dos, la `nota` debe llevar la fuente o la URL consultada.
