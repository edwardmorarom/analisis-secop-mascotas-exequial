import re

VOCALES = {"a": "Á", "e": "É", "i": "Í", "o": "Ó", "u": "Ú"}
VOCAL_SUELTA = re.compile(r"(?<=[A-ZÑ])[aeiou](?=[A-ZÑ]|\b)")
PALABRA = re.compile(r"\w+")


def reparar_tildes(texto):
    """El campo `detalle_del_objeto_a_contratar` de SECOP I guarda las vocales con tilde en mayúscula como
    minúscula sin tilde (INHUMACIoN, CADaVERES). Se restituye solo en palabras con dos o más mayúsculas."""
    if not isinstance(texto, str):
        return texto

    def palabra(m):
        w = m.group(0)
        if any(c.isdigit() for c in w) or sum(c.isupper() for c in w) < 2:
            return w
        return VOCAL_SUELTA.sub(lambda v: VOCALES[v.group(0)], w)

    return PALABRA.sub(palabra, texto)
