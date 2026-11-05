import numpy as np

SEMILLA = 2026


def chapman(n1, n2, m, z=1.96):
    """Estimador de Chapman de captura y recaptura: N = (n1+1)(n2+1)/(m+1) - 1, con varianza
    (n1+1)(n2+1)(n1-m)(n2-m) / ((m+1)^2 (m+2)) e intervalo N ± z·√Var, con límite inferior n1+n2-m (los ya vistos)."""
    if not (0 <= m <= min(n1, n2)):
        raise ValueError("m debe estar entre 0 y min(n1, n2)")
    n = (n1 + 1) * (n2 + 1) / (m + 1) - 1
    var = (n1 + 1) * (n2 + 1) * (n1 - m) * (n2 - m) / ((m + 1) ** 2 * (m + 2))
    visto = n1 + n2 - m
    mitad = z * np.sqrt(var)
    return {"n1": n1, "n2": n2, "m": m, "estimado": n, "varianza": var, "ee": float(np.sqrt(var)),
            "ic_inf": max(n - mitad, visto), "ic_sup": n + mitad, "observados": visto}


def bootstrap(n1, n2, m, reps=2000, semilla=SEMILLA, nivel=0.95):
    """Intervalo percentil por remuestreo de los prestadores observados (en ambas fuentes, solo en 1, solo en 2); se usa si m < 10."""
    unidades = np.array([2] * m + [0] * (n1 - m) + [1] * (n2 - m))
    rng = np.random.default_rng(semilla)
    est = np.empty(reps)
    for k in range(reps):
        r = rng.choice(unidades, size=len(unidades), replace=True)
        a, b, ab = int(np.isin(r, [0, 2]).sum()), int(np.isin(r, [1, 2]).sum()), int((r == 2).sum())
        est[k] = (a + 1) * (b + 1) / (ab + 1) - 1
    q = (1 - nivel) / 2
    return float(np.quantile(est, q)), float(np.quantile(est, 1 - q))


def estimar(n1, n2, m):
    r = chapman(n1, n2, m)
    if m < 10:
        r["bootstrap_inf"], r["bootstrap_sup"] = bootstrap(n1, n2, m)
    return r
