import csv
from datetime import datetime

from src.etl.comun import RAIZ, ahora, cargar_config, ruta, sha256

CAMPOS = ["archivo", "origen", "url_origen", "fecha", "tamano_bytes", "sha256"]


def leer(path):
    if not path.exists():
        return {}
    with open(path, encoding="utf-8", newline="") as f:
        return {fila["archivo"]: fila for fila in csv.DictReader(f)}


def registrar(path_archivo, url_origen, config=None):
    """Registra un archivo descargado por script, con su URL de origen."""
    config = config or cargar_config()
    manifiesto = ruta(config, "manifiesto")
    filas = leer(manifiesto)
    path_archivo = path_archivo.resolve()
    clave = path_archivo.relative_to(ruta(config, "raw").resolve()).as_posix()
    filas[clave] = {
        "archivo": clave,
        "origen": "api",
        "url_origen": url_origen,
        "fecha": ahora(),
        "tamano_bytes": path_archivo.stat().st_size,
        "sha256": sha256(path_archivo),
    }
    escribir(manifiesto, filas)


def escribir(manifiesto, filas):
    with open(manifiesto, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        for clave in sorted(filas):
            w.writerow(filas[clave])


def main():
    config = cargar_config()
    raw = ruta(config, "raw")
    manifiesto = ruta(config, "manifiesto")
    previo = leer(manifiesto)
    filas = {}
    for p in sorted(raw.rglob("*")):
        if not p.is_file() or p.resolve() == manifiesto.resolve():
            continue
        clave = p.relative_to(raw).as_posix()
        digest = sha256(p)
        anterior = previo.get(clave)
        if anterior and anterior["sha256"] == digest:
            filas[clave] = anterior
            continue
        filas[clave] = {
            "archivo": clave,
            "origen": "manual",
            "url_origen": "",
            "fecha": ahora() if anterior else _mtime(p),
            "tamano_bytes": p.stat().st_size,
            "sha256": digest,
        }
    escribir(manifiesto, filas)
    nuevos = sum(1 for k in filas if k not in previo)
    print(f"{len(filas)} archivos en {manifiesto.relative_to(RAIZ)} ({nuevos} nuevos)")


def _mtime(p):
    return datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds")


if __name__ == "__main__":
    main()
