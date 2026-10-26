import re

import pandas as pd

from src.etl.comun import cargar_config, ruta
from src.etl.descargar_secop1 import DATASET, where_secop1
from src.etl.seudonimo import clave, seudonimo
from src.etl.socrata import consultar, contar

JURIDICA = "Nit de Persona Jurídica"


def main():
    config = cargar_config()
    dom, pagina = config["secop"]["dominio"], config["secop"]["pagina"]
    where = where_secop1(config, ["Celebrado", "Liquidado", "Terminado sin Liquidar"])
    total, offset, filas = contar(dom, DATASET, where), 0, []
    while offset < total:
        lote = consultar(dom, DATASET, {
            "$select": "uid, tipo_identifi_del_contratista, identificacion_del_contratista",
            "$where": where, "$order": "uid", "$limit": pagina, "$offset": offset})
        filas += lote
        offset += len(lote)
        if not lote:
            break
    df = pd.DataFrame(filas).drop_duplicates("uid", keep="first")
    llave = clave()
    natural = df["tipo_identifi_del_contratista"].fillna("") != JURIDICA
    documento = df["identificacion_del_contratista"].fillna("").map(lambda t: re.sub(r"\D", "", t))
    df["contratista_persona_natural"] = natural
    df["contratista_id"] = [
        seudonimo("secop1", d, llave) if n and d else (d if not n else None) for n, d in zip(natural, documento)]
    df["contratista_id"] = df["contratista_id"].where(~natural | documento.ne(""), None)
    salida = df[["uid", "tipo_identifi_del_contratista", "contratista_persona_natural", "contratista_id"]]
    destino = ruta(config, "interim") / "secop1_contratistas.parquet"
    salida.to_parquet(destino, index=False)
    print(f"{len(salida):,} uid; personas naturales: {int(natural.sum()):,}; sin documento: {int((natural & documento.eq('')).sum())}; "
          f"seudónimos distintos: {salida.loc[natural, 'contratista_id'].nunique():,}")


if __name__ == "__main__":
    main()
