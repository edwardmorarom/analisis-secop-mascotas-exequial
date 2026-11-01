import pandas as pd

from src.etl.comun import cargar_config, ruta
from src.modelos.muestra_secop import subestrato
from src.modelos.verificar_semillas import sha256, sortear

NOMBRE = "marco_muestra_400.parquet"


def main():
    config = cargar_config()
    interim, procesado = ruta(config, "interim"), ruta(config, "processed")
    a = pd.concat([pd.read_parquet(interim / f"{n}_senales.parquet") for n in ("secop1", "secop2")], ignore_index=True)
    a["subestrato"] = a.apply(subestrato, axis=1)
    marco = a[~((a["fuente"] == "secop1") & (a["anio"] >= 2023))].reset_index(drop=True)
    destino = procesado / NOMBRE
    marco.to_parquet(destino, index=False)
    huella = sha256(destino)
    (procesado / (NOMBRE + ".sha256")).write_text(f"{huella}  {NOMBRE}\n", encoding="utf-8")
    original = pd.read_parquet(procesado / "muestra_secop_maestra.parquet")[["id_muestra", "fuente", "llave"]]
    r = sortear(pd.read_parquet(destino), config["seed"])
    iguales = r.merge(original, on=["id_muestra", "fuente", "llave"]).shape[0]
    print(f"{NOMBRE}: {len(marco):,} filas; SHA-256 {huella}; el sorteo desde la copia reproduce {iguales}/400")


if __name__ == "__main__":
    main()
