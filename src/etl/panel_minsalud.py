import numpy as np
import pandas as pd

from src.etl.comun import cargar_config, ruta

ANIOS = (2014, 2016, 2017, 2019, 2023, 2024)
VACUNADOS_PERROS = ("vacunados_perros", "perros_vacunados")
TOLERANCIA_TOTAL_DEPARTAMENTO = 0.005
COLUMNAS = ["cod_divipola", "anio", "tipo", "municipio_pdf", "bloque", "pob_dane", "poblacion_perros", "poblacion_gatos",
            "vacunados_perros", "vacunados_perros_x1000hab", "vacunados_perros_gatos",
            "vacunados_perros_gatos_x1000hab", "hab_por_perro", "metodo_estimacion",
            "densidad_analizable", "cobertura_100", "ajuste_cobertura", "marca_inconsistencia",
            "fuente", "anio_fuente", "pagina"]


def marcas_departamento(interim, anio):
    ruta_dep = interim / f"minsalud_{anio}_departamentos.parquet"
    if not ruta_dep.exists():
        return {}
    dep = pd.read_parquet(ruta_dep)
    marcas = {}
    for fila in dep.itertuples(index=False):
        fila = fila._asdict()
        malas = [c[: -len("_dif")] for c in fila if c.endswith("_dif")
                 and fila[c[: -len("_dif")] + "_pdf"] and abs(fila[c]) / fila[c[: -len("_dif")] + "_pdf"] > TOLERANCIA_TOTAL_DEPARTAMENTO]
        if malas:
            marcas[fila["departamento"]] = "total_departamental_no_cierra:" + ",".join(malas)
    return marcas


def armonizar(df, marcas):
    df = df.copy()
    vac = next((c for c in VACUNADOS_PERROS if c in df.columns), None)
    df["vacunados_perros"] = df[vac] if vac else np.nan
    for c in ("ajuste_cobertura", "identidad_ok", "pagina"):
        if c not in df.columns:
            df[c] = np.nan
    if "vacunados_perros_gatos" not in df.columns:
        df["vacunados_perros_gatos"] = np.nan
    df["vacunados_perros_x1000hab"] = df["vacunados_perros"] / df["pob_dane"] * 1000
    df["vacunados_perros_gatos_x1000hab"] = df["vacunados_perros_gatos"] / df["pob_dane"] * 1000
    df["densidad_analizable"] = ((df["anio"] == 2019) & (df["metodo_estimacion"] == "posible_medido")).astype(int)
    avisos = []
    for r in df.itertuples():
        a = []
        if r.identidad_ok == 0:
            a.append("identidad_tabla_no_cierra")
        if r.ajuste_cobertura == 1:
            a.append("ajuste_cobertura_asterisco")
        if r.tipo == "municipio" and r.bloque in marcas:
            a.append(marcas[r.bloque])
        avisos.append(";".join(a) or None)
    df["marca_inconsistencia"] = avisos
    return df


def main():
    config = cargar_config()
    interim, salida = ruta(config, "interim"), ruta(config, "processed")
    salida.mkdir(parents=True, exist_ok=True)
    partes = []
    for anio in ANIOS:
        p = interim / f"minsalud_{anio}.parquet"
        if p.exists():
            partes.append(armonizar(pd.read_parquet(p), marcas_departamento(interim, anio)))
    todo = pd.concat(partes, ignore_index=True)
    for c in COLUMNAS:
        if c not in todo.columns:
            todo[c] = np.nan
    unidad = todo["tipo"].isin(["municipio", "distrito"])
    panel = todo.loc[unidad, COLUMNAS]
    con_cod = panel.dropna(subset=["cod_divipola"])
    assert not con_cod.duplicated(["cod_divipola", "anio"]).any(), "llave cod_divipola + anio no única"
    panel.to_parquet(salida / "panel_minsalud_municipal.parquet", index=False)
    todo.loc[todo["tipo"] == "localidad", [c for c in COLUMNAS if c != "cod_divipola"]].assign(
        cod_divipola_ciudad="11001").to_parquet(salida / "minsalud_localidades_bogota.parquet", index=False)
    print(panel.groupby("anio").agg(unidades=("tipo", "size"), con_cod=("cod_divipola", "count"),
                                    con_indicador=("vacunados_perros_x1000hab", "count"),
                                    marcadas=("marca_inconsistencia", "count"),
                                    densidad=("densidad_analizable", "sum")).to_string())


if __name__ == "__main__":
    main()
