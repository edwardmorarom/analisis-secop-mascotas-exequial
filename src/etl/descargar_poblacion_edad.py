"""Proyecciones de población departamental por área, sexo y edad 2018-2050 (DANE, actualización de agosto de 2025), para estandarizar tasas por edad (D107b)."""
import sys

import requests

from src.etl.comun import cargar_config, ruta
from src.etl.manifiesto import registrar

URL = "https://www.dane.gov.co/files/censo2018/proyecciones-de-poblacion/Departamental/PPED-AreaSexoEdadDep-2018-2050_VP.xlsx"
NOMBRE = "dane_proyecciones_departamentales_area_sexo_edad_2018_2050.xlsx"


def main():
    config = cargar_config()
    destino = ruta(config, "raw") / "dane" / NOMBRE
    r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=300)
    if r.status_code != 200 or not r.content.startswith(b"PK\x03\x04"):
        print(f"No se pudo descargar ({r.status_code}); bajar a mano {URL}")
        return 1
    destino.write_bytes(r.content)
    registrar(destino, URL, config)
    print(destino.name, len(r.content))
    return 0


if __name__ == "__main__":
    sys.exit(main())
