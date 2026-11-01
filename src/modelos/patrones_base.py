import pandas as pd

from src.etl.comun import cargar_config, ruta
from src.modelos.perfil_variables import cargar, homologar

COMPONENTES = ["inhumacion_cremacion", "traslado", "ataudes_bienes", "plan_exequial", "operacion_cementerio", "atencion_vulnerables_NN"]
CATEGORICAS = ["tipo_entidad", "modalidad_grupo", "tipo_contrato_hom", "orden_nivel", "cuartil_valor"]
UMBRAL_RARA = 0.01


def agrupar_raras(serie, umbral=UMBRAL_RARA):
    frec = serie.value_counts(normalize=True)
    raras = frec[frec < umbral].index
    return serie.where(~serie.isin(raras), "otras")


def construir():
    f = homologar(cargar(cargar_config())).reset_index(drop=True)
    b = pd.DataFrame({"fuente": f["fuente"], "anio": f["anio"].astype(int), "mes": f["fecha_firma"].dt.to_period("M").astype("string"),
                      "entidad_id": f["nit_entidad"].astype("string").fillna(f["entidad"].astype("string")),
                      "valor_constante_2025": f["valor_constante_2025"]})
    for c in CATEGORICAS:
        b[c] = agrupar_raras(f[c].astype("string").fillna("sin_dato"))
    for c in COMPONENTES:
        b[c] = f["incluye_" + c].astype(int)
    return b


def main():
    b = construir()
    destino = ruta(cargar_config(), "processed") / "resultados_secop" / "patrones_base.csv"
    b.to_csv(destino, index=False, encoding="utf-8")
    print(destino, b.shape)
    print("mes nulo:", int(b["mes"].isna().sum()), "| valor <= 0 o nulo:", int((~(b["valor_constante_2025"] > 0)).sum()),
          "| entidades:", b["entidad_id"].nunique())
    print("anio vs mes:", int((b["mes"].dropna().str[:4].astype(int) != b.loc[b["mes"].notna(), "anio"]).sum()), "discrepancias")
    for c in CATEGORICAS:
        print(c, b[c].value_counts().to_dict())
    print({c: int(b[c].sum()) for c in COMPONENTES})


if __name__ == "__main__":
    main()
