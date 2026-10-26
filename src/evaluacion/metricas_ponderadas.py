import numpy as np
import pandas as pd


def metricas_clase(y, pred, peso, clase="funerario"):
    """Precisión, sensibilidad y F1 de `clase` ponderados por el peso muestral (N/n del estrato)."""
    y, pred, peso = np.asarray(y), np.asarray(pred), np.asarray(peso, dtype=float)
    vp = peso[(y == clase) & (pred == clase)].sum()
    predichos, reales = peso[pred == clase].sum(), peso[y == clase].sum()
    precision = vp / predichos if predichos else np.nan
    sensibilidad = vp / reales if reales else np.nan
    f1 = 2 * precision * sensibilidad / (precision + sensibilidad) if vp else 0.0
    return {"precision": precision, "sensibilidad": sensibilidad, "f1": f1}


def bootstrap(y, pred, peso, estrato, clase="funerario", repeticiones=2000, semilla=2026, nivel=0.95):
    """Intervalo percentil; remuestrea dentro de cada estrato para respetar el diseño y conserva el peso N/n."""
    y, pred, peso, estrato = map(np.asarray, (y, pred, peso, estrato))
    rng = np.random.default_rng(semilla)
    grupos = [np.flatnonzero(estrato == e) for e in np.unique(estrato)]
    salida = []
    for _ in range(repeticiones):
        idx = np.concatenate([rng.choice(g, len(g)) for g in grupos])
        salida.append(metricas_clase(y[idx], pred[idx], peso[idx], clase))
    t = pd.DataFrame(salida)
    bajo, alto = (1 - nivel) / 2, 1 - (1 - nivel) / 2
    return {c: (t[c].quantile(bajo), t[c].quantile(alto)) for c in t}


def fila_resumen(nombre, y, pred, peso, estrato, clase="funerario", **kw):
    puntual, ic = metricas_clase(y, pred, peso, clase), bootstrap(y, pred, peso, estrato, clase, **kw)
    fila = {"modelo": nombre}
    for c, v in puntual.items():
        fila[c] = v
        fila[f"{c}_ic_bajo"], fila[f"{c}_ic_alto"] = ic[c]
    fila["exactitud_ponderada"] = float(np.average(np.asarray(y) == np.asarray(pred), weights=peso))
    return fila
