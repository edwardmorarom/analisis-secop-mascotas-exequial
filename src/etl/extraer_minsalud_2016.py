import re

import numpy as np
import pandas as pd
import pdfplumber
from rapidfuzz import fuzz

from src.etl.comun import cargar_config, ruta
from src.etl.extraer_minsalud import (DISTRITOS, EQUIVALENCIAS_DEPARTAMENTO, EQUIVALENCIAS_MUNICIPIO, cargar_pob_dane,
                                      clave_distrito, cruzar_divipola, normalizar)

NUMERO = re.compile(r"^(\d[\d.]*|nan)$")
SIN_DATO = re.compile(r"^(nr|n\.r\.?)$", re.I)
X_NOMBRE = 100
COLUMNAS = ["poblacion_perros", "poblacion_gatos", "poblacion_perros_gatos", "vacunados_perros_gatos",
            "cobertura_perros_gatos", "stock_vacuna"]
ORDEN_BLOQUES = ["AMAZONAS", "ANTIOQUIA", "ARAUCA", "ATLANTICO", "BARRANQUILLA", "BOGOTA", "BOLIVAR", "BOYACA",
                 "BUENAVENTURA", "CALDAS", "CAQUETA", "CARTAGENA", "CASANARE", "CAUCA", "CESAR", "CHOCO", "CORDOBA",
                 "CUNDINAMARCA", "GUAINIA", "GUAVIARE", "HUILA", "LA GUAJIRA", "MAGDALENA", "META", "NARINO",
                 "NORTE DE SANTANDER", "PUTUMAYO", "QUINDIO", "RISARALDA", "SAN ANDRES", "SANTA MARTA", "SANTANDER",
                 "SUCRE", "TOLIMA", "VALLE DEL CAUCA", "VAUPES", "VICHADA"]
BLOQUES_DISTRITO = {"BARRANQUILLA", "BOGOTA", "BUENAVENTURA", "CARTAGENA", "SANTA MARTA"}


def entero(texto):
    if texto == "nan":
        return np.nan
    return float(texto.replace(".", ""))


def texto_derecha(chars):
    out, previo = "", None
    for c in sorted((c for c in chars if c["x0"] >= X_NOMBRE), key=lambda c: c["x0"]):
        if c["text"].strip() == "":
            continue
        if previo is not None and c["x0"] - previo["x1"] > 1.5:
            out += " "
        out += c["text"]
        previo = c
    return out


def leer_lineas(path):
    filas, ignoradas, pais = [], [], None
    with pdfplumber.open(path) as pdf:
        for i, pg in enumerate(pdf.pages, 1):
            for linea in pg.extract_text_lines():
                palabras = ["nan" if SIN_DATO.match(p) else p for p in texto_derecha(linea["chars"]).split()]
                n = 0
                while n < len(palabras) and NUMERO.match(palabras[-1 - n]):
                    n += 1
                if not 5 <= n <= 6 or n == len(palabras):
                    ignoradas.append((i, " ".join(palabras)))
                    continue
                valores = [entero(x) for x in palabras[-n:]] + [np.nan] * (6 - n)
                nombre = " ".join(palabras[:-n])
                fila = {"pagina": i, "municipio_pdf": nombre, **dict(zip(COLUMNAS, valores))}
                if re.match(r"(?i)^(to)?tal pa", nombre):
                    pais = fila
                else:
                    filas.append(fila)
    return pd.DataFrame(filas), pais, ignoradas


def marcar_localidades(df, localidades):
    """Las 20 localidades de Bogotá van seguidas, sin fila de la ciudad; la fila de Bogotá se construye sumándolas."""
    df = df.copy()
    df["tipo"] = "municipio"
    clave = set(localidades.map(normalizar))
    es = df["municipio_pdf"].map(lambda n: normalizar(n) in clave)
    inicio = df.index[df["municipio_pdf"].map(lambda n: normalizar(n) == "USAQUEN")]
    assert len(inicio) == 1, "se esperaba Usaquén una vez"
    indices = df.index[inicio[0]:inicio[0] + 20]
    assert es[indices].all(), "las 20 filas siguientes a Usaquén no son todas localidades"
    df.loc[indices, "tipo"] = "localidad"
    suma = df.loc[indices, COLUMNAS[:4]].sum()
    fila = {"pagina": int(df.loc[indices[0], "pagina"]), "municipio_pdf": "BOGOTA", "tipo": "distrito",
            "fila_derivada": 1, **suma.to_dict(), "cobertura_perros_gatos": np.nan, "stock_vacuna": np.nan}
    df["fila_derivada"] = 0
    df = pd.concat([df.loc[:indices[0] - 1], pd.DataFrame([fila]), df.loc[indices[0]:]], ignore_index=True)
    return df


def nombres_por_bloque(divipola):
    deps = {normalizar(x): x for x in divipola["Nombre Departamento"].unique()}
    for k, v in EQUIVALENCIAS_DEPARTAMENTO.items():
        deps[k] = deps[normalizar(v)]
    nombres = {}
    for bloque in ORDEN_BLOQUES:
        if bloque in BLOQUES_DISTRITO:
            nombres[bloque] = {bloque}
            continue
        g = divipola[divipola["Nombre Departamento"] == deps[bloque]]
        nombres[bloque] = set(g["Nombre Municipio"].map(normalizar))
        codigo = g["Código Departamento"].iloc[0]
        nombres[bloque] |= {alias for (dep, alias) in EQUIVALENCIAS_MUNICIPIO if dep == codigo}
        if bloque == "VALLE DEL CAUCA":
            nombres[bloque].add("CALI")
    return nombres


def coincide(nombre, candidatos):
    n = normalizar(nombre)
    if n in candidatos:
        return True
    palabras = set(n.split())
    return any(fuzz.ratio(n, c) >= 90 or palabras <= set(c.split()) for c in candidatos)


def asignar_por_orden(df, divipola):
    """Segmenta las filas, en orden, en los bloques departamentales alfabéticos maximizando los nombres que
    coinciden con el departamento asignado (programación dinámica)."""
    nombres = nombres_por_bloque(divipola)
    n, b = len(df), len(ORDEN_BLOQUES)
    ok = np.zeros((b, n + 1), dtype=int)
    for j, bloque in enumerate(ORDEN_BLOQUES):
        ok[j, 1:] = np.cumsum([coincide(x, nombres[bloque]) for x in df["municipio_pdf"]])
    menos = -10 ** 9
    mejor = np.full((b + 1, n + 1), menos)
    mejor[0, 0] = 0
    corte = np.zeros((b + 1, n + 1), dtype=int)
    for j in range(1, b + 1):
        for fin in range(j, n + 1):
            candidatos = mejor[j - 1, :fin] + ok[j - 1, fin] - ok[j - 1, :fin]
            inicio = int(np.argmax(candidatos))
            mejor[j, fin], corte[j, fin] = candidatos[inicio], inicio
    fin, bloques = n, [None] * n
    for j in range(b, 0, -1):
        inicio = corte[j, fin]
        for k in range(inicio, fin):
            bloques[k] = ORDEN_BLOQUES[j - 1]
        fin = inicio
    out = df.copy()
    out["bloque_orden"] = bloques
    out["nombre_coincide"] = [coincide(x, nombres[bl]) for x, bl in zip(out["municipio_pdf"], bloques)]
    return out


def procesar(config, divipola, anio=2016):
    path = ruta(config, "raw") / "minsalud" / f"minsalud_vacunacion_{anio}.pdf"
    df, pais, ignoradas = leer_lineas(path)
    localidades = pd.read_parquet(ruta(config, "interim") / "minsalud_2019.parquet").query("tipo == 'localidad'")["municipio_pdf"]
    df = marcar_localidades(df, localidades)
    es_mun = df["tipo"] != "localidad"
    asignado = asignar_por_orden(df[es_mun], divipola)
    df["bloque_orden"] = asignado["bloque_orden"]
    df["nombre_coincide"] = asignado["nombre_coincide"]
    deps = {normalizar(x): x for x in divipola["Nombre Departamento"].unique()}
    for k, v in EQUIVALENCIAS_DEPARTAMENTO.items():
        deps[k] = deps[normalizar(v)]
    df["bloque"] = df["bloque_orden"].map(lambda b: "DISTRITO" if b in BLOQUES_DISTRITO else deps.get(b))
    df.loc[df["tipo"] == "localidad", "bloque"] = "DISTRITO"
    df["municipio_limpio"] = df["municipio_pdf"]
    df.loc[df["tipo"] == "distrito", "municipio_limpio"] = "BOGOTA"
    clave = df["municipio_limpio"].map(clave_distrito)
    df.loc[clave.notna() & (df["tipo"] == "municipio") & ((df["bloque"] == "DISTRITO") | (clave == "CALI")), "tipo"] = "distrito"
    df = cruzar_divipola(df, divipola, columna_nombre="municipio_limpio")
    es_muni = df["tipo"].isin(["municipio", "distrito"])
    df["pob_dane"] = np.where(es_muni, df["cod_divipola"].map(cargar_pob_dane(config, anio)), np.nan)
    df["identidad_ok"] = (df["poblacion_perros"] + df["poblacion_gatos"]).sub(df["poblacion_perros_gatos"]).abs().le(1).astype(int)
    df["cobertura_100"] = np.where(es_muni, (df["cobertura_perros_gatos"] == 100).astype(int), np.nan)
    df["metodo_estimacion"] = np.where(es_muni, "no_detectable", None)
    df["anio"], df["anio_fuente"], df["fuente"] = anio, anio, path.name
    return df, pais, ignoradas


def totales_pais(df, pais):
    base = df[df["tipo"].isin(["municipio", "distrito"])]
    return {c: (float(base[c].sum()), float(pais[c]), float(base[c].sum() - pais[c])) for c in COLUMNAS[:4]}
