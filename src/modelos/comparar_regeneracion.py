"""Compara las salidas regeneradas de data/processed con una copia previa (reproducibilidad, bloque 1 del 2026-11-01)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from src.etl.comun import cargar_config, ruta

TOL = 1e-9


def comparar_csv(a, b):
    x, y = pd.read_csv(a), pd.read_csv(b)
    if x.shape != y.shape or list(x.columns) != list(y.columns):
        return "forma o columnas distintas", np.nan
    dif = 0.0
    for c in x.columns:
        if pd.api.types.is_numeric_dtype(x[c]) and pd.api.types.is_numeric_dtype(y[c]):
            d = np.nanmax(np.abs(x[c].to_numpy(float) - y[c].to_numpy(float))) if len(x) else 0.0
            dif = max(dif, 0.0 if np.isnan(d) else float(d))
        elif not x[c].astype(str).equals(y[c].astype(str)):
            return f"texto distinto en {c}", np.nan
    return ("igual" if dif <= TOL else "difiere"), dif


def main(copia, subdir="resultados_secop", excluir=("patrones",)):
    copia = Path(copia)
    base = ruta(cargar_config(), "processed")
    filas = []
    for a in sorted((copia / subdir).glob("*.csv")) if subdir else sorted(copia.glob("*.csv")):
        b = base / subdir / a.name if subdir else base / a.name
        if not b.exists():
            filas.append((a.name, "falta en lo regenerado", np.nan))
            continue
        estado, dif = comparar_csv(a, b)
        filas.append((a.name, estado, dif))
    t = pd.DataFrame(filas, columns=["archivo", "estado", "diferencia_maxima"])
    print(t.to_string(index=False))
    print("\nresumen:", t["estado"].value_counts().to_dict())
    return t


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "resultados_secop")
