import sys

import pandas as pd
from sklearn.metrics import adjusted_rand_score

from src.etl.comun import RAIZ
from src.modelos.grupos_hcpc import COLORES, MARCA_VALIDACION, PATRONES
from src.modelos.validacion_grupos import GRUPOS_CLAVE, MIN_CONTRATOS_MAPA, calcular, correr_r, lectura_v

GRAFICOS = RAIZ / "docs/resultados/graficos"


def pf(p):
    return "< 0,001" if p < 0.001 else f"{p:.3f}".replace(".", ",")


def fmt(x, decimales=1):
    return f"{x:,.{decimales}f}".replace(",", "#").replace(".", ",").replace("#", ".")


def estilo(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e8e7e2", lw=0.8)
    ax.set_facecolor("#fcfcfb")


def grafico_inercia_silueta(r, destino):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    n = r["numero"]
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4), facecolor="#fcfcfb")
    g = n["gan"].head(20)
    a.plot(g["de_k_a_k_mas_1"], g["ganancia"], color="#2a78d6", lw=2, marker="o", ms=6)
    a.axvline(10.5, color="#c9c8c2", lw=1, ls="--")
    a.annotate("11 grupos", (10.5, g["ganancia"].max() * 0.9), xytext=(4, 0), textcoords="offset points", fontsize=9, color="#52514e")
    a.set(xlabel="Paso de k a k + 1 grupos", ylabel="Ganancia de inercia (proporción de la inercia total)", title="Ganancia de inercia de HCPC", xticks=range(1, 21, 2))
    b.plot(n["sil"]["k"], n["sil"]["silueta"], color="#2a78d6", lw=2, marker="o", ms=6)
    b.set(xlabel="Número de grupos (k)", ylabel="Silueta media (coordenadas del ACM)", title="Silueta por número de grupos", xticks=range(4, 13))
    for ax in (a, b):
        estilo(ax)
    fig.tight_layout()
    fig.savefig(destino, dpi=140)
    plt.close(fig)


def grafico_mapa(r, destino):
    import geopandas as gpd
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    dom = r["territorio"]["dominante"].set_index("cod_dpto")
    m = gpd.read_file(RAIZ / "data/raw/dane/mgn/MGN_ADM_MPIO_GRAFICO.shp")
    m["dpto_ccdgo"] = m["dpto_ccdgo"].astype(str).str.zfill(2)
    dep = m.dissolve(by="dpto_ccdgo")
    color = {f"Grupo {i}": c for i, c in enumerate(COLORES, 1)}
    fig, ax = plt.subplots(figsize=(7.5, 8.5), facecolor="#fcfcfb")
    for cod, fila in dep.iterrows():
        serie = gpd.GeoSeries([fila.geometry])
        if cod not in dom.index:
            serie.plot(ax=ax, facecolor="#e8e7e2", edgecolor="white", linewidth=0.6)
            continue
        x = dom.loc[cod]
        pocos = x["total"] < MIN_CONTRATOS_MAPA
        serie.plot(ax=ax, facecolor=color[x["grupo"]], edgecolor="white", linewidth=0.6, alpha=0.55 if pocos else 1, hatch="///" if pocos else None)
        c = fila.geometry.representative_point()
        ax.annotate(x["grupo"].split()[1], (c.x, c.y), ha="center", va="center", fontsize=8, color="#0b0b0b", fontweight="bold")
    presentes = sorted(dom["grupo"].unique())
    ax.legend(handles=[Patch(facecolor=color[g], label=g) for g in presentes] + [Patch(facecolor="#fcfcfb", edgecolor="#52514e", hatch="///", label=f"menos de {MIN_CONTRATOS_MAPA} contratos")],
              loc="lower left", frameon=False, fontsize=9, title="Grupo dominante")
    ax.set_xlim(-79.6, -66.4)
    ax.set_ylim(-4.4, 13.2)
    ax.set_axis_off()
    ax.set_title("Grupo con más contratos por departamento (ubicación de la entidad)", fontsize=11)
    fig.tight_layout()
    fig.savefig(destino, dpi=140)
    plt.close(fig)


def tabla_md(filas, cabecera):
    return ["| " + " | ".join(cabecera) + " |", "|" + "---|" * len(cabecera)] + ["| " + " | ".join(str(x) for x in fila) + " |" for fila in filas]


def tabla_cruce(cr):
    return tabla_md([(i,) + tuple(fmt(v, 0) if v else "·" for v in fila) for i, fila in zip(cr.index, cr.values)], ["D98"] + [str(c) for c in cr.columns])


def lista_residuos(fuertes, nivel):
    L = []
    for g, s in fuertes.groupby("grupo"):
        s = s.sort_values("residuo", ascending=False)
        sobre = ", ".join(f"{f[nivel]} (+{fmt(f['residuo'])})" for _, f in s[s["residuo"] > 0].iterrows())
        bajo = ", ".join(f"{f[nivel]} ({fmt(f['residuo'])})" for _, f in s[s["residuo"] < 0].iterrows())
        L.append(f"- **{g}.** Más de lo esperado: {sobre or 'ninguno'}. Menos de lo esperado: {bajo or 'ninguno'}.")
    return L


def guardar_csv(r):
    p, t, e, n = r["plataforma"], r["territorio"], r["externa"], r["numero"]
    p["v"].to_csv(PATRONES / "validacion_plataforma_v_cramer.csv", index=False)
    p["comp"].to_csv(PATRONES / "validacion_plataforma_comparacion.csv", index=False)
    for nombre, tabla in p["cruces"].items():
        tabla.to_csv(PATRONES / f"validacion_plataforma_cruce_{'k11' if 'k = 11' in nombre else 'k_auto'}.csv")
    for nivel in ["departamento", "region"]:
        t[nivel]["fuertes"].to_csv(PATRONES / f"validacion_territorio_{nivel}_residuos_mayores_3.csv", index=False)
        t[nivel]["residuos"].to_csv(PATRONES / f"validacion_territorio_{nivel}_residuos.csv")
    t["dominante"].to_csv(PATRONES / "validacion_territorio_grupo_dominante.csv", index=False)
    n["cruce"].to_csv(PATRONES / "validacion_pam_cruce.csv")
    e["pares"].to_csv(PATRONES / "validacion_dunn_holm.csv", index=False)
    e["tend"].to_csv(PATRONES / "validacion_tendencia_anual.csv", index=False)
    e["prop"].to_csv(PATRONES / "validacion_proporcion_por_anio.csv")
    r["proveedores"].to_csv(PATRONES / "validacion_proveedores.csv", index=False)


def seccion_plataforma(d, r):
    p = r["plataforma"]
    comp, pg = p["comp"], p["por_grupo"]
    s2 = pd.read_csv(PATRONES / "validacion_secop2_grupos.csv")
    igual = adjusted_rand_score(s2["grupo_auto"], s2["grupo_k11"]) == 1
    L = ["### 1. Plataforma (SECOP I frente a SECOP II)", "", "V de Cramér de grupo × fuente (8 grupos reportados):", ""]
    L += tabla_md([(x.periodo, fmt(x.n, 0), fmt(x.chi2), f"{x.gl}", pf(x.p), fmt(x.V, 2), x.lectura) for x in p["v"].itertuples()], ["Período", "Contratos", "χ²", "gl", "p", "V", "Lectura"])
    L += ["", "Porcentaje de SECOP II dentro de cada grupo: " + ", ".join(f"{g} {fmt(v)} %" for g, v in pg["secop2"].items()) + f" (en todo el conjunto, SECOP II es {fmt((d['fuente'] == 'secop2').mean() * 100)} % de los contratos).", "",
          f"Se repitió el ACM + HCPC con las mismas variables solo con los {fmt(comp.loc[0, 'contratos'], 0)} contratos de SECOP II (`validacion_grupos.R`). El HCPC sugirió {comp.loc[0, 'k_nuevo']} grupos" + (" y forzar 11 da la misma partición." if igual else "; forzar 11 da otra partición (segunda fila).") + " Comparación con los grupos de D98 restringidos a SECOP II:", ""]
    filas = [(comp.loc[i, "variante"], fmt(comp.loc[i, "ARI"], 3)) + tuple(f"{fmt(comp.loc[i, f'{g} jaccard'], 2)} ({fmt(comp.loc[i, f'{g} pct_d98'], 0)} %)" for g in GRUPOS_CLAVE) for i in [0, 1]]
    L += tabla_md(filas, ["Variante", "ARI"] + [f"{g}: Jaccard (% de su grupo de D98 en un solo grupo nuevo)" for g in GRUPOS_CLAVE])
    L += ["", f"Con la fuente como variable suplementaria el ACM no cambia (una suplementaria no entra en los ejes) y el HCPC reproduce D98 exactamente (ARI = {fmt(comp.loc[2, 'ARI'], 3)}); es una comprobación y no una prueba independiente.", "",
          "Tabla de cruce (filas: grupos de D98; columnas: grupos del HCPC solo con SECOP II, numeración arbitraria):", ""]
    L += tabla_cruce(p["cruces"]["SECOP II solo, k automático"])
    g2 = comp.loc[0, "Grupo 2 jaccard"]
    veredicto = "se sostiene" if p["reproducen"] else "no se sostiene"
    L += ["", f"**Conclusión 1: {veredicto} que los Grupos 1, 2 y 3 no son un efecto de la plataforma, con dos matices.** Con SECOP II solo el ARI es {fmt(comp.loc[0, 'ARI'], 2)} (umbral 0,5) y los Grupos 1 y 3 se recuperan casi enteros (Jaccard {fmt(comp.loc[0, 'Grupo 1 jaccard'], 2)} y {fmt(comp.loc[0, 'Grupo 3 jaccard'], 2)}). El Grupo 2 cumple el criterio por el ARI, pero su Jaccard es {fmt(g2, 2)}: casi todos sus contratos de SECOP II caen en un solo grupo nuevo que además absorbe contratos del Grupo 1, y solo {fmt(pg.loc['Grupo 2', 'secop2'])} % del Grupo 2 es de SECOP II, así que la evidencia sobre él es delgada. **Matiz:** la composición por plataforma es muy desigual (V = {fmt(p['v'].loc[0, 'V'], 2)}, asociación mediana, también en cada período): los Grupos 2 y 4 son más del 90 % de SECOP I y los Grupos 6 y 7 son mayoritariamente de SECOP II. Los grupos describen perfiles de compra que aparecen en las dos plataformas, pero la frecuencia de cada uno depende de la plataforma (en parte porque las columnas de cada fuente se homologaron, D98).", ""]
    return L


def seccion_territorio(r):
    t = r["territorio"]
    td, tr, dom = t["departamento"], t["region"], t["dominante"]
    deps = sorted(c for c in td["agrupada"].columns if c != "Otros")
    pocos = dom[dom["total"] < MIN_CONTRATOS_MAPA]
    L = ["### 2. Territorio", "", "Ubicación de la entidad (`departamento_entidad`); se excluyen los 7 contratos sin departamento definido. Los departamentos pequeños se agrupan en «Otros» hasta cumplir la regla de Cochran (D106).", ""]
    L += tabla_md([("Grupo × departamento", f"{td['agrupada'].shape[1]} ({td['bruta'].shape[1]} sin agrupar)", fmt(td["chi2"]["chi2"]), f"{td['chi2']['gl']}", pf(td["chi2"]["p"]), pf(td["p_perm"]), fmt(td["chi2"]["V"], 2), lectura_v(td["chi2"]["V"])),
                   ("Grupo × región", "5", fmt(tr["chi2"]["chi2"]), f"{tr['chi2']['gl']}", pf(tr["chi2"]["p"]), pf(tr["p_perm"]), fmt(tr["chi2"]["V"], 2), lectura_v(tr["chi2"]["V"]))],
                  ["Tabla", "Columnas", "χ²", "gl", "p (χ²)", "p (permutación, 9.999)", "V de Cramér", "Lectura"])
    L += ["", f"Departamentos que quedaron separados: {', '.join(deps)}; el resto está en «Otros». El valor p por permutación usa la tabla sin agrupar (el mínimo posible con 9.999 permutaciones es 0,0001).", "",
          f"**Residuos estandarizados ajustados con |residuo| > 3** (entre paréntesis): {len(td['fuertes'])} de {td['celdas']} combinaciones grupo × departamento y {len(tr['fuertes'])} de {tr['celdas']} grupo × región. Con tantas celdas, el umbral de Bonferroni de 0,05 sería |z| ≈ 3,5.", "", "*Por departamento:*", ""]
    L += lista_residuos(td["fuertes"], "departamento") + ["", "*Por región:*", ""] + lista_residuos(tr["fuertes"], "region")
    L += ["", "![Grupo dominante por departamento](graficos/validacion_mapa_grupo_dominante.png)", "",
          "El grupo dominante es el que reúne más contratos en las entidades del departamento; el número dentro de cada departamento es el del grupo. Departamentos por grupo dominante: " + ", ".join(f"{g} ({v})" for g, v in dom["grupo"].value_counts().items()) + f". Rayados: {len(pocos)} departamentos con menos de {MIN_CONTRATOS_MAPA} contratos, donde el dominante es poco informativo. San Andrés y Providencia (1 contrato, Grupo 4) queda fuera del recuadro.", "",
          f"**Conclusión 2: la asociación con el territorio se sostiene: mediana por departamento (V = {fmt(td['chi2']['V'], 2)}) y pequeña por región (V = {fmt(tr['chi2']['V'], 2)}); los grupos no son independientes del territorio.** Hay combinaciones extremas, como el Grupo 7 en Bogotá D.C., el Grupo 2 en Nariño o el Grupo 1 en Meta. Los contratos de una misma entidad no son independientes, así que parte del efecto puede deberse a entidades concretas y no a un patrón regional (no se midió cuántas entidades hay detrás de cada combinación); por eso conviene leer los residuos más grandes y no cada |residuo| > 3. En el mapa domina el Grupo 1 en casi todo el país y el Grupo 2 en el suroccidente y el Caribe.", ""]
    return L


def seccion_numero(r):
    n = r["numero"]
    gn = n["gan"].set_index("de_k_a_k_mas_1")["ganancia"]
    L = ["### 3. Número de grupos y método", "", "![Ganancia de inercia y silueta](graficos/validacion_inercia_silueta.png)", "",
         f"- **Ganancia de inercia (HCPC).** Pasar de 10 a 11 grupos aún gana {fmt(gn[10] * 100)} % de la inercia total; de 11 a 12, {fmt(gn[11] * 100)} %, y de 12 a 13, {fmt(gn[12] * 100)} %. Hay un quiebre después de 11 grupos, pero antes la ganancia ya había bajado de {fmt(gn[8] * 100)} % (8 a 9) a {fmt(gn[9] * 100)} %: el codo es moderado, no un corte nítido.",
         "- **Silueta (coordenadas del ACM, k = 4 a 12).** " + ", ".join(f"k = {int(x.k)}: {fmt(x.silueta, 2)}" for x in n["sil"].itertuples()) + ". La silueta **sube con k** (no tiene máximo en 11) y desde k = 7 el grupo más pequeño tiene un solo contrato. Con variables categóricas, muchos contratos tienen exactamente el mismo perfil y forman grupos compactos que inflan la silueta, así que no sirve para elegir k.",
         f"- **PAM sobre la distancia de Gower (k = 11).** ARI con D98 = {fmt(n['ari'], 2)} ({fmt(n['ari_reportados'], 2)} entre los contratos de los 8 grupos reportados). Mejores emparejamientos: " + "; ".join(f"{g}: Jaccard {fmt(m['jaccard'], 2)}, {fmt(m['pct_del_grupo_d98'], 0)} % del grupo en un grupo de PAM" for g, m in n["claves"].items()) + ".", "",
         "Tabla de cruce (filas: grupos de D98; columnas: grupos de PAM):", ""]
    L += tabla_cruce(n["cruce"])
    L += ["", f"**Conclusión 3: el número de grupos tiene un respaldo débil y la partición no se sostiene con otro método.** La ganancia de inercia da un quiebre moderado en 11, pero la silueta no discrimina y el ARI con PAM-Gower ({fmt(n['ari'], 2)}) queda por debajo del umbral de 0,5: con otro algoritmo los contratos se reparten distinto (el Grupo 3, por ejemplo, se dispersa). Los grupos son una descripción útil del ACM + HCPC (D98, D99), no una partición única de los datos; coincide con la conclusión exploratoria de D98.", ""]
    return L


def seccion_externa(r):
    e = r["externa"]
    kw, tr3, pr = e["kw"], e["traslado"], e["prop"]
    nosig = e["pares"][e["pares"]["p_holm"] >= 0.05]
    res = e["resumen"].set_index("grupo")["mediana"]
    tot2020 = int(e["cuenta"].loc[2020].sum())
    L = ["### 4. Validación externa: valor y tiempo", "",
         f"**Valor.** Kruskal-Wallis del log del valor en pesos constantes de 2025 (n = {fmt(kw['n'], 0)}; se excluyen {kw['excluidos']} contratos con valor no positivo, como en D98): H = {fmt(kw['H'])}, p {pf(kw['p'])}, ε² = {fmt(kw['epsilon2'], 3)} ({kw['lectura']}). El valor no entró al ACM (D98 no lo usa). Medianas: " + ", ".join(f"{g} {fmt(v / 1e6)} millones" for g, v in res.items()) + ".", "",
         f"Comparaciones de Dunn con corrección de Holm: {int((e['pares']['p_holm'] < 0.05).sum())} de {len(e['pares'])} pares difieren (p ajustado < 0,05). No difieren: " + "; ".join(f"{x.a} y {x.b} (p ajustado {pf(x.p_holm)})" for x in nosig.itertuples()) + ".", "",
         "**Proporción de cada grupo por año** (% de los contratos del año):", ""]
    L += tabla_md([(int(a),) + tuple(fmt(v) for v in fila) + (fmt(e["cuenta"].loc[a].sum(), 0),) for a, fila in zip(pr.index, pr.values)], ["Año"] + list(pr.columns) + ["Contratos"])
    L += ["", f"χ² de grupo × año: V = {fmt(e['chi2_anual']['V'], 2)} (p {pf(e['chi2_anual']['p'])}). χ² de tendencia (Cochran-Armitage, año como puntaje; p ajustado con Holm entre los 8 grupos), con todos los contratos y solo con SECOP II (SECOP I llega solo hasta 2022, así que la composición por plataforma cambia con los años):", ""]
    L += tabla_md([(x.grupo, f"{x.signo} {fmt(x.chi2_tendencia)}", pf(x.p_holm), f"{x.signo_solo_secop2} {fmt(x.chi2_tendencia_solo_secop2)}", pf(x.p_holm_solo_secop2)) for x in e["tend"].itertuples()],
                  ["Grupo", "χ² de tendencia (signo)", "p ajustado", "Solo SECOP II: χ² (signo)", "p ajustado"])
    sig_total = e["tend"][e["tend"]["p_holm"] < 0.05]
    sig_s2 = e["tend"][e["tend"]["p_holm_solo_secop2"] < 0.05]
    cambia = e["tend"][e["tend"]["signo"] != e["tend"]["signo_solo_secop2"]]
    L += ["", f"**Traslado (Grupo 3) en 2020.** {fmt(tr3['pct_2020'])} % de los {fmt(tot2020, 0)} contratos de 2020 frente a {fmt(tr3['pct_resto'])} % en 2021–2025 (razón de momios {fmt(tr3['odds'], 2)}; Fisher p = {pf(tr3['p'])}; residuo ajustado de 2020 = {fmt(tr3['residuo_2020'], 1)}). No hay 2019 en el conjunto, así que se compara con los años siguientes y no se puede atribuir a la pandemia.", "",
          f"**Conclusión 4: la separación por valor se sostiene (efecto {kw['lectura']}, ε² = {fmt(kw['epsilon2'], 3)}); las tendencias anuales no se sostienen como resultado robusto.** El Grupo 5 (mediana de {fmt(res['Grupo 5'] / 1e6, 0)} millones) se separa de todos los demás y los Grupos 6 y 4 son los de menor valor; los pares sin diferencia están listados arriba. En el tiempo, con todos los contratos {len(sig_total)} de los 8 grupos tienen tendencia significativa tras Holm, pero con solo SECOP II el signo cambia en {len(cambia)} grupos ({', '.join(cambia['grupo'])}) y solo {len(sig_s2)} queda significativo ({', '.join(sig_s2['grupo'])}, con signo {'contrario' if len(sig_s2) and sig_s2.iloc[0]['signo'] != sig_s2.iloc[0]['signo_solo_secop2'] else 'igual'} al del conjunto): la composición por plataforma explica gran parte. Sí se sostiene, como hecho descriptivo, que el traslado pesa más en 2020 que en los años siguientes ({fmt(tr3['pct_2020'])} % frente a {fmt(tr3['pct_resto'])} %), con un efecto modesto.", ""]
    return L


def seccion_proveedores(r):
    pv = r["proveedores"]
    x = pv.set_index("grupo")
    L = ["### 5. Proveedores", "", "Concentración sobre el valor (pesos constantes de 2025, contratos con valor positivo) por identificador del proveedor; solo agregados, sin identificar proveedores. «HHI uniforme» es el HHI que tendría el grupo si todos sus proveedores tuvieran la misma participación (10.000 dividido por el número de proveedores), para leer el HHI observado frente al mínimo posible.", ""]
    L += tabla_md([(g.grupo, fmt(g.contratos, 0), fmt(g.proveedores, 0), fmt(g.contratos_por_proveedor), fmt(g.HHI, 0), fmt(10000 / g.proveedores, 0), fmt(g.CR4) + " %") for g in pv.itertuples()],
                  ["Grupo", "Contratos", "Proveedores", "Contratos por proveedor", "HHI", "HHI uniforme", "CR4"])
    L += ["", "La fila «Todos» cuenta cada proveedor una vez aunque aparezca en varios grupos.", "",
          f"**Conclusión 5: los grupos sí se distinguen por la estructura de proveedores, con la salvedad del tamaño.** Los Grupos 1 y 2 son los más fragmentados (HHI de {fmt(x.loc['Grupo 1', 'HHI'], 0)} y {fmt(x.loc['Grupo 2', 'HHI'], 0)}; CR4 de {fmt(x.loc['Grupo 1', 'CR4'])} % y {fmt(x.loc['Grupo 2', 'CR4'])} %) y los Grupos 6 y 8 los más concentrados (HHI de {fmt(x.loc['Grupo 6', 'HHI'], 0)} y {fmt(x.loc['Grupo 8', 'HHI'], 0)}; CR4 de {fmt(x.loc['Grupo 6', 'CR4'])} % y {fmt(x.loc['Grupo 8', 'CR4'])} %, con {fmt(x.loc['Grupo 6', 'proveedores'], 0)} y {fmt(x.loc['Grupo 8', 'proveedores'], 0)} proveedores). Ningún grupo supera un HHI de 1.800 (concentración alta) y los Grupos 6 y 8 quedan en concentración moderada, muy por encima del HHI uniforme. No se puede separar del tamaño del grupo: con menos proveedores el HHI sube por construcción.", ""]
    return L


def seccion(d, r):
    L = [MARCA_VALIDACION, "", "## Validación de los grupos (D106, 2026-11-05)", "",
         "Todo lo de esta sección es validación: no cambia los grupos de D98 ni las etiquetas, y usa los mismos 4.992 contratos (los 8 grupos reportados suman 4.910). Semilla 2026 en lo que se muestrea (permutaciones) y 2034 en el ACM y el HCPC. Los criterios se fijaron en D106 antes de correr. Los valores p son orientativos: los contratos de una misma entidad no son independientes. Resultados completos en `data/processed/resultados_secop/patrones/validacion_*.csv` (no versionados).", ""]
    return L + seccion_plataforma(d, r) + seccion_territorio(r) + seccion_numero(r) + seccion_externa(r) + seccion_proveedores(r)


def escribir(d, r):
    GRAFICOS.mkdir(exist_ok=True)
    grafico_inercia_silueta(r, GRAFICOS / "validacion_inercia_silueta.png")
    grafico_mapa(r, GRAFICOS / "validacion_mapa_grupo_dominante.png")
    destino = RAIZ / "docs/resultados/grupos_hcpc.md"
    previo = destino.read_text(encoding="utf-8")
    corte = previo.index(MARCA_VALIDACION) if MARCA_VALIDACION in previo else len(previo)
    salto = chr(10)
    destino.write_text(previo[:corte].rstrip(salto) + salto + salto + salto.join(seccion(d, r)).rstrip(salto) + salto, encoding="utf-8")
    return destino


def main():
    if "--r" in sys.argv:
        correr_r()
    d, _, r = calcular()
    guardar_csv(r)
    print(escribir(d, r))


if __name__ == "__main__":
    main()
