import argparse
import json
import random

from src.etl.comun import cargar_config, ruta
from src.etl.manifiesto import registrar
from src.etl.socrata import consultar, contar, url_consulta

COLUMNAS = """id_contrato, referencia_del_contrato, proceso_de_compra, urlproceso,
  nombre_entidad, nit_entidad, codigo_entidad, orden, sector, rama,
  departamento, ciudad, localizaci_n, direcci_n_de_ejecuci_n_del_contrato,
  objeto_del_contrato, descripcion_del_proceso, codigo_de_categoria_principal,
  tipo_de_contrato, modalidad_de_contratacion, estado_contrato,
  fecha_de_firma, fecha_de_inicio_del_contrato, fecha_de_fin_del_contrato,
  duraci_n_del_contrato, dias_adicionados,
  valor_del_contrato, valor_facturado, valor_pagado,
  origen_de_los_recursos, destino_gasto,
  codigo_proveedor, proveedor_adjudicado, tipodocproveedor, es_pyme,
  ultima_actualizacion"""

PERIODO = "fecha_de_firma BETWEEN '2020-01-01T00:00:00' AND '2025-12-31T23:59:59'"
PALABRAS_OBJETO = ["FUNERA", "EXEQU", "INHUMA", "CREMACI", "CAD_VER", "SEPELIO", "SEPULT",
                   "OSARIO", "CEMENTERIO", "NECR", "ANIMALES MUERTOS", "ZOONOSIS"]
PALABRAS_DESCRIPCION = ["FUNERA", "EXEQU", "INHUMA", "CREMACI", "ANIMALES MUERTOS"]


def condicion_lexica():
    partes = [f"upper(objeto_del_contrato) LIKE '%{p}%'" for p in PALABRAS_OBJETO]
    partes += [f"upper(descripcion_del_proceso) LIKE '%{p}%'" for p in PALABRAS_DESCRIPCION]
    return " OR ".join(partes)


def condicion_unspsc(codigos, estricta=False):
    patron = (lambda c: f"'V1.{c}%'") if estricta else (lambda c: f"'%{c}%'")
    return " OR ".join(f"codigo_de_categoria_principal LIKE {patron(c)}" for c in codigos)


def condicion_candidatos(config, con_unspsc=True, estricta=False):
    condicion = condicion_lexica()
    if con_unspsc:
        condicion += " OR " + condicion_unspsc(config["secop"]["codigos_unspsc_funerarios"], estricta)
    return condicion


def where_secop2(config, con_unspsc=True, estricta=False):
    return f"{PERIODO} AND ({condicion_candidatos(config, con_unspsc, estricta)})"


def where_anio(where, anio):
    acotado = f"fecha_de_firma BETWEEN '{anio}-01-01T00:00:00' AND '{anio}-12-31T23:59:59'"
    return where.replace(PERIODO, acotado, 1)


def cmd_contar(config):
    s = config["secop"]
    dom, ds = s["dominio"], s["dataset_secop2"]
    variantes = {
        "solo_lexica": where_secop2(config, con_unspsc=False),
        "lexica + UNSPSC (CLAUDE.md, '%cod%')": where_secop2(config),
        "lexica + UNSPSC (prefijo 'V1.cod%')": where_secop2(config, estricta=True),
    }
    anios = range(config["periodo"]["anio_inicio"], config["periodo"]["anio_fin"] + 1)
    for nombre, where in variantes.items():
        por_anio = {a: contar(dom, ds, where_anio(where, a)) for a in anios}
        print(f"{nombre}: {sum(por_anio.values()):,}  {por_anio}", flush=True)


def cmd_descargar(config, estricta):
    s = config["secop"]
    dom, ds, pagina = s["dominio"], s["dataset_secop2"], s["pagina"]
    where = where_secop2(config, estricta=estricta)
    destino = ruta(config, "raw") / "secop" / "secop2_candidatos_2020_2025.jsonl"
    escritas = 0
    with open(destino, "w", encoding="utf-8") as f:
        for anio in range(config["periodo"]["anio_inicio"], config["periodo"]["anio_fin"] + 1):
            w = where_anio(where, anio)
            total, offset = contar(dom, ds, w), 0
            while offset < total:
                filas = consultar(dom, ds, {
                    "$select": COLUMNAS, "$where": w,
                    "$order": "id_contrato", "$limit": pagina, "$offset": offset})
                if not filas:
                    break
                for fila in filas:
                    f.write(json.dumps(fila, ensure_ascii=False) + "\n")
                offset += len(filas)
            escritas += offset
            print(f"{anio}: {offset:,}/{total:,}", flush=True)
    registrar(destino, url_consulta(dom, ds) + "?$where=" + where, config)
    print(f"{escritas:,} filas en {destino}")


def cmd_muestra(config):
    s = config["secop"]
    dom, ds, n = s["dominio"], s["dataset_secop2"], s["muestra_no_recuperados"]
    rng = random.Random(config["seed"])
    anios = list(range(config["periodo"]["anio_inicio"], config["periodo"]["anio_fin"] + 1))
    cuotas = {a: n // len(anios) + (1 if i < n % len(anios) else 0) for i, a in enumerate(anios)}
    candidatos = condicion_candidatos(config)
    filas_muestra = []
    for anio, cuota in cuotas.items():
        periodo = f"fecha_de_firma BETWEEN '{anio}-01-01T00:00:00' AND '{anio}-12-31T23:59:59'"
        where = f"{periodo} AND NOT ({candidatos})"
        total = contar(dom, ds, where)
        for offset in sorted(rng.sample(range(total), cuota)):
            fila = consultar(dom, ds, {
                "$select": COLUMNAS, "$where": where,
                "$order": "id_contrato", "$limit": 1, "$offset": offset})
            filas_muestra += [{**f, "anio_estrato": anio} for f in fila]
        print(anio, f"no recuperados: {total:,}", f"muestra: {cuota}")
    destino = ruta(config, "raw") / "secop" / "secop2_muestra_no_recuperados.jsonl"
    with open(destino, "w", encoding="utf-8") as f:
        for fila in filas_muestra:
            f.write(json.dumps(fila, ensure_ascii=False) + "\n")
    registrar(destino, url_consulta(dom, ds) + "?$where=NOT(filtro candidatos) muestreo seed=2026", config)
    print(len(filas_muestra), "contratos en", destino)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("accion", choices=["contar", "descargar", "muestra"])
    p.add_argument("--estricta", action="store_true", help="UNSPSC como prefijo V1.codigo")
    a = p.parse_args()
    config = cargar_config()
    if a.accion == "contar":
        cmd_contar(config)
    elif a.accion == "descargar":
        cmd_descargar(config, a.estricta)
    else:
        cmd_muestra(config)


if __name__ == "__main__":
    main()
