import re

import pandas as pd
from rapidfuzz import fuzz

from src.etl.clasificar_places import plano

NIVELES = ["solo_red_social", "ficha_google", "sitio_web_verificado", "registro_formal"]
SERVICIOS = ["cremacion_individual", "cremacion_colectiva", "entierro", "compostaje", "recogida"]
COLUMNAS = ["fuente", "id_fuente", "nombre", "nombre_normalizado", "cod_divipola", "nivel_evidencia", "clase", "ambito"] + SERVICIOS
SOCIETARIAS = {"sas", "s", "a", "sa", "ltda", "limitada", "eu", "e", "u", "cia", "y", "de", "del", "la", "las", "los", "el", "en"}
GENERICAS = {"funeraria", "funerarias", "funerales", "mascota", "mascotas", "pet", "pets", "cremacion", "crematorio",
             "crematorio", "servicios", "servicio", "exequiales", "exequial", "animales", "veterinaria", "memorial", "jardin"}
NIVEL_PLACES = {"sitio_web": "sitio_web_verificado", "red_social": "solo_red_social"}


def normalizar(nombre):
    """Minúsculas sin tildes ni signos, sin sufijos societarios (S.A.S., Ltda.) ni artículos."""
    tokens = re.findall(r"[a-z0-9]+", plano(nombre))
    return " ".join(t for t in tokens if t not in SOCIETARIAS)


def distintivo(normalizado):
    return " ".join(sorted(t for t in normalizado.split() if t not in GENERICAS))


def _base(fuente, d, ambito):
    out = pd.DataFrame(index=d.index)
    out["fuente"] = fuente
    out["nombre"] = d["nombre"]
    out["nombre_normalizado"] = d["nombre"].map(normalizar)
    out["cod_divipola"] = d["cod_divipola"].astype("string")
    out["ambito"] = ambito
    for s in SERVICIOS:
        out[s] = d[s] if s in d else pd.NA
    return out


def desde_places(d):
    """`d`: nombre, cod_divipola, place_id, clase (la decidida por revisión), verificado_en."""
    out = _base("places", d, "mascotas")
    out["id_fuente"] = d["place_id"]
    out["clase"] = d["clase"]
    out["nivel_evidencia"] = d["verificado_en"].map(NIVEL_PLACES).fillna("ficha_google")
    return out[COLUMNAS]


def desde_facebook(d):
    """`d`: nombre, cod_divipola (de la ciudad sede) y las cinco columnas sí/no de servicios; solo empresas."""
    out = _base("facebook", d, "mascotas")
    out["id_fuente"] = [f"fb{i}" for i in range(len(d))]
    out["clase"] = pd.NA
    out["nivel_evidencia"] = "solo_red_social"
    return out[COLUMNAS]


def desde_camaras(d):
    """Solo personas jurídicas de CIIU 9603: contexto de personas, no prestadores de mascotas (D101)."""
    d = d[~d["es_persona_natural"]].rename(columns={"razon_social": "nombre"})
    out = _base("camara", d, "personas")
    out["id_fuente"] = [f"cam{i}" for i in range(len(d))]
    out["clase"] = pd.NA
    out["nivel_evidencia"] = "registro_formal"
    return out[COLUMNAS]


def similitud(a, b):
    """0–100 sobre las palabras distintivas; si alguno solo tiene palabras genéricas, compara el nombre completo y limita a 80."""
    da, db = distintivo(a), distintivo(b)
    if not da or not db:
        return min(fuzz.token_set_ratio(a, b), 80.0)
    return float(fuzz.ratio(da, db))


def cruzar(a, b, umbral=90, dudoso=75):
    """Pares entre dos tablas del esquema, solo dentro del mismo municipio y de a uno por registro (el de mayor similitud).
    Devuelve (seguros, dudosos): los dudosos van a revisión manual."""
    filas = []
    for i, x in a.iterrows():
        for j, y in b[b["cod_divipola"] == x["cod_divipola"]].iterrows():
            s = similitud(x["nombre_normalizado"], y["nombre_normalizado"])
            if s >= dudoso:
                filas.append((s, i, j))
    usados_a, usados_b, seguros, dudosos = set(), set(), [], []
    for s, i, j in sorted(filas, key=lambda f: (-f[0], str(f[1]), str(f[2]))):
        if i in usados_a or j in usados_b:
            continue
        usados_a.add(i)
        usados_b.add(j)
        par = {"id_a": a.loc[i, "id_fuente"], "id_b": b.loc[j, "id_fuente"], "nombre_a": a.loc[i, "nombre"], "nombre_b": b.loc[j, "nombre"],
               "cod_divipola": a.loc[i, "cod_divipola"], "similitud": s}
        (seguros if s >= umbral else dudosos).append(par)
    return pd.DataFrame(seguros), pd.DataFrame(dudosos)
