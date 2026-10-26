import re

import numpy as np
import pandas as pd
import pdfplumber

from src.etl.comun import cargar_config, ruta
from src.etl.extraer_minsalud import (DISTRITOS, EQUIVALENCIAS_DEPARTAMENTO, cargar_pob_dane, clave_distrito,
                                      cruzar_divipola, normalizar)

NUMERO = re.compile(r"^\d[\d.,]*$")
ENCABEZADO = re.compile(r"DEPARTAMENTO|Total poblaci|gatos semestre|^gatos$|REPORTE|COLOMBIA A|Fecha|Responsable")
TOTAL = re.compile(r"^\*?\s*Total\s+(?P<nombre>.+)$", re.I)
DISTRITOS_TOTAL = {"BUENAVENTURA", "CARTAGENA", "SANTA MARTA"}
COLUMNAS = ["poblacion_perros", "poblacion_gatos", "poblacion_perros_gatos", "vacunados_perros_gatos", "cobertura_perros_gatos"]
ADITIVAS = COLUMNAS[:4]
TOLERANCIA_BLOQUE = 0.03


def numero(texto):
    t = texto.strip()
    if "," in t:
        return float(t.replace(".", "").replace(",", "."))
    return float(t.replace(".", ""))


def leer_lineas(path):
    filas, ignoradas = [], []
    with pdfplumber.open(path) as pdf:
        for i, pg in enumerate(pdf.pages, 1):
            for linea in (pg.extract_text() or "").split("\n"):
                linea = linea.strip()
                palabras = linea.split()
                n = 0
                while n < len(palabras) and NUMERO.match(palabras[-1 - n]):
                    n += 1
                if not 4 <= n <= 5 or n == len(palabras):
                    if linea and not ENCABEZADO.search(linea):
                        ignoradas.append((i, linea))
                    continue
                v = [numero(x) for x in palabras[-n:]]
                nombre = " ".join(palabras[:-n])
                total = TOTAL.match(nombre)
                fila = {"pagina": i, "municipio_pdf": nombre, "asterisco": int(nombre.startswith("*")),
                        "es_total": bool(total), "nombre_total": total["nombre"].strip() if total else None}
                if len(v) == 4:
                    v = v + [np.nan]
                fila.update(dict(zip(COLUMNAS, v)))
                fila["cobertura_faltante"] = int(np.isnan(fila["cobertura_perros_gatos"]))
                filas.append(fila)
    return pd.DataFrame(filas), ignoradas


def clasificar(df, divipola):
    deps = {normalizar(x): x for x in divipola["Nombre Departamento"].unique()}
    for k, v in EQUIVALENCIAS_DEPARTAMENTO.items():
        deps[k] = deps[normalizar(v)]
    df = df.copy()
    df["tipo"], df["bloque"] = "municipio", None
    df["municipio_limpio"] = df["municipio_pdf"].str.lstrip("* ").str.strip()
    df.loc[df["es_total"], "municipio_limpio"] = df["nombre_total"]
    nacional = df["municipio_limpio"].str.match(r"(?i)^cobertura nacional")
    df.loc[nacional, "tipo"] = "nacional"
    for k in df.index[df["es_total"]]:
        n = normalizar(df.at[k, "nombre_total"])
        if n in DISTRITOS_TOTAL:
            df.at[k, "tipo"], df.at[k, "es_total"] = "distrito", False
        elif "BOGOTA" in n:
            df.at[k, "tipo"], df.at[k, "es_total"] = "distrito", False
        else:
            df.at[k, "tipo"], df.at[k, "bloque"] = "departamento_total", deps[n]
    es_bogota = df["municipio_limpio"].map(lambda n: normalizar(n).startswith("BOGOTA"))
    es_barranquilla = df["municipio_limpio"].map(lambda n: clave_distrito(n) == "BARRANQUILLA")
    df.loc[(df["tipo"] == "municipio") & (es_bogota | es_barranquilla), "tipo"] = "distrito"
    bogota = df.index[es_bogota & (df["tipo"] == "distrito")]
    df.loc[bogota, "municipio_limpio"] = "BOGOTA"
    for b in bogota:
        total, acumulado, j = df.at[b, "poblacion_perros_gatos"], 0, b - 1
        while j >= 0 and acumulado < total * 1.01:
            acumulado += df.at[j, "poblacion_perros_gatos"]
            if abs(acumulado - total) <= max(2, 0.001 * total):
                df.loc[j:b - 1, "tipo"] = "localidad"
                break
            j -= 1
    df.loc[df["tipo"] == "localidad", "bloque"] = "BOGOTÁ"
    df.loc[df["tipo"].isin(["distrito"]), "bloque"] = "DISTRITO"
    buf = []
    for k in df.index:
        if df.at[k, "tipo"] == "municipio":
            buf.append(k)
        elif df.at[k, "tipo"] == "departamento_total":
            df.loc[buf, "bloque"] = df.at[k, "bloque"]
            buf = []
    if buf:
        raise ValueError(f"{len(buf)} filas sin bloque departamental")
    df["cali"] = df["tipo"].eq("municipio") & df["municipio_limpio"].map(lambda n: clave_distrito(n) == "CALI")
    df.loc[df["cali"], "tipo"] = "distrito"
    return df.drop(columns=["cali", "es_total", "nombre_total"])


def comparar_departamentos(df):
    filas = []
    munis = df[df["tipo"].isin(["municipio", "distrito"]) & (df["bloque"] != "DISTRITO")]
    for _, t in df[df["tipo"] == "departamento_total"].iterrows():
        g = munis[munis["bloque"] == t["bloque"]]
        fila = {"departamento": t["bloque"], "municipios": len(g), "pagina_total": t["pagina"]}
        for c in ADITIVAS:
            fila[f"{c}_suma"], fila[f"{c}_pdf"], fila[f"{c}_dif"] = g[c].sum(), t[c], g[c].sum() - t[c]
        filas.append(fila)
    return pd.DataFrame(filas)


def procesar(config, divipola, anio=2017):
    path = ruta(config, "raw") / "minsalud" / f"minsalud_vacunacion_{anio}.pdf"
    df, ignoradas = leer_lineas(path)
    df = clasificar(df, divipola)
    df = cruzar_divipola(df, divipola, columna_nombre="municipio_limpio")
    es_muni = df["tipo"].isin(["municipio", "distrito"])
    df["pob_dane"] = np.where(es_muni, df["cod_divipola"].map(cargar_pob_dane(config, anio)), np.nan)
    df["identidad_ok"] = (df["poblacion_perros"] + df["poblacion_gatos"]).sub(df["poblacion_perros_gatos"]).abs().le(1).astype(int)
    df["cobertura_100"] = np.where(es_muni, (df["cobertura_perros_gatos"] == 100).astype(int), np.nan)
    df["metodo_estimacion"] = np.where(es_muni, "no_detectable", None)
    df["anio"], df["anio_fuente"], df["fuente"] = anio, anio, path.name
    return df, comparar_departamentos(df), ignoradas
