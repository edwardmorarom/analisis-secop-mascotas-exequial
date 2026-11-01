import geopandas as gpd
import numpy as np
import pandas as pd
import requests

from src.etl.comun import RAIZ

URL = "https://places.googleapis.com/v1/places:searchText"
MASCARA = ",".join([
    "places.id", "places.displayName", "places.formattedAddress", "places.location",
    "places.types", "places.primaryType", "places.businessStatus", "nextPageToken",
])
MGN = RAIZ / "data/raw/dane/mgn/MGN_ADM_MPIO_GRAFICO.shp"
DIVIPOLA = RAIZ / "data/raw/dane/dane_divipola.csv"
PANEL = RAIZ / "data/processed/panel_minsalud_municipal.parquet"


class ClaveRechazada(RuntimeError):
    pass


class TopeDeLlamadas(RuntimeError):
    pass


def poligonos():
    return gpd.read_file(MGN).rename(columns={"mpio_cdpmp": "cod_divipola"})[["cod_divipola", "mpio_cnmbr", "geometry"]]


def divipola():
    d = pd.read_csv(DIVIPOLA, dtype=str, encoding="utf-8")
    d.columns = ["cod_dpto", "departamento", "cod_divipola", "municipio", "tipo", "lon", "lat"]
    for c in ("lon", "lat"):
        d[c] = d[c].str.replace(",", ".").astype(float)
    return d


def marco(holgura):
    """Una fila por municipio de DIVIPOLA con su rectángulo de búsqueda (MGN, o punto de DIVIPOLA si no hay polígono)."""
    d, pol = divipola(), poligonos()
    cajas = pol.geometry.bounds.set_index(pol["cod_divipola"])
    m = d.merge(cajas, left_on="cod_divipola", right_index=True, how="left")
    falta = m["minx"].isna()
    m.loc[falta, ["minx", "miny", "maxx", "maxy"]] = np.column_stack([
        m.loc[falta, "lon"] - holgura, m.loc[falta, "lat"] - holgura,
        m.loc[falta, "lon"] + holgura, m.loc[falta, "lat"] + holgura])
    m["sin_poligono"] = falta
    return m


def muestra_prueba(config, semilla):
    """3 grandes (Ibagué y Villavicencio fijos), 4 medianos y 3 pequeños; población DANE 2024 del panel."""
    pob = pd.read_parquet(PANEL).query("anio == 2024")[["cod_divipola", "pob_dane"]].drop_duplicates("cod_divipola")
    pob = pob.sort_values("cod_divipola").reset_index(drop=True)
    fijos = config["places"]["prueba_fijos"]
    rng = np.random.default_rng(semilla)

    def sortear(mascara, n):
        codigos = pob.loc[mascara & ~pob["cod_divipola"].isin(fijos), "cod_divipola"].tolist()
        return sorted(rng.choice(codigos, size=n, replace=False).tolist())

    p = pob["pob_dane"]
    grandes = sortear(p >= 500_000, 3 - len(fijos))
    medianos = sortear((p >= 50_000) & (p < 500_000), 4)
    pequenos = sortear(p < 20_000, 3)
    estrato = {c: "grande" for c in fijos + grandes}
    estrato.update({c: "mediano" for c in medianos})
    estrato.update({c: "pequeno" for c in pequenos})
    return pd.DataFrame({"cod_divipola": list(estrato), "estrato": list(estrato.values())}).merge(pob, on="cod_divipola")


def cuerpo(termino, fila, token=None, tamano=20):
    c = {
        "textQuery": termino, "languageCode": "es", "regionCode": "CO", "pageSize": tamano,
        "locationRestriction": {"rectangle": {
            "low": {"latitude": float(fila["miny"]), "longitude": float(fila["minx"])},
            "high": {"latitude": float(fila["maxy"]), "longitude": float(fila["maxx"])}}},
    }
    if token:
        c["pageToken"] = token
    return c


def llamar(clave, peticion):
    r = requests.post(URL, json=peticion, timeout=60, headers={
        "X-Goog-Api-Key": clave, "X-Goog-FieldMask": MASCARA, "Content-Type": "application/json"})
    estado = ""
    if r.status_code >= 400:
        try:
            estado = r.json().get("error", {}).get("status", "")
        except ValueError:
            pass
    if r.status_code == 429 or estado == "RESOURCE_EXHAUSTED":
        raise TopeDeLlamadas(f"HTTP {r.status_code} {estado}: cuota agotada")
    if r.status_code in (400, 401, 403):
        raise ClaveRechazada(f"HTTP {r.status_code}: {estado}")
    r.raise_for_status()
    return r.json()
