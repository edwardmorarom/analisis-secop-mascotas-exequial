import numpy as np
import pandas as pd


def contar(prestadores):
    """Prestadores por municipio: `sin_mixto` solo cuenta `prestador_mascotas`; `con_mixto` suma las funerarias de personas con servicio para mascotas."""
    p = prestadores[prestadores["ambito"].eq("mascotas") | prestadores["ambito"].isna()]
    p = p.drop_duplicates("id_prestador" if "id_prestador" in p else "id_fuente")
    g = p.groupby("cod_divipola")["clase"]
    return pd.DataFrame({"prestadores_sin_mixto": g.apply(lambda c: int((c == "prestador_mascotas").sum())),
                         "prestadores_con_mixto": g.apply(lambda c: int(c.isin(["prestador_mascotas", "mixto"]).sum()))})


def por_cien_mil(n, denominador):
    return pd.Series(np.where(denominador > 0, n / denominador * 100_000, np.nan), index=n.index)


def tabla_oferta(prestadores, panel, anio):
    """Una fila por municipio del panel en `anio`: prestadores con y sin mixtos, por 100.000 habitantes (DANE) y por 100.000 perros vacunados (MinSalud)."""
    base = panel[panel["anio"] == anio][["cod_divipola", "pob_dane", "vacunados_perros"]].drop_duplicates("cod_divipola")
    t = base.merge(contar(prestadores), left_on="cod_divipola", right_index=True, how="left")
    for c in ("prestadores_sin_mixto", "prestadores_con_mixto"):
        t[c] = t[c].fillna(0).astype(int)
    for variante in ("sin_mixto", "con_mixto"):
        n = t[f"prestadores_{variante}"]
        t[f"por_100mil_hab_{variante}"] = por_cien_mil(n, t["pob_dane"])
        t[f"por_100mil_perros_vacunados_{variante}"] = por_cien_mil(n, t["vacunados_perros"])
    t.insert(1, "anio", anio)
    return t
