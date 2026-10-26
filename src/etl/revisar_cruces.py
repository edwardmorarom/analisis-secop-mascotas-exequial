import argparse

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from src.etl.comun import RAIZ, cargar_config, ruta


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--anio", type=int, default=2019)
    p.add_argument("--n", type=int, default=20)
    a = p.parse_args()
    config = cargar_config()
    df = pd.read_parquet(ruta(config, "interim") / f"minsalud_{a.anio}.parquet")
    divipola = pd.read_csv(ruta(config, "raw") / "dane" / "dane_divipola.csv", dtype=str)
    nombres = divipola.set_index("Código Municipio")["Nombre Municipio"]
    aprox = df[(df["tipo"] == "municipio") & (df["metodo_cruce"] == "aproximado")]
    muestra = aprox.sample(n=a.n, random_state=config["seed"]).sort_values("pagina")
    tabla = pd.DataFrame({
        "n": range(1, a.n + 1), "pagina": muestra["pagina"].values, "departamento": muestra["bloque"].values,
        "nombre_en_pdf": muestra["municipio_pdf"].values,
        "nombre_divipola": muestra["cod_divipola"].map(nombres).values,
        "cod_divipola": muestra["cod_divipola"].values, "puntaje": muestra["puntaje_cruce"].round(1).values,
        "correcto": None, "observaciones": None})
    destino = RAIZ / "docs" / "revision_f2"
    destino.mkdir(parents=True, exist_ok=True)
    path = destino / f"cruces_aproximados_{a.anio}.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        tabla.to_excel(w, index=False, sheet_name="Revision")
        ws = w.sheets["Revision"]
        for c in ws[1]:
            c.font, c.fill = Font(bold=True, color="FFFFFF"), PatternFill("solid", fgColor="1F1F1F")
        for letra, ancho in zip("ABCDEFGHI", (5, 8, 20, 26, 32, 13, 9, 11, 40)):
            ws.column_dimensions[letra].width = ancho
        amarillo = PatternFill("solid", fgColor="FFF2CC")
        for r in range(2, a.n + 2):
            for col in (8, 9):
                ws.cell(r, col).fill = amarillo
            ws.cell(r, 6).number_format = "@"
        dv = DataValidation(type="list", formula1='"sí,no"', allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(f"H2:H{a.n + 1}")
        ws.freeze_panes = "A2"
    print(f"{a.n} de {len(aprox)} cruces aproximados → {path.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
