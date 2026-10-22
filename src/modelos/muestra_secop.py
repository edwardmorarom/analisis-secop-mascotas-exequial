import numpy as np
import pandas as pd

from src.etl.anonimizar import anonimizar
from src.etl.comun import cargar_config, ruta

ASIGNACION = {
    "A1_palabra_y_unspsc": 60, "A2_solo_palabra": 90, "A3_solo_unspsc": 60,
    "B_animales": 23, "C_cementerio": 45, "C_necr": 25, "C_cad_ver": 30,
    "C_mixtas_osario": 17, "D_sin_senal": 50,
}
PALABRAS = ["funera", "exequ", "inhuma", "cremaci", "sepelio", "sepult"]
UNSPSC = ["unspsc_851715", "unspsc_4813", "unspsc_422621"]


def subestrato(r):
    if r.estrato == "A_nucleo":
        palabra, codigo = r[PALABRAS].any(), r[UNSPSC].any()
        return "A1_palabra_y_unspsc" if palabra and codigo else "A2_solo_palabra" if palabra else "A3_solo_unspsc"
    if r.estrato == "B_animales":
        return "B_animales"
    if r.estrato == "D_sin_senal":
        return "D_sin_senal"
    if r.cementerio and not (r.necr or r.cad_ver or r.osario):
        return "C_cementerio"
    if r.necr and not (r.cementerio or r.osario):
        return "C_necr"
    if r.cad_ver and not (r.necr or r.cementerio or r.osario):
        return "C_cad_ver"
    return "C_mixtas_osario"


def reparto(celdas, n):
    cuotas = celdas / celdas.sum() * n
    base = np.floor(cuotas).astype(int)
    resto = n - base.sum()
    orden = (cuotas - base).sort_values(ascending=False).index
    for k in orden[:resto]:
        base[k] += 1
    return base


def main():
    config = cargar_config()
    interim = ruta(config, "interim")
    a = pd.concat([pd.read_parquet(interim / f"{n}_senales.parquet") for n in ("secop1", "secop2")],
                  ignore_index=True)
    a["subestrato"] = a.apply(subestrato, axis=1)
    rng = np.random.default_rng(config["seed"])
    partes = []
    for nombre, n in ASIGNACION.items():
        est = a[a.subestrato == nombre]
        celdas = est.groupby(["fuente", "anio"]).size()
        cuotas = reparto(celdas, n)
        for (fuente, anio), k in cuotas.items():
            if k:
                sub = est[(est.fuente == fuente) & (est.anio == anio)]
                partes.append(sub.sample(n=k, random_state=int(rng.integers(2**31))))
        print(f"{nombre}: N={len(est):,} n={n} peso={len(est) / n:.2f}")
    m = pd.concat(partes)
    m["n_estrato"] = m.subestrato.map(ASIGNACION)
    m["N_estrato"] = m.subestrato.map(a.subestrato.value_counts())
    m["peso"] = m.N_estrato / m.n_estrato
    m = m.sample(frac=1, random_state=config["seed"]).reset_index(drop=True)
    m.insert(0, "id_muestra", [f"M{i:03d}" for i in range(1, len(m) + 1)])
    assert len(m) == sum(ASIGNACION.values()) and m.llave.is_unique

    proc = ruta(config, "processed")
    proc.mkdir(parents=True, exist_ok=True)
    maestra = m[["id_muestra", "fuente", "llave", "anio", "subestrato", "N_estrato", "n_estrato", "peso",
                 "posible_disposicion_animales", *PALABRAS, "cad_ver", "necr", "cementerio", "osario",
                 "zoonosis_disposicion", "animales_muertos", *UNSPSC]]
    maestra.to_parquet(proc / "muestra_secop_maestra.parquet", index=False)
    maestra.to_csv(proc / "muestra_secop_maestra.csv", index=False, encoding="utf-8-sig")

    etiquetado = m[["id_muestra", "fuente", "anio", "nombre_entidad", "objeto", "descripcion", "codigo"]].copy()
    for col in ("objeto", "descripcion"):
        etiquetado[col] = etiquetado[col].map(anonimizar)
    assert not etiquetado[["objeto", "descripcion"]].apply(
        lambda c: c.fillna("").str.contains(r"historia cl[ií]nica\W*\d", case=False)).any().any()
    etiquetado["etiqueta"] = ""
    etiquetado["forense"] = ""
    etiquetado["notas"] = ""
    etiquetado.to_csv(proc / "muestra_secop_etiquetado.csv", index=False, encoding="utf-8-sig")
    print(len(m), "filas;", "peso total =", round(m.peso.sum()), "(debe igualar", len(a), ")")


if __name__ == "__main__":
    main()
