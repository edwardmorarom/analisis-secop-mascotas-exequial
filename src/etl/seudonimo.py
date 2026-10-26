import hashlib
import hmac
import os

from src.etl.comun import cargar_config


def clave():
    cargar_config()
    valor = os.getenv("SEUDONIMO_SALT")
    if not valor:
        raise RuntimeError("Falta SEUDONIMO_SALT en .env (se genera con src.etl.procesar_camaras)")
    return valor.encode()


def seudonimo(fuente, valor, llave=None):
    llave = llave or clave()
    return "PN-" + hmac.new(llave, f"{fuente}|{valor}".encode(), hashlib.sha256).hexdigest()[:12]
