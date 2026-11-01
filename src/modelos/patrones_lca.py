"""Clases latentes de los contratos funerarios (D97): EM propio, 20 arranques, BVR y estabilidad por bootstrap."""
import argparse
import json
import pickle

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment, minimize
from scipy.special import logsumexp
from sklearn.metrics import adjusted_rand_score

from src.etl.comun import cargar_config, ruta
from src.modelos.patrones_base import CATEGORICAS, COMPONENTES

SEMILLA = 2033
MODELOS = {1: "sin covariables", 2: "fuente", 3: "fuente y año"}
CLASES = range(2, 8)
ARRANQUES = 20
MAX_ITER = 1000
TOL = 1e-8
ITEMS = CATEGORICAS + COMPONENTES


def salida():
    d = ruta(cargar_config(), "processed") / "resultados_secop" / "patrones"
    d.mkdir(parents=True, exist_ok=True)
    return d


def cargar_datos():
    b = pd.read_csv(ruta(cargar_config(), "processed") / "resultados_secop" / "patrones_base.csv", dtype={"entidad_id": str})
    niveles, bloques = [], []
    for c in ITEMS:
        cats = sorted(b[c].astype(str).unique())
        niveles.append(cats)
        bloques.append(np.eye(len(cats))[pd.Categorical(b[c].astype(str), categories=cats).codes])
    X = np.hstack(bloques)
    cortes = np.cumsum([0] + [len(c) for c in niveles])
    fuente = (b["fuente"] == "secop2").astype(float).to_numpy()
    anios = pd.get_dummies(b["anio"], drop_first=True).to_numpy(dtype=float)
    covariables = {1: np.ones((len(b), 1)), 2: np.column_stack([np.ones(len(b)), fuente]), 3: np.column_stack([np.ones(len(b)), fuente, anios])}
    return b, X, niveles, cortes, covariables


def normalizar_items(conteos, cortes):
    theta = np.empty_like(conteos)
    for a, z in zip(cortes[:-1], cortes[1:]):
        theta[:, a:z] = conteos[:, a:z] / conteos[:, a:z].sum(axis=1, keepdims=True)
    return theta


def prior_logit(Z, R, B):
    k = R.shape[1]

    def f(v):
        W = v.reshape(Z.shape[1], k - 1)
        eta = np.column_stack([np.zeros(len(Z)), Z @ W])
        lse = logsumexp(eta, axis=1)
        P = np.exp(eta - lse[:, None])
        return -(R * (eta - lse[:, None])).sum(), (Z.T @ (P - R)[:, 1:]).ravel()

    r = minimize(f, B.ravel(), jac=True, method="L-BFGS-B", options={"maxiter": 25})
    return r.x.reshape(Z.shape[1], k - 1)


def log_prior(Z, B, k, modelo, R=None):
    if modelo == 1:
        return np.tile(np.log(R.mean(axis=0)), (len(Z), 1))
    eta = np.column_stack([np.zeros(len(Z)), Z @ B])
    return eta - logsumexp(eta, axis=1, keepdims=True)


def ajustar(X, cortes, Z, k, modelo, semilla, max_iter=MAX_ITER):
    rng = np.random.default_rng(semilla)
    R = rng.dirichlet(np.ones(k), size=len(X))
    B = np.zeros((Z.shape[1], k - 1))
    ll_prev = -np.inf
    for it in range(max_iter):
        theta = normalizar_items(R.T @ X + 1e-12, cortes)
        if modelo == 2:
            celdas = Z[:, 1] == 1
            P = np.vstack([R[~celdas].mean(axis=0), R[celdas].mean(axis=0)]) + 1e-12
            B = np.log(P[:, 1:] / P[:, [0]])
            B = np.vstack([B[0], B[1] - B[0]])
        elif modelo == 3:
            B = prior_logit(Z, R, B)
        lp = log_prior(Z, B, k, modelo, R)
        lj = lp + X @ np.log(np.maximum(theta, 1e-300)).T
        lse = logsumexp(lj, axis=1)
        ll = lse.sum()
        R = np.exp(lj - lse[:, None])
        if abs(ll - ll_prev) < TOL * abs(ll):
            break
        ll_prev = ll
    return {"ll": ll, "theta": theta, "B": B, "R": R, "iter": it + 1, "k": k, "modelo": modelo, "lp": lp}


def n_parametros(k, modelo, cortes, p):
    items = k * sum(z - a - 1 for a, z in zip(cortes[:-1], cortes[1:]))
    prior = {1: k - 1, 2: 2 * (k - 1), 3: p * (k - 1)}[modelo]
    return items + prior


def entropia_relativa(R):
    return 1 - (-(R * np.log(np.maximum(R, 1e-300))).sum()) / (len(R) * np.log(R.shape[1]))


def bvr(X, cortes, ajuste, Z):
    """Residuos bivariados: χ² observado frente a esperado por par de variables, dividido por sus grados de libertad."""
    pi = np.exp(ajuste["lp"])
    th = ajuste["theta"]
    filas = []
    n = len(X)
    for i in range(len(ITEMS)):
        for j in range(i + 1, len(ITEMS)):
            ai, zi, aj, zj = cortes[i], cortes[i + 1], cortes[j], cortes[j + 1]
            O = X[:, ai:zi].T @ X[:, aj:zj]
            E = sum(np.outer(th[k, ai:zi], th[k, aj:zj]) * pi[:, k].sum() for k in range(th.shape[0]))
            m = E > 1e-9
            gl = (zi - ai - 1) * (zj - aj - 1)
            filas.append({"var1": ITEMS[i], "var2": ITEMS[j], "bvr": float((((O - E) ** 2)[m] / E[m]).sum() / max(gl, 1))})
    return pd.DataFrame(filas).sort_values("bvr", ascending=False).reset_index(drop=True)


def ajustar_todo():
    b, X, niveles, cortes, cov = cargar_datos()
    n = len(b)
    filas, guardados = [], {}
    for modelo in MODELOS:
        Z = cov[modelo]
        for k in CLASES:
            lls, mejor = [], None
            for a in range(ARRANQUES):
                r = ajustar(X, cortes, Z, k, modelo, SEMILLA + a)
                lls.append(r["ll"])
                if mejor is None or r["ll"] > mejor["ll"]:
                    mejor = r
            npar = n_parametros(k, modelo, cortes, Z.shape[1])
            tamanos = np.bincount(mejor["R"].argmax(axis=1), minlength=k)
            brv = bvr(X, cortes, mejor, Z)
            fila = {"modelo": modelo, "covariables": MODELOS[modelo], "clases": k, "parametros": npar, "logLik": mejor["ll"],
                    "BIC": -2 * mejor["ll"] + npar * np.log(n), "AIC": -2 * mejor["ll"] + 2 * npar, "entropia_relativa": entropia_relativa(mejor["R"]),
                    "arranques_con_el_maximo": int(sum(abs(x - mejor["ll"]) < 1e-3 for x in lls)), "iteraciones": mejor["iter"],
                    "tamano_minimo_pct": 100 * tamanos.min() / n, "tamanos": json.dumps(tamanos.tolist()),
                    "bvr_maximo": float(brv["bvr"].iloc[0]), "pares_bvr_mayor_10": int((brv["bvr"] > 10).sum()), "pares_bvr_mayor_3_84": int((brv["bvr"] > 3.84).sum())}
            filas.append(fila)
            guardados[(modelo, k)] = {"ajuste": mejor, "bvr": brv}
            print(f"modelo {modelo} K={k}: BIC {fila['BIC']:.1f}, arranques con el máximo {fila['arranques_con_el_maximo']}/{ARRANQUES}, BVR máx {fila['bvr_maximo']:.1f}", flush=True)
    t = pd.DataFrame(filas)
    t.to_csv(salida() / "lca_comparacion.csv", index=False, encoding="utf-8-sig")
    with open(salida() / "lca_ajustes.pkl", "wb") as f:
        pickle.dump({"ajustes": guardados, "niveles": niveles, "cortes": cortes}, f)
    return t


def remuestreo(modelo, k, r, arranques, datos):
    X, cortes, Z, original = datos
    rng = np.random.default_rng(SEMILLA + 1000 + r)
    idx = rng.integers(0, len(X), len(X))
    mejor = None
    for a in range(arranques):
        aj = ajustar(X[idx], cortes, Z[idx], k, modelo, SEMILLA + 100000 + 10 * r + a)
        if mejor is None or aj["ll"] > mejor["ll"]:
            mejor = aj
    lp = np.tile(mejor["lp"][0], (len(X), 1)) if modelo == 1 else log_prior(Z, mejor["B"], k, modelo)
    boot = (lp + X @ np.log(np.maximum(mejor["theta"], 1e-300)).T).argmax(axis=1)
    tabla = pd.crosstab(original, boot).reindex(index=range(k), columns=range(k), fill_value=0).to_numpy()
    fila, col = linear_sum_assignment(-tabla)
    jac = []
    for i, j in zip(fila, col):
        inter = tabla[i, j]
        union = tabla[i].sum() + tabla[:, j].sum() - inter
        jac.append(inter / union if union else 0.0)
    return jac, adjusted_rand_score(original, boot)


def estabilidad_tramo(modelo, k, desde, hasta, arranques=5):
    b, X, niveles, cortes, cov = cargar_datos()
    with open(salida() / "lca_ajustes.pkl", "rb") as f:
        base = pickle.load(f)["ajustes"][(modelo, k)]["ajuste"]
    datos = (X, cortes, cov[modelo], base["R"].argmax(axis=1))
    res = []
    for r in range(desde, hasta):
        res.append(remuestreo(modelo, k, r, arranques, datos))
        print(f"modelo {modelo} K={k}: remuestreo {r + 1}", flush=True)
    with open(salida() / f"lca_estab_tramo_m{modelo}_k{k}_{desde}_{hasta}.pkl", "wb") as f:
        pickle.dump(res, f)


def estabilidad_resumen(modelo, k, remuestreos=200):
    res = []
    for archivo in sorted(salida().glob(f"lca_estab_tramo_m{modelo}_k{k}_*.pkl")):
        with open(archivo, "rb") as f:
            res += pickle.load(f)
    assert len(res) == remuestreos, f"faltan remuestreos: {len(res)} de {remuestreos}"
    jac = np.array([r[0] for r in res])
    aris = [r[1] for r in res]
    out = {"modelo": modelo, "clases": k, "jaccard_medio_por_clase": jac.mean(axis=0).round(3).tolist(), "jaccard_minimo_medio": float(jac.mean(axis=0).min()),
           "ari_medio": float(np.mean(aris)), "ari_p05": float(np.percentile(aris, 5)), "remuestreos": remuestreos}
    (salida() / f"lca_estabilidad_m{modelo}_k{k}.json").write_text(json.dumps(out), encoding="utf-8")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("etapa", choices=["ajustar", "estabilidad", "resumen"])
    ap.add_argument("--modelo", type=int)
    ap.add_argument("--clases", type=int)
    ap.add_argument("--desde", type=int, default=0)
    ap.add_argument("--hasta", type=int, default=200)
    a = ap.parse_args()
    if a.etapa == "ajustar":
        print(ajustar_todo().round(2).to_string())
    elif a.etapa == "estabilidad":
        estabilidad_tramo(a.modelo, a.clases, a.desde, a.hasta)
    else:
        print(estabilidad_resumen(a.modelo, a.clases))


if __name__ == "__main__":
    main()
