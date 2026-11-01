"""Perfil de clases, residuos bivariados y comparación con ACM + HCPC de la tipología de menor BIC (D97)."""
import json
import pickle

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

from src.modelos.patrones_lca import ITEMS, salida


def perfiles(ajuste, niveles, cortes):
    th = ajuste["theta"]
    clases = ajuste["R"].argmax(axis=1)
    n = len(clases)
    filas = []
    for k in range(th.shape[0]):
        for i, var in enumerate(ITEMS):
            for j, cat in enumerate(niveles[i]):
                filas.append({"clase": k + 1, "variable": var, "categoria": cat, "prob_en_clase": th[k, cortes[i] + j]})
    p = pd.DataFrame(filas)
    tam = pd.DataFrame({"clase": np.arange(1, th.shape[0] + 1), "contratos": np.bincount(clases, minlength=th.shape[0])})
    tam["pct"] = 100 * tam["contratos"] / n
    tam["prob_media_posterior"] = [ajuste["R"][clases == k, k].mean() if (clases == k).any() else np.nan for k in range(th.shape[0])]
    return p, tam, clases


def main(modelo=3, k=7):
    with open(salida() / "lca_ajustes.pkl", "rb") as f:
        datos = pickle.load(f)
    aj = datos["ajustes"][(modelo, k)]
    p, tam, clases = perfiles(aj["ajuste"], datos["niveles"], datos["cortes"])
    p.to_csv(salida() / f"lca_perfiles_m{modelo}_k{k}.csv", index=False, encoding="utf-8-sig")
    tam.to_csv(salida() / f"lca_tamanos_m{modelo}_k{k}.csv", index=False, encoding="utf-8-sig")
    aj["bvr"].head(15).to_csv(salida() / f"lca_bvr_m{modelo}_k{k}.csv", index=False, encoding="utf-8-sig")
    hc = pd.read_csv(salida() / "acm_hcpc_grupos.csv")["grupo_hcpc"].to_numpy()
    res = {"modelo": modelo, "clases": k, "ari_acm_hcpc_vs_lca": float(adjusted_rand_score(clases, hc)),
           "tamanos_hcpc": np.bincount(hc)[1:].tolist()}
    cruce = pd.crosstab(pd.Series(clases + 1, name="clase_lca"), pd.Series(hc, name="grupo_hcpc"))
    cruce.to_csv(salida() / "lca_vs_hcpc_cruce.csv", encoding="utf-8-sig")
    (salida() / "lca_vs_hcpc.json").write_text(json.dumps(res), encoding="utf-8")
    print(tam.round(2).to_string(index=False)); print(res)
    pd.set_option("display.width", 200)
    for kk in range(k):
        top = p[(p["clase"] == kk + 1) & (p["prob_en_clase"] > 0.5)].sort_values("prob_en_clase", ascending=False)
        print(kk + 1, "; ".join(f"{r.variable}={r.categoria} ({r.prob_en_clase:.2f})" for r in top.itertuples()))


if __name__ == "__main__":
    main()
