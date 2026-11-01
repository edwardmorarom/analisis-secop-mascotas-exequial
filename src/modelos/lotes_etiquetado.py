import numpy as np
import pandas as pd
from openpyxl.styles import Alignment, Font

from src.etl.anonimizar import anonimizar
from src.etl.comun import RAIZ, cargar_config, guardar_libro, ruta
from src.evaluacion.plantillas_etiquetado import libro
from src.evaluacion.reglas_etiquetado import D20, D21
from src.modelos.sensibilidad_mixtos import humanitarios, universo
from src.modelos.validacion_externa import REGLAS_NUEVAS

N_HUMANITARIOS, MINIMO_POR_ESTRATO, SEMILLA_HUMANITARIOS = 40, 10, 2028
N_ESTRATO_D, SEMILLA_D = 150, 2029
REVISION = RAIZ / "docs" / "revision_f4"
COLUMNAS_TEXTO = ["llave", "nombre_entidad", "objeto", "descripcion"]


def textos(config, fuente_llave):
    interim = ruta(config, "interim")
    t = pd.concat([pd.read_parquet(interim / f"{n}_senales.parquet", columns=["fuente"] + COLUMNAS_TEXTO) for n in ("secop1", "secop2")])
    t = fuente_llave.merge(t, on=["fuente", "llave"], how="left", validate="one_to_one")
    assert t["objeto"].notna().all()
    for col in ("objeto", "descripcion"):
        t[col] = t[col].map(anonimizar)
    return t.assign(codigo=None)


def asignar_proporcional(tamanos, n, minimo):
    cuota = (tamanos / tamanos.sum() * n).round().astype(int).clip(lower=minimo)
    while cuota.sum() > n:
        cuota[cuota.idxmax()] -= 1
    return cuota


def muestrear(marco, cuotas, semilla, prefijo):
    rng = np.random.default_rng(semilla)
    partes = []
    for estrato, n in cuotas.items():
        g = marco[marco["subestrato"] == estrato].sort_values(["fuente", "llave"])
        partes.append(g.sample(n=n, random_state=int(rng.integers(2**31))).assign(N_estrato=len(g), n_estrato=n, peso=len(g) / n))
    m = pd.concat(partes).drop(columns=["id_muestra"], errors="ignore").sample(frac=1, random_state=semilla).reset_index(drop=True)
    m.insert(0, "id_muestra", [f"{prefijo}{i:03d}" for i in range(1, len(m) + 1)])
    return m


def libro_a_ciegas(datos, titulo):
    wb = libro(datos[["id_muestra", "fuente", "anio", "nombre_entidad", "objeto", "descripcion", "codigo"]], "edward", calibracion=0)
    ws = wb["Instrucciones"]
    ws["A1"] = titulo
    fila = ws.max_row + 2
    ws.cell(fila, 1, "CRITERIO COMPLETO (D20, D21 y reglas 10 a 13)").font = Font(bold=True)
    for t in D20 + D21 + REGLAS_NUEVAS:
        fila += 1
        ws.cell(fila, 1, t).alignment = Alignment(wrap_text=True, vertical="top")
    return wb


def guardar(wb, destino):
    guardar_libro(wb, destino)


def lote_humanitarios(config, u):
    s = humanitarios(u)
    s = s[s["etiqueta"].isna()]
    cuotas = asignar_proporcional(s.groupby("subestrato").size(), N_HUMANITARIOS, MINIMO_POR_ESTRATO)
    m = muestrear(s, cuotas, SEMILLA_HUMANITARIOS, "H")
    m[["id_muestra", "fuente", "llave", "anio", "subestrato", "N_estrato", "n_estrato", "peso"]].to_parquet(ruta(config, "processed") / "humanitarios_40_maestra.parquet", index=False)
    guardar(libro_a_ciegas(textos(config, m[["id_muestra", "fuente", "llave", "anio"]]), "Humanitarios con componente funerario — revisor: Edward (40 contratos)"), REVISION / "humanitarios_40.xlsx")
    return m, s.groupby("subestrato").size()


def lote_estrato_d(config, u):
    nuevo = (u["fuente"] == "secop1") & (u["anio"] >= 2023)
    marco = u[(u["subestrato"] == "D_sin_senal") & ~nuevo & u["etiqueta"].isna()]
    m = muestrear(marco, pd.Series({"D_sin_senal": N_ESTRATO_D}), SEMILLA_D, "E")
    m[["id_muestra", "fuente", "llave", "anio", "subestrato", "N_estrato", "n_estrato", "peso"]].to_parquet(ruta(config, "processed") / "estrato_d_150_maestra.parquet", index=False)
    wb = libro_a_ciegas(textos(config, m[["id_muestra", "fuente", "llave", "anio"]]), "Estrato D (sin señal) — revisor: Edward (150 contratos)")
    v = u[(u["fuente"] == "secop2") & (u["llave"] == "CO1.PCCNTR.4107452")][["fuente", "llave", "anio", "etiqueta"]].assign(id_muestra="V006")
    t = textos(config, v[["fuente", "llave", "anio", "id_muestra"]])
    hoja = wb.create_sheet("V006")
    hoja.append(["id_muestra", "fuente", "anio", "entidad", "objeto", "descripcion", "etiqueta_actual"])
    for c in hoja[1]:
        c.font = Font(bold=True)
    r = t.iloc[0]
    hoja.append([r["id_muestra"], r["fuente"], int(r["anio"]), r["nombre_entidad"], r["objeto"], r["descripcion"], v["etiqueta"].iloc[0]])
    for letra, ancho in zip("ABCDEFG", (11, 9, 7, 40, 100, 70, 16)):
        hoja.column_dimensions[letra].width = ancho
    for celda in hoja[2]:
        celda.alignment = Alignment(wrap_text=True, vertical="top")
    guardar(wb, REVISION / "estrato_d_150.xlsx")
    return m, len(marco)


def lote_no_recuperados(config):
    """Libro a ciegas con la muestra de 100 contratos de SECOP II que la consulta original no recupera (D22); el crudo no se modifica."""
    d = pd.read_json(ruta(config, "raw") / "secop" / "secop2_muestra_no_recuperados.jsonl", lines=True, dtype=False)
    d = d.sample(frac=1, random_state=config["seed"]).reset_index(drop=True)
    d.insert(0, "id_muestra", [f"R{i:03d}" for i in range(1, len(d) + 1)])
    d["anio"] = d["fecha_de_firma"].astype(str).str[:4].astype(int)
    d["fuente"] = "secop2"
    d[["id_muestra", "fuente", "id_contrato", "anio"]].rename(columns={"id_contrato": "llave"}).to_parquet(
        ruta(config, "processed") / "no_recuperados_100_maestra.parquet", index=False)
    texto = pd.DataFrame({"id_muestra": d["id_muestra"], "fuente": d["fuente"], "anio": d["anio"], "nombre_entidad": d["nombre_entidad"],
                          "objeto": d["objeto_del_contrato"].fillna("").map(anonimizar), "descripcion": d["descripcion_del_proceso"].fillna("").map(anonimizar),
                          "codigo": None})
    guardar(libro_a_ciegas(texto, "No recuperados por la consulta original (D22) — revisor: Edward (100 contratos)"), REVISION / "no_recuperados_100.xlsx")
    return d


def asignacion_neyman(config):
    p = ruta(config, "processed")
    m = pd.read_parquet(p / "muestra_secop_maestra.parquet")[["id_muestra", "subestrato", "N_estrato"]]
    e = pd.read_parquet(p / "etiquetas_finales.parquet")[["id_muestra", "etiqueta"]]
    d = m.merge(e, on="id_muestra")
    g = d.groupby("subestrato").agg(N=("N_estrato", "first"), n_usado=("id_muestra", "size"), funerarios=("etiqueta", lambda s: int((s == "funerario").sum())))
    g["p_observada"] = g["funerarios"] / g["n_usado"]
    g["p_usada"] = np.where(g["funerarios"] == 0, 3 / g["n_usado"], g["p_observada"])
    g["NS"] = g["N"] * np.sqrt(g["p_usada"] * (1 - g["p_usada"]))
    g["neyman_sin_tope"] = 400 * g["NS"] / g["NS"].sum()
    resto = g.drop(index="B_animales")
    g["neyman_B_censo"] = (400 - g.loc["B_animales", "n_usado"]) * resto["NS"] / resto["NS"].sum()
    g.loc["B_animales", "neyman_B_censo"] = g.loc["B_animales", "n_usado"]
    return g


def main():
    config = cargar_config()
    u = universo(config)
    h, n_h = lote_humanitarios(config, u)
    print("humanitarios sin etiqueta por estrato:", n_h.to_dict(), "| muestra:", h.groupby("subestrato").size().to_dict(), "| pesos:", h.groupby("subestrato")["peso"].first().round(3).to_dict())
    d, marco = lote_estrato_d(config, u)
    print("estrato D: marco", marco, "muestra", len(d), "peso", round(d["peso"].iloc[0], 2), d.groupby("anio").size().to_dict(), d.groupby("fuente").size().to_dict())
    g = asignacion_neyman(config)
    g.to_csv(ruta(config, "processed") / "asignacion_neyman.csv", encoding="utf-8-sig")
    pd.set_option("display.width", 220)
    print(g.round(3).to_string())


if __name__ == "__main__":
    main()
