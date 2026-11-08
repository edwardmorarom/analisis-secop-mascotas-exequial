"""Defunciones no fetales por departamento de residencia y grupo de causa (EEVV, DANE), 2020 a 2025 (D107): Cuadro 5 (lista 6/67) y U07 del Cuadro 16."""
import re

import pandas as pd
from unidecode import unidecode

from src.etl.comun import cargar_config, ruta
from src.etl.eevv_lectura import libro

ANIOS = range(2020, 2026)
ANIOS_COVID = (2020, 2021, 2022)
GRUPOS = {
    "agresiones_homicidios": range(512, 513),
    "accidentes_transporte": range(501, 502),
    "otros_accidentes_causas_externas": [*range(502, 512), 513, 514],
    "circulatorio": range(301, 310),
    "neoplasias": range(201, 216),
}
GRUPO_DE_CODIGO = {c: g for g, cs in GRUPOS.items() for c in cs}
CODIGO_INFECCIOSAS_RESTO = 109
ORDEN_GRUPOS = ["agresiones_homicidios", "accidentes_transporte", "otros_accidentes_causas_externas", "covid19", "circulatorio", "neoplasias", "demas_causas"]


def grupo_de(codigo):
    return GRUPO_DE_CODIGO.get(codigo, "demas_causas")


def codigo_dpto(codigo_col0, etiqueta):
    m = re.match(r"\s*(\d{1,2})\s", str(etiqueta))
    return f"{int(m.group(1)):02d}" if m else f"{int(codigo_col0):02d}"


def bloques_cuadro5(d):
    """Genera (cod_dpto, codigo_causa o 'TOTAL', defunciones) solo de los bloques departamentales."""
    actual, modo = None, None
    for c0, c2, c3, c4, c5 in d[[0, 1 + 1, 3, 4, 5]].itertuples(index=False):
        if isinstance(c2, str) and c2.strip().startswith("Fuente"):
            break
        if isinstance(c2, str) and pd.notna(c0):
            actual, modo = codigo_dpto(c0, c2), "dpto"
            nombre = c2
        elif pd.isna(c2) and isinstance(c3, str) and not c3.strip().lower().startswith("total dpto") and pd.notna(c0):
            modo = "municipio"
        if modo != "dpto" or actual is None or not isinstance(c4, str) or pd.isna(c5):
            continue
        causa = c4.strip()
        if causa.upper().startswith("TOTAL"):
            yield actual, "TOTAL", int(c5), nombre
        else:
            m = re.match(r"(\d{3})\b", causa)
            if m:
                yield actual, int(m.group(1)), int(c5), nombre


def cuadro5(anio, x):
    d = pd.read_excel(x, sheet_name="Cuadro5", header=None, usecols=[0, 1, 2, 3, 4, 5]).iloc[9:]
    d.columns = [0, 1, 2, 3, 4, 5]
    filas = pd.DataFrame(list(bloques_cuadro5(d)), columns=["cod_dpto", "causa", "defunciones", "nombre"])
    filas.insert(0, "anio", anio)
    return filas


def u07_cuadro16(anio, x):
    d = pd.read_excel(x, sheet_name="Cuadro16", header=None, usecols=[0, 1, 2, 3]).iloc[9:]
    d.columns = ["c0", "dep", "causa", "n"]
    d["dep"] = d["dep"].ffill()
    d["c0"] = d["c0"].ffill()
    u = d[d["causa"].astype(str).str.upper().str.startswith("U07")]
    return pd.DataFrame({"anio": anio, "cod_dpto": [codigo_dpto(c, e) for c, e in zip(u["c0"], u["dep"])], "u07": u["n"].astype(int).values})


def total_indice(x):
    d = pd.read_excel(x, sheet_name="Indice", header=None)
    for v in d.values.ravel():
        m = re.search(r"Total Nacional:\s*([\d.]+)", v) if isinstance(v, str) else None
        if m:
            return int(m.group(1).replace(".", ""))


def construir(config=None):
    config = config or cargar_config()
    largos, verificacion, u07 = [], [], []
    for anio in ANIOS:
        x = libro(anio, config)
        c5 = cuadro5(anio, x)
        nacional = c5[c5["cod_dpto"] == "03"]
        dptos = c5[c5["cod_dpto"] != "03"]
        totales = dptos[dptos["causa"] == "TOTAL"].set_index("cod_dpto")["defunciones"]
        grupos = dptos[dptos["causa"] != "TOTAL"].assign(grupo_causa=lambda t: t["causa"].map(grupo_de)).groupby(["anio", "cod_dpto", "grupo_causa"], as_index=False)["defunciones"].sum()
        c = pd.DataFrame()
        if anio in ANIOS_COVID:
            c = u07_cuadro16(anio, x)
            c = c[c["cod_dpto"] != "03"]
            resto = dptos[dptos["causa"] == CODIGO_INFECCIOSAS_RESTO].set_index("cod_dpto")["defunciones"]
            for _, f in c.iterrows():
                m = (grupos["cod_dpto"] == f["cod_dpto"]) & (grupos["grupo_causa"] == "demas_causas")
                grupos.loc[m, "defunciones"] -= f["u07"]
            grupos = pd.concat([grupos, pd.DataFrame({"anio": anio, "cod_dpto": c["cod_dpto"], "grupo_causa": "covid19", "defunciones": c["u07"]})], ignore_index=True)
            u07.append(c.assign(infecciosas_resto=c["cod_dpto"].map(resto)))
        grupos["fuente"] = "eevv_cuadro5"
        grupos.loc[grupos["grupo_causa"] == "covid19", "fuente"] = "eevv_cuadro16"
        largos.append(grupos)
        suma_dptos = int(totales.sum())
        n_nacional = int(nacional.loc[nacional["causa"] == "TOTAL", "defunciones"].iloc[0])
        verificacion.append({"anio": anio, "total_indice_dane": total_indice(x), "total_nacional_cuadro5": n_nacional, "suma_departamentos_mas_no_asignados": suma_dptos,
                             "suma_grupos": int(grupos.loc[grupos["grupo_causa"] != "covid19", "defunciones"].sum() + grupos.loc[grupos["grupo_causa"] == "covid19", "defunciones"].sum()),
                             "covid_u07_suma_departamentos": int(c["u07"].sum()) if len(c) else None})
    largo = pd.concat(largos, ignore_index=True)
    return largo[["anio", "cod_dpto", "grupo_causa", "defunciones", "fuente"]].sort_values(["anio", "cod_dpto", "grupo_causa"]).reset_index(drop=True), pd.DataFrame(verificacion), pd.concat(u07, ignore_index=True)


def nombres_divipola(config=None):
    config = config or cargar_config()
    d = pd.read_csv(ruta(config, "raw") / "dane" / "dane_divipola.csv", dtype=str)
    return d.drop_duplicates("Código Departamento").set_index("Código Departamento")["Nombre Departamento"]


def main():
    config = cargar_config()
    largo, verificacion, u07 = construir(config)
    interim = ruta(config, "interim") / "eevv_defunciones.parquet"
    largo.to_parquet(interim, index=False)
    salida = ruta(config, "processed") / "resultados_secop" / "causas"
    salida.mkdir(parents=True, exist_ok=True)
    verificacion.to_csv(salida / "verificacion_totales.csv", index=False)
    u07.to_csv(salida / "covid_u07_cuadro16.csv", index=False)
    print(interim, len(largo))
    print(verificacion.to_string(index=False))


if __name__ == "__main__":
    main()
