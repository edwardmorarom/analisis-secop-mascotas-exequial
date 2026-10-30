import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from scipy.stats import chi2_contingency, kurtosis, skew

from src.etl.anonimizar import anonimizar
from src.etl.comun import RAIZ, cargar_config, ruta
from src.modelos import mercado_patrones as mp

DESTINO = RAIZ / "docs" / "resultados" / "perfil_variables_secop.md"
DERIVADAS = RAIZ / "docs" / "revision_f4" / "derivadas.xlsx"
SEMILLA = 2030
SENTINELAS = {"", "no definido", "no aplica", "no aplica/no pertenece", "unspecified", "n/a", "na", "nd", "otro", "other"}
RAREZA = 0.01
CATEGORICAS = ["entidad", "nit_entidad", "orden", "nivel_o_sector", "rama", "departamento_entidad", "municipio_entidad", "lugar_ejecucion", "modalidad",
               "tipo_contrato", "estado", "destino_gasto", "origen_recursos", "es_pyme", "tipo_doc_proveedor", "categoria_unspsc"]
COLUMNAS = {
    "secop1": {"entidad": "nombre_entidad", "nit_entidad": "nit_de_la_entidad", "orden": "orden_entidad", "nivel_o_sector": "nivel_entidad", "rama": None,
               "departamento_entidad": "departamento_entidad", "municipio_entidad": "municipio_entidad", "lugar_ejecucion": "municipios_ejecucion",
               "modalidad": "modalidad_de_contratacion", "tipo_contrato": "tipo_de_contrato", "estado": "estado_del_proceso", "destino_gasto": "destino_gasto",
               "origen_recursos": None, "es_pyme": "es_mipyme", "tipo_doc_proveedor": "tipo_identifi_del_contratista", "categoria_unspsc": "id_clase",
               "valor_inicial": "cuantia_contrato", "valor_con_adiciones": "valor_contrato_con_adiciones", "valor_adiciones": "valor_total_de_adiciones",
               "valor_facturado": None, "valor_pagado": None, "dias_adicionados": None, "duracion": "plazo_de_ejec_del_contrato",
               "fecha_firma": "fecha_de_firma_del_contrato", "fecha_inicio": "fecha_ini_ejec_contrato", "fecha_fin": "fecha_fin_ejec_contrato"},
    "secop2": {"entidad": "nombre_entidad", "nit_entidad": "nit_entidad", "orden": "orden", "nivel_o_sector": "sector", "rama": "rama",
               "departamento_entidad": "departamento", "municipio_entidad": "ciudad", "lugar_ejecucion": "localizaci_n",
               "modalidad": "modalidad_de_contratacion", "tipo_contrato": "tipo_de_contrato", "estado": "estado_contrato", "destino_gasto": "destino_gasto",
               "origen_recursos": "origen_de_los_recursos", "es_pyme": "es_pyme", "tipo_doc_proveedor": "tipodocproveedor", "categoria_unspsc": "codigo_de_categoria_principal",
               "valor_inicial": "valor_del_contrato", "valor_con_adiciones": None, "valor_adiciones": None,
               "valor_facturado": "valor_facturado", "valor_pagado": "valor_pagado", "dias_adicionados": "dias_adicionados", "duracion": "duraci_n_del_contrato",
               "fecha_firma": "fecha_de_firma", "fecha_inicio": "fecha_de_inicio_del_contrato", "fecha_fin": "fecha_de_fin_del_contrato"}}
NUMERICAS = ["valor_inicial", "valor_con_adiciones", "valor_adiciones", "valor_facturado", "valor_pagado", "dias_adicionados"]
FECHAS = ["fecha_firma", "fecha_inicio", "fecha_fin"]
INVENTARIO = [
    ("Entidad (nombre, NIT)", "nombre_entidad, nit_de_la_entidad", "nombre_entidad, nit_entidad", "directa", ""),
    ("Orden", "orden_entidad (11 valores, con nivel municipal 1 a 6)", "orden (2 valores)", "parcial", "SECOP II no trae la categoría municipal"),
    ("Nivel o sector", "nivel_entidad (territorial o nacional)", "sector (18 valores) y rama (4)", "parcial", "SECOP I no tiene sector ni rama; SECOP II no tiene un nivel aparte de orden"),
    ("Ubicación de la entidad", "departamento_entidad, municipio_entidad", "departamento, ciudad", "directa", "cruce con DIVIPOLA en D66"),
    ("Lugar de ejecución", "municipios_ejecucion (texto)", "localizaci_n y direcci_n_de_ejecuci_n_del_contrato (texto)", "parcial", "formatos distintos; la dirección de SECOP II es texto libre"),
    ("Modalidad", "modalidad_de_contratacion (6 valores)", "modalidad_de_contratacion (10 valores)", "parcial", "vocabularios distintos; se agrupan con `modalidad_grupo`"),
    ("Tipo de contrato", "tipo_de_contrato (10 valores)", "tipo_de_contrato (13 valores)", "parcial", "SECOP II separa seguros, servicios financieros y Decreto 092"),
    ("Estado", "estado_del_proceso (filtrado a Celebrado, Liquidado y Terminado sin Liquidar)", "estado_contrato (7 valores)", "no comparable", "la selección de SECOP I ya filtra por estado (CLAUDE.md)"),
    ("Destino del gasto", "destino_gasto", "destino_gasto", "directa", "centinelas distintos («No aplica» frente a «No Definido»)"),
    ("Origen de los recursos", "—", "origen_de_los_recursos", "sin equivalente en SECOP I", ""),
    ("Valor inicial", "cuantia_contrato", "valor_del_contrato", "directa", "base de las series (D67)"),
    ("Valor con adiciones", "valor_contrato_con_adiciones, valor_total_de_adiciones", "—", "sin equivalente en SECOP II", "SECOP II solo trae `dias_adicionados`"),
    ("Valor facturado y pagado", "—", "valor_facturado, valor_pagado", "sin equivalente en SECOP I", ""),
    ("Fecha de firma", "fecha_de_firma_del_contrato", "fecha_de_firma", "directa", "año y estacionalidad"),
    ("Fechas de inicio y fin", "fecha_ini_ejec_contrato, fecha_fin_ejec_contrato", "fecha_de_inicio_del_contrato, fecha_de_fin_del_contrato", "directa", ""),
    ("Duración", "plazo_de_ejec_del_contrato (número sin unidad)", "duraci_n_del_contrato (texto con unidad: Dia(s), Mes(es))", "parcial", "la unidad de SECOP I no está en el conjunto descargado"),
    ("Adición en tiempo", "—", "dias_adicionados", "sin equivalente en SECOP I", ""),
    ("Proveedor (identificador, tipo de documento)", "identificacion_del_contratista, tipo_identifi_del_contratista", "codigo_proveedor, tipodocproveedor", "parcial", "identificadores distintos (D15)"),
    ("Tamaño de empresa", "es_mipyme", "es_pyme", "parcial", "SECOP I tiene «No definido»; SECOP II solo Si y No"),
    ("Categoría UNSPSC", "id_clase, id_familia, nombre_clase", "codigo_de_categoria_principal (con prefijo V1.)", "directa", "ver CLAUDE.md"),
    ("Número de oferentes", "—", "—", "no existe en ninguno de los dos conjuntos", "está en los conjuntos de procesos, que no se descargaron"),
]
TIPO_CONTRATO = [("Prestación de Servicios", "Prestación de servicios"), ("Suministro", "Suministros"), ("Compraventa", "Compraventa"),
                 ("Arrendamiento", "Arrendamiento de inmuebles | Arrendamiento de muebles"), ("Obra", "Obra"), ("Consultoría", "Consultoría"),
                 ("Concesión", "Concesión"), ("Comodato", "Comodato"), ("Otro Tipo de Contrato", "Otro"), ("Acuerdo Marco", "—"),
                 ("—", "Seguros"), ("—", "Decreto 092 de 2017"), ("—", "Servicios financieros")]
DESTINO_GASTO = [("Inversion", "Inversión"), ("Funcionamiento", "Funcionamiento"), ("No aplica", "No Definido (no equivale)")]
TIPO_DOC = [("Nit de Persona Jurídica", "NIT (incluye personas naturales con NIT)"), ("Nit de Persona Natural", "NIT (no se distingue)"),
            ("Cédula de Ciudadanía", "Cédula de Ciudadanía"), ("Nit de Extranjería", "Cédula de Extranjería (aproximada)"), ("Nuip", "Otro"), ("Carné Diplomático", "Otro")]
EQUIV_TIPO = {"Prestación de Servicios": "prestacion_servicios", "Prestación de servicios": "prestacion_servicios", "Suministro": "suministro", "Suministros": "suministro",
              "Compraventa": "compraventa", "Arrendamiento": "arrendamiento", "Arrendamiento de inmuebles": "arrendamiento", "Arrendamiento de muebles": "arrendamiento",
              "Obra": "obra", "Consultoría": "consultoria"}


def coma(v, d=1):
    return "" if pd.isna(v) else f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def entero(v):
    return f"{int(v):,}".replace(",", ".")


def tabla(df, cols=None):
    cols = cols or list(df.columns)
    filas = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "---|" * len(cols)]
    filas += ["| " + " | ".join("" if pd.isna(r[c]) else str(r[c]) for c in cols) + " |" for _, r in df.iterrows()]
    return "\n".join(filas)


def cargar(config):
    d = pd.read_parquet(ruta(config, "processed") / "resultados_secop" / "universo_mercado.parquet")
    f = mp.preparar(d).reset_index(drop=True)
    interim = ruta(config, "interim")
    partes = []
    for fuente, mapa in COLUMNAS.items():
        raw = pd.read_parquet(interim / f"{fuente}_senales.parquet")
        x = f.loc[f["fuente"] == fuente, ["llave"]].merge(raw, on="llave", how="left", validate="one_to_one")
        s = pd.DataFrame({"fuente": fuente, "llave": x["llave"]})
        for concepto, col in mapa.items():
            s[concepto] = x[col] if col else pd.NA
        partes.append(s)
    v = pd.concat(partes, ignore_index=True)
    for c in NUMERICAS:
        v[c] = pd.to_numeric(v[c], errors="coerce")
    for c in FECHAS:
        v[c] = pd.to_datetime(v[c], errors="coerce")
    columnas_duplicadas = [c for c in v.columns if c in f.columns and c not in ("fuente", "llave")]
    return f.drop(columns=columnas_duplicadas).merge(v, on=["fuente", "llave"], validate="one_to_one")


def faltante(serie):
    s = serie.astype("string").str.strip().str.lower()
    nulo = serie.isna() | s.isna()
    return nulo, s.isin(SENTINELAS) & ~nulo


def calidad_categoricas(f):
    filas = []
    for c in CATEGORICAS:
        for fuente, x in f.groupby("fuente"):
            if x[c].isna().all():
                filas.append({"variable": c, "fuente": fuente, "% faltante": "no existe", "% centinela": "", "categorías": "", "categorías raras (< 1 %)": "", "% de contratos en raras": ""})
                continue
            nulo, cent = faltante(x[c])
            validos = x.loc[~nulo & ~cent, c].astype(str)
            frec = validos.value_counts(normalize=True)
            raras = frec[frec < RAREZA]
            filas.append({"variable": c, "fuente": fuente, "% faltante": coma(nulo.mean() * 100), "% centinela": coma(cent.mean() * 100), "categorías": entero(frec.size),
                          "categorías raras (< 1 %)": entero(raras.size), "% de contratos en raras": coma(raras.sum() * validos.size / len(x) * 100)})
    return pd.DataFrame(filas)


def duracion_dias(x):
    if (x["fuente"] == "secop2").all():
        e = x["duracion"].astype("string").str.extract(r"(\d+)\s*(Dia|Mes|A)", expand=True)
        return pd.to_numeric(e[0], errors="coerce") * e[1].map({"Dia": 1, "Mes": 30, "A": 365})
    return pd.to_numeric(x["duracion"], errors="coerce")


def calidad_numericas(f):
    filas = []
    for c in NUMERICAS + FECHAS + ["duracion"]:
        for fuente, x in f.groupby("fuente"):
            if x[c].isna().all():
                filas.append({"variable": c, "fuente": fuente, "% faltante": "no existe", "% ≤ 0": "", "mínimo": "", "mediana": "", "máximo": ""})
            elif c in FECHAS:
                v = x[c]
                filas.append({"variable": c, "fuente": fuente, "% faltante": coma(v.isna().mean() * 100), "% ≤ 0": "", "mínimo": str(v.min().date()),
                              "mediana": str(v.median().date()), "máximo": str(v.max().date())})
            else:
                v = duracion_dias(x) if c == "duracion" else x[c]
                filas.append({"variable": c + (" (días; SECOP I sin unidad)" if c == "duracion" else ""), "fuente": fuente, "% faltante": coma(v.isna().mean() * 100),
                              "% ≤ 0": coma((v <= 0).mean() * 100), "mínimo": coma(v.min(), 0), "mediana": coma(v.median(), 0), "máximo": coma(v.max(), 0)})
    return pd.DataFrame(filas)


def inconsistencias(f):
    s1, s2 = f[f["fuente"] == "secop1"], f[f["fuente"] == "secop2"]
    anio = lambda x: x[FECHAS].apply(lambda c: c.dt.year)
    reglas = [
        ("fecha de fin anterior a la de inicio", "ambas", lambda x: x["fecha_fin"] < x["fecha_inicio"]),
        ("fecha de inicio más de 30 días antes de la firma", "ambas", lambda x: (x["fecha_firma"] - x["fecha_inicio"]).dt.days > 30),
        ("fecha de inicio más de 365 días después de la firma", "ambas", lambda x: (x["fecha_inicio"] - x["fecha_firma"]).dt.days > 365),
        ("alguna fecha fuera de 2000–2035", "ambas", lambda x: ((anio(x) < 2000) | (anio(x) > 2035)).any(axis=1)),
        ("valor inicial ≤ 0", "ambas", lambda x: x["valor_inicial"] <= 0),
        ("valor con adiciones menor que el inicial", "secop1", lambda x: x["valor_con_adiciones"] < x["valor_inicial"]),
        ("valor con adiciones distinto de inicial + adiciones", "secop1", lambda x: (x["valor_con_adiciones"] - x["valor_inicial"] - x["valor_adiciones"]).abs() > 1),
        ("valor facturado mayor que el valor del contrato", "secop2", lambda x: x["valor_facturado"] > x["valor_inicial"] * 1.0001),
        ("valor pagado mayor que el facturado", "secop2", lambda x: x["valor_pagado"] > x["valor_facturado"] * 1.0001 + 1),
        ("días adicionados negativos", "secop2", lambda x: x["dias_adicionados"] < 0),
    ]
    filas = []
    for nombre, aplica, regla in reglas:
        fila = {"regla": nombre}
        for etiqueta, clave, x in (("SECOP I", "secop1", s1), ("SECOP II", "secop2", s2)):
            if aplica not in ("ambas", clave):
                fila[etiqueta] = "no aplica"
            else:
                r = regla(x).fillna(False)
                fila[etiqueta] = f"{int(r.sum())} ({coma(r.mean() * 100)} %)"
        filas.append(fila)
    plazo = pd.to_numeric(s1["duracion"], errors="coerce")
    razon = (s1["fecha_fin"] - s1["fecha_inicio"]).dt.days / plazo.replace(0, np.nan)
    n = int(plazo.notna().sum())
    dias, meses = int(razon.between(0.9, 1.1).sum()), int(razon.between(25, 35).sum())
    filas.append({"regla": "plazo de SECOP I frente a los días entre inicio y fin: razón 0,9–1,1 (días) / 25–35 (meses de 30 días) / otra",
                  "SECOP I": f"{dias} ({coma(dias / n * 100)} %) / {meses} ({coma(meses / n * 100)} %) / {n - dias - meses} ({coma((n - dias - meses) / n * 100)} %)", "SECOP II": "no aplica"})
    d2 = duracion_dias(s2)
    ok = int(((d2 - (s2["fecha_fin"] - s2["fecha_inicio"]).dt.days).abs() <= 3).sum())
    filas.append({"regla": "duración declarada de SECOP II coincide (±3 días) con los días entre inicio y fin", "SECOP I": "no aplica",
                  "SECOP II": f"{ok} de {int(d2.notna().sum())} ({coma(ok / d2.notna().sum() * 100)} %)"})
    return pd.DataFrame(filas)


def homologar(f):
    f = f.copy()
    f["tipo_contrato_hom"] = f["tipo_contrato"].map(EQUIV_TIPO).fillna("sin_equivalente")
    f["destino_hom"] = f["destino_gasto"].astype("string").str.lower().str.replace("ó", "o").map({"inversion": "inversion", "funcionamiento": "funcionamiento"}).fillna("sin_dato")
    f["orden_nivel"] = f["nivel_o_sector"].where(f["fuente"] == "secop1", f["orden"]).astype("string").str.upper().str.strip()
    f["orden_nivel"] = f["orden_nivel"].where(f["orden_nivel"].isin(["TERRITORIAL", "NACIONAL"]), "otro")
    f["cuartil_valor"] = pd.qcut(f["valor_constante_2025"], 4, labels=["Q1", "Q2", "Q3", "Q4"]).astype(str)
    f["periodo"] = np.where(f["anio"] <= 2022, "2020-2022", "2023-2025")
    return f


def cramer(a, b):
    t = pd.crosstab(a, b)
    if t.shape[0] < 2 or t.shape[1] < 2:
        return np.nan
    chi2 = chi2_contingency(t, correction=False)[0]
    n = t.values.sum()
    phi2 = max(0, chi2 / n - (t.shape[0] - 1) * (t.shape[1] - 1) / (n - 1))
    k = t.shape[1] - (t.shape[1] - 1) ** 2 / (n - 1)
    r = t.shape[0] - (t.shape[0] - 1) ** 2 / (n - 1)
    return float(np.sqrt(phi2 / max(1e-12, min(k - 1, r - 1))))


def distribucion_valor(f):
    filas = []
    for nombre, x in [("todos", f)] + list(f.groupby("fuente")):
        v = x["valor_constante_2025"]
        p = v.quantile([0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99])
        filas.append({"grupo": nombre, "contratos": entero(len(x)), "media (millones)": coma(v.mean() / 1e6, 1), "asimetría": coma(skew(v), 1),
                      "asimetría de ln(valor)": coma(skew(np.log(v[v > 0])), 2), "curtosis": coma(kurtosis(v), 0),
                      **{f"p{int(q * 100)} (millones)": coma(p[q] / 1e6, 2) for q in p.index}, "máximo (millones)": coma(v.max() / 1e6, 0),
                      "% del valor en el 1 % mayor": coma(v.nlargest(max(1, len(v) // 100)).sum() / v.sum() * 100, 1),
                      "% del valor en los 10 mayores": coma(v.nlargest(10).sum() / v.sum() * 100, 1)})
    return pd.DataFrame(filas)


def cramer_pares(f):
    vars_ = {"fuente": "fuente", "año": "anio", "tipo de entidad": "tipo_entidad", "grupo de modalidad": "modalidad_grupo", "tipo de contrato (homologado)": "tipo_contrato_hom",
             "destino del gasto (homologado)": "destino_hom", "territorial o nacional": "orden_nivel", "cuartil del valor": "cuartil_valor"}
    comp = [c for c in mp.COMPONENTES if f[c].any()]
    x = f.assign(**{c: f[c].map({True: "si", False: "no"}) for c in comp})
    nombres = list(vars_) + [c.replace("incluye_", "componente: ") for c in comp]
    cols = list(vars_.values()) + comp
    m = pd.DataFrame([[cramer(x[a], x[b]) if a != b else np.nan for b in cols] for a in cols], index=nombres, columns=nombres)
    return m, vars_, comp, x


def v_con_fuente(x, vars_, comp):
    crudas = [("modalidad (texto original)", "modalidad"), ("tipo de contrato (texto original)", "tipo_contrato"), ("orden (texto original)", "orden"),
              ("destino del gasto (texto original)", "destino_gasto")]
    todo = [(n, c) for n, c in vars_.items() if c != "fuente"] + [(c.replace("incluye_", "componente: "), c) for c in comp] + crudas
    filas = []
    for nombre, col in todo:
        fila = {"variable": nombre}
        for etiqueta, sub in (("todos", x), ("2020–2022", x[x["periodo"] == "2020-2022"]), ("2023–2025", x[x["periodo"] == "2023-2025"])):
            fila[f"V con la fuente ({etiqueta})"] = coma(cramer(sub[col].astype(str), sub["fuente"]), 2)
        presentes = x.groupby(col)["fuente"].nunique()
        fila["% de contratos en categorías presentes en ambas fuentes"] = coma(x[col].map(presentes).eq(2).mean() * 100, 1)
        filas.append(fila)
    return pd.DataFrame(filas)


def excel_derivadas(f, destino):
    rng = np.random.default_rng(SEMILLA)
    wb = Workbook()
    wb.remove(wb.active)
    estilo = PatternFill("solid", fgColor="FFF2CC")
    hojas = {
        "tipo_entidad": ("TE", ["id", "fuente", "anio", "entidad", "orden", "tipo_entidad_derivado", "correcto", "tipo_correcto", "nota"],
                         lambda r: [r.fuente, int(r.anio), r.entidad, r.orden, r.tipo_entidad]),
        "modalidad_grupo": ("MG", ["id", "fuente", "anio", "modalidad_original", "grupo_derivado", "correcto", "grupo_correcto", "nota"],
                            lambda r: [r.fuente, int(r.anio), r.modalidad, r.modalidad_grupo]),
        "componentes": ("CO", ["id", "fuente", "anio", "objeto", "componentes_detectados", "correcto", "componentes_que_sobran_o_faltan", "nota"],
                        lambda r: [r.fuente, int(r.anio), " ".join(anonimizar(r.objeto).split())[:600],
                                   ", ".join(k.replace("incluye_", "") for k in mp.COMPONENTES if getattr(r, k)) or "ninguno"]),
    }
    for hoja, (prefijo, cols, fila) in hojas.items():
        ws = wb.create_sheet(hoja)
        ws.append(cols)
        for c in ws[1]:
            c.font = Font(bold=True)
        muestra = f.iloc[np.sort(rng.choice(len(f), 20, replace=False))]
        for i, r in enumerate(muestra.itertuples(), 1):
            valores = fila(r)
            ws.append([f"{prefijo}{i:02d}"] + valores + [None] * (len(cols) - 1 - len(valores)))
        col_ok = cols.index("correcto") + 1
        dv = DataValidation(type="list", formula1='"sí,no"', allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(f"{ws.cell(2, col_ok).coordinate}:{ws.cell(21, col_ok).coordinate}")
        for fila_ in range(2, 22):
            for k in range(1, len(cols) + 1):
                ws.cell(fila_, k).alignment = Alignment(wrap_text=True, vertical="top")
                if k >= col_ok:
                    ws.cell(fila_, k).fill = estilo
        for letra, ancho in zip("ABCDEFGHI", (8, 9, 7, 60 if hoja == "componentes" else 40, 40, 32, 14, 28, 30)):
            ws.column_dimensions[letra].width = ancho
    destino.parent.mkdir(parents=True, exist_ok=True)
    wb.save(destino)


def main():
    config = cargar_config()
    f = homologar(cargar(config))
    excel_derivadas(f, DERIVADAS)
    n1, n2 = int((f["fuente"] == "secop1").sum()), int((f["fuente"] == "secop2").sum())
    inv = pd.DataFrame(INVENTARIO, columns=["concepto", "SECOP I", "SECOP II", "equivalencia", "nota"])
    cat, num, inc, dist = calidad_categoricas(f), calidad_numericas(f), inconsistencias(f), distribucion_valor(f)
    m, vars_, comp, x = cramer_pares(f)
    vf = v_con_fuente(x, vars_, comp)
    corr_mod = f.groupby(["fuente", "modalidad", "modalidad_grupo"]).size().rename("contratos").reset_index()
    corr_mod["contratos"] = corr_mod["contratos"].map(entero)
    corr_ent = f.groupby(["tipo_entidad", "fuente"]).size().unstack(fill_value=0).reset_index()
    sin_tipo = f.groupby("fuente")["tipo_contrato_hom"].apply(lambda s: coma((s == "sin_equivalente").mean() * 100))
    matriz = m.apply(lambda col: col.map(lambda v: coma(v, 2))).reset_index().rename(columns={"index": "variable"})
    L = ["# Perfil de variables de los contratos `funerario` (SECOP I y II, 2020–2025)", "",
         "Solo diagnóstico: no propone método, no corre modelos y no registra decisiones. Generado por `python -m src.modelos.perfil_variables`. "
         f"Universo: contratos con clase final `funerario` (TF-IDF con la jerarquía de etiquetas, D84): **{entero(len(f))}** ({entero(n1)} de SECOP I y {entero(n2)} de SECOP II).", "",
         "Convenciones: «faltante» es nulo o vacío; «centinela» es un valor que nombra la ausencia («No Definido», «No aplica», «UNSPECIFIED», «Otro»). Las categorías raras tienen menos de 1 % de los contratos con dato de su fuente.", "",
         "## 1. Inventario de columnas útiles para patrones", "", tabla(inv), "",
         "## 2. Calidad por variable y fuente", "", "### 2a. Variables categóricas", "", tabla(cat), "",
         "### 2b. Variables numéricas, fechas y duración", "", tabla(num), "",
         "### 2c. Valores inconsistentes", "", "Contratos (y porcentaje de la fuente) que violan cada regla; «no aplica» cuando la columna no existe en esa fuente.", "", tabla(inc), "",
         "## 3. Homologación entre SECOP I y SECOP II", "",
         "### Modalidad (agrupada con `modalidad_grupo`)", "", tabla(corr_mod), "",
         "### Tipo de contrato", "", tabla(pd.DataFrame(TIPO_CONTRATO, columns=["SECOP I", "SECOP II"])), "",
         f"Contratos en categorías sin equivalente en la otra fuente (las que aparecen con «—»): SECOP I {sin_tipo.get('secop1')} %, SECOP II {sin_tipo.get('secop2')} %. «Otro» y «Otro Tipo de Contrato» se tratan como correspondientes aunque no se sabe qué contienen.", "",
         "### Destino del gasto", "", tabla(pd.DataFrame(DESTINO_GASTO, columns=["SECOP I", "SECOP II"])), "",
         "### Tipo de documento del proveedor", "", tabla(pd.DataFrame(TIPO_DOC, columns=["SECOP I", "SECOP II"])), "",
         "### Orden, nivel y sector", "",
         "SECOP I: `nivel_entidad` (territorial o nacional) y `orden_entidad` (11 valores, con nivel municipal 1 a 6 y departamental centralizado o descentralizado). SECOP II: `orden` (territorial o nacional), `sector` (18 valores) y `rama` (4). Se pueden unir en territorial o nacional; la categoría municipal de SECOP I y el sector de SECOP II no tienen equivalente en la otra fuente.", "",
         "### Qué se puede unir y con qué pérdida", "",
         "- **Sin pérdida:** entidad (nombre, NIT), ubicación de la entidad, valor inicial, fechas de firma, inicio y fin, objeto, categoría UNSPSC.",
         "- **Con pérdida:** modalidad (se agrupa y se pierden las variantes «con ofertas» y las precisiones de ley), tipo de contrato (SECOP II separa seguros, servicios financieros y Decreto 092; SECOP I no), orden (se pierde la categoría municipal), tipo de documento del proveedor (SECOP II junta personas naturales y jurídicas bajo NIT), tamaño de empresa («No definido» en SECOP I).",
         "- **No se unen:** sector y rama (solo SECOP II), origen de los recursos (solo SECOP II), valor con adiciones (solo SECOP I), valor facturado y pagado y días adicionados (solo SECOP II), estado (SECOP I está filtrado por estado), lugar de ejecución (formatos distintos), número de oferentes (no existe en ninguno de los dos conjuntos).", "",
         "## 4. Variables derivadas para validar", "",
         f"`docs/revision_f4/derivadas.xlsx` (no se versiona): 20 contratos al azar (semilla {SEMILLA}) por cada variable derivada, en tres hojas (`tipo_entidad`, `modalidad_grupo` y `componentes`), con una columna `correcto` (sí o no) y otras para la corrección. El texto de los objetos va anonimizado.", "",
         "Tipo de entidad derivado, por fuente (todos los contratos `funerario`):", "", tabla(corr_ent), "",
         "## 5. Exploración", "", "### 5a. Distribución del valor (pesos constantes de 2025)", "", tabla(dist), "",
         "### 5b. V de Cramér entre pares de variables categóricas (con corrección de sesgo)", "",
         "La V va de 0 (sin asociación) a 1. Se calcula sobre las variables homologadas para que no mida solo que las dos plataformas usen vocabularios distintos.", "", tabla(matriz), "",
         "### 5c. V de Cramér de cada variable con la fuente", "",
         "Las filas con «(texto original)» comparan las categorías tal como vienen: si el vocabulario de las dos plataformas no coincide, la V sube por construcción (la última columna indica qué parte de los contratos está en categorías presentes en las dos fuentes). Las variables homologadas y derivadas separan mejor la forma de comprar de la plataforma. Se reporta también por período porque SECOP I domina 2020–2022.", "",
         tabla(vf), ""]
    DESTINO.write_text("\n".join(L), encoding="utf-8")
    print("escrito", DESTINO, len(L))
    print(inc.to_string())
    print(vf.to_string())


if __name__ == "__main__":
    main()
