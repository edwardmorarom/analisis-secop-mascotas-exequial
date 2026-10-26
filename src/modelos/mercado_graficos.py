import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.etl.comun import RAIZ, cargar_config, ruta

SUPERFICIE, TEXTO, TEXTO_2, REJILLA = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
AZUL, NARANJA, AGUA = "#2a78d6", "#eb6834", "#1baf7a"
CARPETA = RAIZ / "docs" / "resultados" / "graficos"
NOMBRES_FUENTE = {"secop1": "SECOP I", "secop2": "SECOP II"}
NOMBRES_SUBTIPO = {"inhumacion_NN_vulnerables": "Inhumación de NN o vulnerables", "plan_o_poliza_exequial": "Plan o póliza exequial",
                   "traslado": "Traslado", "cremacion": "Cremación", "cofres_y_bienes": "Cofres y bienes",
                   "operacion_cementerio": "Operación de cementerio", "disposicion_animales": "Disposición de animales", "otro": "Otro"}
NOMBRES_COMPONENTE = {"incluye_inhumacion_cremacion": "Inhumación o cremación (servicio directo)", "incluye_traslado": "Traslado",
                      "incluye_ataudes_bienes": "Ataúdes y bienes", "incluye_plan_exequial": "Plan, póliza o auxilio funerario",
                      "incluye_operacion_cementerio": "Operación de cementerio", "incluye_disposicion_animales": "Disposición de animales",
                      "incluye_atencion_vulnerables_NN": "Atención a vulnerables o NN"}
NOMBRES_MODALIDAD = {"contratacion_directa": "Contratación directa", "minima_cuantia": "Mínima cuantía", "seleccion_abreviada": "Selección abreviada",
                     "licitacion_concurso": "Licitación o concurso", "regimen_especial": "Régimen especial", "otra": "Otra"}


def estilo():
    plt.rcParams.update({"figure.facecolor": SUPERFICIE, "axes.facecolor": SUPERFICIE, "savefig.facecolor": SUPERFICIE,
                         "axes.edgecolor": REJILLA, "axes.labelcolor": TEXTO_2, "xtick.color": TEXTO_2, "ytick.color": TEXTO_2,
                         "text.color": TEXTO, "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlelocation": "left"})


def rejilla(ax, eje="y"):
    ax.grid(axis=eje, color=REJILLA, linewidth=0.8)
    ax.set_axisbelow(True)


def guardar(fig, nombre):
    CARPETA.mkdir(parents=True, exist_ok=True)
    fig.savefig(CARPETA / nombre, dpi=150, bbox_inches="tight")
    plt.close(fig)


def serie_anual(t):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    p = t.pivot(index="anio", columns="fuente", values="valor_constante_2025").fillna(0) / 1e9
    inferior = pd.Series(0.0, index=p.index)
    for fuente, color in (("secop1", AZUL), ("secop2", NARANJA)):
        if fuente in p:
            ax.bar(p.index, p[fuente], bottom=inferior, color=color, width=0.55, edgecolor=SUPERFICIE, linewidth=2, label=NOMBRES_FUENTE[fuente])
            inferior += p[fuente]
    for x, y in inferior.items():
        ax.text(x, y + 1, f"{y:.0f}", ha="center", color=TEXTO_2, fontsize=9)
    ax.set_title("Valor de los contratos funerarios por año (miles de millones de pesos de 2025)")
    ax.set_xlabel("Año de firma. SECOP I solo cubre 2020-2022: la caída de 2023 es un cambio de fuente.")
    rejilla(ax)
    ax.legend(frameon=False, loc="upper right")
    guardar(fig, "1_serie_anual_pesos_constantes.png")


def departamentos(t):
    t = t[t["poblacion_2025"] > 0].copy()
    t["valor_mm"] = t["valor_constante_x100mil_anual"] / 1e6
    top = t.sort_values("valor_mm", ascending=False).head(10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(top["departamento"].str.replace("ARCHIPIÉLAGO DE SAN ANDRÉS, PROVIDENCIA Y SANTA CATALINA", "SAN ANDRÉS Y PROVIDENCIA").str.title(), top["valor_mm"], color=AZUL, height=0.55)
    for y, v in enumerate(top["valor_mm"]):
        ax.text(v + 1, y, f"{v:.0f}", va="center", color=TEXTO_2, fontsize=9)
    ax.set_title("Diez departamentos con mayor valor por 100.000 habitantes (millones de pesos de 2025 por año)")
    ax.set_xlabel("Promedio anual 2020-2025 por sede de la entidad; los departamentos pequeños pesan mucho.")
    rejilla(ax, "x")
    guardar(fig, "2_departamentos_por_100mil.png")


def modalidad(t):
    t = t.sort_values("pct_valor")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    y = range(len(t))
    ax.barh([i + 0.2 for i in y], t["pct_valor"], height=0.35, color=AZUL, label="% del valor", edgecolor=SUPERFICIE, linewidth=2)
    ax.barh([i - 0.2 for i in y], t["pct_contratos"], height=0.35, color=NARANJA, label="% de los contratos", edgecolor=SUPERFICIE, linewidth=2)
    ax.set_yticks(list(y))
    ax.set_yticklabels([NOMBRES_MODALIDAD.get(m, m) for m in t["modalidad_grupo"]])
    ax.set_title("Modalidad de contratación (borrador)")
    ax.set_xlabel("Porcentaje del total 2020-2025")
    rejilla(ax, "x")
    ax.legend(frameon=False, loc="lower right")
    guardar(fig, "3_modalidad.png")


def componentes(t):
    t = t[t["componente"] != "ninguno_de_los_componentes"].sort_values("pct_valor")
    nombres = [NOMBRES_COMPONENTE.get(c, c) for c in t["componente"]]
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    y = range(len(t))
    ax.barh([i + 0.2 for i in y], t["pct_valor"], height=0.35, color=AZUL, label="% del valor", edgecolor=SUPERFICIE, linewidth=2)
    ax.barh([i - 0.2 for i in y], t["pct_contratos"], height=0.35, color=NARANJA, label="% de los contratos", edgecolor=SUPERFICIE, linewidth=2)
    ax.set_yticks(list(y))
    ax.set_yticklabels(nombres)
    ax.set_title("Contratos que incluyen cada componente (no excluyentes; borrador)")
    ax.set_xlabel("Porcentaje del total 2020-2025; un contrato puede incluir varios componentes")
    rejilla(ax, "x")
    ax.legend(frameon=False, loc="lower right")
    guardar(fig, "4_componentes.png")


def concentracion(anual, dep):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.2), gridspec_kw={"width_ratios": [1, 1.2]})
    a1.bar(anual["anio"], anual["HHI"], color=AZUL, width=0.55)
    for x, y in zip(anual["anio"], anual["HHI"]):
        a1.text(x, y + 20, f"{y:.0f}", ha="center", color=TEXTO_2, fontsize=9)
    a1.axhline(1500, color=TEXTO_2, linewidth=1, linestyle="--")
    a1.text(anual["anio"].min() - 0.4, 1530, "1.500", color=TEXTO_2, fontsize=8)
    a1.set_title("HHI nacional por año")
    a1.set_xlabel("Año de firma")
    rejilla(a1)
    con = dep[dep["proveedores"] >= 5]
    a2.hist(con["HHI"], bins=[0, 500, 1000, 1500, 2000, 2500, 3000, 3500], color=AZUL, edgecolor=SUPERFICIE, linewidth=2)
    a2.axvline(2500, color=TEXTO_2, linewidth=1, linestyle="--")
    a2.text(2520, a2.get_ylim()[1] * 0.9, "2.500", color=TEXTO_2, fontsize=8)
    a2.set_title("HHI por departamento (con 5 o más proveedores)")
    a2.set_xlabel(f"HHI 2020-2025 (n = {len(con)} departamentos)")
    a2.set_ylabel("Departamentos")
    rejilla(a2)
    fig.suptitle("Concentración de proveedores (borrador)", x=0.01, y=1.04, ha="left", fontweight="bold")
    guardar(fig, "5_concentracion_proveedores.png")


def main():
    estilo()
    s = ruta(cargar_config(), "processed") / "resultados_secop"
    serie_anual(pd.read_csv(s / "serie_anual_fuente.csv"))
    departamentos(pd.read_csv(s / "departamento_resumen.csv"))
    modalidad(pd.read_csv(s / "borrador_modalidad.csv"))
    componentes(pd.read_csv(s / "componentes.csv"))
    concentracion(pd.read_csv(s / "proveedores_hhi_cr4_anual.csv"), pd.read_csv(s / "proveedores_hhi_departamento.csv"))
    print("gráficos en", CARPETA)


if __name__ == "__main__":
    main()
