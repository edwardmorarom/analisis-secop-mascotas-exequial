"""Verifica los SHA-256 del paquete de datos del agente (SHA256SUMS.txt) contra los archivos de data/.

Uso: python -m src.agentes.verificar_paquete [ruta/a/SHA256SUMS.txt]
"""
import hashlib
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SUMAS = "SHA256SUMS.txt"


def sha256(ruta, bloque=1 << 20):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for parte in iter(lambda: f.read(bloque), b""):
            h.update(parte)
    return h.hexdigest()


def leer_sumas(archivo):
    sumas = {}
    for linea in Path(archivo).read_text(encoding="utf-8").splitlines():
        if not linea.strip():
            continue
        huella, _, nombre = linea.partition("  ")
        sumas[nombre.strip().lstrip("*")] = huella.strip().lower()
    return sumas


def verificar(archivo, raiz=RAIZ):
    """Devuelve (correctos, faltantes, distintos)."""
    correctos, faltantes, distintos = [], [], []
    for nombre, esperado in leer_sumas(archivo).items():
        ruta = Path(raiz) / nombre
        if not ruta.is_file():
            faltantes.append(nombre)
        elif sha256(ruta) == esperado:
            correctos.append(nombre)
        else:
            distintos.append(nombre)
    return correctos, faltantes, distintos


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    archivo = Path(argv[0]) if argv else RAIZ / SUMAS
    if not archivo.is_file():
        print(f"No existe {archivo}: descomprime el paquete en la raíz del repositorio.")
        return 2
    correctos, faltantes, distintos = verificar(archivo, archivo.parent if argv else RAIZ)
    print(f"correctos: {len(correctos)} | faltantes: {len(faltantes)} | con otra huella: {len(distintos)}")
    for n in faltantes:
        print("  falta:", n)
    for n in distintos:
        print("  huella distinta:", n)
    return 0 if not faltantes and not distintos else 1


if __name__ == "__main__":
    sys.exit(main())
