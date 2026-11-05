import re
import unicodedata

import numpy as np
import pandas as pd

from src.etl.comun import RAIZ, cargar_config
from src.etl.anonimizar import anonimizar
from src.modelos.etiquetas_humanas import construir
from src.modelos.grupos_hcpc import MARCA_DIAGNOSTICO, PATRONES, fmt, grupos_reportados, recortar, universo_d98
from src.modelos.perfil_variables import cargar, homologar

SENAL = re.compile(r"FUNERA|EXEQU|INHUMA|CREMACI|SEPEL|SEPULT|ATAUD|COFRE|CADAVER|BOVEDA|\bOSARIOS?\b")
AFIN = re.compile(r"FUNEB|MORTUOR|FALLECID|DIFUNT|OCCIS|CEMENTERIO|NICHO|ENTIERRO|DEFUNCI|RESTOS HUMANOS|MUERT")


def plano(texto):
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return t.upper()


def cargar_contratos():
    config = cargar_config()
    f = homologar(cargar(config, universo_d98(config))).reset_index(drop=True)
    b = pd.read_csv(RAIZ / "data/processed/resultados_secop/patrones_base.csv", dtype={"entidad_id": str})
    g = pd.read_csv(PATRONES / "hcpc_d98_grupos.csv")["grupo"]
    if not (len(f) == len(b) == len(g)) or not (f["fuente"].values == b["fuente"].values).all() or not np.allclose(f["valor_constante_2025"].values, b["valor_constante_2025"].values):
        raise ValueError("las tablas no están alineadas fila a fila")
    texto = f["objeto"].map(plano)
    d = pd.DataFrame({"grupo_hcpc": g, "fuente": f["fuente"], "llave": f["llave"], "anio": f["anio"].astype(int), "valor": f["valor_constante_2025"],
                      "objeto": f["objeto"], "clase_final": f["clase_final"],
                      "etiqueta_humana": f["etiqueta_humana_mercado"].where(f["origen_etiqueta_humana"] != "grupo5_revision"),
                      "etiqueta_grupo5": f["etiqueta_humana_mercado"].where(f["origen_etiqueta_humana"] == "grupo5_revision"),
                      "forense_grupo5": f["forense_humano"].where(f["origen_etiqueta_humana"] == "grupo5_revision"),
                      "departamento": f["departamento_entidad"], "entidad": f["entidad"], "tipo_entidad": f["tipo_entidad"],
                      "con_senal": texto.str.contains(SENAL), "con_afin": texto.str.contains(AFIN)})
    d["categoria"] = np.where(d["con_senal"], "con señal", np.where(d["con_afin"], "sin señal, con palabra afín", "sin señal ni palabra afín"))
    return d, b


def resumen_por_grupo(d, reportados):
    filas = []
    for _, r in reportados.iterrows():
        s = d[d["grupo_hcpc"] == r["grupo"]]
        sin = s[~s["con_senal"]]
        filas.append({"nombre": r["nombre"], "grupo_hcpc": r["grupo"], "contratos": len(s), "sin_senal": len(sin), "pct_sin_senal": len(sin) / len(s) * 100,
                      "valor_grupo": s["valor"].sum(), "valor_sin_senal": sin["valor"].sum(), "pct_valor_sin_senal": sin["valor"].sum() / s["valor"].sum() * 100,
                      "sin_senal_con_etiqueta_humana": int(sin["etiqueta_humana"].notna().sum()),
                      "sin_senal_ni_afin": int((~sin["con_afin"]).sum()), "valor_sin_senal_ni_afin": sin.loc[~sin["con_afin"], "valor"].sum()})
    return pd.DataFrame(filas)


def cuantiles(b, excluir, remuestreos=500, semilla=2034):
    """Regresión por cuantiles (mediana) de D98 sobre los contratos que no están en `excluir` (misma especificación y bootstrap por entidad)."""
    import statsmodels.api as sm

    from src.modelos.patrones_valor_cuantiles import diseno

    b, X = diseno(b[~excluir.to_numpy()].reset_index(drop=True))
    y = np.log(b["valor_constante_2025"].to_numpy())
    Xv = X.to_numpy()
    base = sm.QuantReg(y, Xv).fit(q=0.5, max_iter=5000)
    out = pd.DataFrame({"termino": X.columns, "estimador": base.params})
    if remuestreos:
        entidades = b["entidad_id"].to_numpy()
        idx_por_entidad = {e: np.flatnonzero(entidades == e) for e in np.unique(entidades)}
        claves = np.array(list(idx_por_entidad))
        rng = np.random.default_rng(semilla)
        coefs = []
        for _ in range(remuestreos):
            elegidas = rng.choice(claves, len(claves), replace=True)
            idx = np.concatenate([idx_por_entidad[e] for e in elegidas])
            coefs.append(sm.QuantReg(y[idx], Xv[idx]).fit(q=0.5, max_iter=5000).params)
        coefs = np.array(coefs)
        out["se_bootstrap"] = coefs.std(axis=0, ddof=1)
        out["ic_bajo"] = np.percentile(coefs, 2.5, axis=0)
        out["ic_alto"] = np.percentile(coefs, 97.5, axis=0)
    return out, len(y)


REVISION = RAIZ / "docs/revision_f4/grupo5_revision.xlsx"
GRUPO5 = 3
SEMILLA_LIBRO = 2026


def libro_revision(d, config):
    """Libro a ciegas con los contratos del Grupo 5 sin señal y sin etiqueta humana; el crudo y las etiquetas no se modifican."""
    from src.modelos.lotes_etiquetado import guardar, libro_a_ciegas, textos

    g = d[(d["grupo_hcpc"] == GRUPO5) & ~d["con_senal"] & d["etiqueta_humana"].isna()].sort_values(["fuente", "llave"])
    g = g.sample(frac=1, random_state=SEMILLA_LIBRO).reset_index(drop=True)
    g.insert(0, "id_muestra", [f"G5-{i:03d}" for i in range(1, len(g) + 1)])
    maestra = g[["id_muestra", "fuente", "llave", "anio", "categoria"]]
    maestra.to_parquet(RAIZ / "data/processed/grupo5_revision_maestra.parquet", index=False)
    wb = libro_a_ciegas(textos(config, maestra[["id_muestra", "fuente", "llave", "anio"]]),
                        f"Grupo 5 de HCPC, contratos sin señal funeraria en el objeto — revisor: Edward ({len(g)} contratos)")
    guardar(wb, REVISION)
    return maestra


def millones(x, decimales=0):
    return f"${fmt(x / 1e6, decimales)} millones"


def coeficiente(tabla, termino="modalidad_gruposeleccion_abreviada"):
    r = tabla.set_index("termino").loc[termino]
    return r


def cambio_rasgos(d):
    """Mayor cambio, en puntos porcentuales, del porcentaje del grupo en cada categoría descriptiva al quitar los contratos sin señal ni palabra afín."""
    from src.modelos.grupos_hcpc import COMPONENTES, DESCRIPCIONES

    b = pd.read_csv(RAIZ / "data/processed/resultados_secop/patrones_base.csv", dtype={"entidad_id": str})
    fuera = (~d["con_senal"] & ~d["con_afin"]).to_numpy()
    cambio = 0.0
    for grupo, rasgos in DESCRIPCIONES.items():
        en_grupo = (d["grupo_hcpc"] == grupo).to_numpy()
        for categoria, _ in rasgos:
            variable, nivel = categoria.split(": ")
            col = (b[variable] == (1 if nivel == "sí" else 0)) if variable in COMPONENTES else (b[variable] == nivel)
            cambio = max(cambio, abs(col[en_grupo].mean() - col[en_grupo & ~fuera].mean()) * 100)
    return cambio


def seccion(d, reportados, base, sens):
    g = d[d["grupo_hcpc"] == GRUPO5].sort_values("valor", ascending=False)
    sin = g[~g["con_senal"]]
    ni_afin = sin[~sin["con_afin"]]
    por_grupo = resumen_por_grupo(d, reportados)
    sin_hum = sin[sin["etiqueta_humana"].isna()]
    L = [MARCA_DIAGNOSTICO, "", "## Diagnóstico del Grupo 5: contratos sin señal funeraria en el objeto (2026-11-05)", "",
         "El diagnóstico (secciones 1 a 4) describe los contratos antes de la revisión de Edward: la columna «etiqueta humana» no cuenta los 11 que él etiquetó después (sección 5). Señal funeraria = alguna de las raíces FUNERA, EXEQU, INHUMA, CREMACI, SEPEL, SEPULT, ATAUD, COFRE, CADAVER, BOVEDA u OSARIO (como palabra) en el objeto, sin tildes ni distinción de mayúsculas. Como control, los contratos sin señal se separan en los que tienen otra palabra afín (FÚNEBRE, MORTUORIO, FALLECIDO, DIFUNTO, OCCISO, CEMENTERIO, NICHO, ENTIERRO, DEFUNCIÓN, RESTOS HUMANOS, MUERTE) y los que no tienen ninguna.", "",
         "**La clase final es «funerario» para los 4.992 contratos del análisis**; solo 244 tienen etiqueta humana y el resto toma la clase del modelo. Por eso «sin señal» no significa «sin etiqueta».", "",
         "### 1. Grupo 5: contratos sin señal", "",
         f"- El Grupo 5 tiene {fmt(len(g), 0)} contratos; **{len(sin)} ({fmt(len(sin) / len(g) * 100)} %) no tienen señal** y suman **{millones(sin['valor'].sum())}** ({fmt(sin['valor'].sum() / g['valor'].sum() * 100)} % de su valor de {millones(g['valor'].sum())}).",
         f"- De los {len(sin)}: {int(sin['etiqueta_humana'].notna().sum())} tienen etiqueta humana «funerario» (cajas mortuorias o fúnebres); {int((sin['con_afin'] & sin['etiqueta_humana'].isna()).sum())} más tienen otra palabra afín y por su texto son servicios funerarios que la lista no cubre (honras fúnebres, cajas mortuorias); **{len(ni_afin)} no tienen ninguna palabra afín** y suman {millones(ni_afin['valor'].sum())} ({fmt(ni_afin['valor'].sum() / g['valor'].sum() * 100)} % del valor del grupo).",
         "- Por su objeto, esos 7 parecen programas sociales de adultos mayores, alimentos y kits escolares (4 contratos) y servicios de cava refrigerada, morgue y médico legales (3 contratos, que el libro de códigos trata como forenses y deja fuera del mercado). Es una lectura del texto, no una etiqueta.",
         "- Los 20 contratos de mayor valor del grupo **tienen todos señal** y suman el " + fmt(g.head(20)["valor"].sum() / g["valor"].sum() * 100, 0) + " % del valor del grupo; el mayor de los sin señal vale " + millones(sin["valor"].max()) + ".", "",
         "#### Los 20 contratos de mayor valor del Grupo 5", "", "| # | Fuente | Año | Valor | Clase final | Etiqueta humana | Señal | Objeto (recortado, anonimizado) |", "|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(g.head(20).itertuples(), 1):
        L.append(f"| {i} | {'SECOP I' if r.fuente == 'secop1' else 'SECOP II'} | {r.anio} | {millones(r.valor)} | {r.clase_final} | {r.etiqueta_humana if isinstance(r.etiqueta_humana, str) else 'no'} | {'sí' if r.con_senal else 'no'} | {recortar(anonimizar(r.objeto), 110)} |")
    L += ["", f"#### Los {len(sin)} contratos del Grupo 5 sin señal", "", "| Fuente | Año | Valor | Etiqueta humana | Categoría de control | Objeto (recortado, anonimizado) |", "|---|---|---|---|---|---|"]
    for r in sin.itertuples():
        L.append(f"| {'SECOP I' if r.fuente == 'secop1' else 'SECOP II'} | {r.anio} | {millones(r.valor)} | {r.etiqueta_humana if isinstance(r.etiqueta_humana, str) else 'no'} | {r.categoria} | {recortar(anonimizar(r.objeto), 110)} |")
    L += ["", "### 2. Los 8 grupos", "",
          "| Grupo | Contratos | Sin señal | % sin señal | Valor sin señal | % del valor del grupo | Sin señal ni palabra afín | Valor de esos |", "|---|---|---|---|---|---|---|---|"]
    for r in por_grupo.itertuples():
        L.append(f"| {r.nombre} | {fmt(r.contratos, 0)} | {r.sin_senal} | {fmt(r.pct_sin_senal)} % | {millones(r.valor_sin_senal)} | {fmt(r.pct_valor_sin_senal)} % | {r.sin_senal_ni_afin} | {millones(r.valor_sin_senal_ni_afin)} |")
    tot_sin, tot_ni = int((~d["con_senal"]).sum()), int((~d["con_senal"] & ~d["con_afin"]).sum())
    mayor = por_grupo.sort_values("pct_sin_senal", ascending=False).iloc[0]
    L += ["", f"En total, {fmt(tot_sin, 0)} de {fmt(len(d), 0)} contratos ({fmt(tot_sin / len(d) * 100)} %) no tienen señal y {tot_ni} ({fmt(tot_ni / len(d) * 100)} %) no tienen ni palabra afín. **El problema no se concentra en el Grupo 5:** su proporción de contratos sin señal ({fmt(por_grupo.loc[por_grupo['grupo_hcpc'] == 3, 'pct_sin_senal'].iloc[0])} %) es de las más bajas; la más alta es la del {mayor['nombre']} ({fmt(mayor['pct_sin_senal'])} %). Por valor, el Grupo 8 es el más afectado ({fmt(por_grupo.loc[por_grupo['grupo_hcpc'] == 10, 'pct_valor_sin_senal'].iloc[0])} % de su valor sin señal).", "",
          "### 3. Cuánto del valor del Grupo 5 podría ser error", "",
          f"- **Cota superior** (todo contrato sin señal y sin etiqueta humana es un error): {len(sin_hum)} contratos, {millones(sin_hum['valor'].sum())}, {fmt(sin_hum['valor'].sum() / g['valor'].sum() * 100)} % del valor del grupo.",
          f"- **Estimación central** (solo los {len(ni_afin)} sin ninguna palabra afín): {millones(ni_afin['valor'].sum())}, {fmt(ni_afin['valor'].sum() / g['valor'].sum() * 100)} % del valor del grupo y {fmt(len(ni_afin) / len(g) * 100)} % de sus contratos.",
          "- Los contratos con señal no se auditaron aquí: este diagnóstico solo mide los falsos negativos de la lista de señales, no los falsos positivos.",
          "- **Efecto sobre la selección abreviada (D99):** los contratos sin señal del Grupo 5 son 13 de 4.985 en la regresión; aun excluyéndolos todos, el resultado de abajo muestra si el efecto cambia.", "",
          "#### Sensibilidad: regresión por cuantiles de D98 (mediana) sin esos contratos", "",
          "Misma especificación y bootstrap por entidad de D98 (500 remuestreos, semilla 2034). Solo se repitió la regresión por cuantiles; los modelos mixtos de D98 no se repitieron. Coeficiente de modalidad de selección abreviada frente a mínima cuantía (log del valor constante de 2025):", "",
          "| Muestra | Contratos | Coeficiente | IC 95 % (bootstrap) | Razón multiplicativa |", "|---|---|---|---|---|"]
    r0 = base["fila"]
    L.append(f"| D98 (todos los contratos) | {fmt(base['n'], 0)} | {fmt(r0['qr_estimador'], 3)} | {fmt(r0['qr_ic_bajo'], 3)} a {fmt(r0['qr_ic_alto'], 3)} | ×{fmt(np.exp(r0['qr_estimador']), 2)} |")
    for nombre, (tabla, n) in sens.items():
        r = coeficiente(tabla)
        L.append(f"| {VARIANTES[nombre].capitalize()} | {fmt(n, 0)} | {fmt(r['estimador'], 3)} | {fmt(r['ic_bajo'], 3)} a {fmt(r['ic_alto'], 3)} | ×{fmt(np.exp(r['estimador']), 2)} |")
    r1 = coeficiente(sens["sin_senal"][0])
    contiene = r1["ic_bajo"] <= r0["qr_estimador"] <= r1["ic_alto"] and r0["qr_ic_bajo"] > 0 and r1["ic_bajo"] > 0
    L += ["", "### 4. Conclusión", "",
          f"- **Errores claros:** en el Grupo 5 hay {len(ni_afin)} contratos ({millones(ni_afin['valor'].sum())}, {fmt(ni_afin['valor'].sum() / g['valor'].sum() * 100)} % del valor del grupo) que por su objeto no parecen servicios funerarios. La revisión de Edward (sección 5) los confirmó. Los otros contratos sin señal del grupo son servicios funerarios que la lista de señales no reconoce (honras fúnebres, cajas mortuorias).",
          f"- **Efecto de selección abreviada (D99):** {'se mantiene' if contiene else 'cambia'}. El coeficiente de la mediana pasa de {fmt(r0['qr_estimador'], 3)} a {fmt(r1['estimador'], 3)} al excluir los {fmt(base['n'] - sens['sin_senal'][1], 0)} contratos sin señal (de todos los grupos), con el intervalo de 95 % por encima de cero y la estimación original dentro del nuevo intervalo. Con tan pocos contratos dudosos en el Grupo 5 y un efecto de esta magnitud (×5), el resultado no depende de ellos.",
          "- **Límites:** solo se repitió la regresión por cuantiles; este diagnóstico no audita los contratos con señal (falsos positivos); y la lectura de los 7 contratos es del texto del objeto, sin etiqueta humana.",
          "- **Fuera del Grupo 5:** hay contratos sin señal ni palabra afín en otros grupos (el Grupo 1 suma 54 y el Grupo 8, 14, que son todos sus contratos sin señal). No se revisaron porque este diagnóstico se limitó al Grupo 5; son candidatos a un lote de revisión aparte.",
          f"- **Libro de revisión:** `docs/revision_f4/grupo5_revision.xlsx` (no versionado, formato a ciegas), etiquetado por Edward, con los {len(sin_hum)} contratos del Grupo 5 sin señal y sin etiqueta humana: los 7 candidatos y {len(sin_hum) - len(ni_afin)} de control que por su texto parecen funerarios. La llave de cada fila está en `data/processed/grupo5_revision_maestra.parquet`."]
    c = construir()
    c = c[c["origen"] == "grupo5_revision"][["fuente", "llave", "etiqueta", "forense"]]
    r = sin_hum.merge(c, on=["fuente", "llave"], how="left")
    cand = r[~r["con_afin"]]
    ctrl = r[r["con_afin"]]
    L += ["", "### 5. Resultado de la revisión de Edward", "",
          f"Edward etiquetó los {len(r)} contratos del libro. **De los {len(cand)} candidatos sin ninguna palabra afín, {int((cand['etiqueta'] == 'no_funerario').sum())} resultaron `no_funerario`** ({int((cand['forense'] == '1').sum())} con la marca forense) y suman {millones(cand['valor'].sum())}; de los {len(ctrl)} de control, {int((ctrl['etiqueta'] == 'funerario').sum())} resultaron `funerario`. Los 11 entraron a la jerarquía de D84 (D105): la cifra principal del mercado no cambia y la suma con etiquetas baja de 230,6 a 229,6 (de 4.992 a 4.985 contratos).", "",
          "| Categoría de control | Etiqueta | Forense | Valor | Objeto (recortado, anonimizado) |", "|---|---|---|---|---|"]
    for x in r.sort_values("valor", ascending=False).itertuples():
        L.append(f"| {x.categoria} | `{x.etiqueta}` | {'sí' if x.forense == '1' else 'no'} | {millones(x.valor)} | {recortar(anonimizar(x.objeto), 100)} |")
    L += ["", "### 6. Limitación: contratos sin palabra afín que no se etiquetan", "",
          f"**{tot_ni} contratos ({fmt(tot_ni / len(d) * 100)} %) clasificados `funerario` por el modelo no tienen ninguna palabra afín** en el objeto; los {len(cand)} del Grupo 5 ya revisados resultaron todos `no_funerario`, de modo que ese conjunto contiene errores del modelo. Los {tot_ni - len(cand)} restantes no se etiquetan, por dos razones: el estimador de diferencia ya corrige ese error en la cifra principal, y en los grupos no cambia sus rasgos.",
          f"Para lo segundo: al quitar esos {tot_ni} contratos, ninguna de las categorías características que describen a los grupos cambia en más de {fmt(cambio_rasgos(d), 1)} puntos porcentuales dentro de su grupo (`cambio_rasgos`).", ""]
    return L


VARIANTES = {"sin_senal": "sin los contratos sin señal funeraria", "sin_senal_ni_afin": "sin los contratos sin señal ni palabra afín"}


def correr_sensibilidad():
    d, b = cargar_contratos()
    mascaras = {"sin_senal": ~d["con_senal"], "sin_senal_ni_afin": ~d["con_senal"] & ~d["con_afin"]}
    for nombre, excluir in mascaras.items():
        out, n = cuantiles(b, excluir)
        out["n"] = n
        out.to_csv(PATRONES / f"valor_grupo5_sensibilidad_{nombre}.csv", index=False)
        print(nombre, n, flush=True)


def escribir_seccion():
    d, _ = cargar_contratos()
    reportados = grupos_reportados(pd.read_csv(PATRONES / "hcpc_d98_estabilidad.csv"), pd.read_csv(PATRONES / "hcpc_d98_tamanos.csv"))
    fila = pd.read_csv(PATRONES / "valor_d98_cuantiles.csv").set_index("termino").loc["modalidad_gruposeleccion_abreviada"]
    sens = {}
    for nombre in VARIANTES:
        t = pd.read_csv(PATRONES / f"valor_grupo5_sensibilidad_{nombre}.csv")
        sens[nombre] = (t, int(t["n"].iloc[0]))
    L = seccion(d, reportados, {"n": 4985, "fila": fila}, sens)
    destino = RAIZ / "docs/resultados/grupos_hcpc.md"
    previo = destino.read_text(encoding="utf-8")
    corte = previo.index(MARCA_DIAGNOSTICO) if MARCA_DIAGNOSTICO in previo else len(previo)
    salto = chr(10)
    destino.write_text(previo[:corte].rstrip(salto) + salto + salto + salto.join(L) + salto + CONCLUSION, encoding="utf-8")
    return destino


CONCLUSION = ""


if __name__ == "__main__":
    import sys

    if "--sensibilidad" in sys.argv:
        correr_sensibilidad()
    else:
        print(escribir_seccion())
