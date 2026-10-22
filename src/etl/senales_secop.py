import re

import pandas as pd
from unidecode import unidecode

from src.etl.comun import cargar_config, ruta

PALABRAS = {
    "funera": r"FUNERA", "exequ": r"EXEQU", "inhuma": r"INHUMA", "cremaci": r"CREMACI",
    "cad_ver": r"CAD.VER", "sepelio": r"SEPELIO", "sepult": r"SEPULT",
    "cementerio": r"CEMENTERIO", "necr": r"NECR", "animales_muertos": r"ANIMALES MUERTOS",
}
EN_DESCRIPCION = ["funera", "exequ", "inhuma", "cremaci", "animales_muertos"]
OSARIO_ANTES = r"OSARIO"
OSARIO_AHORA = r"\bOSARIOS?\b"
ZOONOSIS = r"ZOONOSIS"
DISPOSICION = r"ANIMALES MUERTOS|CADAVER|DISPOSICION FINAL|INCINERA|RECOLECCION DE ANIMALES|SEPULT"
UNSPSC = {"unspsc_851715": "851715", "unspsc_4813": "4813", "unspsc_422621": "422621"}
SENALES_AHORA = (list(PALABRAS) + ["osario", "zoonosis_disposicion", *UNSPSC])


def norm(serie):
    return serie.fillna("").map(lambda t: unidecode(str(t)).upper())


def contiene(serie, patron):
    return serie.str.contains(patron, regex=True)


def cargar(config):
    raw = ruta(config, "raw") / "secop"
    s2 = pd.read_json(raw / "secop2_candidatos_2020_2025.jsonl", lines=True, dtype=False)
    s1 = pd.read_json(raw / "secop1_candidatos_2020_2022.jsonl", lines=True, dtype=False)
    s2 = s2.assign(fuente="secop2", llave=s2["id_contrato"], objeto=s2["objeto_del_contrato"],
                   descripcion=s2["descripcion_del_proceso"],
                   codigo=s2["codigo_de_categoria_principal"].fillna("").str.replace("V1.", "", regex=False),
                   anio=pd.to_datetime(s2["fecha_de_firma"]).dt.year)
    s1 = s1.assign(fuente="secop1", llave=s1["uid"], objeto=s1["detalle_del_objeto_a_contratar"],
                   descripcion=s1["objeto_del_contrato_a_la"],
                   codigo=s1["id_clase"].fillna(""),
                   anio=pd.to_datetime(s1["fecha_de_firma_del_contrato"]).dt.year)
    return s1.drop_duplicates("uid", keep="first"), s2.drop_duplicates("id_contrato", keep="first")


def senales_antes(df):
    o, d = norm(df["objeto"]), norm(df["descripcion"])
    m = {}
    for k, p in PALABRAS.items():
        m[k] = contiene(o, p) | (contiene(d, p) if k in EN_DESCRIPCION else False)
    m["osario"] = contiene(o, OSARIO_ANTES)
    m["zoonosis"] = contiene(o, ZOONOSIS)
    for k, c in UNSPSC.items():
        m[k] = df["codigo"].str.startswith(c)
    return pd.DataFrame(m)


def senales_ahora(df):
    o, d = norm(df["objeto"]), norm(df["descripcion"])
    texto = o + " | " + d
    m = {}
    for k, p in PALABRAS.items():
        m[k] = contiene(o, p) | (contiene(d, p) if k in EN_DESCRIPCION else False)
    m["osario"] = contiene(o, OSARIO_AHORA)
    m["zoonosis_disposicion"] = contiene(o, ZOONOSIS) & contiene(texto, DISPOSICION)
    for k, c in UNSPSC.items():
        m[k] = df["codigo"].str.startswith(c)
    return pd.DataFrame(m)


def estrato(m):
    nucleo = m[["funera", "exequ", "inhuma", "cremaci", "sepelio", "sepult",
                *UNSPSC]].any(axis=1)
    animales = m["animales_muertos"] | m["zoonosis_disposicion"]
    pendientes = m[["cad_ver", "necr", "cementerio", "osario"]].any(axis=1)
    return pd.Series(
        ["A_nucleo" if a else "B_animales" if b else "C_pendientes" if c else "D_sin_senal"
         for a, b, c in zip(nucleo, animales, pendientes)], index=m.index)


def main():
    config = cargar_config()
    s1, s2 = cargar(config)
    destino = ruta(config, "interim")
    destino.mkdir(parents=True, exist_ok=True)
    antes, despues = [], []
    for nombre, df in (("secop1", s1), ("secop2", s2)):
        m = senales_ahora(df)
        out = pd.concat([df.reset_index(drop=True), m], axis=1)
        out["posible_disposicion_animales"] = m["animales_muertos"] | m["zoonosis_disposicion"]
        out["estrato"] = estrato(m).values
        out.to_parquet(destino / f"{nombre}_senales.parquet", index=False)
        antes.append(senales_antes(df).sum().rename(nombre))
        despues.append(m.sum().rename(nombre))
    pd.set_option("display.width", 200)
    print("ANTES (filtro original, sobre crudos)"); print(pd.concat(antes, axis=1).fillna(0).astype(int))
    print("\nDESPUÉS (OSARIO con límite de palabra, ZOONOSIS solo con disposición)")
    print(pd.concat(despues, axis=1).fillna(0).astype(int))


if __name__ == "__main__":
    main()
