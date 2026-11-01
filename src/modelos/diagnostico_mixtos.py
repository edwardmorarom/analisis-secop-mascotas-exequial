import re

import pandas as pd

from src.etl.anonimizar import anonimizar
from src.etl.comun import cargar_config, ruta
from src.modelos.mercado_patrones import indicadores, normalizar_texto

FRASE_FUNERARIA = re.compile(r"[^;.]*(FUNERA|EXEQU|INHUMA|CREMACI|SEPELIO)[^;.]*", re.I)


def frase_funeraria(texto):
    t = normalizar_texto(texto)
    trozos = [m.group(0).strip() for m in FRASE_FUNERARIA.finditer(t)]
    return " | ".join(dict.fromkeys(trozos))[:260]


def tabla_mixtos(config):
    procesado = ruta(config, "processed")
    m = pd.read_parquet(procesado / "top_valor_maestra.parquet")
    e = pd.read_excel(procesado.parent.parent / "docs" / "revision_f4" / "top_valor.xlsx", sheet_name="Etiquetado", dtype=str)[["id_muestra", "etiqueta", "notas"]]
    u = pd.read_parquet(procesado / "resultados_secop" / "universo_mercado.parquet")[["fuente", "llave", "entidad", "modalidad", "tipo_contrato", "objeto"]]
    d = m.merge(e, on="id_muestra").merge(u, on=["fuente", "llave"])
    d = d[d["etiqueta"] == "mixto"].sort_values("valor_constante_2025", ascending=False).reset_index(drop=True)
    d["valor_mm_2025"] = d["valor_constante_2025"] / 1e9
    d["valor_mm_corriente"] = d["valor"] / 1e9
    d["parte_funeraria"] = d["objeto"].map(frase_funeraria)
    ind = pd.DataFrame([indicadores(o) for o in d["objeto"]])
    d["componentes_detectados"] = ind.apply(lambda r: ", ".join(k.replace("incluye_", "") for k, v in r.items() if v), axis=1)
    d["objeto_anonimizado"] = d["objeto"].map(anonimizar)
    return d


def main():
    config = cargar_config()
    d = tabla_mixtos(config)
    pd.set_option("display.width", 250, "display.max_colwidth", 140)
    print(d[["id_muestra", "anio", "valor_mm_2025", "entidad", "modalidad", "componentes_detectados", "parte_funeraria"]].round(2).to_string(index=False))
    d.drop(columns=["objeto"]).to_csv(ruta(config, "processed") / "resultados_secop" / "top_valor_mixtos.csv", index=False, encoding="utf-8-sig")
    gran = d.iloc[0]
    u = pd.read_parquet(ruta(config, "processed") / "resultados_secop" / "universo_mercado.parquet")
    est = pd.read_csv(ruta(config, "processed") / "resultados_secop" / "estimador_diferencia.csv")
    est = est[est["con_censo"] & (est["mixto"] == "con mixto")].set_index("modelo")
    v = gran["valor_constante_2025"]
    print(f"\nContrato mayor: {gran['id_muestra']} ({gran['llave']}), {v / 1e9:.2f} miles de millones de 2025")
    for modelo in ("tfidf", "e5"):
        clase = u[f"pred_{modelo}"]
        total = u.loc[clase.isin(["funerario", "mixto"]), "valor_constante_2025"].sum()
        e = est.loc[modelo]
        print(f"{modelo}: total con mixto con la jerarquía {total / 1e9:.1f} -> {(total - v) / 1e9:.1f}; "
              f"estimador {e['estimador_diferencia'] / 1e9:.1f} (IC {e['ic95_bajo'] / 1e9:.1f} a {e['ic95_alto'] / 1e9:.1f}) -> "
              f"{(e['estimador_diferencia'] - v) / 1e9:.1f} (IC {(e['ic95_bajo'] - v) / 1e9:.1f} a {(e['ic95_alto'] - v) / 1e9:.1f})")
        sin = u[~((u["fuente"] == gran["fuente"]) & (u["llave"] == gran["llave"]))]
        serie = sin[sin[f"pred_{modelo}"].isin(["funerario", "mixto"])].groupby("anio")["valor_constante_2025"].sum() / 1e9
        print("   serie anual sin ese contrato:", serie.round(1).to_dict())


if __name__ == "__main__":
    main()
