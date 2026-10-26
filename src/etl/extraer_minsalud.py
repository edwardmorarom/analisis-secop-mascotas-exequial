import argparse
import itertools
import re

import camelot
import numpy as np
import pandas as pd
import pdfplumber
from rapidfuzz import fuzz, process
from unidecode import unidecode

from src.etl.comun import cargar_config, ruta

NUMERICAS_2019 = ["pob_pdf", "poblacion_perros", "poblacion_gatos", "poblacion_perros_gatos",
                  "vacunados_dts", "vacunados_particulares", "perros_vacunados", "cobertura_perros",
                  "acumulado_vacunados", "cobertura_perros_gatos", "vacunados_venezolanos", "revacunados_foco"]
ADITIVAS = ["pob_pdf", "poblacion_perros", "poblacion_gatos", "poblacion_perros_gatos", "vacunados_dts",
            "vacunados_particulares", "perros_vacunados", "acumulado_vacunados"]
TOLERANCIA_BLOQUE = 0.03
# Instructivo 2019 (págs. 2–3): sin metodología propia, población = pob_pdf / razón entera (perros 1–9, gatos 1–25).
RAZON_MAXIMA = {"perro": 9, "gato": 25}
TOLERANCIA_ANIMALES = 1
LIMITES_DIF_POBLACION = (0.8, 1.25)

# Distritos que el PDF lista como DTS aparte (fuera del total de su departamento) y su código DIVIPOLA.
DISTRITOS = {"BARRANQUILLA": "08001", "BOGOTA": "11001", "BUENAVENTURA": "76109",
             "CALI": "76001", "CARTAGENA": "13001", "SANTA MARTA": "47001"}
EQUIVALENCIAS_NOMBRE = {"BARRABQUILLA": "BARRANQUILLA"}
EQUIVALENCIAS_DEPARTAMENTO = {"SAN ANDRES": "ARCHIPIELAGO DE SAN ANDRES PROVIDENCIA Y SANTA CATALINA"}
# (código de departamento, nombre normalizado del PDF) -> código DIVIPOLA; nombres abreviados o escritos distinto.
EQUIVALENCIAS_MUNICIPIO = {
    ("05", "SANTAFE DE ANTIOQUIA"): "05042", ("05", "S J DE LA MONTANA"): "05658",
    ("13", "MARIALABAJA"): "13442", ("85", "SABANA LARGA"): "85300",
    ("27", "CANTON DE S P"): "27135", ("27", "LITORAL DEL S J"): "27250", ("27", "UNION PANAME"): "27810",
    ("23", "PUEBLO ESCONDIDO"): "23574", ("47", "S B DE PINTO"): "47720", ("47", "SITIO NUEVO"): "47745",
    ("50", "VISTA HERMOSA"): "50711", ("52", "FCO PIZARRO"): "52520", ("52", "R PAYAN"): "52621",
    ("54", "VILLACARO"): "54871", ("86", "VILLA GARZON"): "86885", ("76", "DARIEN"): "76126",
}
ABREVIATURAS = {"PTO": "PUERTO", "STA": "SANTA", "STO": "SANTO", "SN": "SAN"}


def normalizar(texto):
    t = unidecode(str(texto)).upper()
    t = re.sub(r"[^A-Z0-9 ]", " ", t)
    return " ".join(ABREVIATURAS.get(w, w) for w in t.split())


def numero(celda):
    if celda is None or str(celda).strip() == "":
        return None
    return int(str(celda).replace(",", "").replace(".", "").strip())


def fila_valida(r):
    return len(r) == 13 and r[0] and not re.search(r"\d", r[0]) and any(c not in ("", None) for c in r[1:])


def tablas_pdfplumber(pdf, indice):
    filas, problemas = [], []
    for tabla in pdf.pages[indice].extract_tables():
        for r in tabla:
            if r[0] == "Municipio" or (len(r) == 1 and not re.search(r"\d", r[0] or "")):
                continue
            if len(r) != 13:
                continue
            if fila_valida(r):
                filas.append(r)
            else:
                problemas.append(re.split(r"\s+\d", re.sub(r"\s+", " ", r[0] or ""))[0].strip())
    return filas, problemas


def recuperar_camelot(path, pagina, nombres):
    """Respaldo de D25: filas que pdfplumber no separó en columnas se leen con camelot (stream)."""
    t = camelot.read_pdf(str(path), pages=str(pagina), flavor="stream", backend="ghostscript")
    recuperadas = []
    for tabla in t:
        for _, f in tabla.df.iterrows():
            nombre = re.sub(r"\s+", " ", f[0]).strip()
            if any(nombre.upper().startswith(n.upper()) for n in nombres if n):
                recuperadas.append([nombre] + [c.strip() for c in f[1:13]])
    return recuperadas


def extraer_2019(path):
    filas, bitacora = [], []
    with pdfplumber.open(path) as pdf:
        for i in range(len(pdf.pages)):
            texto = pdf.pages[i].extract_text() or ""
            if "COBERTURA DE VACUNACIÓN ANTIRRÁBICA POR MUNICIPIO" not in texto and i < 3:
                continue
            tablas = pdf.pages[i].extract_tables()
            if not tablas or tablas[0][0][0] != "Municipio":
                continue
            ok, problemas = tablas_pdfplumber(pdf, i)
            for r in ok:
                filas.append((i + 1, r, "pdfplumber"))
            if problemas:
                rec = recuperar_camelot(path, i + 1, problemas)
                bitacora.append({"pagina": i + 1, "problemas": problemas, "recuperadas_camelot": len(rec)})
                for r in rec:
                    filas.append((i + 1, r, "camelot"))
    datos = []
    for pagina, r, metodo in filas:
        nombre = re.sub(r"\s+", " ", r[0]).strip()
        datos.append({"pagina": pagina, "municipio_pdf": nombre, "metodo_extraccion": metodo,
                      **dict(zip(NUMERICAS_2019, [numero(c) for c in r[1:13]]))})
    return pd.DataFrame(datos), bitacora


def clave_distrito(nombre):
    n = EQUIVALENCIAS_NOMBRE.get(normalizar(nombre), normalizar(nombre))
    return n if n in DISTRITOS else None


def asignar_bloques(df, divipola):
    deps = {normalizar(x): x for x in divipola["Nombre Departamento"].unique()}
    deps_busqueda = {**deps, **{k: deps[normalizar(v)] for k, v in EQUIVALENCIAS_DEPARTAMENTO.items()
                                if normalizar(v) in deps}}
    df = df.copy()
    df["tipo"] = "municipio"
    df["bloque"] = None
    es_nacional = df["municipio_pdf"].str.upper().str.startswith("NACIONAL")
    df.loc[es_nacional, "tipo"] = "nacional"
    df.loc[~es_nacional & df["pob_pdf"].isna(), "tipo"] = "localidad"
    buf = []
    for k in df.index[(df["tipo"] == "municipio")]:
        nombre = normalizar(df.at[k, "municipio_pdf"])
        if nombre in deps_busqueda and buf:
            total = df.at[k, "pob_pdf"]
            candidatos = [b for b in buf if clave_distrito(df.at[b, "municipio_pdf"])]
            mejor = None
            for m in range(len(candidatos) + 1):
                for excluir in itertools.combinations(candidatos, m):
                    s = df.loc[[b for b in buf if b not in excluir], "pob_pdf"].sum()
                    e = abs(s - total) / max(total, 1)
                    if mejor is None or e < mejor[0]:
                        mejor = (e, excluir)
            if mejor[0] < TOLERANCIA_BLOQUE:
                dep = deps_busqueda[nombre]
                df.at[k, "tipo"] = "departamento_total"
                df.at[k, "bloque"] = dep
                for b in buf:
                    if df.at[b, "tipo"] == "localidad":
                        df.at[b, "bloque"] = "DISTRITO"
                    elif b in mejor[1]:
                        df.at[b, "tipo"] = "distrito"
                        df.at[b, "bloque"] = "DISTRITO"
                    else:
                        df.at[b, "bloque"] = dep
                buf = []
                continue
        buf.append(k)
    df.loc[df["tipo"] == "localidad", "bloque"] = "DISTRITO"
    if buf:
        raise ValueError(f"{len(buf)} filas sin bloque departamental")
    return df


def cruzar_divipola(df, divipola, umbral=90, margen=5):
    divipola = divipola.assign(nombre_norm=divipola["Nombre Municipio"].map(normalizar))
    por_dep = {d: g for d, g in divipola.groupby("Nombre Departamento")}
    out = df.copy()
    out["cod_divipola"], out["metodo_cruce"], out["puntaje_cruce"] = None, "sin_cruce", 0.0
    for k in out.index[out["tipo"] == "distrito"]:
        out.at[k, "cod_divipola"] = DISTRITOS[clave_distrito(out.at[k, "municipio_pdf"])]
        out.at[k, "metodo_cruce"], out.at[k, "puntaje_cruce"] = "distrito_tabla", 100.0
    for k in out.index[out["tipo"] == "localidad"]:
        out.at[k, "metodo_cruce"] = "localidad_de_bogota"
    for dep, g in por_dep.items():
        filas = out.index[(out["tipo"] == "municipio") & (out["bloque"] == dep)]
        libres = dict(zip(g["Código Municipio"], g["nombre_norm"]))
        pendientes = []
        for k in filas:
            nombre = normalizar(out.at[k, "municipio_pdf"])
            nombre = EQUIVALENCIAS_NOMBRE.get(nombre, nombre)
            coinciden = [c for c, n in libres.items() if n == nombre]
            if len(coinciden) == 1:
                out.at[k, "cod_divipola"] = coinciden[0]
                out.at[k, "metodo_cruce"], out.at[k, "puntaje_cruce"] = "exacto", 100.0
                del libres[coinciden[0]]
            else:
                pendientes.append(k)
        for k in pendientes:
            nombre = normalizar(out.at[k, "municipio_pdf"])
            clave = (g["Código Departamento"].iloc[0], nombre)
            if clave in EQUIVALENCIAS_MUNICIPIO and EQUIVALENCIAS_MUNICIPIO[clave] in libres:
                cod = EQUIVALENCIAS_MUNICIPIO[clave]
                out.at[k, "cod_divipola"] = cod
                out.at[k, "metodo_cruce"], out.at[k, "puntaje_cruce"] = "tabla_equivalencias", 100.0
                del libres[cod]
        for k in [k for k in pendientes if out.at[k, "cod_divipola"] is None]:
            nombre = normalizar(out.at[k, "municipio_pdf"])
            if not libres:
                continue
            ranking = process.extract(nombre, libres, scorer=fuzz.token_set_ratio, limit=2)
            if ranking and ranking[0][1] >= umbral and (len(ranking) == 1 or ranking[0][1] - ranking[1][1] >= margen):
                cod = ranking[0][2]
                out.at[k, "cod_divipola"] = cod
                out.at[k, "metodo_cruce"], out.at[k, "puntaje_cruce"] = "aproximado", float(ranking[0][1])
                del libres[cod]
    return out


def cargar_pob_dane(config, anio):
    path = ruta(config, "raw") / "dane" / "dane_proyecciones_municipales_2018_2042.xlsx"
    x = pd.read_excel(path, sheet_name="PobMunicipalxÁrea", header=7, dtype=str)
    x = x[(x["AÑO"] == str(anio)) & (x["ÁREA GEOGRÁFICA"] == "Total")]
    return x.set_index("MPIO")["TOTAL"].astype(float).rename("pob_dane")


def razon_reproducible(poblacion, animales, maximo):
    """Razón entera R (1..maximo) con la que round(poblacion / R) reproduce `animales` con ±1 animal; NaN si ninguna."""
    poblacion = np.asarray(poblacion, dtype=float)
    animales = np.asarray(animales, dtype=float)
    valido = ~(np.isnan(poblacion) | np.isnan(animales))
    r = np.arange(1, maximo + 1)
    error = np.abs(np.floor(np.nan_to_num(poblacion)[:, None] / r + 0.5) - np.nan_to_num(animales)[:, None])
    razon = np.where(error.min(axis=1) <= TOLERANCIA_ANIMALES, r[error.argmin(axis=1)], np.nan)
    return np.where(valido, razon, np.nan)


def agregar_estimacion(df, pob_dane):
    out = df.copy()
    es_muni = out["tipo"].isin(["municipio", "distrito"])
    out["pob_dane"] = out["cod_divipola"].map(pob_dane)
    out.loc[~es_muni, "pob_dane"] = np.nan
    cociente = out["pob_pdf"] / out["pob_dane"]
    bajo, alto = LIMITES_DIF_POBLACION
    out["dif_poblacion"] = np.where(es_muni & cociente.notna(), ((cociente < bajo) | (cociente > alto)).astype(int), np.nan)
    for especie, columna in (("perro", "poblacion_perros"), ("gato", "poblacion_gatos")):
        out[f"razon_hab_{especie}"] = np.where(es_muni, out["pob_pdf"] / out[columna].replace(0, np.nan), np.nan)
        razon = razon_reproducible(out["pob_pdf"], out[columna], RAZON_MAXIMA[especie])
        out[f"razon_entera_{especie}"] = np.where(es_muni, razon, np.nan)
        out[f"reproducible_{especie}"] = np.where(es_muni, (~np.isnan(razon)).astype(int), np.nan)
        out[f"metodo_estimacion_{especie}"] = np.where(
            es_muni, np.where(out[f"reproducible_{especie}"] == 1, "imputado", "posible_medido"), None)
        out[f"hab_por_{especie}"] = np.where(es_muni, out["pob_dane"] / out[columna].replace(0, np.nan), np.nan)
    out["metodo_estimacion"] = out["metodo_estimacion_perro"]
    for nombre, columna in (("cobertura_100", "cobertura_perros_gatos"), ("cobertura_perros_100", "cobertura_perros")):
        out[nombre] = np.where(es_muni & out[columna].notna(), (out[columna] == 100).astype(int), np.nan)
    return out


def quitar_duplicados(df):
    claves = ["municipio_pdf"] + NUMERICAS_2019
    return df.drop_duplicates(subset=claves, keep="first").reset_index(drop=True)


def comparar_departamentos(df):
    filas = []
    for dep, g in df[df["tipo"].isin(["municipio", "departamento_total"])].groupby("bloque"):
        total = g[g["tipo"] == "departamento_total"]
        munis = g[g["tipo"] == "municipio"]
        if total.empty:
            continue
        t = total.iloc[0]
        fila = {"departamento": dep, "municipios": len(munis), "pagina_total": t["pagina"]}
        for c in ADITIVAS:
            fila[f"{c}_suma"] = int(munis[c].sum())
            fila[f"{c}_pdf"] = t[c]
            fila[f"{c}_dif"] = int(munis[c].sum() - t[c])
        filas.append(fila)
    return pd.DataFrame(filas)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--anio", type=int, required=True)
    a = p.parse_args()
    if a.anio != 2019:
        raise SystemExit(f"Solo está implementado 2019; el formato de {a.anio} se revisa antes de extraerlo.")
    config = cargar_config()
    path = ruta(config, "raw") / "minsalud" / f"minsalud_vacunacion_{a.anio}.pdf"
    divipola = pd.read_csv(ruta(config, "raw") / "dane" / "dane_divipola.csv", dtype=str)
    df, bitacora = extraer_2019(path)
    filas_leidas = len(df)
    df = asignar_bloques(quitar_duplicados(df), divipola)
    duplicados = filas_leidas - len(df)
    df = agregar_estimacion(cruzar_divipola(df, divipola), cargar_pob_dane(config, a.anio))
    df["anio"] = a.anio
    df["anio_fuente"] = a.anio
    df["fuente"] = path.name
    interim = ruta(config, "interim")
    interim.mkdir(parents=True, exist_ok=True)
    df.to_parquet(interim / f"minsalud_{a.anio}.parquet", index=False)
    comparar_departamentos(df).to_parquet(interim / f"minsalud_{a.anio}_departamentos.parquet", index=False)
    print(f"duplicados eliminados (p. 34/35 y resto): {duplicados}")
    print(f"filas: {len(df)} | por tipo: {df['tipo'].value_counts().to_dict()} | respaldo camelot: {bitacora}")


if __name__ == "__main__":
    main()
