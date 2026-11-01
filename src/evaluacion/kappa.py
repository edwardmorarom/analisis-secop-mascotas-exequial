import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from sklearn.metrics import cohen_kappa_score

from src.etl.anonimizar import anonimizar
from src.etl.comun import RAIZ, cargar_config, ruta

CLASES = ["funerario", "no_funerario", "mixto"]
CARPETA = RAIZ / "docs" / "etiquetado"


def leer(path, revisor):
    d = pd.read_excel(path, sheet_name="Etiquetado", dtype=str)
    d["etiqueta"] = d["etiqueta"].str.strip().str.lower()
    d["forense"] = pd.to_numeric(d["forense"], errors="coerce")
    d["revisor"] = revisor
    return d


def validar(d):
    problemas = []
    for r in d.itertuples():
        if pd.isna(r.etiqueta):
            problemas.append((r.id_muestra, r.revisor, "sin etiqueta"))
        elif r.etiqueta not in CLASES:
            problemas.append((r.id_muestra, r.revisor, "etiqueta inválida"))
        if pd.isna(r.forense):
            problemas.append((r.id_muestra, r.revisor, "sin marca forense"))
        elif r.forense not in (0, 1):
            problemas.append((r.id_muestra, r.revisor, "forense inválido"))
        if r.forense == 1 and r.etiqueta == "funerario":
            problemas.append((r.id_muestra, r.revisor, "incoherente: forense = 1 con funerario"))
    return pd.DataFrame(problemas, columns=["id_muestra", "revisor", "problema"])


def kappa(a, b):
    if len(a) == 0 or (a.nunique() == 1 and (a == b).all()):
        return np.nan
    return cohen_kappa_score(a, b)


def resumen(nombre, sub, umbral):
    k = kappa(sub["etiqueta_e"], sub["etiqueta_n"])
    return {"grupo": nombre, "n": len(sub),
            "acuerdo_etiqueta": (sub["etiqueta_e"] == sub["etiqueta_n"]).mean(), "kappa_etiqueta": k,
            "acuerdo_forense": (sub["forense_e"] == sub["forense_n"]).mean(),
            "kappa_forense": kappa(sub["forense_e"], sub["forense_n"]),
            "cumple_umbral": bool(k >= umbral) if pd.notna(k) else None}


def calcular(e, n, maestra, umbral):
    m = e.merge(n, on="id_muestra", suffixes=("_e", "_n")).merge(
        maestra[["id_muestra", "subestrato"]], on="id_muestra")
    m["macro"] = m["subestrato"].str[0]
    m = m.dropna(subset=["etiqueta_e", "etiqueta_n", "forense_e", "forense_n"])
    filas = [resumen("global", m, umbral)]
    for ronda, sub in m.groupby("ronda_e"):
        filas.append(resumen(f"ronda: {ronda}", sub, umbral))
    for macro, sub in m.groupby("macro"):
        filas.append(resumen(f"estrato {macro}", sub, umbral))
    for est, sub in m.groupby("subestrato"):
        filas.append(resumen(f"subestrato {est}", sub, umbral))
    return m, pd.DataFrame(filas)


def exportar_desacuerdos(m, destino):
    if destino.exists():
        raise SystemExit(f"{destino.name} ya existe: no se sobrescribe (puede tener etiquetas de Harold).")
    d = m.copy()
    d["incoherente"] = ((d.forense_e == 1) & (d.etiqueta_e == "funerario")) | \
                       ((d.forense_n == 1) & (d.etiqueta_n == "funerario"))
    d["dif_etiqueta"] = d.etiqueta_e != d.etiqueta_n
    d["dif_forense"] = d.forense_e != d.forense_n
    d = d[d.dif_etiqueta | d.dif_forense | d.incoherente].copy()
    d["tipo"] = d.apply(lambda r: ", ".join(t for t, f in (
        ("etiqueta", r.dif_etiqueta), ("forense", r.dif_forense), ("incoherencia", r.incoherente)) if f), axis=1)
    azar = np.random.default_rng(2026).random(len(d)) < 0.5
    d["etiqueta_a"] = np.where(azar, d.etiqueta_n, d.etiqueta_e)
    d["etiqueta_b"] = np.where(azar, d.etiqueta_e, d.etiqueta_n)
    d["forense_a"] = np.where(azar, d.forense_n, d.forense_e)
    d["forense_b"] = np.where(azar, d.forense_e, d.forense_n)
    clave = pd.DataFrame({"id_muestra": d["id_muestra"].values, "a_es": np.where(azar, "natalia", "edward")})
    d = d[["n_e", "ronda_e", "id_muestra", "objeto_e", "descripcion_e", "tipo", "etiqueta_a", "etiqueta_b",
           "forense_a", "forense_b"]].rename(columns={
        "n_e": "n", "ronda_e": "ronda", "objeto_e": "objeto", "descripcion_e": "descripcion"})
    for c in ("objeto", "descripcion"):
        d[c] = d[c].map(anonimizar)
    d["n"] = d["n"].astype(int)
    d = d.sort_values("n")
    for c in ("etiqueta_final", "forense_final", "notas_harold"):
        d[c] = None
    d.to_excel(destino, index=False, sheet_name="Desacuerdos")
    wb = load_workbook(destino)
    ws = wb["Desacuerdos"]
    for letra, ancho in zip("ABCDEFGHIJKLM", (6, 12, 11, 70, 50, 20, 15, 15, 10, 10, 15, 11, 40)):
        ws.column_dimensions[letra].width = ancho
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="1F1F1F")
    amarillo = PatternFill("solid", fgColor="FFF2CC")
    for r in range(2, ws.max_row + 1):
        for col in (4, 5):
            ws.cell(r, col).alignment = Alignment(wrap_text=True, vertical="top")
        for col in (11, 12, 13):
            ws.cell(r, col).fill = amarillo
    if ws.max_row > 1:
        clases = DataValidation(type="list", formula1='"' + ",".join(CLASES) + '"', allow_blank=True)
        marca = DataValidation(type="list", formula1='"0,1"', allow_blank=True)
        ws.add_data_validation(clases)
        ws.add_data_validation(marca)
        clases.add(f"K2:K{ws.max_row}")
        marca.add(f"L2:L{ws.max_row}")
    ws.freeze_panes = "D2"
    wb.save(destino)
    return d, clave


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--edward", default=CARPETA / "etiquetado_edward.xlsx")
    p.add_argument("--natalia", default=CARPETA / "etiquetado_natalia.xlsx")
    p.add_argument("--salida", default=CARPETA)
    a = p.parse_args()
    config = cargar_config()
    umbral = config["evaluacion"]["umbrales"]["kappa"]
    maestra = pd.read_parquet(ruta(config, "processed") / "muestra_secop_maestra.parquet")
    e, n = leer(a.edward, "edward"), leer(a.natalia, "natalia")
    assert e["id_muestra"].tolist() == n["id_muestra"].tolist(), \
        "los dos libros deben tener los mismos casos en el mismo orden"

    problemas = validar(pd.concat([e, n]))
    if len(problemas):
        print(f"Validación: {len(problemas)} problemas")
        print(problemas.groupby(["revisor", "problema"]).size().to_string())
    else:
        print("Validación: sin problemas")
    m, tabla = calcular(e, n, maestra, umbral)
    pd.set_option("display.width", 200)
    print(f"\nκ de Cohen (umbral {umbral}); casos comparables: {len(m)} de {len(e)}")
    print(tabla.round(3).to_string(index=False))
    salida = Path(a.salida)
    tabla.to_csv(salida / "kappa_etiquetado.csv", index=False, encoding="utf-8-sig")
    d, clave = exportar_desacuerdos(m, salida / "desacuerdos_para_harold.xlsx")
    clave.to_csv(ruta(config, "processed") / "clave_desacuerdos.csv", index=False)
    print(f"\nDesacuerdos exportados: {len(d)} → {salida / 'desacuerdos_para_harold.xlsx'}")


if __name__ == "__main__":
    main()
