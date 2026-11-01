import argparse
import json
import os
from datetime import date

from src.etl import places
from src.etl.comun import ahora, cargar_config, ruta
from src.etl.manifiesto import registrar


def avance(destino, tamano=20, max_paginas=3):
    """Por búsqueda (cod, término): None si terminó; (página siguiente, token) si quedó a medias."""
    estado = {}
    if not destino.exists():
        return estado
    with open(destino, encoding="utf-8") as f:
        for linea in f:
            r = json.loads(linea)
            resp = r["respuesta"]
            token = resp.get("nextPageToken")
            seguir = token and len(resp.get("places", [])) >= tamano and r["pagina"] < max_paginas
            estado[(r["cod_divipola"], r["termino"])] = (r["pagina"] + 1, token) if seguir else None
    return estado


def faltan(estado, cod, terminos):
    return [t for t in terminos if (cod, t) not in estado or estado[(cod, t)] is not None]


def buscar(llamar, clave, fila, termino, cfg, salida, estado, inicio=None):
    pagina, token = inicio or (1, None)
    while True:
        if estado["llamadas"] >= estado["corte"]:
            raise places.TopeDeLlamadas(f"corte de {estado['corte']} llamadas")
        peticion = places.cuerpo(termino, fila, token, cfg["tamano_pagina"])
        respuesta = llamar(clave, peticion)
        estado["llamadas"] += 1
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


def correr(clave, marco, terminos, cfg, directorio, corte, llamar=places.llamar, registrar_archivo=None):
    """Un archivo por municipio; reanuda sin repetir búsquedas ya guardadas. Devuelve el resumen de la ejecución."""
    directorio.mkdir(parents=True, exist_ok=True)
    estado = {"llamadas": 0, "corte": corte}
    tocados, motivo = [], "completa"
    try:
        for cod, fila in marco.set_index("cod_divipola", drop=False).iterrows():
            destino = directorio / f"places_{cod}.jsonl"
            previo = avance(destino, cfg["tamano_pagina"], cfg["max_paginas"])
            pendientes_cod = faltan(previo, cod, terminos)
            if not pendientes_cod:
                continue
            tocados.append(destino)
            with open(destino, "a", encoding="utf-8") as salida:
                for t in pendientes_cod:
                    buscar(llamar, clave, fila, t, cfg, salida, estado, previo.get((cod, t)))
    except places.TopeDeLlamadas as e:
        motivo = f"detenida: {e}"
    except places.ClaveRechazada as e:
        motivo = f"clave rechazada: {e}"
    finally:
        for destino in list(tocados):
            if destino.stat().st_size == 0:
                destino.unlink()
                tocados.remove(destino)
        if registrar_archivo:
            for destino in tocados:
                registrar_archivo(destino)
    pendientes = sum(
        1 for cod in marco["cod_divipola"]
        if faltan(avance(directorio / f"places_{cod}.jsonl", cfg["tamano_pagina"], cfg["max_paginas"]), cod, terminos))
    return {"llamadas": estado["llamadas"], "municipios_pendientes": pendientes, "motivo": motivo}


def corrida_prueba(config, clave):
    cfg = config["places"]
    mm = places.marco(cfg["holgura_nuevo_belen_grados"]).set_index("cod_divipola", drop=False)
    sel = places.muestra_prueba(config, config["seed"])
    terminos = cfg["terminos"] + cfg["terminos_solo_prueba"]
    destino = ruta(config, "raw") / "places" / f"places_prueba_{date.today():%Y%m%d}.jsonl"
    destino.parent.mkdir(parents=True, exist_ok=True)
    previo = avance(destino, cfg["tamano_pagina"], cfg["max_paginas"])
    estado = {"llamadas": 0, "corte": cfg["tope_llamadas_prueba"]}
    try:
        with open(destino, "a", encoding="utf-8") as salida:
            for cod in sel["cod_divipola"]:
                for t in terminos:
                    if faltan(previo, cod, [t]):
                        buscar(places.llamar, clave, mm.loc[cod], t, cfg, salida, estado, previo.get((cod, t)))
    except places.ClaveRechazada as e:
        print("La clave de Google fue rechazada:", e)
        raise SystemExit(2)
    except places.TopeDeLlamadas as e:
        print("Detenido:", e)
    registrar(destino, f"{places.URL} (Text Search Pro; términos {terminos})", config)
    print(f"llamadas en esta ejecución: {estado['llamadas']}")


def corrida_completa(config, clave):
    cfg = config["places"]
    marco = places.marco(cfg["holgura_nuevo_belen_grados"]).sort_values("cod_divipola")
    directorio = ruta(config, "raw") / cfg["directorio_corrida"]
    resumen = correr(
        clave, marco, cfg["terminos"], cfg, directorio, cfg["corte_llamadas_corrida"],
        registrar_archivo=lambda p: registrar(p, f"{places.URL} (Text Search Pro; términos {cfg['terminos']})", config))
    print(resumen)
    if resumen["motivo"].startswith("clave"):
        raise SystemExit(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prueba", action="store_true")
    ap.add_argument("--completa", action="store_true", help="1.122 municipios × 2 términos; requiere la cuota diaria subida a 2.500")
    ap.add_argument("--cuota-subida-a-2500", action="store_true", help="confirma que Edward subió la cuota de SearchTextRequest per day")
    args = ap.parse_args()
    config = cargar_config()
    clave = os.getenv("GOOGLE_MAPS_API_KEY")
    if not clave:
        raise SystemExit("Falta GOOGLE_MAPS_API_KEY en .env")
    if args.prueba:
        corrida_prueba(config, clave)
    elif args.completa:
        if not args.cuota_subida_a_2500:
            raise SystemExit("Falta --cuota-subida-a-2500: la cuota normal (150 al día) no alcanza para la corrida completa")
        corrida_completa(config, clave)
    else:
        raise SystemExit("Indique --prueba o --completa")


if __name__ == "__main__":
    main()
