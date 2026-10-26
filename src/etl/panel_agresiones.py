import numpy as np
import pandas as pd

from src.etl.comun import cargar_config, ruta

DENOMINADOR_OTRO_ANIO = {2022: 2023, 2025: 2024}
COLUMNAS_PANEL = ["cod_divipola", "anio", "poblacion_perros", "poblacion_gatos", "vacunados_perros", "metodo_estimacion",
                  "marca_inconsistencia", "pagina", "fuente"]


def construir(config):
    interim, procesado = ruta(config, "interim"), ruta(config, "processed")
    ins = pd.read_parquet(interim / "ins_agresiones_municipal.parquet")
    ins = ins[ins["cod_divipola"].notna()].rename(columns={"pagina": "pagina_ins", "archivo": "archivo_ins"})
    assert not ins.duplicated(["cod_divipola", "anio"]).any(), "(cod_divipola, anio) repetido en el INS"
    panel = pd.read_parquet(procesado / "panel_minsalud_municipal.parquet")
    panel = panel[panel["cod_divipola"].notna()]
    por_anio = panel.drop_duplicates(["cod_divipola", "anio"])[COLUMNAS_PANEL].rename(
        columns={"pagina": "pagina_minsalud", "fuente": "archivo_minsalud", "anio": "anio_perros"})
    ins["anio_perros"] = ins["anio"].map(lambda a: a if a in (2023, 2024) else DENOMINADOR_OTRO_ANIO.get(a))
    out = ins.merge(por_anio, on=["cod_divipola", "anio_perros"], how="left", validate="many_to_one")
    out["denominador_otro_anio"] = (out["anio"] != out["anio_perros"]).astype(int)
    perros = out["poblacion_perros"].where(out["poblacion_perros"] > 0)
    out["agresiones_x1000_perros"] = out["casos"] / perros * 1000
    out["agresiones_x1000_vacunados"] = out["casos"] / out["vacunados_perros"].where(out["vacunados_perros"] > 0) * 1000
    out["poblacion_perros_imputacion"] = out["metodo_estimacion"].fillna("sin_dato_minsalud")
    return out


def main():
    config = cargar_config()
    out = construir(config)
    out.to_parquet(ruta(config, "processed") / "panel_agresiones.parquet", index=False)
    pd.set_option("display.width", 200)
    print(out.groupby("anio").agg(municipios=("cod_divipola", "size"), con_perros=("agresiones_x1000_perros", "count"),
                                  mediana=("agresiones_x1000_perros", "median"), p90=("agresiones_x1000_perros", lambda s: s.quantile(.9)),
                                  mayor_de_1000=("agresiones_x1000_perros", lambda s: (s > 1000).sum())).round(1).to_string())


if __name__ == "__main__":
    main()
