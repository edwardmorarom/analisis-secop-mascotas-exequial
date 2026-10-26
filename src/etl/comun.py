import hashlib
import os
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[2]


def cargar_config():
    with open(RAIZ / "config.yaml", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    load_dotenv(RAIZ / ".env")
    return config


def ruta(config, clave):
    return RAIZ / config["rutas"][clave]


def sha256(path, bloque=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(bloque):
            h.update(chunk)
    return h.hexdigest()


def token_socrata():
    return os.getenv("SOCRATA_APP_TOKEN") or None


def ahora():
    return datetime.now().isoformat(timespec="seconds")
