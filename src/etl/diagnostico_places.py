import json
import re
import unicodedata
from collections import Counter

import geopandas as gpd
import numpy as np
import pandas as pd
from rapidfuzz import fuzz

from src.etl import places
from src.etl.comun import RAIZ, cargar_config
from src.etl.seudonimo import seudonimo

CRUDO = RAIZ / "data/raw/places/places_prueba_20261101.jsonl"
CAMARAS = RAIZ / "data/interim/camaras_ciiu9603.parquet"
SALIDA = RAIZ / "docs/resultados/places_prueba.md"
GENERICAS = {"FUNERARIA", "FUNERARIAS", "FUNERALES", "MASCOTAS", "MASCOTA", "PARA", "DE", "LA", "EL", "LOS", "LAS", "Y",
             "SAS", "S", "A", "LTDA", "SA", "CIA", "EN", "SERVICIOS", "SERVICIO", "EXEQUIALES", "CEMENTERIO", "JARDIN",
             "JARDINES", "PARQUE", "CREMACION", "SEDE", "ADMINISTRATIVA", "OFICINAS", "EL", "DEL"}
VOCABULARIO = re.compile(r"mascota|pet|funer|crema|cement|jard|veterin|clinic|centro|parque|club|oficina|eps|ltda|sas|s\.a|"
                         r"concentrado|osario|memori|hospital|huella|animal|previs|exequ|velaci|casa|alma|bosque|santuario|grupo|recordar|"
                         r"silencio|cielo|capilla|paz|sendero|patit|celest|guarderia|procuradur|compost|lealtad|lado|hotel|incimas", re.I)


def normalizar(texto):
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode().upper()
    return [w for w in re.findall(r"[A-Z0-9]+", t)]


def nucleo(texto):
    return " ".join(w for w in normalizar(texto) if w not in GENERICAS)


def parece_persona(nombre):
    n = unicodedata.normalize("NFKC", nombre)
    sin_tildes = unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode()
    palabras = n.split()
    return 2 <= len(palabras) <= 4 and all(w.isalpha() for w in palabras) and not VOCABULARIO.search(sin_tildes)


def leer_crudo():
    filas, llamadas = [], 0
    with open(CRUDO, encoding="utf-8") as f:
        for linea in f:
            r = json.loads(linea)
            llamadas += 1
            for p in r["respuesta"].get("places", []):
                filas.append({
                    "place_id": p["id"], "nombre": p["displayName"]["text"], "direccion": p.get("formattedAddress"),
                    "lat": p["location"]["latitude"], "lon": p["location"]["longitude"], "tipos": p.get("types", []),
                    "tipo_principal": p.get("primaryType"), "estado_negocio": p.get("businessStatus"),
                    "cod_busqueda": r["cod_divipola"], "termino": r["termino"], "pagina": r["pagina"]})
    return pd.DataFrame(filas), llamadas


def unicos(d, pol):
    u = d.groupby("place_id").agg(
        nombre=("nombre", "first"), direccion=("direccion", "first"), lat=("lat", "first"), lon=("lon", "first"),
        tipos=("tipos", "first"), tipo_principal=("tipo_principal", "first"), estado_negocio=("estado_negocio", "first"),
        cod_busqueda=("cod_busqueda", lambda s: sorted(set(s))), terminos=("termino", lambda s: sorted(set(s)))).reset_index()
    g = gpd.GeoDataFrame(u, geometry=gpd.points_from_xy(u.lon, u.lat), crs=4326)
    g = g.sjoin(pol[["cod_divipola", "geometry"]], how="left", predicate="within").drop(columns=["index_right", "geometry"])
    g["fuera_del_buscado"] = [pd.notna(c) and c not in b for c, b in zip(g["cod_divipola"], g["cod_busqueda"])]
    g["sin_municipio"] = g["cod_divipola"].isna()
    g["nombre_persona"] = g["nombre"].map(parece_persona)
    g.loc[g["nombre_persona"], "nombre"] = g.loc[g["nombre_persona"], "place_id"].map(lambda i: seudonimo("places", i))
    return pd.DataFrame(g)


def cruce_camaras(u):
    c = pd.read_parquet(CAMARAS)
    filas = []
    for camara, cod in (("ibague", "73001"), ("villavicencio", "50001")):
        reg = c[(c["camara"] == camara) & (c["cod_divipola"] == cod)]
        pl = u[u["cod_divipola"] == cod]
        for _, r in reg.iterrows():
            nom = r["razon_social"]
            nuc = nucleo(nom)
            comparable = (not r["es_persona_natural"]) and bool(nuc)
            cand = [(fuzz.token_set_ratio(nuc, nucleo(x)), x) for x in pl["nombre"] if nucleo(x)] if comparable else []
            mejor, lugar = max(cand, default=(0, "")) if comparable else (np.nan, "")
            filas.append({"camara": camara, "cod_divipola": cod, "persona_natural": bool(r["es_persona_natural"]),
                          "activa": str(r["estado_matricula"]).upper().startswith("MATRICULA ACTIVA"),
                          "comparable": comparable, "mejor_similitud": mejor, "lugar_places": lugar, "razon_social": nom})
    return pd.DataFrame(filas)


def fmt(df):
    cols = list(df.columns)
    return "\n".join(["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)] +
                     ["| " + " | ".join(str(v).replace("|", "/") for v in f) + " |" for f in df.itertuples(index=False)])


def main():
    config = cargar_config()
    d, llamadas = leer_crudo()
    pol = places.poligonos()
    nombres = places.marco(config["places"]["holgura_nuevo_belen_grados"]).set_index("cod_divipola")["municipio"]
    u = unicos(d, pol)
    u.to_parquet(RAIZ / "data/interim/places_prueba_unicos.parquet", index=False)

    por_termino = d.groupby("termino").agg(resultados=("place_id", "size"), unicos=("place_id", "nunique")).reset_index()
    por_mun = d.groupby("cod_busqueda").agg(resultados=("place_id", "size"), unicos=("place_id", "nunique")).reset_index()
    por_mun["municipio"] = por_mun["cod_busqueda"].map(nombres)
    todos = Counter(t for ts in u["tipos"] for t in ts)
    tipos = pd.DataFrame(todos.most_common(), columns=["tipo", "lugares_con_el_tipo"])
    principal = u["tipo_principal"].fillna("(sin tipo principal)").value_counts().rename_axis("tipo_principal").reset_index(name="lugares")
    multi = int((u["terminos"].map(len) > 1).sum())

    rng = np.random.default_rng(config["seed"])
    ej = u.iloc[np.sort(rng.choice(len(u), size=min(15, len(u)), replace=False))]
    ej = pd.DataFrame({"nombre": ej["nombre"], "tipo_principal": ej["tipo_principal"].fillna("-"),
                       "tipos": ej["tipos"].map(lambda t: ", ".join(t[:4])),
                       "municipio": ej["cod_divipola"].map(nombres)})

    cr = cruce_camaras(u)
    resumen = cr.groupby("camara").agg(
        registros=("razon_social", "size"), activas=("activa", "sum"), personas_naturales=("persona_natural", "sum"),
        comparables=("comparable", "sum"), con_similitud_85=("mejor_similitud", lambda s: int((s >= 85).sum())),
        con_similitud_70_84=("mejor_similitud", lambda s: int(((s >= 70) & (s < 85)).sum()))).reset_index()
    cerca = cr[cr["mejor_similitud"] >= 70].sort_values("mejor_similitud", ascending=False)
    pl_cam = u[u["cod_divipola"].isin(["73001", "50001"])]
    tipos_cam = pl_cam["tipo_principal"].fillna("-").value_counts().to_dict()

    partes = [
        "# Prueba de Google Places (D101): diagnóstico, sin decisiones",
        f"Prueba del 2026-11-01 con 10 municipios (semilla 2026). Crudo: `data/raw/places/{CRUDO.name}` (con huella en el manifiesto).",
        "## 1. Llamadas y resultados",
        f"- Llamadas gastadas: **{llamadas}** de 150 al día (30 búsquedas de una página: 10 municipios × 3 términos; ninguna llenó 20 resultados, así que no hubo páginas adicionales).",
        f"- Resultados devueltos: **{len(d)}**; lugares únicos por `place_id`: **{len(u)}**; recuperados por más de un término: {multi}.",
        f"- Únicos que caen **fuera del municipio buscado** (punto en polígono del MGN): **{int(u['fuera_del_buscado'].sum())}**; sin municipio (fuera de todo polígono): {int(u['sin_municipio'].sum())}.",
        f"- Nombres con aspecto de persona natural (reemplazados por seudónimo `PN-…`): {int(u['nombre_persona'].sum())}.",
        "### Por término", fmt(por_termino), "### Por municipio buscado", fmt(por_mun),
        "## 2. Tipos de Google (sobre lugares únicos)", "### Todos los tipos", fmt(tipos), "### Tipo principal", fmt(principal),
        "## 3. 15 ejemplos (azar con semilla 2026, solo empresas)", fmt(ej),
        "## 4. Cruce con las cámaras de comercio (Ibagué 73001 y Villavicencio 50001)",
        "Las cámaras traen CIIU 9603 (pompas fúnebres: servicios funerarios humanos), mientras que la prueba busca términos de mascotas: el cruce mide solapamiento de nombres, no cobertura. Comparables = personas jurídicas con nombre no genérico (se excluyen de la comparación las palabras funeraria, mascotas, exequial, etc.). Similitud = `token_set_ratio` de rapidfuzz contra los lugares de Places del mismo municipio.",
        fmt(resumen), "### Pares con similitud ≥ 70 (revisión a mano)",
        fmt(cerca[["camara", "mejor_similitud", "razon_social", "lugar_places"]].round({"mejor_similitud": 1})) if len(cerca) else "Ninguno.",
        f"- Lugares de Places en esos dos municipios por tipo principal: {tipos_cam}.",
    ]
    SALIDA.write_text("\n\n".join(partes) + "\n", encoding="utf-8")
    print("\n\n".join(partes))


if __name__ == "__main__":
    main()
