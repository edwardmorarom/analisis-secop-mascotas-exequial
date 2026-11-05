import pandas as pd

from src.etl.comun import RAIZ

ORIGEN = RAIZ / "data/interim/camaras_ciiu9603.parquet"
DESTINO = RAIZ / "data/processed"
AVISO = "Contexto de la oferta funeraria formal de personas (CIIU 9603): no mide la oferta de mascotas (D101)."


def registros(c):
    """Registros sin NIT: las personas naturales llevan el seudónimo PN-… de D15 en lugar del nombre."""
    r = c[["camara", "cod_divipola", "razon_social", "es_persona_natural", "organizacion", "estado_matricula"]].copy()
    r["anio_matricula"] = pd.to_numeric(c["fecha_matricula"].astype("string").str[:4], errors="coerce").astype("Int64")
    r["matricula_activa"] = c["estado_matricula"].astype("string").str.upper().str.contains(r"\bACTIVA", na=False)
    r["aviso"] = AVISO
    return r


def tabla_municipal(r):
    """Una fila por cámara y municipio. `matricula_activa` cuenta solo los estados con la palabra ACTIVA; los códigos
    abreviados de las cámaras (MA, MC, MI, MF, IA) no están decodificados y quedan en `estado_codigo_sin_decodificar`."""
    abreviado = r["estado_matricula"].astype("string").str.len().le(2).fillna(False)
    g = r.assign(abreviado=abreviado).groupby(["camara", "cod_divipola"])
    t = g.agg(registros=("razon_social", "size"), personas_naturales=("es_persona_natural", "sum"),
              matriculas_activas=("matricula_activa", "sum"), estado_codigo_sin_decodificar=("abreviado", "sum"),
              primera_matricula=("anio_matricula", "min"), ultima_matricula=("anio_matricula", "max")).reset_index()
    t["personas_juridicas"] = t["registros"] - t["personas_naturales"]
    t["aviso"] = AVISO
    return t[["camara", "cod_divipola", "registros", "personas_juridicas", "personas_naturales", "matriculas_activas",
              "estado_codigo_sin_decodificar", "primera_matricula", "ultima_matricula", "aviso"]]


def main():
    r = registros(pd.read_parquet(ORIGEN))
    t = tabla_municipal(r)
    r.to_parquet(DESTINO / "camaras_contexto_registros.parquet", index=False)
    t.to_csv(DESTINO / "camaras_contexto_municipal.csv", index=False, encoding="utf-8-sig")
    print(len(r), "registros;", len(t), "filas camara-municipio;", int(r["es_persona_natural"].sum()), "personas naturales")


if __name__ == "__main__":
    main()
