import json

from src.etl.comun import RAIZ, ahora, cargar_config
from src.etl.socrata import consultar


def main():
    config = cargar_config()
    dom, ds = config["secop"]["dominio"], config["secop"]["dataset_secop2"]
    cuenta = int(consultar(dom, ds, {"$select": "count(*)"})[0]["count"])
    vista = consultar_vista(dom, ds)
    registro = {"fecha_consulta": ahora(), "dataset": ds, "count": cuenta, "vista_modificada_epoch": vista}
    destino = RAIZ / config["rutas"]["logs"] / "secop2_count.jsonl"
    destino.parent.mkdir(parents=True, exist_ok=True)
    with open(destino, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro) + "\n")
    print(registro)


def consultar_vista(dominio, dataset):
    import requests

    return requests.get(f"https://{dominio}/api/views/{dataset}.json", timeout=120).json().get("viewLastModified")


if __name__ == "__main__":
    main()
