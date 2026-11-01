import numpy as np
import pandas as pd

from src.etl.comun import cargar_config, ruta
from src.modelos.datos_clasificacion import cargar
from src.modelos.evaluar_validacion import cargar_validacion

Z = 1.96


def kish(w):
    w = np.asarray(w, dtype=float)
    n = len(w)
    n_efectivo = w.sum() ** 2 / (w ** 2).sum()
    return {"n": n, "efecto_diseno_kish": n / n_efectivo, "tamano_efectivo_kish": n_efectivo}


def wilson(p, n, z=Z):
    centro = (p + z ** 2 / (2 * n)) / (1 + z ** 2 / n)
    medio = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / (1 + z ** 2 / n)
    return centro - medio, centro + medio


def por_estrato(d, nombre):
    filas = []
    for e, g in d.groupby("subestrato"):
        n, N = len(g), g["peso"].iloc[0] * len(g)
        y = (g["etiqueta"] == "funerario").astype(float)
        p = y.mean()
        fpc = max(0.0, 1 - n / N)
        normal = Z * np.sqrt(fpc * p * (1 - p) / (n - 1)) if n > 1 else np.nan
        bajo, alto = wilson(p, n)
        filas.append({"muestra": nombre, "estrato": e, "N": round(N), "n": n, "peso": g["peso"].iloc[0], "funerarios": int(y.sum()),
                      "proporcion_funerario": p, "margen_normal_con_fpc": normal, "wilson_bajo": bajo, "wilson_alto": alto,
                      "margen_wilson": (alto - bajo) / 2})
    return pd.DataFrame(filas)


def estimador_ht(d):
    """Proporción de funerarios de la población con el estimador de Horvitz-Thompson y varianza estratificada."""
    N = d["peso"].sum()
    p = (d["peso"] * (d["etiqueta"] == "funerario")).sum() / N
    var = 0.0
    for _, g in d.groupby("subestrato"):
        n, Nh = len(g), g["peso"].iloc[0] * len(g)
        y = (g["etiqueta"] == "funerario").astype(float)
        if n > 1:
            var += (Nh / N) ** 2 * (1 - n / Nh) * y.var(ddof=1) / n
    ee = np.sqrt(var)
    return p, ee


def resumen(d, nombre):
    funerarios = d[d["etiqueta"] == "funerario"]
    g, f = kish(d["peso"]), kish(funerarios["peso"])
    p, ee = estimador_ht(d)
    return {"muestra": nombre, "n_global": g["n"], "deff_global": g["efecto_diseno_kish"], "n_efectivo_global": g["tamano_efectivo_kish"],
            "n_funerarios": f["n"], "deff_funerarios": f["efecto_diseno_kish"], "n_efectivo_funerarios": f["tamano_efectivo_kish"],
            "proporcion_funerario_HT": p, "ee_HT": ee, "ic95_bajo": p - Z * ee, "ic95_alto": p + Z * ee}


def main():
    config = cargar_config()
    d400 = cargar(config)
    d60 = cargar_validacion(config)
    r = pd.DataFrame([resumen(d400, "400 etiquetas"), resumen(d60, "60 validación externa")])
    e = pd.concat([por_estrato(d400, "400 etiquetas"), por_estrato(d60, "60 validación externa")])
    salida = ruta(config, "processed")
    r.to_csv(salida / "diseno_muestral_resumen.csv", index=False, encoding="utf-8-sig")
    e.to_csv(salida / "diseno_muestral_estratos.csv", index=False, encoding="utf-8-sig")
    pd.set_option("display.width", 250)
    print(r.round(3).T.to_string())
    print(e.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
