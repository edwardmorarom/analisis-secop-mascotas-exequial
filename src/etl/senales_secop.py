import re
from collections import Counter

import pandas as pd
from unidecode import unidecode

from src.etl.anonimizar import PATRONES, anonimizar_con_conteo
from src.etl.comun import cargar_config, ruta
from src.etl.seudonimo import clave, seudonimo
from src.etl.tildes import reparar_tildes

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


TEXTO_ORIGINAL = ["objeto_del_contrato", "descripcion_del_proceso",
                  "detalle_del_objeto_a_contratar", "objeto_del_contrato_a_la"]


def censurar(df, conteo=None, ejemplos=None):
    for col in ("objeto", "descripcion"):
        nuevos = []
        for fuente, llave, texto in zip(df["fuente"], df["llave"], df[col]):
            if fuente == "secop1":
                texto = reparar_tildes(texto)
            censurado, cuenta = anonimizar_con_conteo(texto)
            if cuenta:
                if conteo is not None:
                    conteo.update(cuenta)
                    conteo["filas_afectadas"] += 1
                if ejemplos is not None:
                    ejemplos.append((fuente, llave, col, censurado, tuple(cuenta)))
            nuevos.append(censurado)
        df[col] = nuevos
    return df.drop(columns=TEXTO_ORIGINAL, errors="ignore")


def seudonimizar_proveedores(s1, s2, config):
    """D15: nombres y documentos de personas naturales salen de interim; las jurídicas conservan nombre y NIT."""
    llave = clave()
    archivos_ids = sorted((ruta(config, "interim")).glob("secop1_contratistas*.parquet"))
    if not archivos_ids:
        raise FileNotFoundError("Falta secop1_contratistas.parquet: ejecute python -m src.etl.contratistas_secop1")
    ids = pd.concat([pd.read_parquet(a)[["uid", "contratista_persona_natural", "contratista_id"]] for a in archivos_ids]
                    ).drop_duplicates("uid", keep="first")
    s1 = s1.merge(ids, on="uid", how="left", validate="one_to_one")
    if s1["contratista_id"].isna().any() and s1["contratista_persona_natural"].isna().any():
        raise ValueError("uid de SECOP I sin identificador de contratista")
    natural = s1["contratista_persona_natural"].astype(bool)
    s1.loc[natural, "nom_razon_social_contratista"] = s1.loc[natural, "contratista_id"]
    s1.loc[natural, "identificacion_del_contratista"] = None
    s2 = s2.copy()
    s2["proveedor_persona_natural"] = s2["tipodocproveedor"].fillna("") != "NIT"
    pn = s2["proveedor_persona_natural"]
    s2.loc[pn, "codigo_proveedor"] = [seudonimo("secop2", c, llave) for c in s2.loc[pn, "codigo_proveedor"]]
    s2.loc[pn, "proveedor_adjudicado"] = s2.loc[pn, "codigo_proveedor"]
    return s1, s2


def cargar(config, conteo=None, ejemplos=None):
    raw = ruta(config, "raw") / "secop"
    s2 = pd.read_json(raw / "secop2_candidatos_2020_2025.jsonl", lines=True, dtype=False)
    s1 = pd.concat([pd.read_json(a, lines=True, dtype=False) for a in sorted(raw.glob("secop1_candidatos_*.jsonl"))],
                   ignore_index=True)
    s2 = s2.assign(fuente="secop2", llave=s2["id_contrato"], objeto=s2["objeto_del_contrato"],
                   descripcion=s2["descripcion_del_proceso"],
                   codigo=s2["codigo_de_categoria_principal"].fillna("").str.replace("V1.", "", regex=False),
                   anio=pd.to_datetime(s2["fecha_de_firma"]).dt.year)
    s1 = s1.assign(fuente="secop1", llave=s1["uid"], objeto=s1["detalle_del_objeto_a_contratar"],
                   descripcion=s1["objeto_del_contrato_a_la"],
                   codigo=s1["id_clase"].fillna(""),
                   anio=pd.to_datetime(s1["fecha_de_firma_del_contrato"]).dt.year)
    s1, s2 = seudonimizar_proveedores(
        s1.drop_duplicates("uid", keep="first"), s2.drop_duplicates("id_contrato", keep="first"), config)
    return censurar(s1, conteo, ejemplos), censurar(s2, conteo, ejemplos)


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
    conteo, ejemplos = Counter(), []
    s1, s2 = cargar(config, conteo, ejemplos)
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
    print(f"Anonimización sobre {len(s1) + len(s2):,} filas (objeto y descripción):")
    print({k: conteo[k] for k in ["filas_afectadas", *PATRONES]})
    for fuente, llave, col, texto, patrones in pd.Series(ejemplos).sample(
            min(10, len(ejemplos)), random_state=config["seed"]):
        print(f"- [{fuente} {col} {','.join(patrones)}] {texto[:230]}")
    pd.set_option("display.width", 200)
    print("ANTES (filtro original, sobre crudos)"); print(pd.concat(antes, axis=1).fillna(0).astype(int))
    print("\nDESPUÉS (OSARIO con límite de palabra, ZOONOSIS solo con disposición)")
    print(pd.concat(despues, axis=1).fillna(0).astype(int))


if __name__ == "__main__":
    main()
