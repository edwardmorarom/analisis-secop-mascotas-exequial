import json

from src.etl.comun import cargar_config, ruta
from src.etl.manifiesto import registrar
from src.etl.socrata import consultar, url_consulta

EVENTO = "300"
DATASETS = {2017: "84d4-vfax", 2018: "xd2n-cu8j", 2019: "qvnt-2igj", 2021: "fhc4-jjti"}


def main():
    config = cargar_config()
    dom, pagina = config["secop"]["dominio"], config["secop"]["pagina"]
    for anio, dataset in DATASETS.items():
        filas, offset = [], 0
        while True:
            lote = consultar(dom, dataset, {
                "$where": f"cod_eve='{EVENTO}'", "$order": ":id",
                "$limit": pagina, "$offset": offset})
            filas += lote
            if len(lote) < pagina:
                break
            offset += pagina
        destino = ruta(config, "raw") / "ins" / f"ins_sivigila_evento{EVENTO}_{anio}.jsonl"
        with open(destino, "w", encoding="utf-8") as f:
            for fila in filas:
                f.write(json.dumps(fila, ensure_ascii=False) + "\n")
        registrar(destino, f"{url_consulta(dom, dataset)}?cod_eve={EVENTO}", config)
        print(anio, dataset, len(filas), "filas")


if __name__ == "__main__":
    main()
