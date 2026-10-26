import argparse
import json

from src.etl.comun import cargar_config, ruta
from src.etl.descargar_secop import PALABRAS_OBJETO
from src.etl.manifiesto import registrar
from src.etl.socrata import consultar, contar, url_consulta

DATASET = "f789-7hwg"
CAMPOS_OBJETO = ["detalle_del_objeto_a_contratar", "objeto_del_contrato_a_la"]
COLUMNAS = """uid, numero_de_proceso, numero_de_contrato, numero_de_constancia,
  nivel_entidad, orden_entidad, nombre_entidad, nit_de_la_entidad, c_digo_de_la_entidad,
  municipio_entidad, departamento_entidad, municipios_ejecucion,
  modalidad_de_contratacion, estado_del_proceso, tipo_de_contrato,
  objeto_a_contratar, detalle_del_objeto_a_contratar, objeto_del_contrato_a_la,
  id_grupo, id_familia, id_clase, nombre_clase,
  tipo_identifi_del_contratista, identificacion_del_contratista, nom_razon_social_contratista,
  fecha_de_firma_del_contrato, fecha_ini_ejec_contrato, fecha_fin_ejec_contrato,
  plazo_de_ejec_del_contrato, cuantia_proceso, cuantia_contrato,
  valor_total_de_adiciones, valor_contrato_con_adiciones, destino_gasto,
  es_mipyme, ruta_proceso_en_secop_i, ultima_actualizacion"""
PERIODO = "fecha_de_firma_del_contrato BETWEEN '2020-01-01T00:00:00' AND '2022-12-31T23:59:59'"


def condicion(config):
    lex = [f"upper({c}) LIKE '%{p}%'" for c in CAMPOS_OBJETO for p in PALABRAS_OBJETO]
    clases = config["secop"]["codigos_unspsc_funerarios"]
    unspsc = [f"id_clase='{c}'" if len(c) == 6 else f"id_familia='{c}'" for c in clases]
    return " OR ".join(lex + unspsc)


def where_secop1(config, estados=None):
    w = f"{PERIODO} AND ({condicion(config)})"
    if estados:
        lista = ",".join(f"'{e}'" for e in estados)
        w += f" AND estado_del_proceso IN ({lista})"
    return w


def es_nit(fila):
    return "NIT" in fila.get("tipo_identifi_del_contratista", "").upper()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("accion", choices=["estados", "descargar"])
    p.add_argument("--estados", nargs="+", default=["Celebrado", "Liquidado", "Terminado sin Liquidar"])
    a = p.parse_args()
    config = cargar_config()
    dom, pagina = config["secop"]["dominio"], config["secop"]["pagina"]
    if a.accion == "estados":
        r = consultar(dom, DATASET, {"$select": "estado_del_proceso, count(*) as n, count(distinct uid) as uids",
                                     "$where": where_secop1(config), "$group": "estado_del_proceso"})
        for f in r:
            print(f.get("estado_del_proceso"), f["n"], f["uids"])
        return
    where = where_secop1(config, a.estados)
    total = contar(dom, DATASET, where)
    vistos, filas, offset = set(), [], 0
    while offset < total:
        lote = consultar(dom, DATASET, {"$select": COLUMNAS, "$where": where,
                                        "$order": "uid", "$limit": pagina, "$offset": offset})
        if not lote:
            break
        offset += len(lote)
        for f in lote:
            if f["uid"] not in vistos:
                vistos.add(f["uid"])
                if not es_nit(f):
                    f.pop("identificacion_del_contratista", None)
                filas.append(f)
        print(f"{offset:,}/{total:,} filas, {len(filas):,} uid únicos", flush=True)
    destino = ruta(config, "raw") / "secop" / "secop1_candidatos_2020_2022.jsonl"
    with open(destino, "w", encoding="utf-8") as f:
        for fila in filas:
            f.write(json.dumps(fila, ensure_ascii=False) + "\n")
    registrar(destino, f"{url_consulta(dom, DATASET)}?$where={where}", config)
    print(len(filas), "contratos únicos en", destino)


if __name__ == "__main__":
    main()
