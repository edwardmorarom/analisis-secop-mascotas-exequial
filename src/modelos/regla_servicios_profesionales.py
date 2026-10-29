import re

import pandas as pd

from src.etl.anonimizar import anonimizar
from src.etl.comun import RAIZ, cargar_config
from src.modelos.sensibilidad_mixtos import universo

PERSONAL = re.compile(r"SERVICIOS? PROFESIONALES?|SERVICIOS? PERSONALES?|APOYO A LA GESTION|APOYAR LA GESTION|SERVICIOS? DE APOYO A LA GESTION")
FUNERARIO = re.compile(r"FUNERA|EXEQU|INHUMA|CREMACI|SEPELIO")
DESTINO = RAIZ / "docs" / "resultados" / "regla_servicios_profesionales.md"


def tabla(df, cols):
    filas = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    filas += ["| " + " | ".join(str(r[c]) for c in cols) + " |" for _, r in df.iterrows()]
    return "\n".join(filas)


def main():
    u = universo(cargar_config())
    patron = u["texto"].map(lambda t: bool(PERSONAL.search(t)) and bool(FUNERARIO.search(t)))
    x = u[patron & (u["pred_tfidf_modelo"] == "funerario")].copy()
    x["valor_mm"] = x["valor_constante_2025"] / 1e9
    con_etiqueta = x[x["etiqueta"].notna()]
    fmt = lambda v: f"{v:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")
    ej = x.sort_values("valor_mm", ascending=False).head(10).assign(
        valor=lambda t: t["valor_mm"].map(fmt), objeto_anon=lambda t: t["objeto"].map(lambda o: " ".join(anonimizar(o).split())[:240]),
        etiqueta_humana=lambda t: t["etiqueta"].fillna("sin etiqueta"))
    L = ["# Diagnóstico: servicios profesionales o de apoyo a la gestión con término funerario (D92)", "",
         "Solo diagnóstico, sin cambiar etiquetas. Generado por `python -m src.modelos.regla_servicios_profesionales`. Valores en miles de millones de pesos de 2025.", "",
         "Patrón: objeto con «servicios profesionales», «servicios personales», «apoyo a la gestión» o «apoyar la gestión» **y** una raíz funeraria (FUNERA, EXEQU, INHUMA, CREMACI, SEPELIO), sobre los 39.870 contratos candidatos de SECOP I y II.", "",
         f"- Contratos con el patrón: {int(patron.sum())} (valor {fmt(u.loc[patron, 'valor_constante_2025'].sum() / 1e9)}).",
         f"- De ellos, los que TF-IDF clasifica `funerario` (predicción del modelo, antes de la jerarquía de etiquetas): **{len(x)}**, valor **{fmt(x['valor_mm'].sum())}**.",
         f"- Con etiqueta humana: {len(con_etiqueta)} (" + ", ".join(f"{k} {v}" for k, v in con_etiqueta["etiqueta"].value_counts().items()) + ") " +
         "; por origen: " + ", ".join(f"{k} {v}" for k, v in con_etiqueta["origen"].value_counts().items()) + ".",
         f"- Sin etiqueta humana: {len(x) - len(con_etiqueta)} (valor {fmt(x.loc[x['etiqueta'].isna(), 'valor_mm'].sum())}).", "",
         "## 10 ejemplos (mayor valor; objeto anonimizado y recortado a 240 caracteres)", "",
         tabla(ej, ["fuente", "anio", "valor", "etiqueta_humana", "objeto_anon"]), ""]
    DESTINO.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[4:12]))


if __name__ == "__main__":
    main()
