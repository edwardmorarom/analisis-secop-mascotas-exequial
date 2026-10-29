import hashlib
import json

import numpy as np
import pandas as pd

from src.etl.comun import cargar_config, ruta
from src.modelos.muestra_secop import ASIGNACION, reparto, subestrato


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def sortear(a, semilla):
    """Réplica en memoria de `muestra_secop.main` (sin escribir nada)."""
    rng = np.random.default_rng(semilla)
    partes = []
    for nombre, n in ASIGNACION.items():
        est = a[a.subestrato == nombre]
        for (fuente, anio), k in reparto(est.groupby(["fuente", "anio"]).size(), n).items():
            if k:
                sub = est[(est.fuente == fuente) & (est.anio == anio)]
                partes.append(sub.sample(n=k, random_state=int(rng.integers(2**31))))
    m = pd.concat(partes).sample(frac=1, random_state=semilla).reset_index(drop=True)
    m.insert(0, "id_muestra", [f"M{i:03d}" for i in range(1, len(m) + 1)])
    return m[["id_muestra", "fuente", "llave"]]


def main():
    config = cargar_config()
    interim = ruta(config, "interim")
    archivos = {n: interim / f"{n}_senales.parquet" for n in ("secop1", "secop2")}
    for n, p in archivos.items():
        print(n, p.name, sha256(p), p.stat().st_size)
    a = pd.concat([pd.read_parquet(p) for p in archivos.values()], ignore_index=True)
    a["subestrato"] = a.apply(subestrato, axis=1)
    original = pd.read_parquet(ruta(config, "processed") / "muestra_secop_maestra.parquet")[["id_muestra", "fuente", "llave"]]
    nuevo = (a["fuente"] == "secop1") & (a["anio"] >= 2023)
    for nombre, marco in (("marco actual (con SECOP I 2023-2025)", a), ("marco sin SECOP I 2023-2025", a[~nuevo].reset_index(drop=True))):
        r = sortear(marco, config["seed"])
        iguales = int((r.merge(original, on=["id_muestra", "fuente", "llave"]).shape[0]))
        mismas_llaves = len(set(zip(r.fuente, r.llave)) & set(zip(original.fuente, original.llave)))
        print(f"{nombre}: filas del marco {len(marco):,}; id y llave idénticos {iguales}/400; mismas llaves {mismas_llaves}/400")
    nr = pd.read_json(ruta(config, "raw") / "secop" / "secop2_muestra_no_recuperados.jsonl", lines=True)
    cand = pd.read_json(ruta(config, "raw") / "secop" / "secop2_candidatos_2020_2025.jsonl", lines=True, dtype=False)
    print("no recuperados:", len(nr), "únicos", nr["id_contrato"].nunique(), "| también candidatos:", int(nr["id_contrato"].isin(cand["id_contrato"]).sum()),
          "| por año:", nr["fecha_de_firma"].astype(str).str[:4].value_counts().sort_index().to_dict())


if __name__ == "__main__":
    main()
