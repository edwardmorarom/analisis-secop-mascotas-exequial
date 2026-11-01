import re

import pandas as pd

from src.etl.anonimizar import anonimizar
from src.etl.comun import cargar_config, ruta
from src.modelos import estimador_diferencia as ed
from src.modelos.etiquetas_humanas import construir
from src.modelos.mercado_patrones import indicadores, normalizar_texto

FUNERARIA = re.compile(r"ASISTENCIAS? FUNERARIAS?|GASTOS? FUNERARIOS?|AUXILIOS? FUNERARIOS?")
HUMANITARIA = re.compile(r"HUMANITARI|VICTIMAS|JUSTICIA TRANSICIONAL|VULNERABL|COVID")
TRASLADO_FUNERARIO = re.compile(r"MANEJO DE (CADAVERES|CUERPOS)|TRANSPORTE DE (CADAVER|CUERPO|RESTOS|DIFUNTO)|RECOLECCION DE (CADAVER|CUERPO)|(TRASLADO|TRANSPORTE|RECOLECCION|LEVANTAMIENTO).{0,40}(CADAVER|CUERPO|RESTOS|DIFUNTO|OCCISO)")
SERVICIO_FUNERARIO = re.compile(r"FUNERA|INHUMA|SEPELIO|EXEQU|SEPULT|EXHUMA|FUNEBRE|CREMACI|CADAVER|OCCISO|CEMENTERIO")
EMERGENCIA = re.compile(r"EMERGENCIA|URGENCIA|AMBULANCIA|PACIENTE|REFERENCIA")
M214 = ("secop2", "CO1.PCCNTR.2162002")


def universo(config):
    u, _, _ = ed.bloques(config)
    u = ed.subestratos(config, u)
    u = u.merge(construir(config)[["fuente", "llave", "etiqueta", "origen"]], on=["fuente", "llave"], how="left")
    u["texto"] = u["objeto"].map(normalizar_texto)
    return u


def humanitarios(u):
    return u[u["texto"].map(lambda t: bool(FUNERARIA.search(t)) and bool(HUMANITARIA.search(t)))]


def estimar_caso(config, excluir=(), censales=None):
    """Estimador de diferencia (TF-IDF, sin mixto) con contratos excluidos o con contratos añadidos al censo con la etiqueta dada."""
    original_bloques, original_construir = ed.bloques, ed.construir
    censales = censales or {}

    def bloques(c):
        u, d400, d30 = original_bloques(c)
        fuera = set(excluir) | set(censales)
        quitar = lambda d: d[[(f, l) not in fuera for f, l in zip(d["fuente"], d["llave"])]] if len(fuera) else d
        # los censales salen del marco muestral: se corrigen exactamente
        return u, quitar(d400), quitar(d30)

    def construir_(c):
        h = original_construir(c)
        h = h[[(f, l) not in set(excluir) for f, l in zip(h["fuente"], h["llave"])]]
        h = h[[(f, l) not in set(censales) for f, l in zip(h["fuente"], h["llave"])]]
        extra = pd.DataFrame([{"id_muestra": None, "etiqueta": e, "forense": "0", "fuente": f, "llave": l, "origen": "adicionales_d81"} for (f, l), e in censales.items()])
        return pd.concat([h, extra], ignore_index=True)

    def bloques_sin_excluidos(c):
        u, d400, d30 = bloques(c)
        if len(excluir):
            u = u[[(f, l) not in set(excluir) for f, l in zip(u["fuente"], u["llave"])]]
        return u, d400, d30

    ed.bloques, ed.construir = bloques_sin_excluidos, construir_
    try:
        t = ed.estimar(config, con_censo=True)
    finally:
        ed.bloques, ed.construir = original_bloques, original_construir
    return t[(t["modelo"] == "tfidf") & (t["mixto"] == "sin mixto")].iloc[0]


def solo_traslado(u):
    ind = pd.DataFrame([indicadores(o) for o in u["objeto"]], index=u.index)
    tr = ind["incluye_traslado"]
    solo = tr & ~u["texto"].map(lambda t: bool(TRASLADO_FUNERARIO.search(t))) & ~u["texto"].map(lambda t: bool(SERVICIO_FUNERARIO.search(t)))
    return tr, solo


def resumen_humanitarios(u, s):
    s = s.assign(valor_mm=s["valor_constante_2025"] / 1e9)
    por = lambda col: s.groupby(col, dropna=False).agg(contratos=("llave", "size"), valor_mm=("valor_mm", "sum"))
    return {"total": (len(s), s["valor_mm"].sum()), "estrato": por("subestrato"), "origen": por("origen"), "pred": por("pred_tfidf_modelo"),
            "etiqueta": por("etiqueta"), "fuente": por("fuente"), "anio": por("anio")}


def casos(config, u, s):
    llaves = list(zip(s["fuente"], s["llave"]))
    etiquetadas = {(f, l): e for f, l, e in zip(s["fuente"], s["llave"], s["etiqueta"]) if isinstance(e, str)}
    sin_etiqueta = [k for k in llaves if k not in etiquetadas]
    nombres = [("A. Con M214 (estimador publicado, D85)", {}),
               ("B. Sin M214 (se saca del marco y de la muestra)", {"excluir": [M214]}),
               ("C0. Humanitarios como estrato censal; sin etiqueta humana se supone no funerario (mixto)", {"censales": {**etiquetadas, **{k: "mixto" for k in sin_etiqueta}}}),
               ("C1. Humanitarios como estrato censal; sin etiqueta humana se supone funerario", {"censales": {**etiquetadas, **{k: "funerario" for k in sin_etiqueta}}})]
    filas = []
    for nombre, kw in nombres:
        r = estimar_caso(config, **kw)
        filas.append({"caso": nombre, "total_sin_corregir_mm": r["total_sin_corregir"] / 1e9, "estimador_mm": r["estimador_diferencia"] / 1e9,
                      "ic95_bajo_mm": r["ic95_bajo"] / 1e9, "ic95_alto_mm": r["ic95_alto"] / 1e9, "correccion_censo_mm": r["correccion_censo"] / 1e9,
                      "correccion_muestra_400_mm": r["correccion_muestra_400"] / 1e9})
    return pd.DataFrame(filas), len(etiquetadas), len(sin_etiqueta)


def tabla_md(df, cols, formato=None):
    formato = formato or {}
    lineas = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        lineas.append("| " + " | ".join(formato.get(c, str)(r[c]) for c in cols) + " |")
    return "\n".join(lineas)


def main():
    config = cargar_config()
    u = universo(config)
    s = humanitarios(u)
    r = resumen_humanitarios(u, s)
    t, n_et, n_sin = casos(config, u, s)
    tr, solo = solo_traslado(u)
    mm = lambda v: f"{v:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
    L = ["# Sensibilidad del mercado a los contratos mixtos (diagnóstico)", "",
         "Solo diagnóstico: no se registra ninguna decisión ni se cambia el estimador. Generado por `python -m src.modelos.sensibilidad_mixtos`. Valores en miles de millones de pesos de 2025 salvo que se indique.", "",
         "## 1. Ayuda humanitaria con componente funerario en todo el marco", "",
         "Marco: los 39.870 contratos candidatos de SECOP I y II, 2020–2025. Criterio: el objeto (sin tildes, en mayúsculas) contiene «asistencia(s) funeraria(s)», «gasto(s) funerario(s)» o «auxilio(s) funerario(s)» **y** alguno de «humanitari-», «víctimas», «justicia transicional», «vulnerable» o «COVID».", "",
         f"**{r['total'][0]} contratos, {mm(r['total'][1])} miles de millones.** Como son más de 80, **no se exportó** `mixtos_humanitarios.xlsx`.", ""]
    for titulo, k in (("Por estrato de la muestra", "estrato"), ("Por origen de la etiqueta humana (NaN = sin revisión humana)", "origen"),
                      ("Por predicción de TF-IDF (sin jerarquía de etiquetas)", "pred"), ("Por etiqueta humana", "etiqueta"), ("Por fuente", "fuente"), ("Por año", "anio")):
        d = r[k].reset_index()
        d.columns = ["grupo", "contratos", "valor_mm"]
        d["grupo"] = d["grupo"].map(lambda g: str(int(g)) if k == "anio" else str(g).replace("nan", "sin etiqueta"))
        L += [f"### {titulo}", "", tabla_md(d, ["grupo", "contratos", "valor_mm"], {"valor_mm": mm}), ""]
    L += [f"Con etiqueta humana: {n_et} contratos (en la muestra de 400: 10; en la revisión censal por valor: 10; en D81: 1). Sin etiqueta humana: {n_sin}.", "",
          "## 2. Estimador de diferencia (TF-IDF, sin mixto)", "",
          "El caso A reproduce el estimador publicado (D85). En B, M214 sale del marco y de la muestra (N y n de su estrato bajan en uno). En C, los 317 contratos salen de la muestra y del marco muestral y se corrigen exactamente como censo: con la etiqueta humana donde existe y, en los 296 sin etiqueta, con el supuesto indicado (C0 no funerario; C1 funerario). C0 y C1 son los dos extremos posibles; la etiqueta real de esos 296 la pondrá la revisión. M214 es uno de los 317, por lo que en C queda como censal con su etiqueta `mixto`.", "",
          tabla_md(t, ["caso", "total_sin_corregir_mm", "estimador_mm", "ic95_bajo_mm", "ic95_alto_mm", "correccion_censo_mm", "correccion_muestra_400_mm"], {c: mm for c in t.columns[1:]}), ""]
    ind = u[solo]
    mer = u["pred_tfidf"] == "funerario"
    L += ["## 3. Componente «traslado» activado sin servicio funerario", "",
          "`incluye_traslado` usa la expresión `TRASLADO|MANEJO DE (CADÁVERES|CUERPOS)|TRANSPORTE DE (CADÁVER|CUERPO|RESTOS|DIFUNTO)|RECOLECCIÓN DE (CADÁVER|CUERPO)`. Aquí se cuentan los contratos donde se activó solo por la palabra «traslado» (o «traslado y transporte» de otra cosa): sin una expresión de cadáver, cuerpo, restos, difunto u occiso cerca de «traslado/transporte/recolección/levantamiento» y sin las raíces FUNERA, INHUMA, SEPELIO, EXEQU, SEPULT, EXHUMA, FUNEBRE, CREMACI, CADAVER, OCCISO ni CEMENTERIO en el objeto.", "",
          f"- Contratos con `incluye_traslado` en el marco: {int(tr.sum())}. Solo por traslado sin servicio funerario: **{int(solo.sum())}** ({mm(ind['valor_constante_2025'].sum() / 1e9)} miles de millones); de ellos, {int((solo & u['texto'].map(lambda x: bool(EMERGENCIA.search(x)))).sum())} mencionan emergencia, urgencia, ambulancia, paciente o referencia.",
          f"- Entre los contratos que TF-IDF (con la jerarquía de etiquetas) marca `funerario`: {int((tr & mer).sum())} tienen traslado, de los cuales **{int((solo & mer).sum())}** lo tienen solo por esa vía; con `mixto` incluido, {int((tr & u['pred_tfidf'].isin(['funerario', 'mixto'])).sum())} y {int((solo & u['pred_tfidf'].isin(['funerario', 'mixto'])).sum())}.",
          f"- Clase de TF-IDF de los {int(solo.sum())}: " + ", ".join(f"{k} {v}" for k, v in ind["pred_tfidf"].value_counts().items()) + ".", "",
          "Los 5 que TF-IDF marca `funerario` sí tienen componente funerario (cofres o servicios mortuorios) que la raíz de servicio no recoge; el traslado va junto a bienes funerarios.", "", "### 10 ejemplos (los 5 que TF-IDF marca funerario y los 5 de mayor valor entre el resto; objeto anonimizado y recortado a 260 caracteres)", ""]
    ej = pd.concat([ind[ind["pred_tfidf"] == "funerario"].sort_values("valor_constante_2025", ascending=False).head(5),
                    ind[ind["pred_tfidf"] != "funerario"].sort_values("valor_constante_2025", ascending=False).head(5)])
    ej = ej.assign(valor_mm=ej["valor_constante_2025"] / 1e9, objeto_anon=ej["objeto"].map(lambda x: " ".join(anonimizar(x).split())[:260]), clase=ej["pred_tfidf"])
    ej["valor_mm"] = ej["valor_mm"].map(lambda v: f"{v:.3f}".replace(".", ","))
    L += [tabla_md(ej, ["fuente", "anio", "clase", "valor_mm", "objeto_anon"]), ""]
    destino = ruta(config, "processed").parent.parent / "docs" / "resultados" / "sensibilidad_mixtos.md"
    destino.write_text("\n".join(L), encoding="utf-8")
    t.to_csv(ruta(config, "processed") / "resultados_secop" / "sensibilidad_mixtos.csv", index=False, encoding="utf-8-sig")
    print(destino)


if __name__ == "__main__":
    main()
