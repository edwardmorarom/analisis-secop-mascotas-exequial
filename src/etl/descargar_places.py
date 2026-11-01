import argparse
import json
import os
from datetime import date

from src.etl import places
from src.etl.comun import ahora, cargar_config, ruta
from src.etl.manifiesto import registrar


def hechas(destino):
    if not destino.exists():
        return set(), 0
    claves, llamadas = set(), 0
    with open(destino, encoding="utf-8") as f:
        for linea in f:
            r = json.loads(linea)
            llamadas += 1
            if not r["respuesta"].get("nextPageToken") or len(r["respuesta"].get("places", [])) < 20 or r["pagina"] >= 3:
                claves.add((r["cod_divipola"], r["termino"]))
    return claves, llamadas


def buscar(clave, fila, termino, cfg, salida, contador, tope):
    token, pagina = None, 1
    while True:
        if contador[0] >= tope:
            raise places.TopeDeLlamadas(f"tope de {tope} llamadas")
        peticion = places.cuerpo(termino, fila, token, cfg["tamano_pagina"])
        respuesta = places.llamar(clave, peticion)
        contador[0] += 1
        salida.write(json.dumps({
            "fecha": ahora(), "cod_divipola": fila["cod_divipola"], "termino": termino, "pagina": pagina,
            "peticion": {k: v for k, v in peticion.items() if k != "pageToken"}, "respuesta": respuesta,
        }, ensure_ascii=False) + "\n")
        salida.flush()
        token = respuesta.get("nextPageToken")
        completa = len(respuesta.get("places", [])) >= cfg["tamano_pagina"]
        if not (token and completa and pagina < cfg["max_paginas"]):
            return
        pagina += 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prueba", action="store_true")
    args = ap.parse_args()
    config = cargar_config()
    cfg = config["places"]
    clave = os.getenv("GOOGLE_MAPS_API_KEY")
    if not clave:
        raise SystemExit("Falta GOOGLE_MAPS_API_KEY en .env")
    if not args.prueba:
        raise SystemExit("La corrida completa se hace aparte, tras la prueba y con la cuota subida")
    mm = places.marco(cfg["holgura_nuevo_belen_grados"]).set_index("cod_divipola", drop=False)
    sel = places.muestra_prueba(config, config["seed"])
    terminos = cfg["terminos"] + cfg["terminos_solo_prueba"]
    destino = ruta(config, "raw") / "places" / f"places_prueba_{date.today():%Y%m%d}.jsonl"
    destino.parent.mkdir(parents=True, exist_ok=True)
    previas, usadas = hechas(destino)
    contador = [usadas]
    try:
        with open(destino, "a", encoding="utf-8") as salida:
            for cod in sel["cod_divipola"]:
                for t in terminos:
                    if (cod, t) not in previas:
                        buscar(clave, mm.loc[cod], t, cfg, salida, contador, cfg["tope_llamadas_prueba"])
    except places.ClaveRechazada as e:
        print("La clave de Google fue rechazada:", e)
        raise SystemExit(2)
    except places.TopeDeLlamadas as e:
        print("Detenido:", e)
    registrar(destino, f"{places.URL} (Text Search Pro; términos {terminos})", config)
    print(f"llamadas acumuladas en el archivo: {contador[0]}")


if __name__ == "__main__":
    main()
