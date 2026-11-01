"""Fallecidos por COVID-19 por mes de muerte (INS, datos.gov.co `gt2j-8ykr`): una consulta agregada, sin microdatos (D99)."""
import json
import re
import sys
from datetime import date

import requests

from src.etl.comun import RAIZ, cargar_config, ruta, token_socrata
from src.etl.manifiesto import registrar
from src.etl.socrata import consultar, url_consulta

DOMINIO, DATASET = "www.datos.gov.co", "gt2j-8ykr"
DESDE, HASTA = "2020", "2025"


def columnas_del_conjunto():
    """Solo metadatos de las columnas (no filas); detecta si el conjunto existe."""
    headers = {"X-App-Token": token_socrata()} if token_socrata() else {}
    r = requests.get(f"https://{DOMINIO}/api/views/{DATASET}.json", headers=headers, timeout=120)
    if r.status_code != 200:
        return None
    return {c["fieldName"]: c["dataTypeName"] for c in r.json().get("columns", [])}


def elegir(columnas, patron, tipos=None):
    for nombre, tipo in columnas.items():
        if re.search(patron, nombre) and (tipos is None or tipo in tipos):
            return nombre
    return None


def main():
    columnas = columnas_del_conjunto()
    if columnas is None:
        print("El conjunto gt2j-8ykr no existe o no responde: no se descarga nada.")
        return 1
    muerte = elegir(columnas, r"fecha.*(muerte|falle)", {"calendar_date", "floating_timestamp", "text"})
    depto = elegir(columnas, r"^departamento_nom$") or elegir(columnas, r"^departamento$")
    print("columnas:", sorted(columnas))
    print("columna de fecha de muerte:", muerte, "| departamento:", depto)
    if muerte is None:
        print("No hay columna de fecha de muerte: no se descarga nada más.")
        return 1
    mes = f"substring({muerte}, 1, 7)"
    seleccion = f"{mes} as mes" + (f", {depto} as departamento" if depto else "") + ", count(*) as fallecidos"
    grupo = "mes" + (", departamento" if depto else "")
    params = {"$select": seleccion, "$where": f"{muerte} IS NOT NULL AND substring({muerte}, 1, 4) between '{DESDE}' and '{HASTA}'", "$group": grupo, "$order": "mes", "$limit": 50000}
    filas = consultar(DOMINIO, DATASET, params)
    destino = ruta(cargar_config(), "raw") / "covid" / f"ins_covid_fallecidos_mes_{date.today():%Y%m%d}.jsonl"
    if destino.exists():
        print(destino.name, "ya existe: no se sobrescribe")
        return 1
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("\n".join(json.dumps(f, ensure_ascii=False) for f in filas) + "\n", encoding="utf-8")
    consulta = f"{url_consulta(DOMINIO, DATASET)}?" + "&".join(f"{k}={v}" for k, v in params.items())
    registrar(destino, consulta, cargar_config())
    total = sum(int(f["fallecidos"]) for f in filas)
    print(f"{len(filas)} filas; {total} fallecidos en total; guardado en {destino.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
