import numpy as np
import pandas as pd
from openpyxl import load_workbook

from src.etl.comun import cargar_config, ruta
from src.etl.extraer_minsalud import cargar_pob_dane, clave_distrito, cruzar_divipola, normalizar

ANIO_BASE_PRECIOS = 2025
ALIAS_DEPARTAMENTO = {"DISTRITO CAPITAL DE BOGOTA": "BOGOTA D C", "BOGOTA D C": "BOGOTA D C", "BOGOTA": "BOGOTA D C",
                      "SAN ANDRES PROVIDENCIA Y SANTA CATALINA": "ARCHIPIELAGO DE SAN ANDRES PROVIDENCIA Y SANTA CATALINA"}
ALIAS_MUNICIPIO = {"CUCUTA": "San José de Cúcuta", "EL LIBANO": "Líbano", "EL ESPINAL": "Espinal", "EL GUAMO": "Guamo",
                   "VILLA GARZON VILLA AMAZONICA": "Villa Garzón", "SAN MIGUEL DE MOCOA": "Mocoa",
                   "VALLE DEL GUAMUEZ LA HORMIGA": "Valle del Guamuez", "SANTA ROSA DE LIMA": "Santa Rosa",
                   "SAN MIGUEL LA DORADA": "San Miguel", "DISTRITO CAPITAL": "Bogotá"}
COLUMNAS_SECOP1 = {"municipio": "municipio_entidad", "departamento": "departamento_entidad", "valor": "cuantia_contrato",
                   "fecha": "fecha_de_firma_del_contrato", "modalidad": "modalidad_de_contratacion",
                   "tipo_contrato": "tipo_de_contrato", "orden": "orden_entidad", "sector": "nivel_entidad",
                   "entidad": "nombre_entidad", "nit_entidad": "nit_de_la_entidad"}
COLUMNAS_SECOP2 = {"municipio": "ciudad", "departamento": "departamento", "valor": "valor_del_contrato",
                   "fecha": "fecha_de_firma", "modalidad": "modalidad_de_contratacion", "tipo_contrato": "tipo_de_contrato",
                   "orden": "orden", "sector": "sector", "entidad": "nombre_entidad", "nit_entidad": "nit_entidad"}


def cargar_ipc(config):
    ws = load_workbook(ruta(config, "raw") / "dane" / "dane_ipc_indices.xlsx", read_only=True)["IndicesIPC"]
    filas = list(ws.iter_rows(values_only=True))
    anios = [a for a in filas[8][1:] if isinstance(a, (int, float))]
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    indice = {}
    for fila in filas[9:21]:
        mes = meses.index(str(fila[0]).strip()) + 1
        for a, v in zip(anios, fila[1:]):
            if isinstance(v, (int, float)):
                indice[(int(a), mes)] = float(v)
    base = np.mean([indice[(ANIO_BASE_PRECIOS, m)] for m in range(1, 13)])
    return indice, base


def universo_atributos(config):
    interim = ruta(config, "interim")
    partes = []
    for fuente, cols in (("secop1", COLUMNAS_SECOP1), ("secop2", COLUMNAS_SECOP2)):
        d = pd.read_parquet(interim / f"{fuente}_senales.parquet")
        proveedor = (d["identificacion_del_contratista"].where(d["identificacion_del_contratista"].notna() & (d["identificacion_del_contratista"] != ""),
                                                              d["nom_razon_social_contratista"]) if fuente == "secop1" else d["codigo_proveedor"])
        pn = (d["identificacion_del_contratista"].isna() | (d["identificacion_del_contratista"] == "")) if fuente == "secop1" else d["proveedor_persona_natural"]
        partes.append(pd.DataFrame({
            "fuente": fuente, "llave": d["llave"], "fecha_firma": pd.to_datetime(d[cols["fecha"]]),
            "departamento_entidad": d[cols["departamento"]], "municipio_entidad": d[cols["municipio"]],
            "orden": d[cols["orden"]], "sector": d[cols["sector"]], "entidad": d[cols["entidad"]],
            "modalidad": d[cols["modalidad"]], "tipo_contrato": d[cols["tipo_contrato"]],
            "proveedor_id": proveedor.astype(str), "proveedor_persona_natural": pn.astype(bool),
            "objeto": d["objeto"], "posible_disposicion_animales": d["posible_disposicion_animales"],
            "estrato": d["estrato"]}))
    return pd.concat(partes, ignore_index=True)


def cruzar_ubicacion(atributos, divipola):
    pares = atributos[["departamento_entidad", "municipio_entidad"]].fillna("").drop_duplicates().reset_index(drop=True)
    deps = {normalizar(x): x for x in divipola["Nombre Departamento"].unique()}
    pares["bloque"] = pares["departamento_entidad"].map(lambda x: deps.get(ALIAS_DEPARTAMENTO.get(normalizar(x), normalizar(x))))
    limpio = pares["municipio_entidad"].str.replace(r"(?i)^cartagena de indias$", "Cartagena", regex=True).str.replace(
        r"(?i)^bogot[aá],? ?d\.?c\.?$", "Bogotá", regex=True).str.replace(r"(?i)^distrito (capital )?de ", "", regex=True).str.strip()
    pares["municipio_limpio"] = [ALIAS_MUNICIPIO.get(normalizar(n), n) for n in limpio]
    limpio = pares["municipio_limpio"]
    pares["tipo"] = np.where(limpio.map(lambda n: clave_distrito(n) is not None) | limpio.map(lambda n: normalizar(n) == "BOGOTA"),
                             "distrito", "municipio")
    pares["clave"] = pares["municipio_limpio"].map(normalizar)
    unicos = pares[pares["bloque"].notna()].drop_duplicates(["bloque", "clave", "tipo"]).reset_index(drop=True)
    cruzado = cruzar_divipola(unicos, divipola, columna_nombre="municipio_limpio")[
        ["bloque", "clave", "tipo", "cod_divipola", "metodo_cruce", "puntaje_cruce"]]
    salida = pares.merge(cruzado, on=["bloque", "clave", "tipo"], how="left")
    salida["metodo_cruce"] = salida["metodo_cruce"].fillna("sin_departamento")
    return salida


def codigo_departamento(divipola):
    return {normalizar(n): c for n, c in divipola[["Nombre Departamento", "Código Departamento"]].drop_duplicates().itertuples(index=False)}


def construir_universo(config, columna_clase="pred_tfidf"):
    procesado = ruta(config, "processed")
    divipola = pd.read_csv(ruta(config, "raw") / "dane" / "dane_divipola.csv", dtype=str)
    clasif = pd.read_parquet(procesado / "clasificacion_universo.parquet")
    clasif["clase_final"] = clasif[columna_clase]
    atributos = universo_atributos(config)
    cruce = cruzar_ubicacion(atributos, divipola)
    atributos = atributos.assign(departamento_entidad=atributos["departamento_entidad"].fillna(""),
                                 municipio_entidad=atributos["municipio_entidad"].fillna(""))
    atributos = atributos.merge(cruce[["departamento_entidad", "municipio_entidad", "bloque", "cod_divipola", "metodo_cruce", "puntaje_cruce"]],
                                on=["departamento_entidad", "municipio_entidad"], how="left")
    d = clasif.merge(atributos, on=["fuente", "llave"], how="left", validate="one_to_one")
    assert len(d) == len(clasif) and d["fecha_firma"].notna().all()
    indice, base = cargar_ipc(config)
    ipc = [indice.get((f.year, f.month)) for f in d["fecha_firma"]]
    d["ipc_mes"] = ipc
    d["valor_constante_2025"] = d["valor"] * base / d["ipc_mes"]
    d["mes"] = d["fecha_firma"].dt.month
    codigos = codigo_departamento(divipola)
    d["cod_dpto"] = d["bloque"].map(lambda b: codigos.get(normalizar(b)) if isinstance(b, str) else None)
    d["cod_dpto"] = d["cod_dpto"].fillna(d["cod_divipola"].str[:2])
    return d
