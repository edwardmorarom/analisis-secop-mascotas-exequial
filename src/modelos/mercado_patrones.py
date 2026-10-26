import re

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from unidecode import unidecode

from src.etl.anonimizar import anonimizar

SUBTIPOS = ["inhumacion_NN_vulnerables", "plan_o_poliza_exequial", "traslado", "cremacion", "cofres_y_bienes",
            "operacion_cementerio", "disposicion_animales", "otro"]
MODALIDADES = [
    ("contratacion_directa", r"CONTRATACION DIRECTA"),
    ("regimen_especial", r"REGIMEN ESPECIAL"),
    ("minima_cuantia", r"MINIMA CUANTIA"),
    ("seleccion_abreviada", r"SELECCION ABREVIADA|SUBASTA"),
    ("licitacion_concurso", r"LICITACION|CONCURSO"),
]
TIPOS_ENTIDAD = [
    ("salud_hospital_ese", r"\bE\.?S\.?E\.?\b|HOSPITAL|SALUD|CLINICA"),
    ("alcaldia_municipio", r"ALCALDIA|MUNICIPIO|CONCEJO|PERSONERIA"),
    ("gobernacion_departamento", r"GOBERNACION|DEPARTAMENTO|ASAMBLEA"),
    ("servicios_publicos_empresa", r"EMPRESA|\bE\.?S\.?P\.?\b|SERVICIOS PUBLICOS|ACUEDUCTO|ENERGIA"),
    ("educacion_universidad", r"UNIVERSIDAD|COLEGIO|INSTITUCION EDUCATIVA|SENA|ESCUELA"),
    ("seguridad_justicia", r"POLICIA|FISCALIA|CARCEL|INPEC|DEFENSA|EJERCITO|JUSTICIA|MEDICINA LEGAL"),
]
PALABRAS = {
    "animales": r"ANIMALES? MUERTOS?|FAUNA|ANIMALES? DE COMPANIA|MASCOTA|CANINO|FELINO|ZOONOSIS",
    "cremacion": r"CREMACI|INCINERACI",
    "plan_poliza": r"(PLAN|POLIZA|SEGURO|AUXILIO|PREVISION).{0,40}(EXEQU|FUNERA|FUNEBRE)|(EXEQU|FUNERA|FUNEBRE).{0,40}(POLIZA|SEGURO|PLAN )",
    "traslado": r"(TRASLADO|TRANSPORTE|RECOLECCION|LEVANTAMIENTO).{0,40}(CADAVER|CUERPO|RESTOS|DIFUNTO)",
    "bienes": r"COFRE|ATAUD|URNA|LAPIDA|MORTUORI|CAJA FUNERARIA|CARROZA|FLORES",
    "vulnerables": r"\bNN\b|NO IDENTIFICAD|NO RECLAMAD|VULNERABLE|VULNERABILIDAD|ESCASOS RECURSOS|INDIGENT|ABANDON|POBREZA|POBRES|SOLEMNIDAD|SIN FAMILIA|HABITANTE.{0,3} DE CALLE|VICTIMAS|N\.N|ADULTOS? MAYORES?",
    "servicio": r"FUNERA|INHUMA|SEPELIO|EXEQU|SEPULT|EXHUMA|FUNEBRE",
    "cementerio": r"CEMENTERIO|BOVEDA|OSARIO|SEPULTURERO|CAMPOSANTO",
    "operacion": r"ADMINISTRACION|OPERACION|ARRENDAMIENTO|CONCESION|INHUMA|EXHUMA|SEPULTURERO|MANTENIMIENTO",
}


def normalizar_texto(t):
    return unidecode(str(t or "")).upper()


def subtipo_unico_reemplazado(texto, animales):
    """Versión anterior de D68 (un subtipo con prioridad), reemplazada por los indicadores de componentes; solo se conserva."""
    t = normalizar_texto(texto)
    f = {k: re.search(v, t) is not None for k, v in PALABRAS.items()}
    if animales or f["animales"]:
        return "disposicion_animales"
    if f["cremacion"]:
        return "cremacion"
    if f["plan_poliza"]:
        return "plan_o_poliza_exequial"
    if f["traslado"]:
        return "traslado"
    if f["bienes"] and not f["vulnerables"]:
        return "cofres_y_bienes"
    if f["vulnerables"] and (f["servicio"] or f["bienes"]):
        return "inhumacion_NN_vulnerables"
    if f["cementerio"] and f["operacion"]:
        return "operacion_cementerio"
    return "otro"


COMPONENTES = {
    "incluye_inhumacion_cremacion": r"INHUMA|CREMACI|INCINERACI|EXHUMA|SEPULTURA|SEPELIO|SERVICIOS? (FUNERARIOS?|EXEQUIALES?)|APOYO EXEQUIAL|HONRAS FUNEBRES|ASISTENCIA FUNERARIA",
    "incluye_traslado": r"TRASLADO|MANEJO DE (CADAVERES|CUERPOS)|TRANSPORTE DE (CADAVER|CUERPO|RESTOS|DIFUNTO)|RECOLECCION DE (CADAVER|CUERPO)",
    "incluye_ataudes_bienes": r"COFRE|ATAUD|URNAS?|LAPIDA|MORTUORI|CAJAS? FUNERARIA|CARROZA|CENIZARIO",
    "incluye_plan_exequial": r"POLIZA|AFILIACION|AUXILIO (FUNERARIO|EXEQUIAL)|PLAN (EXEQUIAL|FUNERARIO|DE PREVISION)|SEGURO (EXEQUIAL|FUNERARIO)|PREVISION EXEQUIAL",
    "incluye_operacion_cementerio": r"(CEMENTERIO|BOVEDA|OSARIOS?|NICHO|CENIZARIO|SEPULTURERO).{0,120}(ADMINISTRACION|OPERACION|ARRIEND|ARRENDAMIENTO|CONCESION|MANTENIMIENTO|ADQUISICION)|(ADMINISTRACION|OPERACION|ARRIEND|ARRENDAMIENTO|CONCESION|MANTENIMIENTO|ADQUISICION).{0,120}(CEMENTERIO|BOVEDA|OSARIOS?|NICHO|CENIZARIO|SEPULTURERO)",
    "incluye_disposicion_animales": r"ANIMALES? MUERTOS?|FAUNA|ANIMALES? DE COMPANIA|MASCOTA|CANINO|FELINO|ZOONOSIS|VETERINARI|ANIMALES? EN CONDICION|ANIMALES? (ABANDONADOS|APREHENDIDOS)",
    "incluye_atencion_vulnerables_NN": r"NN|N\.N|NO IDENTIFICAD|SIN IDENTIFICAR|NO RECLAMAD|VULNERABL|VULNERABILIDAD|ESCASOS RECURSOS|BAJOS RECURSOS|POBRES?|POBREZA|SOLEMNIDAD|VICTIMAS?|ADULTOS? MAYORES?|INDIGENT|HABITANTE.{0,3} DE CALLE|SIN FAMILIA",
}


def indicadores(texto, animales=False):
    t = normalizar_texto(texto)
    out = {k: re.search(v, t) is not None for k, v in COMPONENTES.items()}
    if animales:
        out["incluye_disposicion_animales"] = True
    if out["incluye_disposicion_animales"]:
        out["incluye_atencion_vulnerables_NN"] = False
    return out


# Verdad por componente a partir del único subtipo que Edward marcó en 40 contratos.
VERDAD = {
    "inhumacion_NN_vulnerables": ("incluye_inhumacion_cremacion", "incluye_atencion_vulnerables_NN"),
    "cremacion": ("incluye_inhumacion_cremacion",), "traslado": ("incluye_traslado",),
    "cofres_y_bienes": ("incluye_ataudes_bienes",), "plan_o_poliza_exequial": ("incluye_plan_exequial",),
    "operacion_cementerio": ("incluye_operacion_cementerio",), "disposicion_animales": ("incluye_disposicion_animales",), "otro": (),
}
# Con la definición nueva (plan solo con plan, póliza, auxilio funerario o afiliación) estas filas dejan de ser plan.
CORRECCIONES = {10: "inhumacion_NN_vulnerables", 16: "inhumacion_NN_vulnerables", 31: "otro"}


def acierto_indicadores(ruta_excel):
    d = pd.read_excel(ruta_excel, dtype=str)
    d["subtipo_corregido"] = [CORRECCIONES.get(int(n), s) for n, s in zip(d["n"], d["subtipo_correcto"])]
    ind = pd.DataFrame([indicadores(o) for o in d["objeto"]])
    filas = []
    for nombre in COMPONENTES:
        verdad = pd.Series([nombre in VERDAD[s] for s in d["subtipo_corregido"]])
        pred = ind[nombre]
        vp, fp, fn = int((verdad & pred).sum()), int((~verdad & pred).sum()), int((verdad & ~pred).sum())
        filas.append({"indicador": nombre, "positivos_marcados_por_edward": int(verdad.sum()), "marcados_por_la_regla": int(pred.sum()),
                      "aciertos": int((verdad == pred).sum()), "acierto": (verdad == pred).mean(),
                      "precision": vp / (vp + fp) if vp + fp else np.nan, "sensibilidad": vp / (vp + fn) if vp + fn else np.nan,
                      "falsos_positivos": fp, "falsos_negativos": fn})
    return pd.DataFrame(filas), d.assign(**{k: ind[k].values for k in COMPONENTES})


def modalidad_grupo(m):
    t = normalizar_texto(m)
    for nombre, patron in MODALIDADES:
        if re.search(patron, t):
            return nombre
    return "otra"


def tipo_entidad(nombre):
    t = normalizar_texto(nombre)
    for k, patron in TIPOS_ENTIDAD:
        if re.search(patron, t):
            return k
    return "otra_entidad"


def preparar(d):
    f = d[d["clase_final"] == "funerario"].copy()
    f["modalidad_grupo"] = f["modalidad"].map(modalidad_grupo)
    f["tipo_entidad"] = f["entidad"].map(tipo_entidad)
    for k in COMPONENTES:
        f[k] = False
    ind = pd.DataFrame([indicadores(o, bool(a)) for o, a in zip(f["objeto"], f["posible_disposicion_animales"])], index=f.index)
    for k in COMPONENTES:
        f[k] = ind[k]
    return f


def agregado(f, por):
    g = f.groupby(por).agg(contratos=("valor", "size"), valor_corriente=("valor", "sum"),
                           valor_constante_2025=("valor_constante_2025", "sum")).reset_index()
    g["pct_contratos"] = g["contratos"] / g["contratos"].sum() * 100
    g["pct_valor"] = g["valor_constante_2025"] / g["valor_constante_2025"].sum() * 100
    return g


def modalidad_directa(f):
    filas = []
    for (anio, fuente), x in f.groupby(["anio", "fuente"]):
        total = x["valor_constante_2025"].sum()
        directa = x.loc[x["modalidad_grupo"] == "contratacion_directa", "valor_constante_2025"].sum()
        especial = x.loc[x["modalidad_grupo"] == "regimen_especial", "valor_constante_2025"].sum()
        filas.append({"anio": anio, "fuente": fuente, "contratos": len(x), "valor_constante_2025": total,
                      "pct_valor_directa": directa / total * 100, "pct_valor_directa_y_especial": (directa + especial) / total * 100,
                      "pct_contratos_directa": (x["modalidad_grupo"] == "contratacion_directa").mean() * 100})
    return pd.DataFrame(filas)


def hhi_cr4(x, valor="valor_constante_2025"):
    s = x.groupby("proveedor_id")[valor].sum()
    s = s[s > 0]
    if s.empty:
        return {"proveedores": 0, "HHI": np.nan, "CR4": np.nan}
    p = s / s.sum()
    return {"proveedores": len(p), "HHI": float((p * 100).pow(2).sum()), "CR4": float(p.nlargest(4).sum() * 100)}


def proveedores_por_anio(f):
    return pd.DataFrame([{"anio": a, **hhi_cr4(x)} for a, x in f.groupby("anio")])


def proveedores_por_departamento(f, nombres_dep):
    filas = []
    for cod, x in f[f["cod_dpto"].notna()].groupby("cod_dpto"):
        filas.append({"cod_dpto": cod, "departamento": nombres_dep.get(cod), **hhi_cr4(x), "contratos": len(x),
                      "valor_constante_2025": x["valor_constante_2025"].sum()})
    return pd.DataFrame(filas)


def participacion_proveedores(f, n=10):
    g = f.groupby(["proveedor_id", "proveedor_persona_natural"]).agg(contratos=("valor", "size"),
                                                                     valor_constante_2025=("valor_constante_2025", "sum")).reset_index()
    g["participacion_valor_pct"] = g["valor_constante_2025"] / g["valor_constante_2025"].sum() * 100
    return g.sort_values("valor_constante_2025", ascending=False).head(n)


def excel_subtipos(f, destino, n=40, semilla=2026):
    rng = np.random.default_rng(semilla)
    partes = []
    por = max(1, n // len(SUBTIPOS))
    for s in SUBTIPOS:
        g = f[f["subtipo"] == s]
        partes.append(g.sample(min(por, len(g)), random_state=int(rng.integers(2**31))))
    m = pd.concat(partes)
    faltan = n - len(m)
    if faltan > 0:
        resto = f[~f.index.isin(m.index)]
        m = pd.concat([m, resto.sample(min(faltan, len(resto)), random_state=semilla)])
    m = m.sample(frac=1, random_state=semilla).reset_index(drop=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "Subtipos"
    ws.append(["n", "fuente", "anio", "objeto", "subtipo_asignado", "subtipo_correcto", "nota"])
    for c in ws[1]:
        c.font = Font(bold=True)
    for i, r in enumerate(m.itertuples(), 1):
        ws.append([i, r.fuente, int(r.anio), anonimizar(r.objeto), r.subtipo, None, None])
        ws.cell(i + 1, 4).alignment = Alignment(wrap_text=True, vertical="top")
        ws.cell(i + 1, 6).fill = PatternFill("solid", fgColor="FFF2CC")
    dv = DataValidation(type="list", formula1='"' + ",".join(SUBTIPOS) + '"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"F2:F{ws.max_row}")
    for letra, ancho in zip("ABCDEFG", (5, 9, 7, 90, 26, 26, 40)):
        ws.column_dimensions[letra].width = ancho
    ws.freeze_panes = "A2"
    destino.parent.mkdir(parents=True, exist_ok=True)
    wb.save(destino)
    return len(m)


def componentes_tabla(f):
    total_v = f["valor_constante_2025"].sum()
    filas = []
    for k in COMPONENTES:
        x = f[f[k]]
        filas.append({"componente": k, "contratos": len(x), "pct_contratos": len(x) / len(f) * 100,
                      "valor_constante_2025": x["valor_constante_2025"].sum(), "pct_valor": x["valor_constante_2025"].sum() / total_v * 100})
    sin = f[~f[list(COMPONENTES)].any(axis=1)]
    filas.append({"componente": "ninguno_de_los_componentes", "contratos": len(sin), "pct_contratos": len(sin) / len(f) * 100,
                  "valor_constante_2025": sin["valor_constante_2025"].sum(), "pct_valor": sin["valor_constante_2025"].sum() / total_v * 100})
    return pd.DataFrame(filas)


def componentes_anual(f):
    filas = []
    for anio, g in f.groupby("anio"):
        for k in COMPONENTES:
            x = g[g[k]]
            filas.append({"anio": anio, "componente": k, "contratos": len(x), "pct_contratos": len(x) / len(g) * 100,
                          "pct_valor": x["valor_constante_2025"].sum() / g["valor_constante_2025"].sum() * 100})
    return pd.DataFrame(filas)
