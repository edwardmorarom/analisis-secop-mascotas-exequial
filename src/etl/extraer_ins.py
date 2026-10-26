import re

import numpy as np
import pandas as pd
import pdfplumber

from src.etl.comun import cargar_config, ruta
from src.etl.extraer_minsalud import (DISTRITOS, EQUIVALENCIAS_DEPARTAMENTO, EQUIVALENCIAS_MUNICIPIO, cargar_pob_dane,
                                      clave_distrito, cruzar_divipola, normalizar)

NUMERO = re.compile(r"^\d[\d.,]*$")
ENCABEZADO = re.compile(r"Departamento Municipio|Casos Poblaci|^2022 2023 2024|^Fuente:|Anexo|rabia por|Municipio ET|"
                        r"^Casos$|^Poblaci|^DANE|^\d{4}$|^P.gina \d+ de|^- \d+ -$|^Incidencia")
EQUIVALENCIAS_DEPARTAMENTO_INS = {"VALLEDEL CAUCA": "VALLE DEL CAUCA", "BOGOTA": "BOGOTA", "BOGOTA D C": "BOGOTA",
                                  "SAN ANDRES": "SAN ANDRES", "SAN ANDRES Y PROVIDENCIA": "SAN ANDRES"}
DISTRITOS_ET = {"BARRANQUILLA", "BOGOTA", "BUENAVENTURA", "CALI", "CARTAGENA", "SANTA MARTA"}


def numero(texto):
    t = texto.strip()
    return float(t.replace(".", "").replace(",", ".")) if "," in t else float(t.replace(".", ""))


def cola_numerica(palabras):
    n = 0
    while n < len(palabras) and NUMERO.match(palabras[-1 - n]):
        n += 1
    return n


def diccionario_departamentos(divipola):
    deps = {normalizar(x).replace(" ", ""): x for x in divipola["Nombre Departamento"].unique()}
    deps["VALLEDELCAUCA"] = deps["VALLEDELCAUCA"]
    deps["SANANDRES"] = deps["ARCHIPIELAGODESANANDRESPROVIDENCIAYSANTACATALINA"]
    deps["ARCHIPIELAGODESANANDRES"] = deps["SANANDRES"]
    deps["BOGOTA"] = deps.get("BOGOTADC", deps.get("BOGOTA"))
    return deps


def separar_departamento(palabras, deps, al_final=False):
    """Devuelve (departamento, resto de palabras); busca el departamento al inicio (2024) o al final (2025)."""
    ordenado = sorted(deps, key=len, reverse=True)
    n = len(palabras)
    for k in range(min(6, n), 0, -1):
        trozo = palabras[n - k:] if al_final else palabras[:k]
        clave = normalizar(" ".join(trozo)).replace(" ", "")
        if clave in deps:
            resto = palabras[:n - k] if al_final else palabras[k:]
            return deps[clave], resto
    return None, palabras


def valores_2024(v, inc):
    if len(v) == 8:
        return [v[0], v[3], v[5]], [v[1], v[4], v[6]], [v[2], np.nan, v[7]]
    if len(v) == 9:
        return [v[0], v[3], v[6]], [v[1], v[4], v[7]], [v[2], v[5], v[8]]
    return [v[0], v[2], v[4]], [v[1], v[3], v[5]], inc or [np.nan] * 3


def emitir_2024(filas, pagina, nombre_palabras, prefijo, v, inc, deps):
    dep, resto = separar_departamento(nombre_palabras, deps)
    et = " ".join(nombre_palabras[:len(nombre_palabras) - len(resto)]) if dep else None
    if dep is None and prefijo:
        combinado = " ".join(prefijo + nombre_palabras).split()
        dep2, resto2 = separar_departamento(combinado, deps)
        if dep2:
            dep, resto, et, prefijo = dep2, resto2, " ".join(prefijo), []
    if dep is None:
        for k in (1, 2):
            if normalizar(" ".join(nombre_palabras[:k])) in DISTRITOS_ET and len(nombre_palabras) > k:
                dep, et, resto = "DISTRITO", "DISTRITO", nombre_palabras[k:]
                break
    municipio = " ".join(prefijo + resto)
    c, p, i = valores_2024(v, inc)
    for anio, cc, pp, ii in zip((2022, 2023, 2024), c, p, i):
        filas.append({"pagina": pagina, "departamento_pdf": et, "bloque": dep, "municipio_pdf": municipio, "anio": anio,
                      "casos": cc, "poblacion": pp, "incidencia_pdf": ii})


def leer_2024(path, deps, paginas=range(31, 55)):
    filas, departamental = [], []
    prefijo, incidencias, pendiente, municipal = [], None, None, False
    with pdfplumber.open(path) as pdf:
        for pagina in paginas:
            for linea in (pdf.pages[pagina - 1].extract_text() or "").split("\n"):
                linea = linea.strip()
                palabras = linea.split()
                n = cola_numerica(palabras)
                if linea.startswith("Anexo 2"):
                    municipal = True
                if ENCABEZADO.search(linea) and n < 3 and not (n <= 1 and pendiente):
                    prefijo, incidencias = [], None
                    continue
                if not municipal:
                    if n in (5, 6) and n < len(palabras):
                        v = [numero(x) for x in palabras[-n:]]
                        departamental.append({"entidad_pdf": " ".join(palabras[:-n]), "casos_2024": v[0],
                                              "poblacion_2024": v[1], "incidencia_2024": v[2]})
                    continue
                if pendiente and n <= 1 and n < len(palabras):
                    v, pref, inc = pendiente
                    emitir_2024(filas, pagina, palabras[:len(palabras) - n], pref, v, inc, deps)
                    pendiente, prefijo, incidencias = None, [], None
                elif n == len(palabras) and n == 3:
                    incidencias = [numero(x) for x in palabras]
                elif n == 0:
                    prefijo.append(linea)
                elif n == len(palabras) and n in (6, 8, 9):
                    pendiente = ([numero(x) for x in palabras], list(prefijo), incidencias)
                    prefijo, incidencias = [], None
                elif n in (6, 9):
                    emitir_2024(filas, pagina, palabras[:-n], prefijo, [numero(x) for x in palabras[-n:]], incidencias, deps)
                    prefijo, incidencias = [], None
    return pd.DataFrame(filas), pd.DataFrame(departamental)


def cruzar(df_largo, divipola):
    df_largo = df_largo.assign(bloque=df_largo["bloque"].fillna(""))
    u = df_largo.drop_duplicates(["pagina", "bloque", "municipio_pdf"])[["pagina", "bloque", "municipio_pdf"]].reset_index(drop=True)
    u["municipio_limpio"] = u["municipio_pdf"].str.replace(r"\s*\((CD|ANM)\)", "", regex=True).str.replace(
        r"(?i)^cartagena de indias$", "Cartagena", regex=True).str.replace(r"(?i)^bogot[aá],? d\.?c\.?$", "Bogotá", regex=True).str.strip()
    por_nombre = divipola.assign(n=divipola["Nombre Municipio"].map(normalizar)).groupby("n")["Nombre Departamento"].agg(["first", "nunique"])
    inferido = u["municipio_limpio"].map(lambda n: por_nombre["first"].get(normalizar(n)) if por_nombre["nunique"].get(normalizar(n)) == 1 else None)
    u["bloque_cruce"] = np.where(u["bloque"] == "", inferido, u["bloque"])
    u["tipo"] = np.where(u["bloque"] == "DISTRITO", "distrito", "municipio")
    u.loc[u["municipio_limpio"].map(lambda n: normalizar(n) == "BOGOTA"), "tipo"] = "distrito"
    base = u.assign(bloque=u["bloque_cruce"])
    cruzado = cruzar_divipola(base, divipola, columna_nombre="municipio_limpio")
    cruzado["bloque_orig"] = u["bloque"]
    salida = cruzado[["pagina", "bloque_orig", "municipio_pdf", "bloque_cruce", "cod_divipola", "metodo_cruce", "puntaje_cruce"]]
    salida = salida.rename(columns={"bloque_orig": "bloque", "bloque_cruce": "bloque_final"})
    return df_largo.merge(salida, on=["pagina", "bloque", "municipio_pdf"], how="left")


def validar_departamental(m, d, deps):
    """Suma municipal de 2024 contra la tabla departamental del Anexo 1 (casos 2024); los distritos van aparte."""
    m24 = m[m["anio"] == 2024]
    codigos_distrito = {"BARRANQUILLA": "08001", "CALI": "76001", "CARTAGENA": "13001", "BUENAVENTURA": "76109",
                        "SANTA MARTA": "47001", "BOGOTA": "11001"}
    alias = {**deps, "VALLE": deps["VALLEDELCAUCA"]}
    filas = []
    for r in d.itertuples():
        n = normalizar(r.entidad_pdf)
        if n == "NACIONAL":
            suma = m24["casos"].sum()
        elif n in codigos_distrito:
            suma = m24[m24["cod_divipola"] == codigos_distrito[n]]["casos"].sum()
        else:
            dep = alias.get(n.replace(" ", ""))
            suma = m24[(m24["bloque_final"] == dep) & ~m24["cod_divipola"].isin(codigos_distrito.values())]["casos"].sum() if dep else np.nan
        filas.append({"entidad": r.entidad_pdf, "casos_pdf": r.casos_2024, "suma_municipal": suma, "dif": suma - r.casos_2024})
    return pd.DataFrame(filas)


def leer_2025(path, deps, paginas=range(49, 81)):
    filas, prefijo = [], []
    with pdfplumber.open(path) as pdf:
        for pagina in paginas:
            prefijo = []
            for linea in (pdf.pages[pagina - 1].extract_text() or "").split("\n"):
                palabras = linea.strip().split()
                n = cola_numerica(palabras)
                if ENCABEZADO.search(linea) or "APTR" in linea:
                    prefijo = []
                    continue
                if n == 0 and palabras:
                    prefijo.append(linea.strip())
                    continue
                if n != 3 or n == len(palabras):
                    continue
                v = [numero(x) for x in palabras[-3:]]
                et, resto = separar_departamento(palabras[:-3], deps, al_final=True)
                if et is None:
                    for k in (1, 2):
                        if normalizar(" ".join(palabras[-3 - k:-3])) in DISTRITOS_ET:
                            et, resto = "DISTRITO", palabras[:-3 - k]
                            break
                filas.append({"pagina": pagina, "bloque": et, "municipio_pdf": " ".join(prefijo + resto), "anio": 2025,
                              "casos": v[0], "poblacion": v[1], "incidencia_pdf": v[2]})
                prefijo = []
    return pd.DataFrame(filas), []


def incidencia_departamental_2025(path, deps):
    """Anexo 2 (pp. 48-49): incidencia por 100.000 habitantes 2018-2025 de cada entidad territorial."""
    filas = []
    with pdfplumber.open(path) as pdf:
        for pagina in (48, 49):
            for linea in (pdf.pages[pagina - 1].extract_text() or "").split(chr(10)):
                palabras = linea.split()
                n = cola_numerica(palabras)
                if n == 8 and n < len(palabras):
                    filas.append({"entidad": " ".join(palabras[:-8]), "pagina": pagina, "incidencia_2025": numero(palabras[-1])})
    return pd.DataFrame(filas)


def validar_2025(x, inc_dep, deps):
    codigos_distrito = {"BARRANQUILLA": "08001", "CALI": "76001", "CARTAGENA": "13001", "BUENAVENTURA": "76109",
                        "SANTA MARTA": "47001", "BOGOTA": "11001"}
    alias = {**deps, "VALLE": deps["VALLEDELCAUCA"]}
    filas = []
    for r in inc_dep.itertuples():
        n = normalizar(r.entidad)
        if n in codigos_distrito:
            g = x[x["cod_divipola"] == codigos_distrito[n]]
        else:
            dep = alias.get(n.replace(" ", ""))
            g = x[(x["bloque_final"] == dep) & ~x["cod_divipola"].isin(codigos_distrito.values())] if dep else x.iloc[0:0]
        calculada = g["casos"].sum() / g["poblacion"].sum() * 1e5 if len(g) else np.nan
        filas.append({"entidad": r.entidad, "pagina": r.pagina, "incidencia_pdf": r.incidencia_2025,
                      "incidencia_calculada": calculada, "dif_relativa": calculada / r.incidencia_2025 - 1})
    return pd.DataFrame(filas)


def main():
    config = cargar_config()
    divipola = pd.read_csv(ruta(config, "raw") / "dane" / "dane_divipola.csv", dtype=str)
    deps = diccionario_departamentos(divipola)
    raw = ruta(config, "raw") / "ins"
    p24, p25 = raw / "ins_agresiones_2024.pdf", raw / "ins_agresiones_2025.pdf"
    m24, dep24 = leer_2024(p24, deps)
    m25, _ = leer_2025(p25, deps)
    x24, x25 = cruzar(m24, divipola).assign(archivo=p24.name), cruzar(m25, divipola).assign(archivo=p25.name)
    todo = pd.concat([x24, x25], ignore_index=True)
    todo["incidencia_calculada"] = todo["casos"] / todo["poblacion"].replace(0, np.nan) * 1e5
    interim = ruta(config, "interim")
    todo.to_parquet(interim / "ins_agresiones_municipal.parquet", index=False)
    v24 = validar_departamental(x24, dep24, deps).assign(archivo=p24.name, anio=2024)
    v25 = validar_2025(x25, incidencia_departamental_2025(p25, deps), deps).assign(archivo=p25.name, anio=2025)
    procesado = ruta(config, "processed")
    v24.to_csv(procesado / "ins_validacion_2024.csv", index=False, encoding="utf-8-sig")
    v25.to_csv(procesado / "ins_validacion_2025.csv", index=False, encoding="utf-8-sig")
    for nombre, x in (("2024 (2022-2024)", x24), ("2025", x25)):
        u = x.drop_duplicates(["pagina", "bloque", "municipio_pdf", "cod_divipola"])
        print(f"{nombre}: {len(u)} municipios, cruce {u['metodo_cruce'].value_counts().to_dict()}, sin código {u['cod_divipola'].isna().sum()}")
    print("totales 2022-2025 (casos):", todo.groupby("anio")["casos"].sum().to_dict())
    print("diferencias 2024 frente a tabla departamental:", v24[v24["dif"] != 0][["entidad", "dif"]].values.tolist())
    print("diferencia de incidencia 2025 mayor de 0,5 %:", v25[v25["dif_relativa"].abs() > 0.005][["entidad", "dif_relativa"]].round(3).values.tolist())


if __name__ == "__main__":
    main()
