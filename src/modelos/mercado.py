import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from src.etl.comun import RAIZ, cargar_config, ruta
from src.modelos.mercado_base import construir_universo

CARPETA_RESULTADOS = "resultados_secop"


def excel_cruces(d, divipola, destino, n=20, semilla=2026):
    aprox = d[d["metodo_cruce"] == "aproximado"].groupby(["departamento_entidad", "municipio_entidad", "cod_divipola", "puntaje_cruce"]).size()
    aprox = aprox.rename("contratos").reset_index()
    nombres = divipola.set_index("Código Municipio")["Nombre Municipio"]
    aprox["municipio_divipola"] = aprox["cod_divipola"].map(nombres)
    muestra = aprox.sample(min(n, len(aprox)), random_state=semilla).sort_values("contratos", ascending=False)
    wb = Workbook()
    ws = wb.active
    ws.title = "Cruces"
    ws.append(["departamento_entidad", "municipio_entidad", "cod_divipola", "municipio_divipola", "puntaje", "contratos", "correcto", "nota"])
    for c in ws[1]:
        c.font = Font(bold=True)
    for r in muestra.itertuples():
        ws.append([r.departamento_entidad, r.municipio_entidad, r.cod_divipola, r.municipio_divipola, round(r.puntaje_cruce, 1), r.contratos, None, None])
    dv = DataValidation(type="list", formula1='"sí,no"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"G2:G{ws.max_row}")
    for letra, ancho in zip("ABCDEFGH", (28, 30, 12, 30, 9, 10, 10, 40)):
        ws.column_dimensions[letra].width = ancho
    for fila in range(2, ws.max_row + 1):
        ws.cell(fila, 7).fill = PatternFill("solid", fgColor="FFF2CC")
    destino.parent.mkdir(parents=True, exist_ok=True)
    wb.save(destino)
    return len(aprox), len(muestra)


def main():
    config = cargar_config()
    divipola = pd.read_csv(ruta(config, "raw") / "dane" / "dane_divipola.csv", dtype=str)
    salida = ruta(config, "processed") / CARPETA_RESULTADOS
    salida.mkdir(parents=True, exist_ok=True)
    d = construir_universo(config)
    d.to_parquet(salida / "universo_mercado.parquet", index=False)
    con_codigo = d["cod_divipola"].notna()
    resumen = pd.DataFrame({
        "universo": [len(d), int(con_codigo.sum()), int(d["cod_dpto"].notna().sum())],
        "funerario_tfidf": [int((d["clase_final"] == "funerario").sum()), int((con_codigo & (d["clase_final"] == "funerario")).sum()),
                            int(((d["clase_final"] == "funerario") & d["cod_dpto"].notna()).sum())]},
        index=["contratos", "con_municipio_DIVIPOLA", "con_departamento"])
    resumen["tasa_universo"] = resumen["universo"] / len(d)
    resumen.to_csv(salida / "tasa_cruce_ubicacion.csv", encoding="utf-8-sig")
    print(resumen.round(4).to_string())
    print(d["metodo_cruce"].value_counts().to_dict())
    print("excel de cruces aproximados:", excel_cruces(d, divipola, RAIZ / "docs" / "revision_f4" / "cruces_secop.xlsx"))


if __name__ == "__main__":
    main()
