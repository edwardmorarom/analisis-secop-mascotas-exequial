import numpy as np
import pandas as pd

from src.etl.anonimizar import anonimizar
from src.etl.comun import RAIZ, cargar_config
from src.modelos.perfil_variables import cargar, homologar

PATRONES = RAIZ / "data/processed/resultados_secop/patrones"
SEMILLA = 2026
UMBRAL_JACCARD = 0.75
UMBRAL_PCT = 1.0
UMBRAL_V = 2.0
MARCA_DIAGNOSTICO = "<!-- diagnostico-grupo5 -->"
COMPONENTES = ["inhumacion_cremacion", "traslado", "ataudes_bienes", "plan_exequial", "operacion_cementerio", "atencion_vulnerables_NN"]


def cargar_todo():
    f = homologar(cargar(cargar_config())).reset_index(drop=True)
    b = pd.read_csv(RAIZ / "data/processed/resultados_secop/patrones_base.csv", dtype={"entidad_id": str})
    g = pd.read_csv(PATRONES / "hcpc_d98_grupos.csv")["grupo"]
    if not (len(f) == len(b) == len(g)) or not (f["fuente"].values == b["fuente"].values).all():
        raise ValueError("las tablas no están alineadas fila a fila")
    d = pd.DataFrame({"grupo_hcpc": g, "fuente": b["fuente"], "anio": b["anio"], "valor": b["valor_constante_2025"],
                      "departamento": f["departamento_entidad"].astype("string"), "objeto": f["objeto"]})
    return d


def grupos_reportados(estab, tamanos):
    t = estab.merge(tamanos[["grupo", "pct"]], on="grupo")
    ok = t[(t["jaccard_medio"] >= UMBRAL_JACCARD) & (t["pct"] >= UMBRAL_PCT)].sort_values("contratos", ascending=False)
    ok["nombre"] = [f"Grupo {i}" for i in range(1, len(ok) + 1)]
    return ok.reset_index(drop=True)


def etiqueta(categoria):
    variable, nivel = categoria.split("=", 1)
    nivel = nivel[len(variable) + 1:] if nivel.startswith(variable + "_") else nivel
    if variable in COMPONENTES:
        return f"{variable}: {'sí' if nivel == 'si' else 'no'}"
    return f"{variable}: {nivel}"


def caracteristicas(vtest, grupo):
    v = vtest[(vtest["grupo"] == grupo) & (vtest["v_test"].abs() > UMBRAL_V)].copy()
    v["orden"] = v["v_test"].clip(-1e9, 1e9)
    v["categoria"] = v["categoria"].map(etiqueta)
    return v.sort_values("orden", ascending=False).rename(columns={
        "pct_del_grupo_en_la_categoria": "pct_grupo", "pct_global": "pct_total", "pct_de_la_categoria_en_el_grupo": "pct_categoria_en_grupo"})


def ficha(d, grupo, vtest, estab):
    s = d[d["grupo_hcpc"] == grupo]
    valor_total = d["valor"].sum()
    e = estab.set_index("grupo").loc[grupo]
    rng = np.random.default_rng(SEMILLA)
    ejemplos = [anonimizar(s["objeto"].iloc[i]) for i in sorted(rng.choice(len(s), size=min(3, len(s)), replace=False))]
    dep = s["departamento"].value_counts().head(3)
    return {"contratos": len(s), "pct_contratos": len(s) / len(d) * 100, "valor_suma": s["valor"].sum(), "valor_mediana": s["valor"].median(),
            "pct_valor": s["valor"].sum() / valor_total * 100, "caracteristicas": caracteristicas(vtest, grupo),
            "fuente": (s["fuente"].value_counts(normalize=True) * 100).round(1), "anio": (s["anio"].value_counts(normalize=True).sort_index() * 100).round(1),
            "departamentos": dep, "jaccard_medio": e["jaccard_medio"], "jaccard_p05": e["jaccard_p05"],
            "pct_disueltos": e["pct_remuestreos_disueltos"], "ejemplos": ejemplos}


COLORES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
GRIS = "#c9c8c2"
# (categoría característica, frase): las cifras salen de la prueba v; solo se nombran categorías con |v| > 2 sobrerrepresentadas
DESCRIPCIONES = {
    5: [("tipo_entidad: alcaldia_municipio", "alcaldías municipales"), ("tipo_contrato_hom: prestacion_servicios", "prestación de servicios"),
        ("ataudes_bienes: no", "sin ataúdes ni bienes"), ("inhumacion_cremacion: sí", "con inhumación o cremación"),
        ("modalidad_grupo: minima_cuantia", "mínima cuantía")],
    1: [("tipo_entidad: alcaldia_municipio", "alcaldías municipales"), ("tipo_contrato_hom: suministro", "suministro"),
        ("ataudes_bienes: sí", "con ataúdes o bienes"), ("modalidad_grupo: minima_cuantia", "mínima cuantía"),
        ("inhumacion_cremacion: no", "sin inhumación ni cremación")],
    4: [("traslado: sí", "con traslado"), ("tipo_entidad: gobernacion_departamento", "gobernaciones o departamentos"),
        ("modalidad_grupo: contratacion_directa", "contratación directa"), ("atencion_vulnerables_NN: no", "sin atención a población vulnerable o NN")],
    2: [("tipo_contrato_hom: compraventa", "compraventa"), ("ataudes_bienes: sí", "con ataúdes o bienes"),
        ("inhumacion_cremacion: no", "sin inhumación ni cremación"), ("modalidad_grupo: minima_cuantia", "mínima cuantía"),
        ("tipo_entidad: alcaldia_municipio", "alcaldías municipales")],
    3: [("modalidad_grupo: seleccion_abreviada", "selección abreviada"), ("inhumacion_cremacion: sí", "con inhumación o cremación"),
        ("tipo_entidad: otra_entidad", "otras entidades")],
    7: [("tipo_entidad: otra_entidad", "otras entidades"), ("orden_nivel: NACIONAL", "orden nacional"), ("plan_exequial: sí", "con plan exequial"),
        ("atencion_vulnerables_NN: no", "sin atención a población vulnerable o NN"), ("modalidad_grupo: regimen_especial", "régimen especial")],
    9: [("tipo_entidad: servicios_publicos_empresa", "empresas de servicios públicos"), ("atencion_vulnerables_NN: no", "sin atención a población vulnerable o NN"),
        ("modalidad_grupo: contratacion_directa", "contratación directa"), ("operacion_cementerio: sí", "con operación de cementerio"),
        ("modalidad_grupo: regimen_especial", "régimen especial")],
    10: [("tipo_entidad: salud_hospital_ese", "entidades de salud u hospitales"), ("modalidad_grupo: regimen_especial", "régimen especial"),
         ("atencion_vulnerables_NN: no", "sin atención a población vulnerable o NN"), ("tipo_contrato_hom: sin_equivalente", "tipo de contrato sin equivalente")],
}


def fmt(x, decimales=1):
    return f"{x:,.{decimales}f}".replace(",", "#").replace(".", ",").replace("#", ".")


def descripcion(grupo, carac):
    c = carac.set_index("categoria")
    partes = []
    for cat, frase in DESCRIPCIONES[grupo]:
        if cat not in c.index or c.loc[cat, "v_test"] <= UMBRAL_V:
            raise ValueError(f"{cat} no es característica sobrerrepresentada del grupo {grupo}")
        partes.append(f"{frase} ({fmt(c.loc[cat, 'pct_grupo'], 0)} % frente a {fmt(c.loc[cat, 'pct_total'], 0)} %)")
    return "Categorías sobrerrepresentadas (porcentaje del grupo frente al del total): " + ", ".join(partes) + "."


def grafico(d, reportados, destino):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    xy = pd.read_csv(PATRONES / "hcpc_d98_coordenadas.csv")
    inercia = pd.read_csv(PATRONES / "hcpc_d98_inercia.csv").set_index("dimension")["pct_varianza"]
    d = pd.concat([d[["grupo_hcpc"]], xy], axis=1).assign(x=lambda t: t["dim1"].round(6), y=lambda t: t["dim2"].round(6))
    puntos = d.groupby(["x", "y", "grupo_hcpc"]).size().reset_index(name="n")
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.edgecolor": "#52514e", "axes.labelcolor": "#52514e", "text.color": "#0b0b0b",
                         "xtick.color": "#52514e", "ytick.color": "#52514e"})
    fig, ejes = plt.subplots(2, 4, figsize=(15, 8), sharex=True, sharey=True, facecolor="#fcfcfb")
    for ax, (_, r), color in zip(ejes.ravel(), reportados.iterrows(), COLORES):
        ax.set_facecolor("#fcfcfb")
        otros = puntos[puntos["grupo_hcpc"] != r["grupo"]]
        propios = puntos[puntos["grupo_hcpc"] == r["grupo"]]
        ax.scatter(otros["x"], otros["y"], s=6 + otros["n"] ** 0.5 * 3, color=GRIS, alpha=0.35, linewidths=0)
        ax.scatter(propios["x"], propios["y"], s=14 + propios["n"] ** 0.5 * 9, color=color, edgecolors="#fcfcfb", linewidths=1.2, alpha=0.95)
        ax.set_title(f"{r['nombre']} · {int(r['contratos']):,} contratos".replace(",", "."), fontsize=11, loc="left")
        ax.grid(color="#e6e5e0", linewidth=0.6)
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
    for ax in ejes[1]:
        ax.set_xlabel(f"Eje 1 ({fmt(inercia[1])} % de la inercia)")
    for ax in ejes[:, 0]:
        ax.set_ylabel(f"Eje 2 ({fmt(inercia[2])} % de la inercia)")
    fig.suptitle("Plano factorial del ACM (ejes 1 y 2): cada panel resalta un grupo; el tamaño del círculo crece con los contratos con el mismo perfil",
                 fontsize=12, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    return puntos


def fv(v):
    return "∞" if v == np.inf else "−∞" if v == -np.inf else fmt(v)


def recortar(texto, n=180):
    t = " ".join(str(texto).split())
    return t if len(t) <= n else t[:n].rstrip() + "…"


def millones(x, decimales=0):
    return f"${fmt(x / 1e6, decimales)} millones"


def escribir(d, reportados, vtest, estab, tamanos):
    grafico_ruta = RAIZ / "docs/resultados/graficos/grupos_hcpc_plano_factorial.png"
    grafico(d, reportados, grafico_ruta)
    fichas = {r["grupo"]: ficha(d, r["grupo"], vtest, estab) for _, r in reportados.iterrows()}
    L = ["# Descripción de los grupos estables de HCPC (D99)", "",
         "> **Descripción exploratoria. Ningún modelo de clases latentes cumplió los supuestos (D97, D98), así que estos grupos describen el mercado y no son una tipología confirmada.**", "",
         "Estado: propuesta, pendiente de revisión de Edward. No se recalculó ningún resultado de D97 a D99; este documento solo describe lo que ya existe.", "",
         "## Cómo leerlo", "",
         f"- **Grupos:** los 11 de HCPC de D98 ({fmt(len(d), 0)} contratos de SECOP I y II, 2020 a 2025). Se describen los {len(reportados)} que cumplen el criterio de D99: Jaccard medio de bootstrap ≥ {fmt(UMBRAL_JACCARD, 2)} y al menos {UMBRAL_PCT:.0f} % de los contratos. Quedan fuera los grupos 6 (47 contratos), 8 (34) y 11 (1), todos por debajo del 1 %.",
         "- **Nombres:** «Grupo 1» a «Grupo 8» en orden de tamaño (nombres neutros). La tabla resumen da la equivalencia con el número de grupo de HCPC de D98.",
         "- **Categorías características:** prueba v de `FactoMineR` (`hcpc_d98_vtest.csv`), solo las de |v| > 2, ordenadas de mayor a menor v (las primeras están sobrerrepresentadas en el grupo y las últimas subrepresentadas). «∞» indica que la prueba es numéricamente infinita (p < 10⁻³⁰⁰): la categoría define al grupo. Las variables son las del ACM de D98: tipo de entidad, modalidad, tipo de contrato, orden, y los seis componentes (inhumación o cremación, traslado, ataúdes o bienes, plan exequial, operación de cementerio, atención a población vulnerable o NN).",
         "- **Porcentajes de la tabla de cada grupo:** «% del grupo» es el porcentaje de los contratos del grupo que tienen la categoría; «% del total» es el mismo porcentaje en los 4.992 contratos; «% de la categoría en el grupo» es qué parte de los contratos con esa categoría cae en el grupo.",
         "- **Valores:** pesos constantes de 2025 (IPC DANE). El porcentaje del valor es sobre el total de los 4.992 contratos.",
         "- **Plano factorial:** coordenadas del mismo ACM (variables y semilla de D98); solo se recuperaron las coordenadas de los contratos, sin correr el HCPC, y los porcentajes de inercia coinciden con `hcpc_d98_inercia.csv`.",
         "- **Ejemplos:** tres objetos por grupo elegidos al azar (semilla 2026), sin filtrar por tema, recortados a 180 caracteres y anonimizados (D15).", "",
         "## Tabla resumen", "",
         "| Grupo | Grupo HCPC (D98) | Contratos | % contratos | Valor total | Mediana | % del valor | Jaccard medio | Rasgos principales |", "|---|---|---|---|---|---|---|---|---|"]
    for _, r in reportados.iterrows():
        f = fichas[r["grupo"]]
        rasgos = "; ".join(frase for _, frase in DESCRIPCIONES[r["grupo"]][:3])
        L.append(f"| {r['nombre']} | {r['grupo']} | {fmt(f['contratos'], 0)} | {fmt(f['pct_contratos'])} % | {millones(f['valor_suma'])} | {millones(f['valor_mediana'], 1)} | {fmt(f['pct_valor'])} % | {fmt(f['jaccard_medio'], 2)} | {rasgos} |")
    tot = len(d)
    cub = sum(fichas[g]["contratos"] for g in fichas)
    L += ["", f"Los {len(reportados)} grupos suman {fmt(cub, 0)} de {fmt(tot, 0)} contratos ({fmt(cub / tot * 100)} %).", "",
          "## Plano factorial del ACM", "", "![Plano factorial del ACM, ejes 1 y 2, un panel por grupo](graficos/grupos_hcpc_plano_factorial.png)", "",
          "Cada panel resalta un grupo en su color y deja los demás contratos en gris. Muchos contratos comparten exactamente el mismo perfil de categorías, por lo que se dibujan como un solo círculo cuyo tamaño crece con el número de contratos. Los dos ejes retienen juntos el 21,8 % de la inercia: el plano es un resumen parcial, y grupos que se ven cercanos pueden separarse en otros ejes.", ""]
    for _, r in reportados.iterrows():
        f = fichas[r["grupo"]]
        c = f["caracteristicas"]
        L += [f"## {r['nombre']} (grupo {r['grupo']} de HCPC)", "", f"**Descripción.** {descripcion(r['grupo'], c)}", "",
              f"- **Tamaño:** {fmt(f['contratos'], 0)} contratos ({fmt(f['pct_contratos'])} % del total).",
              f"- **Valor:** suma {millones(f['valor_suma'])}; mediana {millones(f['valor_mediana'], 1)} ({fmt(f['pct_valor'])} % del valor total).",
              f"- **Estabilidad:** Jaccard medio {fmt(f['jaccard_medio'], 2)}; percentil 5 {fmt(f['jaccard_p05'], 2)}; el grupo se disuelve en {fmt(f['pct_disueltos'])} % de los remuestreos.",
              "- **Fuente:** " + ", ".join(f"{'SECOP I' if k == 'secop1' else 'SECOP II'} {fmt(v)} %" for k, v in f["fuente"].items()) + ".",
              "- **Año:** " + ", ".join(f"{k} {fmt(v)} %" for k, v in f["anio"].items()) + ".",
              "- **Departamentos con más contratos (ubicación de la entidad):** " + ", ".join(f"{k} ({v}, {fmt(v / f['contratos'] * 100)} %)" for k, v in f["departamentos"].items()) + ".", "",
              "| Categoría característica | % del grupo | % del total | % de la categoría en el grupo | v |", "|---|---|---|---|---|"]
        L += [f"| `{x.categoria}` | {fmt(x.pct_grupo)} | {fmt(x.pct_total)} | {fmt(x.pct_categoria_en_grupo)} | {fv(x.v_test)} |" for x in c.itertuples()]
        L += ["", "Objetos de ejemplo (azar, semilla 2026):", ""] + [f"{i}. {recortar(e)}" for i, e in enumerate(f["ejemplos"], 1)] + [""]
    destino = RAIZ / "docs/resultados/grupos_hcpc.md"
    previo = destino.read_text(encoding="utf-8") if destino.exists() else ""
    cola = "\n" + previo[previo.index(MARCA_DIAGNOSTICO):] if MARCA_DIAGNOSTICO in previo else ""
    destino.write_text("\n".join(L).rstrip() + "\n" + cola, encoding="utf-8")
    return destino


def main():
    d = cargar_todo()
    estab = pd.read_csv(PATRONES / "hcpc_d98_estabilidad.csv")
    tamanos = pd.read_csv(PATRONES / "hcpc_d98_tamanos.csv")
    vtest = pd.read_csv(PATRONES / "hcpc_d98_vtest.csv")
    reportados = grupos_reportados(estab, tamanos)
    if reportados["grupo"].tolist() != [5, 1, 4, 2, 3, 7, 9, 10]:
        raise ValueError("los grupos reportados no coinciden con los 8 de D99")
    print(escribir(d, reportados, vtest, estab, tamanos))


if __name__ == "__main__":
    main()
