import subprocess

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import adjusted_rand_score
from statsmodels.stats.multitest import multipletests

from src.etl.comun import RAIZ, cargar_config
from src.modelos.grupos_hcpc import PATRONES, grupos_reportados, universo_d98
from src.modelos.perfil_variables import cargar, homologar

SEMILLA = 2026
PERMUTACIONES = 9999
MIN_CONTRATOS_MAPA = 20
GRUPOS_CLAVE = ["Grupo 1", "Grupo 2", "Grupo 3"]
PERIODOS = {"2020–2022": (2020, 2022), "2023–2025": (2023, 2025)}
CODIGOS_DEPARTAMENTO = {
    "antioquia": "05", "atlntico": "08", "distritocapitaldebogot": "11", "bogotdc": "11", "bolvar": "13", "boyac": "15", "caldas": "17", "caquet": "18",
    "cauca": "19", "cesar": "20", "crdoba": "23", "cundinamarca": "25", "choc": "27", "huila": "41", "laguajira": "44", "magdalena": "47", "meta": "50",
    "nario": "52", "nortedesantander": "54", "quindo": "63", "risaralda": "66", "santander": "68", "sucre": "70", "tolima": "73", "valledelcauca": "76",
    "arauca": "81", "casanare": "85", "putumayo": "86", "sanandrsprovidenciaysantacatalina": "88", "amazonas": "91", "guaina": "94", "guaviare": "95",
    "vaups": "97", "vichada": "99",
}
NOMBRES_DEPARTAMENTO = {
    "05": "Antioquia", "08": "Atlántico", "11": "Bogotá D.C.", "13": "Bolívar", "15": "Boyacá", "17": "Caldas", "18": "Caquetá", "19": "Cauca", "20": "Cesar",
    "23": "Córdoba", "25": "Cundinamarca", "27": "Chocó", "41": "Huila", "44": "La Guajira", "47": "Magdalena", "50": "Meta", "52": "Nariño",
    "54": "Norte de Santander", "63": "Quindío", "66": "Risaralda", "68": "Santander", "70": "Sucre", "73": "Tolima", "76": "Valle del Cauca", "81": "Arauca",
    "85": "Casanare", "86": "Putumayo", "88": "San Andrés y Providencia", "91": "Amazonas", "94": "Guainía", "95": "Guaviare", "97": "Vaupés", "99": "Vichada",
}
REGION_DE_DEPARTAMENTO = {
    **dict.fromkeys(["08", "13", "20", "23", "44", "47", "70", "88"], "Caribe e insular"),
    **dict.fromkeys(["05", "11", "15", "17", "25", "41", "54", "63", "66", "68", "73"], "Andina"),
    **dict.fromkeys(["19", "27", "52", "76"], "Pacífica"),
    **dict.fromkeys(["50", "81", "85", "99"], "Orinoquía"),
    **dict.fromkeys(["18", "86", "91", "94", "95", "97"], "Amazonía"),
}


def clave(nombre):
    return "".join(c for c in str(nombre).lower() if "a" <= c <= "z")


def cargar_validacion():
    config = cargar_config()
    f = homologar(cargar(config, universo_d98(config))).reset_index(drop=True)
    b = pd.read_csv(RAIZ / "data/processed/resultados_secop/patrones_base.csv", dtype={"entidad_id": str})
    g = pd.read_csv(PATRONES / "hcpc_d98_grupos.csv")["grupo"]
    if not (len(f) == len(b) == len(g)) or not (f["fuente"].values == b["fuente"].values).all():
        raise ValueError("las tablas no están alineadas fila a fila")
    d = pd.DataFrame({"grupo_hcpc": g, "fuente": b["fuente"], "anio": b["anio"], "valor": b["valor_constante_2025"], "proveedor": f["proveedor_id"].astype("string")})
    d["cod_dpto"] = f["departamento_entidad"].map(lambda x: CODIGOS_DEPARTAMENTO.get(clave(x)) if pd.notna(x) else None)
    if d["cod_dpto"].isna().sum() > 10:
        raise ValueError("departamentos sin código")
    d["region"] = d["cod_dpto"].map(REGION_DE_DEPARTAMENTO)
    reportados = grupos_reportados(pd.read_csv(PATRONES / "hcpc_d98_estabilidad.csv"), pd.read_csv(PATRONES / "hcpc_d98_tamanos.csv"))
    d["grupo"] = d["grupo_hcpc"].map(dict(zip(reportados["grupo"], reportados["nombre"])))
    return d, reportados


def chi2_v(tabla):
    tabla = tabla.loc[tabla.sum(axis=1) > 0, tabla.sum(axis=0) > 0]
    chi2, p, gl, esp = stats.chi2_contingency(tabla.values, correction=False)
    n = tabla.values.sum()
    v = np.sqrt(chi2 / (n * (min(tabla.shape) - 1)))
    return {"chi2": chi2, "gl": gl, "p": p, "n": int(n), "V": v, "esperada": pd.DataFrame(esp, index=tabla.index, columns=tabla.columns)}


def lectura_v(v):
    return "despreciable" if v < 0.1 else "pequeña" if v < 0.3 else "mediana" if v < 0.5 else "grande"


def mejor_emparejamiento(ref, nuevo, grupo):
    a = set(np.flatnonzero(ref == grupo))
    mejor = (None, 0.0, 0.0, 0.0)
    for j in np.unique(nuevo):
        b = set(np.flatnonzero(nuevo == j))
        inter = len(a & b)
        jac = inter / len(a | b)
        if jac > mejor[1]:
            mejor = (j, jac, inter / len(a), inter / len(b))
    return {"grupo_nuevo": mejor[0], "jaccard": mejor[1], "pct_del_grupo_d98": mejor[2] * 100, "pct_del_grupo_nuevo": mejor[3] * 100}


def plataforma(d, reportados):
    r = d[d["grupo"].notna()]
    filas = []
    for nombre, (a, b) in {"Total 2020–2025": (2020, 2025), **PERIODOS}.items():
        s = r[r["anio"].between(a, b)]
        c = chi2_v(pd.crosstab(s["grupo"], s["fuente"]))
        filas.append({"periodo": nombre, "n": c["n"], "chi2": c["chi2"], "gl": c["gl"], "p": c["p"], "V": c["V"], "lectura": lectura_v(c["V"])})
    por_grupo = pd.crosstab(r["grupo"], r["fuente"], normalize="index").mul(100)

    s2 = pd.read_csv(PATRONES / "validacion_secop2_grupos.csv")
    ref = d.loc[s2["fila"] - 1, "grupo_hcpc"].values
    nombre = dict(zip(reportados["grupo"], reportados["nombre"]))
    comparaciones, cruces = [], {}
    for variante, col in [("SECOP II solo, k automático", "grupo_auto"), ("SECOP II solo, k = 11", "grupo_k11")]:
        nuevo = s2[col].values
        fila = {"variante": variante, "contratos": len(s2), "k_nuevo": len(np.unique(nuevo)), "ARI": adjusted_rand_score(ref, nuevo)}
        for g in GRUPOS_CLAVE:
            h = int(reportados.loc[reportados["nombre"] == g, "grupo"].iloc[0])
            m = mejor_emparejamiento(ref, nuevo, h)
            fila[f"{g} jaccard"] = m["jaccard"]
            fila[f"{g} pct_d98"] = m["pct_del_grupo_d98"]
            fila[f"{g} grupo_nuevo"] = m["grupo_nuevo"]
        comparaciones.append(fila)
        cruces[variante] = pd.crosstab(pd.Series(ref, name="d98").map(lambda h: nombre.get(h, f"HCPC {h} (no reportado)")), pd.Series(nuevo, name="nuevo"))
    sup = pd.read_csv(PATRONES / "validacion_fuente_suplementaria.csv")["grupo_sup"].values
    comparaciones.append({"variante": "fuente suplementaria, todos los contratos", "contratos": len(d), "k_nuevo": len(np.unique(sup)), "ARI": adjusted_rand_score(d["grupo_hcpc"], sup)})
    comp = pd.DataFrame(comparaciones)

    def se_reproducen(i):
        return bool(all(comp.loc[i, f"{g} jaccard"] >= 0.6 or comp.loc[i, "ARI"] >= 0.5 for g in GRUPOS_CLAVE))

    return {"v": pd.DataFrame(filas), "por_grupo": por_grupo, "comp": comp, "cruces": cruces, "reproducen": se_reproducen(0), "reproducen_k11": se_reproducen(1)}


def agrupar_cochran(tabla):
    t = tabla.copy()
    while t.shape[1] > 2:
        esp = stats.contingency.expected_freq(t.values)
        if (esp >= 5).mean() >= 0.8 and (esp >= 1).all():
            break
        candidatas = t.drop(columns="Otros") if "Otros" in t.columns else t
        menor = candidatas.sum(axis=0).idxmin()
        resto = t[menor]
        t = t.drop(columns=menor)
        t["Otros"] = t["Otros"] + resto if "Otros" in t.columns else resto
    return t


def p_permutacion(g, c, observado):
    rng = np.random.default_rng(SEMILLA)
    gi, ci = pd.factorize(g)[0], pd.factorize(c)[0]
    ng, nc = gi.max() + 1, ci.max() + 1
    esperada = np.outer(np.bincount(gi, minlength=ng), np.bincount(ci, minlength=nc)) / len(g)
    mayor = 0
    for _ in range(PERMUTACIONES):
        tabla = np.bincount(gi * nc + rng.permutation(ci), minlength=ng * nc).reshape(ng, nc)
        mayor += ((tabla - esperada) ** 2 / esperada).sum() >= observado - 1e-9
    return (mayor + 1) / (PERMUTACIONES + 1)


def residuos(tabla):
    esp = stats.contingency.expected_freq(tabla.values)
    n = tabla.values.sum()
    pf = tabla.sum(axis=1).values[:, None] / n
    pc = tabla.sum(axis=0).values[None, :] / n
    return pd.DataFrame((tabla.values - esp) / np.sqrt(esp * (1 - pf) * (1 - pc)), index=tabla.index, columns=tabla.columns)


def territorio(d):
    r = d[d["grupo"].notna() & d["cod_dpto"].notna()].copy()
    r["departamento"] = r["cod_dpto"].map(NOMBRES_DEPARTAMENTO)
    resultado = {}
    for nivel in ["departamento", "region"]:
        bruta = pd.crosstab(r["grupo"], r[nivel])
        agr = agrupar_cochran(bruta) if nivel == "departamento" else bruta
        c = chi2_v(agr)
        cb = chi2_v(bruta)
        res = residuos(agr)
        fuertes = [{"grupo": g, nivel: col, "residuo": res.loc[g, col], "contratos": int(agr.loc[g, col]), "esperado": float(c["esperada"].loc[g, col])}
                   for g in res.index for col in res.columns if abs(res.loc[g, col]) > 3]
        tabla_fuertes = pd.DataFrame(fuertes, columns=["grupo", nivel, "residuo", "contratos", "esperado"])
        resultado[nivel] = {"bruta": bruta, "agrupada": agr, "chi2": c, "chi2_bruta": cb, "p_perm": p_permutacion(r["grupo"].values, r[nivel].values, cb["chi2"]),
                            "residuos": res, "fuertes": tabla_fuertes.sort_values("residuo", key=abs, ascending=False), "celdas": int(res.size)}
    dom = r.groupby(["cod_dpto", "grupo"]).size().rename("n").reset_index()
    dom["total"] = dom.groupby("cod_dpto")["n"].transform("sum")
    dom["pct"] = dom["n"] / dom["total"] * 100
    resultado["dominante"] = dom.sort_values(["cod_dpto", "n", "grupo"], ascending=[True, False, True]).drop_duplicates("cod_dpto")
    return resultado


def dunn(valores, grupos):
    s = pd.DataFrame({"v": valores, "g": grupos})
    s["r"] = s["v"].rank()
    n = len(s)
    _, conteo = np.unique(s["v"], return_counts=True)
    varianza = n * (n + 1) / 12 - (conteo ** 3 - conteo).sum() / (12 * (n - 1))
    res = s.groupby("g")["r"].agg(["mean", "size"])
    nombres = list(res.index)
    filas = []
    for i in range(len(nombres)):
        for j in range(i + 1, len(nombres)):
            a, b = nombres[i], nombres[j]
            z = (res.loc[a, "mean"] - res.loc[b, "mean"]) / np.sqrt(varianza * (1 / res.loc[a, "size"] + 1 / res.loc[b, "size"]))
            filas.append({"a": a, "b": b, "z": z, "p": 2 * stats.norm.sf(abs(z))})
    t = pd.DataFrame(filas)
    t["p_holm"] = multipletests(t["p"], method="holm")[1]
    return t


def lectura_epsilon(e):
    return "despreciable" if e < 0.01 else "débil" if e < 0.04 else "moderado" if e < 0.16 else "relativamente fuerte" if e < 0.36 else "fuerte"


def tendencia_ca(x, n):
    t = np.arange(len(x), dtype=float)
    x, n = np.asarray(x, float), np.asarray(n, float)
    p = x.sum() / n.sum()
    z = (t * (x - n * p)).sum() / np.sqrt(p * (1 - p) * ((n * t ** 2).sum() - (n * t).sum() ** 2 / n.sum()))
    return z, 2 * stats.norm.sf(abs(z))


def valor_y_tiempo(d):
    r = d[d["grupo"].notna()]
    pos = r[r["valor"] > 0].copy()
    pos["logv"] = np.log(pos["valor"])
    h, p = stats.kruskal(*[x["logv"].values for _, x in pos.groupby("grupo")])
    n = len(pos)
    eps = h / (n - 1)
    resumen = pos.groupby("grupo")["valor"].agg(contratos="size", mediana="median").reset_index()
    pares = dunn(pos["logv"].values, pos["grupo"].values)
    cuenta = pd.crosstab(r["anio"], r["grupo"])
    prop = cuenta.div(cuenta.sum(axis=1), axis=0).mul(100)
    cuenta2 = pd.crosstab(r.loc[r["fuente"] == "secop2", "anio"], r.loc[r["fuente"] == "secop2", "grupo"])
    filas = []
    for g in cuenta.columns:
        z, pz = tendencia_ca(cuenta[g].values, cuenta.sum(axis=1).values)
        z2, pz2 = tendencia_ca(cuenta2[g].values, cuenta2.sum(axis=1).values)
        filas.append({"grupo": g, "chi2_tendencia": z ** 2, "p": pz, "signo": "+" if z > 0 else "−",
                      "chi2_tendencia_solo_secop2": z2 ** 2, "p_solo_secop2": pz2, "signo_solo_secop2": "+" if z2 > 0 else "−"})
    tend = pd.DataFrame(filas)
    tend["p_holm"] = multipletests(tend["p"], method="holm")[1]
    tend["p_holm_solo_secop2"] = multipletests(tend["p_solo_secop2"], method="holm")[1]
    g3 = cuenta["Grupo 3"]
    resto = cuenta.sum(axis=1) - g3
    a, b = g3.loc[2020], resto.loc[2020]
    c, e = g3.loc[g3.index != 2020].sum(), resto.loc[resto.index != 2020].sum()
    odds, p_f = stats.fisher_exact([[a, b], [c, e]])
    traslado = {"pct_2020": a / (a + b) * 100, "pct_resto": c / (c + e) * 100, "n_2020": int(a), "odds": odds, "p": p_f,
                "residuo_2020": residuos(cuenta).loc[2020, "Grupo 3"], "serie": (g3 / cuenta.sum(axis=1) * 100).to_dict()}
    return {"kw": {"H": h, "p": p, "n": n, "epsilon2": eps, "lectura": lectura_epsilon(eps), "excluidos": len(r) - n}, "resumen": resumen, "pares": pares,
            "prop": prop, "cuenta": cuenta, "tend": tend, "traslado": traslado, "chi2_anual": chi2_v(cuenta)}


def concentracion(valores):
    p = valores.sort_values(ascending=False) / valores.sum()
    return float((p ** 2).sum() * 10000), float(p.head(4).sum() * 100)


def proveedores(d):
    r = d[d["grupo"].notna() & (d["valor"] > 0)]
    filas = []
    for g, s in [*r.groupby("grupo"), ("Todos", r)]:
        con = s[s["proveedor"].notna()]
        v = con.groupby("proveedor")["valor"].sum()
        hhi, cr4 = concentracion(v)
        filas.append({"grupo": g, "contratos": len(s), "sin_proveedor": int(s["proveedor"].isna().sum()), "proveedores": int(v.size),
                      "contratos_por_proveedor": len(con) / v.size, "HHI": hhi, "CR4": cr4})
    return pd.DataFrame(filas)


def numero_de_grupos(d):
    pam = pd.read_csv(PATRONES / "validacion_pam_gower.csv")["grupo_pam"].values
    ref = d["grupo_hcpc"].values
    rep = d["grupo"].notna().values
    claves = {g: mejor_emparejamiento(ref, pam, int(d.loc[d["grupo"] == g, "grupo_hcpc"].iloc[0])) for g in GRUPOS_CLAVE}
    return {"sil": pd.read_csv(PATRONES / "validacion_silueta.csv"), "gan": pd.read_csv(PATRONES / "validacion_hcpc_ganancia_inercia.csv"), "ari": adjusted_rand_score(ref, pam),
            "ari_reportados": adjusted_rand_score(ref[rep], pam[rep]), "cruce": pd.crosstab(d["grupo"].fillna("No reportado"), pd.Series(pam, name="PAM")), "claves": claves}


def correr_r():
    subprocess.run(["Rscript", str(RAIZ / "src/modelos/validacion_grupos.R")], check=True)


def calcular():
    d, reportados = cargar_validacion()
    return d, reportados, {"plataforma": plataforma(d, reportados), "territorio": territorio(d), "numero": numero_de_grupos(d),
                           "externa": valor_y_tiempo(d), "proveedores": proveedores(d)}
