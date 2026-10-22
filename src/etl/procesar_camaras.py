import hashlib
import hmac
import json
import os
import secrets

import pandas as pd

from src.etl.comun import RAIZ, cargar_config, ruta
from src.etl.descargar_camaras import CAMARAS

RENOMBRAR = {
    "municipio_comercial": "municipio", "mun_comercial": "municipio",
    "estado_de_la_matricula": "estado_matricula", "est_matricula": "estado_matricula",
    "fecha_de_matricula": "fecha_matricula", "fec_matricula": "fecha_matricula",
    "fecha_renovacion": "fecha_renovacion", "fec_renovacion": "fecha_renovacion",
}


def salt():
    cargar_config()
    valor = os.getenv("SEUDONIMO_SALT")
    if not valor:
        valor = secrets.token_hex(32)
        with open(RAIZ / ".env", "a", encoding="utf-8") as f:
            f.write(f"\nSEUDONIMO_SALT={valor}\n")
    return valor.encode()


def seudonimo(camara, razon_social, clave):
    mensaje = f"{camara}|{razon_social}".encode()
    return "PN-" + hmac.new(clave, mensaje, hashlib.sha256).hexdigest()[:12]


def main():
    config = cargar_config()
    clave = salt()
    tablas = []
    for camara, spec in CAMARAS.items():
        raw = ruta(config, "raw") / "camaras" / f"camara_{camara}_ciiu{config['camaras']['ciiu']}.jsonl"
        filas = [json.loads(linea) for linea in open(raw, encoding="utf-8")]
        for f in filas:
            f["camara"] = camara
            f["es_persona_natural"] = spec["persona_natural"](f)
            if f["es_persona_natural"]:
                f["razon_social"] = seudonimo(camara, f["razon_social"], clave)
        tablas.append(pd.DataFrame(filas).rename(columns=RENOMBRAR))
    df = pd.concat(tablas, ignore_index=True)
    df["cod_divipola"] = df["municipio"].str.extract(r"^(\d{5})")[0]
    destino = ruta(config, "interim") / "camaras_ciiu9603.parquet"
    destino.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(destino, index=False)
    print(len(df), "registros;", int(df["es_persona_natural"].sum()), "personas naturales seudonimizadas;",
          int(df["cod_divipola"].isna().sum()), "sin cod_divipola")


if __name__ == "__main__":
    main()
