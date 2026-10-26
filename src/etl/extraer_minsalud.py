import argparse
import collections
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
EQUIVALENCIAS_NOMBRE = {"BARRABQUILLA": "BARRANQUILLA", "SANTIAGO DE CALI": "CALI"}
EQUIVALENCIAS_DEPARTAMENTO = {"SAN ANDRES": "ARCHIPIELAGO DE SAN ANDRES PROVIDENCIA Y SANTA CATALINA"}
# (código de departamento, nombre normalizado del PDF) -> código DIVIPOLA; nombres abreviados o escritos distinto.
EQUIVALENCIAS_MUNICIPIO = {
    ("05", "SANTAFE DE ANTIOQUIA"): "05042", ("05", "S J DE LA MONTANA"): "05658",
    ("13", "MARIALABAJA"): "13442", ("85", "SABANA LARGA"): "85300",
    ("27", "CANTON DE S P"): "27135", ("27", "LITORAL DEL S J"): "27250", ("27", "UNION PANAME"): "27810",
    ("23", "PUEBLO ESCONDIDO"): "23574", ("47", "S B DE PINTO"): "47720", ("47", "SITIO NUEVO"): "47745",
    ("50", "VISTA HERMOSA"): "50711", ("52", "FCO PIZARRO"): "52520", ("52", "R PAYAN"): "52621",
    ("54", "VILLACARO"): "54871", ("86", "VILLA GARZON"): "86885", ("76", "DARIEN"): "76126",
    ("13", "MOMPOS"): "13468", ("47", "CHIBOLO"): "47170", ("70", "TOLU VIEJO"): "70823",
    ("05", "S A DE CUERQUIA"): "05647", ("05", "S P DE LOS MILAGROS"): "05664", ("05", "SAN PEDRO DE U"): "05665",
    ("85", "HATOCOROZAL"): "85125", ("27", "CARM DE ATRATO"): "27245", ("27", "CARMEN DEL DA"): "27150",
    ("97", "MILTU"): "97001",
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


COLUMNAS_ANUAL = ["poblacion_perros", "poblacion_gatos", "poblacion_perros_gatos",
                  "vacunados_perros_dts", "vacunados_perros_particulares", "vacunados_gatos_dts",
                  "vacunados_gatos_particulares", "vacunados_perros", "vacunados_gatos", "vacunados_perros_gatos",
                  "cobertura_perros", "cobertura_gatos", "cobertura_perros_gatos"]
ADITIVAS_ANUAL = COLUMNAS_ANUAL[:10]
NUMERO_ES = re.compile(r"^\d{1,3}(\.\d{3})*$|^\d+$")
PORCENTAJE_ES = re.compile(r"^\d+(,\d+)?\s?%$")
ENCABEZADOS = ("", "municipio", "municipios / distritos")


def celdas_anual(r):
    """Convierte las 13 celdas numéricas según el formato (miles con punto, porcentajes con coma); None si no cuadra."""
    if len(r) != 14 or not r[0] or any(c in (None, "") for c in r[1:]):
        return None
    conteos, porcentajes = [str(c).replace(" ", "") for c in r[1:11]], [str(c).replace(" ", "") for c in r[11:14]]
    if not all(NUMERO_ES.match(c) for c in conteos) or not all(PORCENTAJE_ES.match(c) for c in porcentajes):
        return None
    return [int(c.replace(".", "")) for c in conteos] + [float(c.replace("%", "").replace(",", ".")) for c in porcentajes]


def identidades_anual(valores):
    """La población se redondea por especie y en el total (se admite ±1); las vacunaciones deben sumar exacto."""
    p, g, pg, pd_, pp, gd, gp, vp, vg, vpg = valores[:10]
    return abs(p + g - pg) <= 1 and pd_ + pp == vp and gd + gp == vg and vp + vg == vpg


def respaldo_camelot_anual(path, pagina, nombres):
    """D25: filas que pdfplumber no entrega bien se leen con camelot (stream y luego lattice).
    Se prefiere la lectura que cumple las identidades; si ninguna las cumple, se conserva la primera con formato válido."""
    recuperadas = {}
    for flavor in ("stream", "lattice"):
        faltan = [n for n in nombres if n not in recuperadas or not recuperadas[n][2]]
        if not faltan:
            break
        t = camelot.read_pdf(str(path), pages=str(pagina), flavor=flavor, backend="ghostscript")
        for tabla in t:
            for _, f in tabla.df.iterrows():
                nombre = re.sub(r"\s+", " ", f[0]).strip()
                if nombre not in faltan or len(f) != 14:
                    continue
                valores = celdas_anual([nombre] + [str(c).strip() for c in f[1:14]])
                if valores and (nombre not in recuperadas or (identidades_anual(valores) and not recuperadas[nombre][2])):
                    recuperadas[nombre] = (valores, flavor, identidades_anual(valores))
    return recuperadas


LINEA_ANUAL = re.compile(
    r"^(?P<n>.+?)\s+(?P<v>(?:\d{1,3}(?:\.\d{3})*\s+){10})(?P<p>\d+(?:,\d)?%\s+\d+(?:,\d)?%\s+\d+(?:,\d)?%)\s*$")


def filas_por_texto(path):
    """Capa de texto del PDF: control de completitud independiente de la detección de tablas."""
    filas = []
    with pdfplumber.open(path) as pdf:
        for i, pagina in enumerate(pdf.pages):
            for linea in (pagina.extract_text() or "").split("\n"):
                m = LINEA_ANUAL.match(linea.strip())
                if m:
                    nombre = re.sub(r"\s+", " ", m.group("n")).strip()
                    valores = celdas_anual([nombre] + m.group("v").split() + m.group("p").split())
                    filas.append({"pagina": i + 1, "nombre": nombre, "valores": valores})
    return filas


def completar_desde_texto(filas, texto):
    """Inserta, en su posición, las filas que están en el texto de la página y que la tabla omitió."""
    resultado, k, agregadas = [], 0, []
    for t in texto:
        if k < len(filas) and filas[k]["pagina"] == t["pagina"] and filas[k]["nombre"] == t["nombre"]:
            resultado.append(filas[k])
            k += 1
        else:
            nueva = {"pagina": t["pagina"], "nombre": t["nombre"], "valores": t["valores"],
                     "identidad_ok": bool(t["valores"]) and identidades_anual(t["valores"]), "metodo": "texto"}
            resultado.append(nueva)
            agregadas.append((t["pagina"], t["nombre"]))
    resultado += filas[k:]
    return resultado, agregadas


def extraer_anual(path):
    filas, pendientes = [], collections.defaultdict(list)
    with pdfplumber.open(path) as pdf:
        for i, pagina in enumerate(pdf.pages):
            for tabla in pagina.extract_tables():
                if not tabla or len(tabla[0]) != 14:
                    continue
                for r in tabla:
                    nombre = re.sub(r"\s+", " ", r[0] or "").strip()
                    if not nombre or nombre.lower() in ENCABEZADOS:
                        continue
                    valores = celdas_anual([nombre] + list(r[1:]))
                    ok = bool(valores) and identidades_anual(valores)
                    if not ok:
                        pendientes[i + 1].append(len(filas))
                    filas.append({"pagina": i + 1, "nombre": nombre, "valores": valores, "identidad_ok": ok,
                                  "metodo": "pdfplumber" if valores else "pendiente"})
    bitacora = []
    for pagina, posiciones in pendientes.items():
        nombres = list({filas[k]["nombre"] for k in posiciones})
        rec = respaldo_camelot_anual(path, pagina, nombres)
        mejoradas = 0
        for k in posiciones:
            fila = filas[k]
            if fila["nombre"] in rec:
                valores, flavor, ok = rec[fila["nombre"]]
                if ok or fila["valores"] is None:
                    fila.update(valores=valores, identidad_ok=ok, metodo=f"camelot_{flavor}")
                    mejoradas += 1
        bitacora.append({"pagina": pagina, "filas_revisadas": len(posiciones), "recuperadas_camelot": mejoradas})
    filas, agregadas = completar_desde_texto(filas, filas_por_texto(path))
    if agregadas:
        bitacora.append({"completadas_desde_texto": agregadas})
    sin_resolver = [(f["pagina"], f["nombre"]) for f in filas if f["valores"] is None]
    datos = []
    for f in filas:
        if f["valores"] is None:
            continue
        limpio = re.sub(r"\(ANM\)|\*", "", f["nombre"])
        datos.append({"pagina": f["pagina"], "municipio_pdf": f["nombre"], "municipio_limpio": " ".join(limpio.split()),
                      "anm": int("(ANM)" in f["nombre"]), "ajuste_cobertura": int("*" in f["nombre"]),
                      "metodo_extraccion": f["metodo"], "identidad_ok": int(f["identidad_ok"]),
                      **dict(zip(COLUMNAS_ANUAL, f["valores"]))})
    return pd.DataFrame(datos), bitacora, sin_resolver


def comparar_departamentos_anual(df):
    return comparar_departamentos(df, ADITIVAS_ANUAL)


def clave_distrito(nombre):
    n = EQUIVALENCIAS_NOMBRE.get(normalizar(nombre), normalizar(nombre))
    return n if n in DISTRITOS else None


def marcar_localidades(df, control, columna_nombre):
    """Sin población DANE que las delate, las localidades de Bogotá son las filas contiguas previas a BOGOTÁ que suman su total."""
    for b in df.index[df[columna_nombre].map(lambda n: clave_distrito(n) == "BOGOTA")]:
        total, acumulado, j = df.at[b, control], 0, b - 1
        while j >= 0 and acumulado < total * 1.01:
            acumulado += df.at[j, control]
            if abs(acumulado - total) <= max(2, 0.001 * total) and j < b - 1:
                df.loc[j:b - 1, "tipo"] = "localidad"
                break
            j -= 1


def asignar_bloques(df, divipola, control="pob_pdf", columna_nombre="municipio_pdf", localidades_por_suma=False):
    deps = {normalizar(x): x for x in divipola["Nombre Departamento"].unique()}
    deps_busqueda = {**deps, **{k: deps[normalizar(v)] for k, v in EQUIVALENCIAS_DEPARTAMENTO.items()
                                if normalizar(v) in deps}}
    df = df.copy()
    df["tipo"] = "municipio"
    df["bloque"] = None
    es_nacional = df[columna_nombre].str.upper().str.match(r"^(TOTAL\s+)?NACIONAL\b")
    df.loc[es_nacional, "tipo"] = "nacional"
    df.loc[~es_nacional & df[control].isna(), "tipo"] = "localidad"
    if localidades_por_suma:
        marcar_localidades(df, control, columna_nombre)
    buf = []
    for k in df.index[(df["tipo"] == "municipio")]:
        nombre = normalizar(df.at[k, columna_nombre])
        if nombre in deps_busqueda and buf:
            total = df.at[k, control]
            candidatos = [b for b in buf if clave_distrito(df.at[b, columna_nombre])]
            mejor = None
            for m in range(len(candidatos) + 1):
                for excluir in itertools.combinations(candidatos, m):
                    s = df.loc[[b for b in buf if b not in excluir], control].sum()
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


def cruzar_divipola(df, divipola, umbral=90, margen=5, columna_nombre="municipio_pdf"):
    divipola = divipola.assign(nombre_norm=divipola["Nombre Municipio"].map(normalizar))
    por_dep = {d: g for d, g in divipola.groupby("Nombre Departamento")}
    out = df.copy()
    out["cod_divipola"], out["metodo_cruce"], out["puntaje_cruce"] = None, "sin_cruce", 0.0
    for k in out.index[out["tipo"] == "distrito"]:
        out.at[k, "cod_divipola"] = DISTRITOS[clave_distrito(out.at[k, columna_nombre])]
        out.at[k, "metodo_cruce"], out.at[k, "puntaje_cruce"] = "distrito_tabla", 100.0
    for k in out.index[out["tipo"] == "localidad"]:
        out.at[k, "metodo_cruce"] = "localidad_de_bogota"
    for dep, g in por_dep.items():
        filas = out.index[(out["tipo"] == "municipio") & (out["bloque"] == dep)]
        libres = dict(zip(g["Código Municipio"], g["nombre_norm"]))
        pendientes = []
        for k in filas:
            nombre = normalizar(out.at[k, columna_nombre])
            nombre = EQUIVALENCIAS_NOMBRE.get(nombre, nombre)
            coinciden = [c for c, n in libres.items() if n == nombre]
            if len(coinciden) == 1:
                out.at[k, "cod_divipola"] = coinciden[0]
                out.at[k, "metodo_cruce"], out.at[k, "puntaje_cruce"] = "exacto", 100.0
                del libres[coinciden[0]]
            else:
                pendientes.append(k)
        for k in pendientes:
            nombre = normalizar(out.at[k, columna_nombre])
            clave = (g["Código Departamento"].iloc[0], nombre)
            if clave in EQUIVALENCIAS_MUNICIPIO and EQUIVALENCIAS_MUNICIPIO[clave] in libres:
                cod = EQUIVALENCIAS_MUNICIPIO[clave]
                out.at[k, "cod_divipola"] = cod
                out.at[k, "metodo_cruce"], out.at[k, "puntaje_cruce"] = "tabla_equivalencias", 100.0
                del libres[cod]
        for k in [k for k in pendientes if out.at[k, "cod_divipola"] is None]:
            nombre = normalizar(out.at[k, columna_nombre])
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
    if anio <= 2017:
        x = pd.read_excel(ruta(config, "raw") / "dane" / "dane_proyecciones_municipales_2005_2017.xlsx",
                          sheet_name="NuevaMpal", header=11, dtype=str)
        x = x[(x["AÑO"] == str(anio)) & (x["ÁREA GEOGRÁFICA"] == "Total")]
        return x.set_index("MPIO")["Población"].astype(float).rename("pob_dane")
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


def comparar_departamentos(df, aditivas=None):
    aditivas = aditivas or ADITIVAS
    filas = []
    for dep, g in df[df["tipo"].isin(["municipio", "departamento_total"])].groupby("bloque"):
        total = g[g["tipo"] == "departamento_total"]
        munis = g[g["tipo"] == "municipio"]
        if total.empty:
            continue
        t = total.iloc[0]
        fila = {"departamento": dep, "municipios": len(munis), "pagina_total": t["pagina"]}
        for c in aditivas:
            fila[f"{c}_suma"] = int(munis[c].sum())
            fila[f"{c}_pdf"] = t[c]
            fila[f"{c}_dif"] = int(munis[c].sum() - t[c])
        filas.append(fila)
    return pd.DataFrame(filas)


def procesar_anual(config, anio, divipola):
    path = ruta(config, "raw") / "minsalud" / f"minsalud_vacunacion_{anio}.pdf"
    df, bitacora, sin_resolver = extraer_anual(path)
    if sin_resolver:
        raise ValueError(f"{len(sin_resolver)} filas sin resolver con pdfplumber ni camelot: {sin_resolver[:5]}")
    filas_leidas = len(df)
    df = df.drop_duplicates(subset=["municipio_pdf"] + COLUMNAS_ANUAL, keep="first").reset_index(drop=True)
    duplicados = filas_leidas - len(df)
    df = asignar_bloques(df, divipola, control="poblacion_perros_gatos", columna_nombre="municipio_limpio",
                         localidades_por_suma=True)
    df = cruzar_divipola(df, divipola, columna_nombre="municipio_limpio")
    es_muni = df["tipo"].isin(["municipio", "distrito"])
    df["pob_dane"] = np.where(es_muni, df["cod_divipola"].map(cargar_pob_dane(config, anio)), np.nan)
    df["cobertura_100"] = np.where(es_muni, (df["cobertura_perros_gatos"] == 100.0).astype(int), np.nan)
    for especie, columna in (("perro", "poblacion_perros"), ("gato", "poblacion_gatos")):
        df[f"hab_por_{especie}"] = np.where(es_muni, df["pob_dane"] / df[columna].replace(0, np.nan), np.nan)
    df["metodo_estimacion"] = np.where(es_muni, "no_detectable", None)
    df["anio"], df["anio_fuente"], df["fuente"] = anio, anio, path.name
    return df, comparar_departamentos_anual(df), bitacora, duplicados


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--anio", type=int, required=True)
    a = p.parse_args()
    if a.anio not in (2017, 2019, 2023, 2024):
        raise SystemExit(f"Solo están implementados 2017, 2019, 2023 y 2024; el formato de {a.anio} se revisa antes de extraerlo.")
    config = cargar_config()
    divipola = pd.read_csv(ruta(config, "raw") / "dane" / "dane_divipola.csv", dtype=str)
    interim = ruta(config, "interim")
    interim.mkdir(parents=True, exist_ok=True)
    if a.anio == 2017:
        from src.etl.extraer_minsalud_2017 import procesar
        df, dep, ignoradas = procesar(config, divipola, a.anio)
        df.to_parquet(interim / "minsalud_2017.parquet", index=False)
        dep.to_parquet(interim / "minsalud_2017_departamentos.parquet", index=False)
        print(f"filas: {len(df)} | por tipo: {df['tipo'].value_counts().to_dict()} | líneas ignoradas: {len(ignoradas)}")
        return
    if a.anio != 2019:
        df, dep, bitacora, duplicados = procesar_anual(config, a.anio, divipola)
        df.to_parquet(interim / f"minsalud_{a.anio}.parquet", index=False)
        dep.to_parquet(interim / f"minsalud_{a.anio}_departamentos.parquet", index=False)
        print(f"duplicados eliminados: {duplicados} | filas: {len(df)} | por tipo: {df['tipo'].value_counts().to_dict()}")
        print("respaldo camelot por página:", bitacora)
        return
    path = ruta(config, "raw") / "minsalud" / f"minsalud_vacunacion_{a.anio}.pdf"
    df, bitacora = extraer_2019(path)
    filas_leidas = len(df)
    df = asignar_bloques(quitar_duplicados(df), divipola)
    duplicados = filas_leidas - len(df)
    df = agregar_estimacion(cruzar_divipola(df, divipola), cargar_pob_dane(config, a.anio))
    df["anio"] = a.anio
    df["anio_fuente"] = a.anio
    df["fuente"] = path.name
    df.to_parquet(interim / f"minsalud_{a.anio}.parquet", index=False)
    comparar_departamentos(df).to_parquet(interim / f"minsalud_{a.anio}_departamentos.parquet", index=False)
    print(f"duplicados eliminados (p. 34/35 y resto): {duplicados}")
    print(f"filas: {len(df)} | por tipo: {df['tipo'].value_counts().to_dict()} | respaldo camelot: {bitacora}")


if __name__ == "__main__":
    main()
