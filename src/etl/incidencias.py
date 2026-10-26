import numpy as np
import pandas as pd

from src.etl.comun import cargar_config, ruta
from src.etl.extraer_minsalud import normalizar
from src.etl.panel_minsalud import ANIOS, marcas_departamento

LIMITE_SALTO = 0.5
RANGO_HAB_POR_PERRO = (1.7, 11.4)
COLUMNAS = ["cod_divipola", "anio", "regla", "valor_citado", "archivo", "pagina", "conclusion"]


def fila(cod, anio, regla, valor, archivo, pagina, conclusion):
    return {"cod_divipola": cod, "anio": anio, "regla": regla, "valor_citado": valor, "archivo": archivo,
            "pagina": pagina, "conclusion": conclusion}


def reglas_panel(panel):
    filas = []
    base = panel[panel["cod_divipola"].notna()]
    for r in base[base.duplicated(["cod_divipola", "anio"], keep=False)].itertuples():
        filas.append(fila(r.cod_divipola, r.anio, "duplicado", f"{r.poblacion_perros}", r.fuente, r.pagina,
                          "mismo municipio y año repetido; conservar una fila"))
    ordenado = base.drop_duplicates(["cod_divipola", "anio"]).sort_values(["cod_divipola", "anio"])
    previo = ordenado.groupby("cod_divipola")[["anio", "poblacion_perros"]].shift(1)
    consecutivo = (ordenado["anio"] - previo["anio"]) == 1
    cambio = ordenado["poblacion_perros"] / previo["poblacion_perros"].where(previo["poblacion_perros"] > 0) - 1
    for r in ordenado[consecutivo & (cambio.abs() > LIMITE_SALTO)].itertuples():
        c = cambio.loc[r.Index]
        filas.append(fila(r.cod_divipola, r.anio, "salto_poblacion", f"{c:+.1%}", r.fuente, r.pagina,
                          f"población de perros cambió más de ±50 % frente a {r.anio - 1}; revisar en el PDF"))
    for r in base[base["cobertura_100"] == 1].itertuples():
        filas.append(fila(r.cod_divipola, r.anio, "cobertura_100", "100", r.fuente, r.pagina,
                          "cobertura exactamente en 100 %: posible tope y no medición"))
    medido = base[(base["metodo_estimacion"] == "posible_medido") & base["hab_por_perro"].notna()]
    fuera = medido[(medido["hab_por_perro"] < RANGO_HAB_POR_PERRO[0]) | (medido["hab_por_perro"] > RANGO_HAB_POR_PERRO[1])]
    for r in fuera.itertuples():
        filas.append(fila(r.cod_divipola, r.anio, "habitantes_por_perro_fuera_de_rango", f"{r.hab_por_perro:.2f}", r.fuente, r.pagina,
                          "fuera de 1,7-11,4 habitantes por perro en un municipio posible_medido; revisar población de perros"))
    for r in base[base["marca_inconsistencia"].fillna("").str.contains("identidad_tabla")].itertuples():
        filas.append(fila(r.cod_divipola, r.anio, "identidad_tabla_no_cierra", r.marca_inconsistencia, r.fuente, r.pagina,
                          "las identidades de la tabla del PDF no cierran; el PDF es inconsistente"))
    return filas


def reglas_interim(config, divipola):
    interim = ruta(config, "interim")
    filas = []
    d19 = pd.read_parquet(interim / "minsalud_2019.parquet")
    for r in d19[(d19["dif_poblacion"] == 1)].itertuples():
        filas.append(fila(r.cod_divipola, 2019, "dif_poblacion", f"{r.pob_pdf:.0f} frente a {r.pob_dane:.0f}", r.fuente, r.pagina,
                          "población del PDF fuera de 0,8-1,25 veces la DANE (D41)"))
    codigos = divipola.assign(n=divipola["Nombre Departamento"].map(normalizar)).set_index("n")["Código Departamento"].to_dict()
    for anio in ANIOS:
        for dep, texto in marcas_departamento(interim, anio).items():
            filas.append(fila(f"{codigos.get(normalizar(dep), '00')}000", anio, "total_departamental_no_cierra", texto,
                              f"minsalud_vacunacion_{anio}.pdf", np.nan, f"la suma municipal de {dep} difiere del total impreso en más de 0,5 %"))
    return filas


def reglas_ins(config):
    procesado = ruta(config, "processed")
    filas = []
    for anio in (2024, 2025):
        v = pd.read_csv(procesado / f"ins_validacion_{anio}.csv")
        if anio == 2024:
            for r in v[v["dif"].fillna(0) != 0].itertuples():
                filas.append(fila("00000", 2024, "total_ins_no_cierra", f"{r.entidad}: suma {r.suma_municipal:.0f} frente a {r.casos_pdf:.0f}",
                                  r.archivo, 33, "la suma municipal no coincide con la tabla departamental del INS"))
        else:
            for r in v[v["dif_relativa"].abs() > 0.005].itertuples():
                filas.append(fila("00000", 2025, "total_ins_no_cierra", f"{r.entidad}: incidencia {r.incidencia_calculada:.1f} frente a {r.incidencia_pdf:.1f}",
                                  r.archivo, r.pagina, "la incidencia recalculada no coincide con el Anexo 2; municipios no listados"))
    ins = pd.read_parquet(ruta(config, "interim") / "ins_agresiones_municipal.parquet")
    for r in ins[ins["cod_divipola"].isna()].drop_duplicates(["municipio_pdf", "archivo"]).itertuples():
        filas.append(fila("", r.anio, "municipio_sin_codigo", r.municipio_pdf, r.archivo, r.pagina, "sin cruce con DIVIPOLA; fuera del panel"))
    return filas


def main():
    config = cargar_config()
    divipola = pd.read_csv(ruta(config, "raw") / "dane" / "dane_divipola.csv", dtype=str)
    panel = pd.read_parquet(ruta(config, "processed") / "panel_minsalud_municipal.parquet")
    filas = reglas_panel(panel) + reglas_interim(config, divipola) + reglas_ins(config)
    out = pd.DataFrame(filas, columns=COLUMNAS)
    out.to_csv(ruta(config, "processed") / "incidencias.csv", index=False, encoding="utf-8-sig")
    print(len(out), out.groupby(["regla"]).size().to_dict())
    print(out.groupby(["regla", "anio"]).size().unstack(fill_value=0).to_string())


if __name__ == "__main__":
    main()
