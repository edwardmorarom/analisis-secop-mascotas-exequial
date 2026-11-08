"""Cuadros de salida agregados de defunciones no fetales del DANE (EEVV), 2020 a 2025 (D107). Sin microdatos."""
import sys

import requests

from src.etl.comun import cargar_config, ruta
from src.etl.manifiesto import registrar

BASE = "https://www.dane.gov.co"
ARCHIVOS = {
    2020: "/files/investigaciones/poblacion/2022/25-marzo-2022/defunciones-no-fetales2020-cuadros-unificados-definitivo-2020.xls",
    2021: "/files/investigaciones/poblacion/2022/22-diciembre-2022/defunciones-no-fetales2021-cuadro-definitivo-2021.xls",
    2022: "/files/operaciones/EEVV/2023/21-diciembre-2023/defunciones-no-fetales2022-cuadro-definitivo-2022.xls",
    2023: "/files/operaciones/EEVV/2024/19-dic-2024/anex-EEVV-DefuncionesNoFetales2023pCuadroDefinitivo-2023.xls",
    2024: "/files/operaciones/EEVV/2026/6-feb-2026/anex-EEVV-DefuncionesNoFetalesCuadroUnificado-2024.xlsx",
    2025: "/files/operaciones/EEVV/2026/24-sep-2026/anex-EEVV-DefuncionesNoFetalesCuadroUnificado-2025.xlsx",
}
FIRMAS = (b"\xd0\xcf\x11\xe0", b"PK\x03\x04")


def main():
    config = cargar_config()
    destino = ruta(config, "raw") / "dane" / "eevv"
    destino.mkdir(parents=True, exist_ok=True)
    for anio, rel in ARCHIVOS.items():
        r = requests.get(BASE + rel, headers={"User-Agent": "Mozilla/5.0"}, timeout=180)
        if r.status_code != 200 or not r.content.startswith(FIRMAS):
            print(f"{anio}: no se pudo descargar ({r.status_code}); bajar a mano {BASE + rel}")
            return 1
        archivo = destino / f"dane_eevv_defunciones_no_fetales_{anio}{rel[rel.rindex('.'):]}"
        archivo.write_bytes(r.content)
        registrar(archivo, BASE + rel, config)
        print(anio, archivo.name, len(r.content))
    return 0


if __name__ == "__main__":
    sys.exit(main())
