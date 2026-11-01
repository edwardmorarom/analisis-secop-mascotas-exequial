"""D98: regresión por cuantiles (mediana) del log del valor con bootstrap agrupado por entidad (500 remuestreos, semilla 2034)."""
import numpy as np
import pandas as pd
import statsmodels.api as sm

from src.etl.comun import cargar_config, ruta
from src.modelos.patrones_base import COMPONENTES

SEMILLA = 2034
REMUESTREOS = 500


def diseno(b):
    b = b[b["valor_constante_2025"] > 0].reset_index(drop=True)
    cols = {}
    for v in ("tipo_entidad", "modalidad_grupo", "fuente"):
        ref = b[v].value_counts().index[0]
        for nivel in sorted(b[v].unique()):
            if nivel != ref:
                cols[f"{v}{nivel}"] = (b[v] == nivel).astype(float)
    for c in COMPONENTES:
        cols[c] = b[c].astype(float)
    anios = sorted(b["anio"].unique())
    for a in anios[1:]:
        cols[f"anio{a}"] = (b["anio"] == a).astype(float)
    X = pd.DataFrame(cols)
    X.insert(0, "(Intercept)", 1.0)
    return b, X


def main():
    ruta_base = ruta(cargar_config(), "processed") / "resultados_secop"
    b = pd.read_csv(ruta_base / "patrones_base.csv", dtype={"entidad_id": str})
    b, X = diseno(b)
    y = np.log(b["valor_constante_2025"].to_numpy())
    Xv = X.to_numpy()
    base = sm.QuantReg(y, Xv).fit(q=0.5, max_iter=5000)
    entidades = b["entidad_id"].to_numpy()
    idx_por_entidad = {e: np.flatnonzero(entidades == e) for e in np.unique(entidades)}
    claves = np.array(list(idx_por_entidad))
    rng = np.random.default_rng(SEMILLA)
    coefs = []
    for r in range(REMUESTREOS):
        elegidas = rng.choice(claves, len(claves), replace=True)
        idx = np.concatenate([idx_por_entidad[e] for e in elegidas])
        coefs.append(sm.QuantReg(y[idx], Xv[idx]).fit(q=0.5, max_iter=5000).params)
        if (r + 1) % 100 == 0:
            print("remuestreo", r + 1, flush=True)
    coefs = np.array(coefs)
    out = pd.DataFrame({"termino": X.columns, "qr_estimador": base.params, "qr_se_bootstrap": coefs.std(axis=0, ddof=1),
                        "qr_ic_bajo": np.percentile(coefs, 2.5, axis=0), "qr_ic_alto": np.percentile(coefs, 97.5, axis=0)})
    out.to_csv(ruta_base / "patrones" / "valor_d98_cuantiles.csv", index=False)
    print(out.round(3).to_string(index=False))
    print("n:", len(y), "| entidades:", len(claves))


if __name__ == "__main__":
    main()
