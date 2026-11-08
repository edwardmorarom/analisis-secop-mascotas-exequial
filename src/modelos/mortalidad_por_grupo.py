"""Perfil descriptivo de mortalidad por grupo del clustering (D108): tasa estandarizada del departamento y año de cada contrato, sin pruebas de hipótesis."""
import pandas as pd

from src.etl.comun import RAIZ
from src.modelos.causas_defuncion import CAUSAS, SALIDA
from src.modelos.causas_informe import NOMBRES, fmt, tabla
from src.modelos.validacion_grupos import cargar_validacion

GRUPOS = [f"Grupo {i}" for i in range(1, 9)]
DESTINO_MD = RAIZ / "docs/resultados/mortalidad_por_grupo.md"


def mil(n):
    return f"{n:,}".replace(",", ".")


def contratos_con_tasas():
    d, _ = cargar_validacion()
    t = pd.read_csv(SALIDA / "tasas_estandarizadas_dpto_anio.csv", dtype={"cod_dpto": str}, encoding="utf-8-sig")
    ancho = t.pivot(index=["cod_dpto", "anio"], columns="grupo_causa", values="tasa_estandarizada_100mil").reset_index()
    d = d.merge(ancho, on=["cod_dpto", "anio"], how="left", validate="many_to_one")
    return d


def perfil(d):
    filas = []
    subconjuntos = [(g, d[d["grupo"] == g]) for g in GRUPOS] + [("Total", d)]
    for g, s in subconjuntos:
        for c in CAUSAS:
            v = s[s[c].notna()]
            q = v[c].quantile([0.25, 0.5, 0.75])
            filas.append({"grupo": g, "causa": c, "contratos_grupo": len(s), "departamentos_grupo": s["cod_dpto"].nunique(), "contratos_con_tasa": len(v), "departamentos_con_tasa": v["cod_dpto"].nunique(),
                          "mediana": q[0.5], "p25": q[0.25], "p75": q[0.75]})
    return pd.DataFrame(filas)


def informe(d, p):
    sin_dpto = int(d["cod_dpto"].isna().sum())
    L = ["# Perfil de mortalidad por grupo del clustering (D108)", "",
         "> Descriptivo, sin pruebas de hipótesis ni valores p. Propuesta pendiente de revisión de Edward (D108; alcance de D107 cambiado en D107c). Rama `causas-defuncion`, sin integrar a `main`.", "",
         f"A cada uno de los {mil(len(d))} contratos con grupo HCPC (D97 a D99) se le asigna la **tasa de defunción estandarizada por edad** (método directo, población estándar Colombia 2020, por 100.000 habitantes) del departamento de la **entidad contratante** y el año de firma, para las siete causas de D107. Cada celda es **mediana (p25 a p75)** sobre contratos: cada contrato pesa una vez, de modo que los departamentos con más contratos pesan más. G1 a G8 son los grupos reportados en D98 y D105 (4.910 contratos); el total incluye los {mil(len(d) - int(d['grupo'].notna().sum()))} contratos de grupos no reportados. {sin_dpto} contratos sin código de departamento no reciben tasa.", "",
         "**Lectura.** Las tasas describen la mortalidad de la población del departamento donde está la entidad, no la de los fallecidos atendidos por el contrato (D107, limitaciones: sede frente a residencia, falacia ecológica). **COVID-19:** solo hay dato en 2020–2022 y en los departamentos-año donde `U07` está entre las diez primeras causas, y es tasa **cruda** (el Cuadro 16 no trae edad); «demás causas» incluye la COVID-19 de 2020 a 2022.", ""]
    cab = ["Grupo", "Contratos", "Departamentos"] + [NOMBRES[c] for c in CAUSAS]
    filas = []
    for g in GRUPOS + ["Total"]:
        s = p[p["grupo"] == g]
        fila = [g, f"{s['contratos_grupo'].iloc[0]:,}".replace(",", "."), s["departamentos_grupo"].iloc[0]]
        for c in CAUSAS:
            f = s[s["causa"] == c].iloc[0]
            fila.append(f"{fmt(f['mediana'])} ({fmt(f['p25'])} a {fmt(f['p75'])})")
        filas.append(fila)
    L += ["## Tasa por 100.000 habitantes: mediana (p25 a p75)", ""] + tabla(filas, cab) + [""]
    cov = p[p["causa"] == "covid19"]
    L += ["## Contratos y departamentos con tasa de COVID-19", ""] + tabla([(f.grupo, f"{f.contratos_con_tasa:,}".replace(",", "."), f"{f.contratos_grupo:,}".replace(",", "."), f.departamentos_con_tasa) for f in cov.itertuples()], ["Grupo", "Contratos con tasa", "Contratos del grupo", "Departamentos con tasa"]) + [""]
    L += ["Las demás causas tienen tasa en todos los contratos con departamento (contratos con tasa = contratos del grupo menos los sin departamento). El detalle por causa (contratos y departamentos con tasa, mediana, p25 y p75) está en `docs/resultados/mortalidad_por_grupo.csv`.", ""]
    return L


def main():
    d = contratos_con_tasas()
    p = perfil(d)
    SALIDA.mkdir(parents=True, exist_ok=True)
    p.to_csv(SALIDA / "mortalidad_por_grupo.csv", index=False, encoding="utf-8-sig")
    p.to_csv(DESTINO_MD.with_suffix(".csv"), index=False, encoding="utf-8-sig")
    DESTINO_MD.write_text(chr(10).join(informe(d, p)).rstrip() + chr(10), encoding="utf-8")
    print(DESTINO_MD)


if __name__ == "__main__":
    main()
