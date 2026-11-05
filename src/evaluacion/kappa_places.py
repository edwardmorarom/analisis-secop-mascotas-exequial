import argparse

import pandas as pd
from openpyxl import load_workbook
from sklearn.metrics import cohen_kappa_score

from src.etl.clasificar_places import CLASES, RAIZ

CARPETA = RAIZ / "docs/revision_f5"


def leer(path, ronda="calibracion"):
    ws = load_workbook(path, read_only=True)["revision"]
    filas = list(ws.iter_rows(values_only=True))
    d = pd.DataFrame(filas[1:], columns=filas[0])
    d = d[d["ronda"] == ronda].copy()
    for c in ("clase", "verificado_en", "nota"):
        d[c] = d[c].astype("string").str.strip()
    d["clase"] = d["clase"].str.lower()
    return d.set_index("id_revision")


def comparar(a, b, omitir_sin_clase=False):
    """κ de Cohen sobre las filas de la ronda, matriz de confusión y lista de desacuerdos."""
    faltan = [i for i in a.index if pd.isna(a.loc[i, "clase"]) or pd.isna(b.loc[i, "clase"])]
    if omitir_sin_clase and faltan:
        a, b = a.drop(index=faltan), b.drop(index=faltan)
        faltan = []
    invalidas = sorted((set(a["clase"].dropna()) | set(b["clase"].dropna())) - set(CLASES))
    if faltan or invalidas:
        raise ValueError(f"entrega incompleta o con clases inválidas: sin clase {faltan}; inválidas {invalidas}")
    j = a[["nombre", "clase", "verificado_en", "nota"]].join(
        b[["clase", "verificado_en", "nota"]], lsuffix="_a", rsuffix="_b", how="inner")
    kappa = cohen_kappa_score(j["clase_a"], j["clase_b"], labels=CLASES)
    confusion = pd.crosstab(j["clase_a"], j["clase_b"]).reindex(index=CLASES, columns=CLASES, fill_value=0)
    desacuerdos = j[j["clase_a"] != j["clase_b"]].reset_index()
    return {"n": len(j), "acuerdo": float((j["clase_a"] == j["clase_b"]).mean()), "kappa": float(kappa),
            "confusion": confusion, "desacuerdos": desacuerdos}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", default=str(CARPETA / "places_revision_edward.xlsx"))
    ap.add_argument("--omitir-sin-clase", action="store_true", help="excluye las filas sin clase en alguno de los libros y las informa")
    ap.add_argument("--ronda", default="calibracion")
    ap.add_argument("--salida", default="desacuerdos_calibracion.csv")
    ap.add_argument("--b", default=str(CARPETA / "places_revision_harold.xlsx"))
    args = ap.parse_args()
    a, b = leer(args.a, args.ronda), leer(args.b, args.ronda)
    if args.omitir_sin_clase:
        sin = [i for i in a.index if pd.isna(a.loc[i, "clase"]) or pd.isna(b.loc[i, "clase"])]
        print(f"filas omitidas por no tener clase en algún libro: {sin}")
    r = comparar(a, b, omitir_sin_clase=args.omitir_sin_clase)
    print(f"filas de calibración: {r['n']} | acuerdo observado: {r['acuerdo']:.3f} | κ de Cohen: {r['kappa']:.3f}")
    print(r["confusion"].to_string())
    destino = CARPETA / args.salida
    r["desacuerdos"].to_csv(destino, index=False, encoding="utf-8-sig")
    print(f"{len(r['desacuerdos'])} desacuerdos en {destino}")


if __name__ == "__main__":
    main()
