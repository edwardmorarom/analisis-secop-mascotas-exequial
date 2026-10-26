import json

from src.etl.comun import cargar_config, ruta
from src.etl.manifiesto import registrar
from src.etl.socrata import consultar, url_consulta

CIIU_ARAUCA_IBAGUE = ["ciiu_1", "ciiu_2", "ciiu_3", "ciiu_4"]

CAMARAS = {
    "ibague": {
        "columnas": ["nit", "razon_social", "organizacion", *CIIU_ARAUCA_IBAGUE,
                     "municipio_comercial", "estado_de_la_matricula",
                     "fecha_de_matricula", "fecha_renovacion"],
        "ciiu": CIIU_ARAUCA_IBAGUE,
        "persona_natural": lambda f: f.get("organizacion") == "PERSONA NATURAL",
    },
    "arauca": {
        "columnas": ["nit", "razon_social", "organizacion", *CIIU_ARAUCA_IBAGUE,
                     "mun_comercial", "est_matricula", "fec_matricula", "fec_renovacion"],
        "ciiu": CIIU_ARAUCA_IBAGUE,
        "persona_natural": lambda f: f.get("organizacion") == "1",
    },
    "villavicencio": {
        "columnas": ["razon_social", "organizacion", "ciiu_principal",
                     "mun_comercial", "est_matricula", "fec_matricula", "fec_renovacion"],
        "ciiu": ["ciiu_principal"],
        "persona_natural": lambda f: f.get("organizacion") == "PERSONA NATURAL",
    },
}


def main():
    config = cargar_config()
    dom, ciiu = config["secop"]["dominio"], config["camaras"]["ciiu"]
    for camara, spec in CAMARAS.items():
        dataset = config["camaras"]["datasets"][camara]
        where = " OR ".join(f"{c} LIKE '%{ciiu}%'" for c in spec["ciiu"])
        filas = consultar(dom, dataset, {
            "$select": ",".join(spec["columnas"]), "$where": where, "$limit": config["secop"]["pagina"]})
        sin_documento = 0
        for f in filas:
            if spec["persona_natural"](f) and f.pop("nit", None):
                sin_documento += 1
        destino = ruta(config, "raw") / "camaras" / f"camara_{camara}_ciiu{ciiu}.jsonl"
        with open(destino, "w", encoding="utf-8") as out:
            for f in filas:
                out.write(json.dumps(f, ensure_ascii=False) + "\n")
        registrar(destino, f"{url_consulta(dom, dataset)}?$where={where}", config)
        print(f"{camara}: {len(filas)} registros; NIT omitido en {sin_documento} personas naturales")


if __name__ == "__main__":
    main()
