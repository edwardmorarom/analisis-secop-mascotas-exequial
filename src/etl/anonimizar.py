import re
from collections import Counter

from unidecode import unidecode

TOKEN = r"[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]{2,}"
SECUENCIA = rf"{TOKEN}(?:\s+{TOKEN}){{0,3}}"
NUMERO_DOC = r"\d{1,3}(?:[.,]\d{3}){1,3}|\d{5,12}"

PALABRAS_NO_NOMBRE = set("""
DE DEL LA LOS LAS EL AL CON EN PARA POR QUE QUIEN IDENTIFICADO IDENTIFICADA HOSPITALIZADOS
HOSPITALIZADAS ATENDIDOS ATENDIDAS PACIENTE PACIENTES SUBRED HOSPITAL MUNICIPIO ALCALDIA ALCALDE
GOBERNADOR GOBERNACION PRESIDENTE DIRECTOR DIRECTORA GERENTE SECRETARIO SECRETARIA REPRESENTANTE
DOCTOR DOCTORA JUEZ NUMERO HISTORIA CLINICA DIAGNOSTICO ESE EMPRESA SOCIAL ESTADO POBLACION
CRONICOS CRONICAS ADULTOS AMBULATORIOS MUNICIPAL DEPARTAMENTAL DISTRITAL NACIONAL SERVICIOS SERVICIO
SALUD CONTRATO PRESTACION APOYO GESTION UNIDAD PROGRAMA PROYECTO
ESTE ESTA ESTOS ESTAS ESOS BAJO SOBRE SEGUN ANTE ENTRE DESDE HASTA SIN CUANDO DONDE COMO ASI TAMBIEN
MAS MENOS SEA SER SON FUE DURANTE MEDIANTE CONFORME TRAS CONTRA HACIA TODOS TODAS OTROS OTRAS CADA
SUS NUESTRO NUESTRA SINO PERO MUY
COVID CORONAVIRUS SOSPECHOSOS POSITIVOS CONFIRMADOS SARS CRITICOS ENFERMOS DIABETICOS HIPERTENSOS
CONTINGENCIA METROS CUADRADOS INMUEBLE DENOMINADO VICTIMA DESARROLLO ROSARIO
""".split())

SEPARADOR = re.compile(r"(\s+)")


def _censurar_inicio(secuencia, minimo=2):
    partes = SEPARADOR.split(secuencia)
    n = 0
    for i in range(0, len(partes), 2):
        if unidecode(partes[i]).upper() in PALABRAS_NO_NOMBRE:
            break
        n += 1
    if n < minimo:
        return secuencia, False
    resto = "".join(partes[2 * n - 1:]) if 2 * n - 1 < len(partes) else ""
    return "[NOMBRE]" + resto, True


def _censurar_final(secuencia, minimo=1):
    partes = SEPARADOR.split(secuencia)
    n = 0
    for i in range(len(partes) - 1, -1, -2):
        if unidecode(partes[i]).upper() in PALABRAS_NO_NOMBRE:
            break
        n += 1
    if n < minimo:
        return secuencia, False
    return "".join(partes[:len(partes) - 2 * n + 1]) + "[NOMBRE]", True


HISTORIA = re.compile(
    rf"(?:({SECUENCIA})\s+)?((?:N[º°o]\.?\s*)?(?i:historia\s+cl[ií]nica)\s*(?:(?i:n[º°o.]*)\s*)?:?\s*)([\dA-Za-z\-]*\d[\dA-Za-z\-]*)")
DOCUMENTO = re.compile(
    rf"(?i:\b((?:c\.?\s?c\.?|c[eé]dula(?:\s+de\s+ciudadan[ií]a)?|c\.\s?e\.|t\.\s?i\.|pasaporte)"
    rf"\s*(?:n[úu]mero|no\.?|n[º°o]\.?|#)?\s*[:.]?\s*))(?:{NUMERO_DOC})")
PACIENTE = re.compile(rf"((?i:pacientes?)[:\s]+)({SECUENCIA})")
TITULO = re.compile(rf"\b((?i:se[ñn]ora|se[ñn]or|sra|sr|hijo|hija|accionante|afiliado|afiliada)\.?\s+)({SECUENCIA})")
TELEFONO = re.compile(
    r"(?i:(?:tel[eé]fono|tel\.?|cel\.?|celular|m[oó]vil)\s*:?\s*[\d\s().\-+]{7,}\d)"
    r"|(?<![\w.])(?:\+?57[\s-]?)?\(?3\d{2}\)?[\s.-]?\d{3}[\s.-]?\d{4}(?![\w])"
    r"|(?<![\w.])\(?60\d\)?[\s.-]?\d{7}(?![\w])")
IDENTIFICADO = re.compile(
    rf"({SECUENCIA})[;,]?\s+(?=(?i:identificad[oa]\s+con\s+(?:c[eé]dula|c\.?\s?c\b|c\.?\s?e\b|pasaporte)"
    rf"|con\s+c[eé]dula|con\s+c\.?\s?c\b))")
CORREO = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")

PATRONES = ["historia_clinica", "documento", "nombre_paciente", "nombre_titulo", "nombre_identificado",
            "telefono", "correo"]


def anonimizar_con_conteo(texto):
    cuenta = Counter()
    if not isinstance(texto, str):
        return texto, cuenta

    def historia(m):
        nombre, _, _ = m.groups()
        cuenta["historia_clinica"] += 1
        previo = ""
        if nombre:
            previo, hallado = _censurar_final(nombre)
            previo += " "
            if hallado:
                cuenta["nombre_paciente"] += 1
        return f"{previo}[HISTORIA CLÍNICA]"

    def con_prefijo(patron, nombre_patron):
        def f(m):
            if unidecode(m.string[max(0, m.start() - 8):m.start()]).upper().endswith("NUESTRA "):
                return m.group(0)
            sec, hallado = _censurar_inicio(m.group(2))
            if hallado:
                cuenta[nombre_patron] += 1
            return m.group(1) + sec
        return f

    def identificado(m):
        sec, hallado = _censurar_final(m.group(1), minimo=2)
        if hallado:
            cuenta["nombre_identificado"] += 1
        return sec + m.group(0)[len(m.group(1)):]

    def documento(m):
        cuenta["documento"] += 1
        return m.group(1) + "[DOCUMENTO]"

    def simple(nombre):
        def f(m):
            cuenta[nombre] += 1
            return f"[{nombre.upper()}]"
        return f

    texto = HISTORIA.sub(historia, texto)
    texto = IDENTIFICADO.sub(identificado, texto)
    texto = DOCUMENTO.sub(documento, texto)
    texto = PACIENTE.sub(con_prefijo(PACIENTE, "nombre_paciente"), texto)
    texto = TITULO.sub(con_prefijo(TITULO, "nombre_titulo"), texto)
    texto = CORREO.sub(simple("correo"), texto)
    texto = TELEFONO.sub(simple("telefono"), texto)
    return texto, cuenta


def anonimizar(texto):
    return anonimizar_con_conteo(texto)[0]
