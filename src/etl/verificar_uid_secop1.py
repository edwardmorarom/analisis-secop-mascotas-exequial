import pandas as pd

from src.etl.comun import cargar_config, ruta
from src.etl.descargar_secop1 import DATASET, where_secop1
from src.etl.socrata import consultar

SELECT = ("uid, count(*) as n, min(cuantia_contrato) as cmin, max(cuantia_contrato) as cmax, "
          "min(valor_contrato_con_adiciones) as amin, max(valor_contrato_con_adiciones) as amax, "
          "min(fecha_de_firma_del_contrato) as fmin, max(fecha_de_firma_del_contrato) as fmax")


def main():
    config = cargar_config()
    where = where_secop1(config, ["Celebrado", "Liquidado", "Terminado sin Liquidar"])
    filas = consultar(config["secop"]["dominio"], DATASET, {
        "$select": SELECT, "$where": where, "$group": "uid",
        "$having": "count(*)>1", "$order": "uid", "$limit": 50000})
    d = pd.DataFrame(filas)
    for k in ("n", "cmin", "cmax", "amin", "amax"):
        d[k] = pd.to_numeric(d[k])
    d["dif_cuantia"] = d.cmin != d.cmax
    d["dif_adiciones"] = d.amin.fillna(-1) != d.amax.fillna(-1)
    d["dif_fecha"] = d.fmin != d.fmax
    d["alguna"] = d[["dif_cuantia", "dif_adiciones", "dif_fecha"]].any(axis=1)
    d.to_parquet(ruta(config, "interim") / "secop1_uid_repetidos.parquet", index=False)
    print(f"uid con más de una fila: {len(d)}; filas sobrantes: {int((d.n - 1).sum())}")
    print(d[["dif_cuantia", "dif_adiciones", "dif_fecha", "alguna"]].sum().to_string())


if __name__ == "__main__":
    main()
