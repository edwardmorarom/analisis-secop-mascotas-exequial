import json
import re
import shutil
import unicodedata

import geopandas as gpd
import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from src.etl import places
from src.etl.comun import RAIZ, cargar_config, guardar_libro, ruta
from src.etl.diagnostico_places import parece_persona
from src.etl.seudonimo import seudonimo

MASCOTA = re.compile(r"mascota|\bpets?\b|pet\b|canin|felin|animal|huella|patita")
FUNERARIA = re.compile(r"funerar|crema|crematorio|cementerio|memorial|exequial|biocrem|cenizas|inhuma")
NO_FUNERARIA = re.compile(r"\beps\b|clinic|concentrado|supermercado")
TIPOS_NO_PRESTADOR = {"veterinary_care", "pet_store", "hospital", "corporate_office"}
TIPOS_HUMANOS = {"funeral_home", "cemetery"}
CLASES = ["prestador_mascotas", "no_prestador", "mixto"]
MAESTRA = RAIZ / "data/interim/places_clasificacion_reglas.parquet"
LIBROS = [RAIZ / "docs/revision_f5/places_revision_edward.xlsx", RAIZ / "docs/revision_f5/places_revision_segunda_revisora.xlsx"]


def plano(texto):
    t = unicodedata.normalize("NFKC", str(texto))
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()


def regla(nombre, tipo_principal):
    """Reglas de D102 en orden; devuelve (regla, clase probable)."""
    n = plano(nombre)
    if MASCOTA.search(n) and FUNERARIA.search(n):
        return "R1", "prestador_mascotas"
    if (tipo_principal in TIPOS_NO_PRESTADOR or NO_FUNERARIA.search(n)) and not FUNERARIA.search(n):
        return "R2", "no_prestador"
    if tipo_principal in TIPOS_HUMANOS and not MASCOTA.search(n):
        return "R3", "no_prestador"
    return "R4", "revision"


def leer_corrida(directorio):
    filas, llamadas, busquedas = [], 0, set()
    for archivo in sorted(directorio.glob("places_*.jsonl")):
        with open(archivo, encoding="utf-8") as f:
            for linea in f:
                r = json.loads(linea)
                llamadas += 1
                busquedas.add((r["cod_divipola"], r["termino"]))
                for p in r["respuesta"].get("places", []):
                    filas.append({
                        "place_id": p["id"], "nombre": p["displayName"]["text"], "direccion": p.get("formattedAddress"),
                        "lat": p["location"]["latitude"], "lon": p["location"]["longitude"], "tipos": list(p.get("types", [])),
                        "tipo_principal": p.get("primaryType"), "estado_negocio": p.get("businessStatus"),
                        "cod_busqueda": r["cod_divipola"], "termino": r["termino"], "pagina": r["pagina"]})
    return pd.DataFrame(filas), llamadas, busquedas


def consolidar(d, pol, divipola):
    u = d.groupby("place_id").agg(
        nombre=("nombre", "first"), direccion=("direccion", "first"), lat=("lat", "first"), lon=("lon", "first"),
        tipos=("tipos", "first"), tipo_principal=("tipo_principal", "first"), estado_negocio=("estado_negocio", "first"),
        cod_busqueda=("cod_busqueda", lambda s: sorted(set(s))), terminos=("termino", lambda s: sorted(set(s)))).reset_index()
    g = gpd.GeoDataFrame(u, geometry=gpd.points_from_xy(u.lon, u.lat), crs=4326)
    g = pd.DataFrame(g.sjoin(pol[["cod_divipola", "geometry"]], how="left", predicate="within").drop(columns=["index_right", "geometry"]))
    g["sin_municipio"] = g["cod_divipola"].isna()
    g["fuera_del_buscado"] = [pd.notna(c) and c not in b for c, b in zip(g["cod_divipola"], g["cod_busqueda"])]
    g["nombre_persona"] = g["nombre"].map(parece_persona)
    g.loc[g["nombre_persona"], "nombre"] = g.loc[g["nombre_persona"], "place_id"].map(lambda i: seudonimo("places", i))
    nombres = divipola.set_index("cod_divipola")
    g["municipio"] = g["cod_divipola"].map(nombres["municipio"])
    g["departamento"] = g["cod_divipola"].map(nombres["departamento"])
    return g


def aplicar_reglas(u):
    r = [regla(n, t) for n, t in zip(u["nombre"], u["tipo_principal"])]
    u = u.copy()
    u["regla"], u["clase_regla"] = zip(*r)
    u["no_operativo"] = u["estado_negocio"].fillna("OPERATIONAL") != "OPERATIONAL"
    return u


def seleccion(u, semilla, limite=300, n_estrato=60):
    """Todos si son <= 300; si no, todos los de R4 y mín(N, 60) por cada regla decidida (D102). Peso = N / n."""
    u = u.copy()
    rng = np.random.default_rng(semilla)
    u["incluido"], u["peso"] = True, 1.0
    if len(u) <= limite:
        return u
    for r, idx in u[u["regla"] != "R4"].groupby("regla").groups.items():
        n = min(len(idx), n_estrato)
        elegidos = set(rng.choice(sorted(idx), size=n, replace=False))
        u.loc[idx, "incluido"] = [i in elegidos for i in idx]
        u.loc[idx, "peso"] = len(idx) / n
    return u


def escribir_libro(sel, semilla, destino):
    orden = sel[sel["incluido"]].sample(frac=1, random_state=semilla).reset_index(drop=True)
    orden["id_revision"] = [f"L{i + 1:03d}" for i in range(len(orden))]
    wb = Workbook()
    ws = wb.active
    ws.title = "revision"
    cab = ["id_revision", "nombre", "direccion", "municipio", "tipos", "clase"]
    ws.append(cab)
    for r in orden.itertuples():
        ws.append([r.id_revision, r.nombre, r.direccion, f"{r.municipio} ({r.departamento})" if pd.notna(r.municipio) else "(sin municipio)",
                   ", ".join(r.tipos), None])
    for c in ws[1]:
        c.font, c.fill = Font(bold=True, color="FFFFFF"), PatternFill("solid", fgColor="305496")
    for col, ancho in zip("ABCDEF", (12, 45, 55, 32, 50, 22)):
        ws.column_dimensions[col].width = ancho
    for fila in ws.iter_rows(min_row=2):
        for c in fila:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A2"
    validacion = DataValidation(type="list", formula1='"' + ",".join(CLASES) + '"', allow_blank=True)
    ws.add_data_validation(validacion)
    validacion.add(f"F2:F{len(orden) + 1}")
    guia = wb.create_sheet("instrucciones")
    for linea in [
        "Clasifique cada lugar en la columna «clase» (lista desplegable) sin consultar al otro revisor.",
        "prestador_mascotas: ofrece cremación, inhumación u otros servicios funerarios para mascotas.",
        "mixto: funeraria o cementerio de personas que declara atender también mascotas.",
        "no_prestador: cualquier otro lugar (veterinaria sin servicio funerario, tienda, oficina, funeraria solo de personas).",
        "Si el nombre no basta, busque el lugar en Google Maps o en su sitio web, pero no guarde datos de personas.",
        "Guarde su copia como places_revision_<iniciales>.xlsx.",
    ]:
        guia.append([linea])
    guia.column_dimensions["A"].width = 120
    destino.parent.mkdir(parents=True, exist_ok=True)
    guardado = guardar_libro(wb, destino)
    return orden[["id_revision", "place_id"]], guardado


def main():
    config = cargar_config()
    directorio = ruta(config, "raw") / config["places"]["directorio_corrida"]
    d, llamadas, busquedas = leer_corrida(directorio)
    u = aplicar_reglas(consolidar(d, places.poligonos(), places.divipola()))
    sel = seleccion(u, config["seed"])
    ids, guardado = escribir_libro(sel, config["seed"], LIBROS[0])
    if guardado:
        shutil.copyfile(LIBROS[0], LIBROS[1])
    sel = sel.merge(ids, on="place_id", how="left")
    sel.to_parquet(MAESTRA, index=False)
    print(f"llamadas={llamadas} busquedas={len(busquedas)} filas={len(d)} unicos={len(u)} libro_nuevo={guardado}")
    print(u.groupby(["regla", "clase_regla"]).size().to_string())
    print(f"fuera_del_buscado={int(u['fuera_del_buscado'].sum())} sin_municipio={int(u['sin_municipio'].sum())} personas={int(u['nombre_persona'].sum())}")
    print(u["departamento"].fillna("(sin municipio)").value_counts().to_string())
    print(u["tipo_principal"].fillna("(sin tipo principal)").value_counts().to_string())
    print(pd.Series([t for ts in u["tipos"] for t in ts]).value_counts().head(15).to_string())
    print("no operativos:", int(u["no_operativo"].sum()), "| incluidos en el libro:", int(sel["incluido"].sum()))


if __name__ == "__main__":
    main()
