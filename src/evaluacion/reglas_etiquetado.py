SECCIONES = {
    "Qué se compra, no dónde (D21)": [
        "Clasifique por lo que el contrato compra, no por el lugar ni la dependencia donde se presta.",
        "Aseo, cafetería, vigilancia y custodia = no_funerario, aunque sea en una funeraria o un cementerio.",
        "Personal administrativo o de apoyo a una dependencia funeraria (supervisión, PQRS, correspondencia, apoyo "
        "financiero o jurídico) = no_funerario: no compra servicios funerarios.",
        "Planes exequiales = funerario.",
        "Sepulturero con otras tareas (albañilería, pintura, aseo) = mixto.",
    ],
    "Marca forense y regla de coherencia": [
        "forense = 1 si el contrato es de necropsias, autopsias, disección, medicina legal, identificación o transporte "
        "de cadáveres con fin judicial. No es una cuarta clase: va en su propia columna (0 o 1).",
        "NN o víctimas, por sí solos, no implican forense: una inhumación de NN o de víctimas es funerario.",
        "Regla de coherencia: si forense = 1, la etiqueta es no_funerario. Excepción: si hay un componente funerario "
        "claro (p. ej. inhumación de cuerpos no identificados), la etiqueta es mixto.",
        "forense = 1 con funerario es un error y se devuelve para revisión. Lo forense se reporta aparte y queda fuera "
        "del tamaño de mercado.",
    ],
    "Cementerios": [
        "Operación o administración del cementerio (inhumación, exhumación, bóvedas, concesión) = funerario.",
        "Obras civiles, mantenimiento físico (luminarias, limpieza, vías), estudios y diseños = no_funerario, aunque "
        "el texto diga «cementerio».",
        "Si el contrato mezcla ambas cosas, mixto. Si el texto no permite decidir, anótelo en notas.",
    ],
}

PRELIMINAR = [
    "Etiquete solo las celdas amarillas: etiqueta (lista) y forense (0 o 1); notas es opcional.",
    "Las tres clases: funerario, no_funerario, mixto. forense es una marca aparte, no una cuarta clase.",
]

FINAL = [
    "Filas 1–40: ronda de calibración. No consulte con la otra persona hasta terminarla.",
    "No modifique el orden de las filas ni las columnas. Detalle en guia_etiquetado.docx.",
]


def instrucciones():
    lineas = list(PRELIMINAR)
    for titulo, reglas in SECCIONES.items():
        lineas.append(titulo.upper())
        lineas += reglas
    return lineas + FINAL


# Criterio completo con el que se etiquetó (D20 y D21 de docs/decisiones.md); lo usa la guía.
D21 = [
    "Se etiqueta según lo que se compra, no según el lugar donde se usa.",
    "Servicios funerarios directos y bienes funerarios (ataúdes, cajas mortuorias, urnas, lápidas) → funerario.",
    "Planes o pólizas de previsión exequial, incluidos los de bienestar para funcionarios → funerario.",
    "Operación o arrendamiento de espacios del cementerio para inhumar → funerario.",
    "Obras, construcción, mantenimiento físico, estudios y diseños, aunque sean en cementerios o edificios "
    "funerarios → no_funerario.",
    "Personal administrativo o de apoyo (supervisión, PQRS, correspondencia, aseo, cafetería, vigilancia, "
    "custodia) de una dependencia funeraria o un cementerio → no_funerario.",
    "Sepulturero junto con otras tareas no funerarias → mixto.",
    "Que un contrato diga «NN» o «víctimas» no lo vuelve forense. Es forense si compra necropsia, toma de muestras, "
    "certificación de defunción, identificación o búsqueda de personas.",
    "Bolsas para cadáveres e insumos para manejar cuerpos en hospitales → manejo sanitario: no_funerario.",
]
D20 = [
    "Tres clases: funerario, no_funerario, mixto. forense es una marca aparte (0 o 1), no una cuarta clase.",
    "Si forense = 1, la etiqueta no puede ser funerario: es no_funerario o, si hay un componente funerario claro "
    "(p. ej. inhumación de cuerpos no identificados), mixto. Lo forense se reporta aparte y queda fuera del tamaño "
    "de mercado.",
]
PROPUESTAS_PENDIENTES = (
    "Propuestas pendientes de la revisión de Harold: la regla 8 en lo relativo a búsqueda de personas y la "
    "infraestructura de Medicina Legal con forense = 1."
)
