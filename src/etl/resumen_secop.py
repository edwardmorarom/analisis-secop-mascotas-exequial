import argparse
import re

import pandas as pd

from src.etl.comun import cargar_config, ruta
from src.etl.descargar_secop import PALABRAS_DESCRIPCION, PALABRAS_OBJETO


def leer(config, nombre):
    return pd.read_json(ruta(config, "raw") / "secop" / nombre, lines=True, dtype=False)


def patron(palabra):
    return re.compile(palabra.replace("_", ".").upper())


def aporte(config):
    df = leer(config, "secop2_candidatos_2020_2025.jsonl")
    objeto = df["objeto_del_contrato"].fillna("").str.upper()
    desc = df["descripcion_del_proceso"].fillna("").str.upper()
    codigo = df["codigo_de_categoria_principal"].fillna("")
    señales = {}
    for p in PALABRAS_OBJETO:
        señales[f"objeto~{p}"] = objeto.str.contains(patron(p))
    for p in PALABRAS_DESCRIPCION:
        señales[f"descripcion~{p}"] = desc.str.contains(patron(p))
    for c in config["secop"]["codigos_unspsc_funerarios"]:
        señales[f"unspsc V1.{c}"] = codigo.str.startswith(f"V1.{c}")
    m = pd.DataFrame(señales)
    tabla = pd.DataFrame({
        "filas": m.sum(),
        "solo_esta_señal": [(m[c] & (m.sum(axis=1) == 1)).sum() for c in m.columns],
    })
    print(f"total filas: {len(df):,}; id_contrato únicos: {df['id_contrato'].nunique():,}")
    print(f"sin ninguna señal reproducible en Python: {(m.sum(axis=1) == 0).sum()}")
    print(tabla.to_string())
    print("\n10 objetos al azar (seed 2026):")
    for o in df["objeto_del_contrato"].sample(10, random_state=config["seed"]):
        print("-", str(o)[:220])


def nit_digitos(serie):
    return serie.astype(str).str.replace(r"\D", "", regex=True)


def duplicados(config):
    s2 = leer(config, "secop2_candidatos_2020_2025.jsonl")
    s1 = leer(config, "secop1_candidatos_2020_2022.jsonl")
    a = pd.DataFrame({
        "nit": nit_digitos(s2["nit_entidad"]),
        "valor": pd.to_numeric(s2["valor_del_contrato"]).round(0),
        "fecha": pd.to_datetime(s2["fecha_de_firma"]).dt.normalize(), "id2": s2["id_contrato"]})
    b = pd.DataFrame({
        "nit": nit_digitos(s1["nit_de_la_entidad"]),
        "valor": pd.to_numeric(s1["cuantia_contrato"]).round(0),
        "fecha": pd.to_datetime(s1["fecha_de_firma_del_contrato"]).dt.normalize(), "uid": s1["uid"]})
    b["nit_sin_dv"] = b["nit"].str[:-1]
    a = a[a["fecha"] <= "2022-12-31"]
    print(f"SECOP II 2020–2022: {len(a):,}; SECOP I: {len(b):,}")
    exacto = a.merge(b, on=["nit", "valor", "fecha"])
    sin_dv = a.merge(b.drop(columns="nit"), left_on=["nit", "valor", "fecha"],
                     right_on=["nit_sin_dv", "valor", "fecha"])
    print(f"coincidencia exacta NIT+valor+fecha: {len(exacto)} pares, {exacto['uid'].nunique()} uid SECOP I")
    print(f"ídem ignorando dígito de verificación: {len(sin_dv)} pares, {sin_dv['uid'].nunique()} uid SECOP I")
    laxa = a.merge(b, on=["nit", "valor"])
    laxa = laxa[(laxa["fecha_x"] - laxa["fecha_y"]).abs() <= pd.Timedelta(days=30)]
    print(f"NIT+valor con fecha ±30 días: {len(laxa)} pares, {laxa['uid'].nunique()} uid SECOP I")
    por_valor = a.merge(b, on=["valor", "fecha"])
    print(f"valor+fecha sin exigir NIT: {len(por_valor)} pares (referencia de falsos positivos)")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("accion", choices=["aporte", "duplicados"])
    a = p.parse_args()
    config = cargar_config()
    aporte(config) if a.accion == "aporte" else duplicados(config)
