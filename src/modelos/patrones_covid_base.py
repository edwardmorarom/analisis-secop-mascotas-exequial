"""Serie mensual de fallecidos por COVID-19 (INS, gt2j-8ykr) a partir de la respuesta agregada guardada en data/raw/covid (D99)."""
import numpy as np
import pandas as pd

from src.etl.comun import cargar_config, ruta

MESES = pd.period_range("2020-01", "2025-12", freq="M")


def serie_mensual():
    config = cargar_config()
    archivos = sorted((ruta(config, "raw") / "covid").glob("ins_covid_fallecidos_mes_*.jsonl"))
    d = pd.read_json(archivos[-1], lines=True, dtype=False)
    d["fallecidos"] = d["fallecidos"].astype(int)
    m = d.groupby("mes")["fallecidos"].sum()
    m.index = pd.PeriodIndex(m.index, freq="M")
    return m.reindex(MESES, fill_value=0), d


def main():
    m, d = serie_mensual()
    p75 = float(np.percentile(m.to_numpy(), 75))
    out = pd.DataFrame({"mes_txt": m.index.strftime("%Y-%m"), "fallecidos": m.to_numpy()})
    out["log1p_fallecidos"] = np.log1p(out["fallecidos"])
    out["sobre_p75"] = (out["fallecidos"] > p75).astype(int)
    destino = ruta(config := cargar_config(), "processed") / "resultados_secop" / "patrones" / "covid_muertes_mensual.csv"
    out.to_csv(destino, index=False)
    print(destino)
    print(f"meses: {len(out)} | meses con 0 (sin muertes registradas): {int((out['fallecidos'] == 0).sum())} | total: {int(out['fallecidos'].sum())} | p75: {p75:.1f} | meses sobre el p75: {int(out['sobre_p75'].sum())}")
    print("meses sobre el p75:", out.loc[out["sobre_p75"] == 1, "mes_txt"].tolist())
    print("departamentos:", d["departamento"].nunique(), "| último mes con muertes:", m[m > 0].index.max(), "| pico:", m.idxmax(), int(m.max()))


if __name__ == "__main__":
    main()
