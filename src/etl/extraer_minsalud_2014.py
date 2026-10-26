import re

import numpy as np
import pandas as pd
import pdfplumber

from src.etl.comun import cargar_config, ruta
from src.etl.extraer_minsalud import (DISTRITOS, EQUIVALENCIAS_DEPARTAMENTO, cargar_pob_dane, clave_distrito,
                                      cruzar_divipola, normalizar)

NUMERO = re.compile(r"^(\d[\d.,]*|#.*DIV.*|\x01\.\x02)$")
COLUMNAS = ["poblacion_perros", "poblacion_gatos", "poblacion_perros_gatos", "vacunados_perros", "vacunados_gatos",
            "cobertura_perros", "cobertura_gatos", "vacunados_perros_gatos", "cobertura_perros_gatos"]
ADITIVAS = COLUMNAS[:5] + ["vacunados_perros_gatos"]


def numero(texto):
    if texto.startswith("#") or texto.startswith("\x01"):
        return np.nan
    if "," in texto:
        return float(texto.replace(".", "").replace(",", "."))
    return float(texto.replace(".", ""))


X_MUNICIPIO, X_NUMEROS = 58, 208


def texto_columna(chars, x0, x1, fila_alta=False):
    elegidos = [c for c in chars if x0 <= c["x0"] < x1]
    if fila_alta and elegidos:
        minimo = min(c["top"] for c in elegidos)
        elegidos = [c for c in elegidos if c["top"] - minimo < 0.3]
    out, previo = "", None
    for c in sorted(elegidos, key=lambda c: c["x0"]):
        if c["text"].strip() == "":
            continue
        if previo is not None and c["x0"] - previo["x1"] > 1.5:
            out += " "
        out += c["text"]
        previo = c
    return out


def quitar_departamento(palabras, letras):
    consumidas = 0
    for k, palabra in enumerate(palabras):
        if consumidas >= letras:
            return " ".join(palabras[k:])
        consumidas += len(palabra)
    return ""


def leer_lineas(path):
    filas, ignoradas = [], []
    with pdfplumber.open(path) as pdf:
        for i, pg in enumerate(pdf.pages, 1):
            for linea in pg.extract_text_lines():
                texto = re.sub(r"(\d) \.(\d{3})", r".", linea["text"].strip())
                palabras = texto.split()
                n = 0
                while n < len(palabras) and NUMERO.match(palabras[-1 - n]):
                    n += 1
                if n != len(COLUMNAS) or n == len(palabras):
                    ignoradas.append((i, texto))
                    continue
                departamento = texto_columna(linea["chars"], 0, X_MUNICIPIO)
                desbordado = departamento.startswith("NORTE")
                if desbordado:
                    municipio = texto_columna(linea["chars"], X_MUNICIPIO, X_NUMEROS, True)
                else:
                    municipio = quitar_departamento(palabras[:-n], len(departamento.replace(" ", "")))
                fila = {"pagina": i, "departamento_pdf": departamento, "municipio_pdf": municipio}
                fila.update(dict(zip(COLUMNAS, [numero(x) for x in palabras[-n:]])))
                filas.append(fila)
    df = pd.DataFrame(filas)
    df["poblacion_gatos_derivada"] = df["poblacion_gatos"].isna().astype(int)
    derivada = df["poblacion_gatos_derivada"] == 1
    df.loc[derivada, "poblacion_gatos"] = df["poblacion_perros_gatos"] - df["poblacion_perros"]
    return df, ignoradas


def asignar_departamento(df, divipola):
    deps = {normalizar(x).replace(" ", ""): x for x in divipola["Nombre Departamento"].unique()}
    out = df.copy()
    bloques = []
    for dep in out["departamento_pdf"]:
        n = normalizar(dep).replace(" ", "")
        candidatos = [d for d in deps if d == n or (len(n) >= 4 and (n in d or n.startswith(d) or d.startswith(n)))]
        if n.startswith(("BARRANQUILLA", "BOGOTA", "CARTAGENA", "SANTAMARTA", "BUENAVENTURA")):
            bloques.append("DISTRITO")
        elif n in deps:
            bloques.append(deps[n])
        elif len(candidatos) == 1:
            bloques.append(deps[candidatos[0]])
        else:
            bloques.append(None)
    out["bloque"] = bloques
    return out


def limpiar_nombre(nombre):
    n = nombre.replace("*", "").strip()
    return re.sub(r"\s*-\s*[A-Z]{1,3}$", "", n).strip()


def procesar(config, divipola, anio=2014):
    path = ruta(config, "raw") / "minsalud" / f"minsalud_vacunacion_{anio}.pdf"
    df, ignoradas = leer_lineas(path)
    df = asignar_departamento(df, divipola)
    sai = df["bloque"].isna() & df["departamento_pdf"].str.startswith("SAN ANDRES")
    assert sai.sum() == 2, "se esperaban dos filas de San Andrés y Providencia"
    indices = df.index[sai]
    assert df.loc[indices[0], "poblacion_perros_gatos"] < df.loc[indices[1], "poblacion_perros_gatos"]
    df.loc[sai, "bloque"] = "ARCHIPI\u00c9LAGO DE SAN ANDR\u00c9S, PROVIDENCIA Y SANTA CATALINA"
    df.loc[indices, "municipio_pdf"] = ["PROVIDENCIA - SP", "SAN ANDRES - SP"]
    if df["bloque"].isna().any():
        raise ValueError(f"{df['bloque'].isna().sum()} filas sin departamento")
    df["foco_rabia"] = df["municipio_pdf"].str.endswith("**").astype(int)
    df["ajuste_cobertura"] = (df["municipio_pdf"].str.endswith("*") & (df["foco_rabia"] == 0)).astype(int)
    df["municipio_limpio"] = df["municipio_pdf"].map(limpiar_nombre)
    df["tipo"] = np.where(df["municipio_limpio"].map(lambda n: clave_distrito(n) is not None), "distrito", "municipio")
    df.loc[df["municipio_limpio"].map(normalizar).str.startswith("BOGOTA"), "municipio_limpio"] = "BOGOTA"
    df["tipo"] = np.where(df["municipio_limpio"] == "BOGOTA", "distrito", df["tipo"])
    df = cruzar_divipola(df, divipola, columna_nombre="municipio_limpio")
    df["pob_dane"] = df["cod_divipola"].map(cargar_pob_dane(config, anio))
    df["identidad_ok"] = (df["poblacion_perros"] + df["poblacion_gatos"]).sub(df["poblacion_perros_gatos"]).abs().le(1).astype(int)
    df["cobertura_100"] = (df["cobertura_perros_gatos"] == 100).astype(int)
    df["metodo_estimacion"] = "no_detectable"
    df["anio"], df["anio_fuente"], df["fuente"] = anio, anio, path.name
    return df, ignoradas
