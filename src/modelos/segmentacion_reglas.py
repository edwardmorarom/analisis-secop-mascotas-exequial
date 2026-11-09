"""Segmentación por reglas del mercado funerario, Comprador × Objeto, con validación estadística P1 a P5 (D109)."""
import argparse
import itertools
import shutil
import sys
import traceback
from datetime import datetime

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import adjusted_rand_score

from src.etl.comun import RAIZ, cargar_config
from src.modelos.grupos_hcpc import universo_d98
from src.modelos.perfil_variables import cargar, homologar
from src.modelos.validacion_grupos import agrupar_cochran, cargar_validacion, chi2_v, concentracion, dunn, lectura_epsilon, p_permutacion

SEMILLA = 2026
REPLICAS = 2000
MIN_PCT_SEGMENTO = 1.0
UMBRAL_EPSILON, UMBRAL_V, UMBRAL_CAMBIO_VALOR = 0.06, 0.20, 2.0
ORDEN_BASE = ("plan", "bienes", "traslado", "servicio")
NOMBRE_OBJETO = {"plan": "Plan exequial", "bienes": "Ataúdes y bienes", "traslado": "Traslado", "servicio": "Servicio de inhumación"}
OTRO_OBJETO, OTROS_SEGMENTOS = "Otro", "Otros segmentos"
COMPRADORES = ["Alcaldía", "Gobernación", "Hospital", "Servicios públicos", "Nacional", "Otra"]
DESTINO = RAIZ / "docs/resultados"
COPIA = RAIZ / "data/processed/resultados_secop/segmentacion"
INFORME = DESTINO / "segmentacion_reglas.md"


def comprador(d):
    t, o = d["tipo_entidad"], d["orden_nivel"]
    return pd.Series(np.select([t == "alcaldia_municipio", t == "gobernacion_departamento", t == "salud_hospital_ese", t == "servicios_publicos_empresa", o == "NACIONAL"],
                               ["Alcaldía", "Gobernación", "Hospital", "Servicios públicos", "Nacional"], default="Otra"), index=d.index)


def objeto(d, orden=ORDEN_BASE):
    cond = {"plan": d["plan_exequial"] == 1, "bienes": (d["ataudes_bienes"] == 1) & (d["inhumacion_cremacion"] == 0), "traslado": d["traslado"] == 1, "servicio": d["inhumacion_cremacion"] == 1}
    r = pd.Series(OTRO_OBJETO, index=d.index)
    for regla in reversed(orden):
        r = r.mask(cond[regla], NOMBRE_OBJETO[regla])
    return r


def segmento_completo(d, orden=ORDEN_BASE):
    return comprador(d) + " · " + objeto(d, orden)


def segmentos_pequenos(seg_vigente):
    pct = seg_vigente.value_counts(normalize=True) * 100
    return sorted(pct[pct < MIN_PCT_SEGMENTO].index)


def agrupar_pequenos(seg, pequenos):
    return seg.where(~seg.isin(pequenos), OTROS_SEGMENTOS)


def cargar_datos():
    config = cargar_config()
    f = homologar(cargar(config, universo_d98(config))).reset_index(drop=True)
    b = pd.read_csv(RAIZ / "data/processed/resultados_secop/patrones_base.csv", dtype={"entidad_id": str})
    v, _ = cargar_validacion()
    if not (len(f) == len(b) == len(v)) or not (f["fuente"].values == b["fuente"].values).all() or not np.allclose(f["valor_constante_2025"], b["valor_constante_2025"]):
        raise ValueError("las tablas no están alineadas fila a fila")
    u = pd.read_parquet(RAIZ / "data/processed/resultados_secop/universo_mercado.parquet", columns=["llave", "origen_etiqueta_humana", "clase_final"])
    retirados = set(u.loc[u["origen_etiqueta_humana"].eq("grupo5_revision") & u["clase_final"].eq("no_funerario"), "llave"])
    d = b.copy()
    d["valor"] = d.pop("valor_constante_2025")
    d["periodo"] = np.where(d["anio"] <= 2022, "2020–2022", "2023–2025")
    d["cod_dpto"] = v["cod_dpto"].values
    d["proveedor"] = v["proveedor"].values
    d["grupo_hcpc"] = v["grupo_hcpc"].values
    d["grupo"] = v["grupo"].values
    d["vigente"] = ~f["llave"].isin(retirados).values
    d["comprador"] = comprador(d)
    d["objeto"] = objeto(d)
    d["segmento_completo"] = d["comprador"] + " · " + d["objeto"]
    return d


def resumen(d, columna, categorias=None):
    t = d.groupby(columna).agg(contratos=("valor", "size"), valor=("valor", "sum"))
    t["pct_contratos"] = t["contratos"] / t["contratos"].sum() * 100
    t["pct_valor"] = t["valor"] / t["valor"].sum() * 100
    q = d.groupby(columna)["valor"].quantile([0.25, 0.5, 0.75]).unstack() / 1e6
    t["mediana"], t["p25"], t["p75"] = q[0.5], q[0.25], q[0.75]
    t = t.drop(columns="valor")
    return t.reindex(categorias) if categorias is not None else t.sort_values("contratos", ascending=False)


def kruskal_valor(d, columna):
    pos = d[d["valor"] > 0]
    pos = pos.assign(logv=np.log(pos["valor"]))
    grupos = [x["logv"].values for _, x in pos.groupby(columna)]
    h, p = stats.kruskal(*grupos)
    n = len(pos)
    eps = h / (n - 1)
    pares = dunn(pos["logv"].values, pos[columna].values)
    return {"H": h, "gl": len(grupos) - 1, "p": p, "n": n, "excluidos": len(d) - n, "epsilon2": eps, "lectura": lectura_epsilon(eps), "sostiene": bool(eps >= UMBRAL_EPSILON),
            "pares": len(pares), "pares_difieren": int((pares["p_holm"] < 0.05).sum())}, pares


def departamento(d, columna):
    s = d[d["cod_dpto"].notna()]
    tabla = pd.crosstab(s[columna], s["cod_dpto"])
    agrupada = agrupar_cochran(tabla)
    dep = s["cod_dpto"].where(s["cod_dpto"].isin(agrupada.columns), "Otros")
    tabla_g = pd.crosstab(s[columna], dep)
    r = chi2_v(tabla_g)
    p_perm = p_permutacion(s[columna].values, dep.values, r["chi2"])
    return {"chi2": r["chi2"], "gl": r["gl"], "p_asintotico": r["p"], "p_permutacion": p_perm, "V": r["V"], "n": r["n"], "departamentos": tabla.shape[1], "departamentos_tras_agrupar": agrupada.shape[1],
            "sostiene": bool(r["V"] >= UMBRAL_V)}


def proveedores_por(d, columna):
    pos = d[(d["valor"] > 0) & d["proveedor"].notna()]
    filas = []
    for g, s in [*pos.groupby(columna), ("Todos", pos)]:
        v = s.groupby("proveedor")["valor"].sum()
        hhi, cr4 = concentracion(v)
        filas.append({"categoria": g, "contratos": len(s), "proveedores": int(v.size), "HHI": hhi, "CR4": cr4})
    return pd.DataFrame(filas)


def orden_de_reglas(d):
    base = d["segmento_completo"]
    pct_base = d.groupby(base)["valor"].sum() / d["valor"].sum() * 100
    filas = []
    for orden in itertools.permutations(ORDEN_BASE):
        seg = segmento_completo(d, orden)
        pct = (d.groupby(seg)["valor"].sum() / d["valor"].sum() * 100).reindex(pct_base.index.union(seg.unique())).fillna(0)
        dif = (pct - pct_base.reindex(pct.index).fillna(0)).abs()
        filas.append({"orden": " > ".join(orden), "pct_contratos_cambian": float((seg != base).mean() * 100), "max_cambio_pct_valor": float(dif.max()), "segmento_max_cambio": dif.idxmax()})
    t = pd.DataFrame(filas)
    return t, {"max_pct_contratos": float(t["pct_contratos_cambian"].max()), "max_cambio_valor": float(t["max_cambio_pct_valor"].max()), "sostiene": bool(t["max_cambio_pct_valor"].max() <= UMBRAL_CAMBIO_VALOR)}


def bootstrap_entidades(d, categorias_por_columna, replicas=REPLICAS, semilla=SEMILLA):
    """IC 95 % (percentiles) del % de contratos, del % del valor y de la mediana por categoría, remuestreando entidades."""
    rng = np.random.default_rng(semilla)
    ent, entidades = pd.factorize(d["entidad_id"])
    indices = [np.flatnonzero(ent == i) for i in range(len(entidades))]
    valor = d["valor"].to_numpy()
    etiquetas = {c: pd.Categorical(d[c], categories=cats) for c, cats in categorias_por_columna.items()}
    codigos = {c: e.codes for c, e in etiquetas.items()}
    salida = {c: {m: np.full((replicas, len(cats)), np.nan) for m in ("pct_contratos", "pct_valor", "mediana")} for c, cats in categorias_por_columna.items()}
    for r in range(replicas):
        idx = np.concatenate([indices[i] for i in rng.integers(0, len(entidades), len(entidades))])
        v = valor[idx]
        for c, cats in categorias_por_columna.items():
            cod = codigos[c][idx]
            k = len(cats)
            n = np.bincount(cod, minlength=k)
            s = np.bincount(cod, weights=v, minlength=k)
            salida[c]["pct_contratos"][r] = n / n.sum() * 100
            salida[c]["pct_valor"][r] = s / s.sum() * 100 if s.sum() > 0 else np.nan
            for j in np.flatnonzero(n):
                salida[c]["mediana"][r, j] = np.median(v[cod == j]) / 1e6
    ic = {}
    for c, cats in categorias_por_columna.items():
        filas = []
        for j, cat in enumerate(cats):
            fila = {"categoria": cat}
            for m in ("pct_contratos", "pct_valor", "mediana"):
                x = salida[c][m][:, j]
                x = x[~np.isnan(x)]
                fila[f"{m}_ic_inf"], fila[f"{m}_ic_sup"] = (np.percentile(x, 2.5), np.percentile(x, 97.5)) if len(x) else (np.nan, np.nan)
            filas.append(fila)
        ic[c] = pd.DataFrame(filas).set_index("categoria")
    return ic


def sensibilidad_sin_grandes(d, fraccion=0.01):
    n_quitar = int(round(len(d) * fraccion))
    sin = d.nsmallest(len(d) - n_quitar, "valor")
    base = d.groupby("comprador")["valor"].sum() / d["valor"].sum() * 100
    nueva = sin.groupby("comprador")["valor"].sum() / sin["valor"].sum() * 100
    orden_base = list(base.sort_values(ascending=False).index)
    orden_nuevo = list(nueva.sort_values(ascending=False).index)
    t = pd.DataFrame({"pct_valor_base": base, "pct_valor_sin_1pct_mayor": nueva}).reindex(orden_base)
    t["posicion_base"] = np.arange(1, len(t) + 1)
    t["posicion_sin_1pct_mayor"] = [orden_nuevo.index(c) + 1 for c in t.index]
    return t, {"quitados": n_quitar, "sostiene": orden_base == orden_nuevo}


def por_subgrupo(d, columna):
    filas = []
    for sub, nombre in [("fuente", None), ("periodo", None)]:
        for g, s in d.groupby(sub):
            t = resumen(s, columna)
            filas += [{"subgrupo": sub, "valor_subgrupo": g, "categoria": c, **f.to_dict()} for c, f in t.iterrows()]
    return pd.DataFrame(filas)


def plataforma_periodo(d):
    por_fuente = d.groupby(["fuente", "segmento"]).size().unstack(fill_value=0)
    top3 = {f: set(por_fuente.loc[f].sort_values(ascending=False).head(3).index) for f in por_fuente.index}
    sin_otros = por_fuente.drop(columns=OTROS_SEGMENTOS, errors="ignore")
    top3_sin_otros = {f: list(sin_otros.loc[f].sort_values(ascending=False).head(3).index) for f in sin_otros.index}
    r = chi2_v(por_fuente)
    return {"chi2": r["chi2"], "gl": r["gl"], "p": r["p"], "V": r["V"], "n": r["n"], "top3": {f: list(por_fuente.loc[f].sort_values(ascending=False).head(3).index) for f in por_fuente.index},
            "top3_sin_otros": top3_sin_otros, "sostiene_sin_otros": len({frozenset(x) for x in top3_sin_otros.values()}) == 1,
            "sostiene": len({frozenset(s) for s in top3.values()}) == 1}


def independencia(d):
    def prueba(comp):
        t = pd.crosstab(comp, d["objeto"])
        r = chi2_v(t)
        esp = r["esperada"].values
        return {"chi2": r["chi2"], "gl": r["gl"], "p": r["p"], "V": r["V"], "n": r["n"], "pct_celdas_esperada_menor_5": float((esp < 5).mean() * 100), "filas": t.shape[0], "columnas": t.shape[1]}
    base = prueba(d["comprador"])
    out = [{"version": "Comprador × Objeto (6 compradores)", **base}]
    if base["pct_celdas_esperada_menor_5"] > 20:
        comp = d["comprador"].replace({"Hospital": "Especializadas", "Servicios públicos": "Especializadas"})
        out.append({"version": "Con Hospital y Servicios públicos agrupados en «Especializadas»", **prueba(comp)})
    return pd.DataFrame(out)


def concordancia_hcpc(d, pequenos):
    seg = agrupar_pequenos(d["segmento_completo"], pequenos)
    g = d["grupo"].fillna("No reportado")
    return {"ari": float(adjusted_rand_score(seg, g)), "n": len(d)}, pd.crosstab(seg.rename("Segmento"), g.rename("Grupo HCPC"))


def calcular(replicas=REPLICAS):
    d = cargar_datos()
    v = d[d["vigente"]].copy()
    pequenos = segmentos_pequenos(v["segmento_completo"])
    v["segmento"] = agrupar_pequenos(v["segmento_completo"], pequenos)
    d["segmento"] = agrupar_pequenos(d["segmento_completo"], pequenos)
    r = {"datos": d, "vigente": v, "pequenos": pequenos}
    r["desc_comprador"] = resumen(v, "comprador", COMPRADORES)
    r["desc_segmento"] = resumen(v, "segmento")
    cats = {"comprador": COMPRADORES, "segmento": list(r["desc_segmento"].index)}
    ic = bootstrap_entidades(v, cats, replicas)
    r["ic"] = ic
    r["p1"] = {}
    for dim in ("comprador", "segmento"):
        kw, pares = kruskal_valor(v, dim)
        r["p1"][dim] = {"kw": kw, "dunn": pares, "dep": departamento(v, dim), "proveedores": proveedores_por(v, dim) if dim == "comprador" else None}
    r["p2_tabla"], r["p2"] = orden_de_reglas(v)
    r["p3_tabla"], r["p3"] = sensibilidad_sin_grandes(v)
    r["p4_comprador"], r["p4_segmento"] = por_subgrupo(v, "comprador"), por_subgrupo(v, "segmento")
    r["p4"] = plataforma_periodo(v)
    r["p5"], r["p5_cruce"] = concordancia_hcpc(d, pequenos)
    r["independencia"] = independencia(v)
    return r


def fmt(x, dec=1):
    return "—" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:,.{dec}f}".replace(",", "#").replace(".", ",").replace("#", ".")


def mil(n):
    return f"{int(n):,}".replace(",", ".")


def pf(p):
    return "< 0,001" if p < 0.001 else f"{p:.3f}".replace(".", ",")


def si(x):
    return "sí" if x else "no"


def tabla_md(filas, cab):
    return ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)] + ["| " + " | ".join(str(x) for x in f) + " |" for f in filas]


def tabla_descriptiva(t, ic):
    filas = []
    for c, f in t.iterrows():
        i = ic.loc[c]
        filas.append((c, f"{int(f.contratos):,}".replace(",", "."), f"{fmt(f.pct_contratos)} ({fmt(i.pct_contratos_ic_inf)} a {fmt(i.pct_contratos_ic_sup)})",
                      f"{fmt(f.pct_valor)} ({fmt(i.pct_valor_ic_inf)} a {fmt(i.pct_valor_ic_sup)})", f"{fmt(f.mediana)} ({fmt(i.mediana_ic_inf)} a {fmt(i.mediana_ic_sup)})", fmt(f.p25), fmt(f.p75)))
    return tabla_md(filas, ["Categoría", "Contratos", "% contratos (IC 95 %)", "% valor (IC 95 %)", "Mediana, millones de 2025 (IC 95 %)", "p25", "p75"])


def informe(r, estado):
    v = r["vigente"]
    p1, p2, p3, p4, p5 = r["p1"], r["p2"], r["p3"], r["p4"], r["p5"]
    nosost = []
    L = ["# Segmentación por reglas del mercado funerario: quién compra × qué compra (D109)", "",
         "> Propuesta pendiente de revisión de Edward (D109). Rama `segmentacion-reglas`, sin integrar a `main`. Respuesta descriptiva principal; el HCPC de D98 es comprobación (P5). Los valores p son **orientativos**: los contratos de una misma entidad no son independientes (ICC 0,52, D97); la incertidumbre principal es el bootstrap por entidad.", "",
         f"Universo: mercado vigente de **{mil(len(v))} contratos `funerario`** (D105), {mil(v['entidad_id'].nunique())} entidades, valor total {fmt(v['valor'].sum() / 1e9)} mil millones de pesos de 2025.", "",
         "**Reglas.** *Comprador:* según `tipo_entidad` y `orden_nivel`. *Objeto* (primera regla que se cumple): plan exequial → Plan exequial; ataúdes o bienes sin inhumación o cremación → Ataúdes y bienes; traslado → Traslado; inhumación o cremación → Servicio de inhumación; si no, Otro. *Segmento* = Comprador × Objeto; los segmentos con menos del 1 % de los contratos van juntos en «Otros segmentos»"
         + (f" ({len(r['pequenos'])} segmentos: " + "; ".join(r["pequenos"]) + ")." if r["pequenos"] else "."), ""]
    L += ["## 1. Descripción", "", "IC 95 % por bootstrap por entidad (2.000 réplicas, semilla 2026, percentiles).", "", "### Por Comprador", ""] + tabla_descriptiva(r["desc_comprador"], r["ic"]["comprador"]) + ["", "### Por Segmento", ""] + tabla_descriptiva(r["desc_segmento"], r["ic"]["segmento"]) + [""]
    ind = r["independencia"]
    L += ["### Independencia Comprador × Objeto", ""] + tabla_md([(x.version, fmt(x.chi2, 1), int(x.gl), pf(x.p), fmt(x.V, 3), fmt(x.pct_celdas_esperada_menor_5, 1) + " %") for x in ind.itertuples()], ["Versión", "χ²", "gl", "p (orientativo)", "V de Cramér", "Celdas con esperada < 5"])
    L += ["", "El Comprador y el Objeto no son independientes (V " + fmt(ind.iloc[0].V, 3) + "); esto describe que la segmentación recoge dos ejes asociados, y es una medida de asociación, no un umbral de la decisión.", ""]
    L += ["## 2. Validación", "", "### P1. Diferencias en variables que no definen los segmentos", ""]
    filas = []
    for dim, nombre in (("comprador", "Comprador"), ("segmento", "Segmento")):
        k, dp = p1[dim]["kw"], p1[dim]["dep"]
        filas.append((f"{nombre}: log del valor (Kruskal-Wallis)", f"H = {fmt(k['H'], 1)}, gl {k['gl']}, n = {mil(k['n'])}", pf(k["p"]), f"ε² = {fmt(k['epsilon2'], 3)} ({k['lectura']})", f"ε² ≥ {fmt(UMBRAL_EPSILON, 2)}", si(k["sostiene"])))
        filas.append((f"{nombre}: departamento (χ², {dp['departamentos']} → {dp['departamentos_tras_agrupar']} departamentos tras Cochran)", f"χ² = {fmt(dp['chi2'], 1)}, gl {dp['gl']}, n = {mil(dp['n'])}", f"{pf(dp['p_permutacion'])} (permutación)", f"V = {fmt(dp['V'], 3)}", f"V ≥ {fmt(UMBRAL_V, 2)}", si(dp["sostiene"])))
        for nom, ok in ((f"{nombre}: valor", k["sostiene"]), (f"{nombre}: departamento", dp["sostiene"])):
            if not ok:
                nosost.append(f"P1, {nom}: no alcanza el umbral.")
    L += tabla_md(filas, ["Prueba", "Estadístico, gl", "p (orientativo)", "Tamaño del efecto", "Umbral", "Se sostiene"])
    L += ["", "Dunn con Holm sobre el log del valor: " + "; ".join(f"{nombre} {p1[dim]['kw']['pares_difieren']} de {p1[dim]['kw']['pares']} pares difieren (p ajustado < 0,05)" for dim, nombre in (("comprador", "Comprador"), ("segmento", "Segmento"))) + ". Detalle en los CSV.", "",
          "**Proveedores por Comprador** (HHI y CR4 sobre el valor, sin umbral):", ""]
    L += tabla_md([(x.categoria, f"{x.contratos:,}".replace(",", "."), f"{x.proveedores:,}".replace(",", "."), fmt(x.HHI, 0), fmt(x.CR4, 1) + " %") for x in p1["comprador"]["proveedores"].itertuples()], ["Comprador", "Contratos con proveedor y valor", "Proveedores", "HHI", "CR4"])
    L += ["", "### P2. Orden de las reglas", "", f"Con las 24 permutaciones del orden de prioridad, como máximo cambian de segmento **{fmt(p2['max_pct_contratos'])} %** de los contratos y el cambio máximo del % del valor por segmento es **{fmt(p2['max_cambio_valor'], 2)} puntos** (umbral ≤ {fmt(UMBRAL_CAMBIO_VALOR, 0)}). **Se sostiene: {si(p2['sostiene'])}.**", ""]
    if not p2["sostiene"]:
        nosost.append(f"P2: el cambio máximo del % del valor por segmento es {fmt(p2['max_cambio_valor'], 2)} puntos (> {fmt(UMBRAL_CAMBIO_VALOR, 0)}).")
    L += ["### P3. Estabilidad frente a contratos grandes", "", f"Los IC del bootstrap por entidad están en las tablas de la sección 1. Sensibilidad sin el 1 % de contratos de mayor valor ({p3['quitados']} contratos): orden de los Compradores por % del valor.", ""]
    L += tabla_md([(c, fmt(f.pct_valor_base), int(f.posicion_base), fmt(f.pct_valor_sin_1pct_mayor), int(f.posicion_sin_1pct_mayor)) for c, f in r["p3_tabla"].iterrows()], ["Comprador", "% valor (base)", "Posición", "% valor (sin 1 % mayor)", "Posición"])
    L += ["", f"**Se sostiene (el orden no cambia): {si(p3['sostiene'])}.**", ""]
    if not p3["sostiene"]:
        nosost.append("P3: el orden de los Compradores por % del valor cambia al quitar el 1 % de contratos de mayor valor.")
    L += ["### P4. Plataforma y periodo", "", f"V de Cramér fuente × Segmento = {fmt(p4['V'], 3)} (χ² = {fmt(p4['chi2'], 1)}, gl {p4['gl']}, n = {mil(p4['n'])}, p {pf(p4['p'])}, orientativo).", "",
          "Tres segmentos con más contratos por plataforma: " + "; ".join(f"{f}: " + ", ".join(s) for f, s in p4["top3"].items()) + f". **Se sostiene (mismo conjunto de tres): {si(p4['sostiene'])}.** Lectura complementaria, que no cambia la decisión: «Otros segmentos» es una bolsa de segmentos pequeños y no un segmento; sin ella, los tres con más contratos son " + "; ".join(f"{f}: " + ", ".join(x) for f, x in p4["top3_sin_otros"].items()) + f" (mismo conjunto: {si(p4['sostiene_sin_otros'])}).", ""]
    if not p4["sostiene"]:
        nosost.append("P4: los tres segmentos con más contratos no son los mismos en SECOP I y SECOP II.")
    for dim, titulo in (("p4_segmento", "Segmento"), ("p4_comprador", "Comprador")):
        t = r[dim]
        L += [f"**{titulo} por plataforma y periodo** (contratos, % de contratos, % del valor y mediana en millones de 2025):", ""]
        L += tabla_md([(f"{x.valor_subgrupo}", x.categoria, mil(x.contratos), fmt(x.pct_contratos), fmt(x.pct_valor), fmt(x.mediana)) for x in t.itertuples()], ["Subgrupo", titulo, "Contratos", "% contratos", "% valor", "Mediana"]) + [""]
    L += ["### P5. Concordancia con el HCPC de D98 (4.992 contratos)", "", f"ARI entre Segmento y los 8 grupos de D98 (no reportados = una categoría) = **{fmt(p5['ari'], 3)}** (n = {mil(p5['n'])}). Sin umbral: por debajo de 0,5 los dos métodos no coinciden como particiones.", ""]
    c = r["p5_cruce"]
    L += tabla_md([(i, *[int(x) for x in f.values]) for i, f in c.iterrows()], ["Segmento", *c.columns]) + [""]
    L += ["## 3. Lo que no se sostiene", ""] + ([f"- {x}" for x in nosost] if nosost else ["- Ningún criterio con umbral falló."]) + [""]
    L.append(estado)
    return L


def guardar_csv(r):
    COPIA.mkdir(parents=True, exist_ok=True)
    p1 = r["p1"]
    kw = pd.DataFrame([{"dimension": d, **p1[d]["kw"]} for d in p1]).drop(columns=[])
    dep = pd.DataFrame([{"dimension": d, **p1[d]["dep"]} for d in p1])
    tablas = {"descriptiva_comprador": r["desc_comprador"].join(r["ic"]["comprador"]), "descriptiva_segmento": r["desc_segmento"].join(r["ic"]["segmento"]),
              "p1_valor_kruskal_wallis": kw, "p1_departamento": dep, "p1_valor_dunn_comprador": p1["comprador"]["dunn"], "p1_valor_dunn_segmento": p1["segmento"]["dunn"],
              "p1_proveedores_comprador": p1["comprador"]["proveedores"], "p2_orden_reglas": r["p2_tabla"], "p3_sensibilidad_sin_1pct_mayor": r["p3_tabla"],
              "p4_segmento_plataforma_periodo": r["p4_segmento"], "p4_comprador_plataforma_periodo": r["p4_comprador"],
              "p4_fuente_x_segmento": pd.DataFrame([{k: v for k, v in r["p4"].items() if k not in ("top3",)} | {"top3": json_top3(r["p4"]["top3"])}]),
              "p5_ari": pd.DataFrame([r["p5"]]), "p5_cruce_segmento_grupo": r["p5_cruce"], "independencia_comprador_objeto": r["independencia"]}
    for nombre, t in tablas.items():
        indice = t.index.name is not None or nombre.startswith(("descriptiva", "p3", "p5_cruce"))
        t.to_csv(DESTINO / f"segmentacion_{nombre}.csv", index=indice, encoding="utf-8-sig")
        shutil.copy(DESTINO / f"segmentacion_{nombre}.csv", COPIA / f"{nombre}.csv")


def json_top3(top3):
    return " | ".join(f"{f}: {', '.join(s)}" for f, s in top3.items())


def escribir(lineas):
    INFORME.write_text(chr(10).join(lineas) + chr(10), encoding="utf-8")


def cerrar(n_pruebas):
    t = INFORME.read_text(encoding="utf-8").rstrip(chr(10)).split(chr(10))
    t[-1] = f"ESTADO: TERMINADO — {datetime.now():%Y-%m-%d %H:%M} — pruebas: {n_pruebas} pasan"
    escribir(t)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cerrar", type=int, help="número de pruebas que pasan; reemplaza la última línea por ESTADO: TERMINADO")
    a = p.parse_args()
    if a.cerrar is not None:
        cerrar(a.cerrar)
        return 0
    try:
        r = calcular()
        guardar_csv(r)
        escribir(informe(r, "ESTADO: BLOQUEADO — pruebas pendientes de correr"))
        print(INFORME)
        return 0
    except Exception as e:
        traza = traceback.format_exc().strip().splitlines()[-1]
        escribir(["# Segmentación por reglas del mercado funerario (D109)", "", "La corrida no terminó.", "", f"ESTADO: BLOQUEADO — {type(e).__name__}: {str(e)[:200]} ({traza[:120]})"])
        raise


if __name__ == "__main__":
    sys.exit(main())
