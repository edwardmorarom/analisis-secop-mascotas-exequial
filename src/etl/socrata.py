import time

import requests

from src.etl.comun import token_socrata


def consultar(dominio, dataset, params, intentos=5, espera=5):
    url = f"https://{dominio}/resource/{dataset}.json"
    headers = {"X-App-Token": token_socrata()} if token_socrata() else {}
    for i in range(intentos):
        r = requests.get(url, params=params, headers=headers, timeout=180)
        if r.status_code == 200:
            return r.json()
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(espera * (i + 1))
            continue
        raise RuntimeError(f"{r.status_code} en {r.url[:200]}: {r.text[:300]}")
    raise RuntimeError(f"Sin respuesta tras {intentos} intentos: {r.url[:200]}")


def contar(dominio, dataset, where):
    filas = consultar(dominio, dataset, {"$select": "count(*)", "$where": where})
    return int(filas[0]["count"])


def url_consulta(dominio, dataset):
    return f"https://{dominio}/resource/{dataset}.json"
