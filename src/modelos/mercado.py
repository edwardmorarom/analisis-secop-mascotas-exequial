import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from src.etl.comun import RAIZ, cargar_config, ruta
from src.etl.extraer_minsalud import cargar_pob_dane
from src.modelos.mercado_base import construir_universo

CARPETA_RESULTADOS = "resultados_secop"


def excel_cruces(d, divipola, destino, n=20, semilla=2026):
    aprox = d[d["metodo_cruce"] == "aproximado"].groupby(["departamento_entidad", "municipio_entidad", "cod_divipola", "puntaje_cruce"]).size()
    aprox = aprox.rename("contratos").reset_index()
    nombres = divipola.set_index("Código Municipio")["Nombre Municipio"]
    aprox["municipio_divipola"] = aprox["cod_divipola"].map(nombres)
    muestra = aprox.sample(min(n, len(aprox)), random_state=semilla).sort_values("contratos", ascending=False)
    wb = Workbook()
    ws = wb.active
    ws.title = "Cruces"
    ws.append(["departamento_entidad", "municipio_entidad", "cod_divipola", "municipio_divipola", "puntaje", "contratos", "correcto", "nota"])
    for c in ws[1]:
        c.font = Font(bold=True)
    for r in muestra.itertuples():
        ws.append([r.departamento_entidad, r.municipio_entidad, r.cod_divipola, r.municipio_divipola, round(r.puntaje_cruce, 1), r.contratos, None, None])
    dv = DataValidation(type="list", formula1='"sí,no"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"G2:G{ws.max_row}")
    for letra, ancho in zip("ABCDEFGH", (28, 30, 12, 30, 9, 10, 10, 40)):
        ws.column_dimensions[letra].width = ancho
    for fila in range(2, ws.max_row + 1):
        ws.cell(fila, 7).fill = PatternFill("solid", fgColor="FFF2CC")
    destino.parent.mkdir(parents=True, exist_ok=True)
    wb.save(destino)
    return len(aprox), len(muestra)


def main():
    config = cargar_config()
    divipola = pd.read_csv(ruta(config, "raw") / "dane" / "dane_divipola.csv", dtype=str)
    salida = ruta(config, "processed") / CARPETA_RESULTADOS
    salida.mkdir(parents=True, exist_ok=True)
    d = construir_universo(config)
    d.to_parquet(salida / "universo_mercado.parquet", index=False)
    con_codigo = d["cod_divipola"].notna()
    resumen = pd.DataFrame({
        "universo": [len(d), int(con_codigo.sum()), int(d["cod_dpto"].notna().sum())],
        "funerario_tfidf": [int((d["clase_final"] == "funerario").sum()), int((con_codigo & (d["clase_final"] == "funerario")).sum()),
                            int(((d["clase_final"] == "funerario") & d["cod_dpto"].notna()).sum())]},
        index=["contratos", "con_municipio_DIVIPOLA", "con_departamento"])
    resumen["tasa_universo"] = resumen["universo"] / len(d)
    resumen.to_csv(salida / "tasa_cruce_ubicacion.csv", encoding="utf-8-sig")
    print(resumen.round(4).to_string())
    print(d["metodo_cruce"].value_counts().to_dict())
    escribir_tablas(config, d, salida, divipola)
    _, pa, dep, n_excel = escribir_patrones(d, salida, divipola)
    print("indicadores de componentes evaluados:", n_excel)
    from src.modelos import mercado_graficos, mercado_informe
    mercado_graficos.estilo()
    mercado_graficos.main()
    mercado_informe.main()
    destino_cruces = RAIZ / "docs" / "revision_f4" / "cruces_secop.xlsx"
    if not destino_cruces.exists():
        print("excel de cruces aproximados:", excel_cruces(d, divipola, destino_cruces))



ESCENARIOS = {
    "tfidf_sin_mixto": ("pred_tfidf", ("funerario",)),
    "tfidf_con_mixto": ("pred_tfidf", ("funerario", "mixto")),
    "e5_sin_mixto": ("pred_e5", ("funerario",)),
    "e5_con_mixto": ("pred_e5", ("funerario", "mixto")),
}


def poblaciones(config, anios):
    return {a: cargar_pob_dane(config, a) for a in anios}


def serie_anual(d):
    filas = []
    for nombre, (col, clases) in ESCENARIOS.items():
        g = d[d[col].isin(clases)].groupby("anio").agg(contratos=("valor", "size"), valor_corriente=("valor", "sum"),
                                                          valor_constante_2025=("valor_constante_2025", "sum"))
        filas.append(g.reset_index().assign(escenario=nombre))
    todo = d.groupby("anio").agg(contratos_candidatos=("valor", "size"), valor_candidatos_constante=("valor_constante_2025", "sum")).reset_index()
    return pd.concat(filas).merge(todo, on="anio")


def por_territorio(d, pobs, nivel):
    llave = "cod_dpto" if nivel == "departamento" else "cod_divipola"
    f = d[(d["clase_final"] == "funerario") & d[llave].notna()]
    g = f.groupby([llave, "anio"]).agg(contratos=("valor", "size"), valor_constante_2025=("valor_constante_2025", "sum"),
                                       valor_corriente=("valor", "sum")).reset_index()
    if nivel == "departamento":
        poblacion = {a: p.groupby(p.index.str[:2]).sum() for a, p in pobs.items()}
    else:
        poblacion = pobs
    g["poblacion"] = [poblacion[a].get(c, np.nan) for c, a in zip(g[llave], g["anio"])]
    g["contratos_x100mil"] = g["contratos"] / g["poblacion"] * 1e5
    g["valor_constante_x100mil"] = g["valor_constante_2025"] / g["poblacion"] * 1e5
    resumen = g.groupby(llave).agg(contratos=("contratos", "sum"), valor_constante_2025=("valor_constante_2025", "sum"),
                                   valor_corriente=("valor_corriente", "sum"),
                                   contratos_x100mil_anual=("contratos_x100mil", "mean"),
                                   valor_constante_x100mil_anual=("valor_constante_x100mil", "mean"),
                                   poblacion_2025=("poblacion", "last")).reset_index()
    return g, resumen


def escribir_tablas(config, d, salida, divipola):
    anios = sorted(d["anio"].unique())
    pobs = poblaciones(config, anios)
    sa = serie_anual(d)
    sa.to_csv(salida / "serie_anual.csv", index=False, encoding="utf-8-sig")
    nombres_dep = divipola.drop_duplicates("Código Departamento").set_index("Código Departamento")["Nombre Departamento"]
    nombres_mun = divipola.set_index("Código Municipio")["Nombre Municipio"]
    gd, rd = por_territorio(d, pobs, "departamento")
    gm, rm = por_territorio(d, pobs, "municipio")
    rd.insert(1, "departamento", rd["cod_dpto"].map(nombres_dep))
    rm.insert(1, "municipio", rm["cod_divipola"].map(nombres_mun))
    rm.insert(2, "departamento", rm["cod_divipola"].str[:2].map(nombres_dep))
    serie_anual_fuente(d).to_csv(salida / "serie_anual_fuente.csv", index=False, encoding="utf-8-sig")
    for nombre, t in (("departamento_anual", gd), ("departamento_resumen", rd), ("municipio_anual", gm), ("municipio_resumen", rm)):
        t.to_csv(salida / f"{nombre}.csv", index=False, encoding="utf-8-sig")
    return sa, rd, rm


def serie_anual_fuente(d):
    f = d[d["clase_final"] == "funerario"]
    return f.groupby(["anio", "fuente"]).agg(contratos=("valor", "size"), valor_corriente=("valor", "sum"),
                                              valor_constante_2025=("valor_constante_2025", "sum")).reset_index()


def escribir_patrones(d, salida, divipola):
    from src.modelos import mercado_patrones as mp
    f = mp.preparar(d)
    nombres_dep = divipola.drop_duplicates("Código Departamento").set_index("Código Departamento")["Nombre Departamento"].to_dict()
    mp.agregado(f, ["fuente", "orden"]).to_csv(salida / "borrador_orden_entidad.csv", index=False, encoding="utf-8-sig")
    mp.agregado(f[f["fuente"] == "secop2"], ["sector"]).to_csv(salida / "borrador_sector_secop2.csv", index=False, encoding="utf-8-sig")
    mp.agregado(f, ["tipo_entidad"]).to_csv(salida / "borrador_tipo_entidad.csv", index=False, encoding="utf-8-sig")
    mp.agregado(f, ["modalidad_grupo"]).to_csv(salida / "borrador_modalidad.csv", index=False, encoding="utf-8-sig")
    mp.modalidad_directa(f).to_csv(salida / "borrador_modalidad_directa_anual.csv", index=False, encoding="utf-8-sig")
    mes = mp.agregado(f, ["mes"])
    mes["pct_valor_mes"] = mes["pct_valor"]
    mes.to_csv(salida / "borrador_mes_firma.csv", index=False, encoding="utf-8-sig")
    comp = mp.componentes_tabla(f)
    comp.to_csv(salida / "componentes.csv", index=False, encoding="utf-8-sig")
    mp.componentes_anual(f).to_csv(salida / "componentes_anual.csv", index=False, encoding="utf-8-sig")
    acierto, _ = mp.acierto_indicadores(RAIZ / "docs" / "revision_f4" / "subtipos.xlsx")
    acierto.to_csv(salida / "acierto_indicadores.csv", index=False, encoding="utf-8-sig")
    pa = mp.proveedores_por_anio(f)
    pa.to_csv(salida / "proveedores_hhi_cr4_anual.csv", index=False, encoding="utf-8-sig")
    pd_ = mp.proveedores_por_departamento(f, nombres_dep)
    pd_.to_csv(salida / "proveedores_hhi_departamento.csv", index=False, encoding="utf-8-sig")
    mp.participacion_proveedores(f, 15).to_csv(salida / "proveedores_top_participacion.csv", index=False, encoding="utf-8-sig")
    interim = ruta(cargar_config(), "interim")
    nombres = pd.concat([
        pd.read_parquet(interim / "secop1_senales.parquet", columns=["llave", "nom_razon_social_contratista"]).rename(
            columns={"nom_razon_social_contratista": "nombre_proveedor"}).assign(fuente="secop1"),
        pd.read_parquet(interim / "secop2_senales.parquet", columns=["llave", "proveedor_adjudicado"]).rename(
            columns={"proveedor_adjudicado": "nombre_proveedor"}).assign(fuente="secop2")])
    por_dep_anio, resumen_dep_anio = mp.hhi_departamento_anual(f, nombres_dep)
    por_dep_anio.to_csv(salida / "proveedores_hhi_departamento_anual.csv", index=False, encoding="utf-8-sig")
    resumen_dep_anio.to_csv(salida / "proveedores_hhi_departamento_resumen_anual.csv", index=False, encoding="utf-8-sig")
    g = f[f["anio"].between(2020, 2024)].nlargest(10, "valor_constante_2025").merge(nombres, on=["fuente", "llave"], how="left")
    g["proveedor"] = np.where(g["proveedor_persona_natural"], "(persona natural: no se muestra)", g["nombre_proveedor"])
    g[["anio", "fuente", "entidad", "valor", "valor_constante_2025", "proveedor", "modalidad", "p_tfidf_funerario", "p_e5_funerario",
       "pred_tfidf_modelo", "pred_e5_modelo", "objeto"]].to_csv(salida / "top10_contratos_2020_2024.csv", index=False, encoding="utf-8-sig")
    mp.top_contratos(f, 2025, nombres).to_csv(salida / "hhi_2025_top10_contratos.csv", index=False, encoding="utf-8-sig")
    mp.hhi_sin_mayores(f, 2025).to_csv(salida / "hhi_2025_sin_mayores.csv", index=False, encoding="utf-8-sig")
    comparacion = []
    for nombre, mascara in (("TF-IDF", d["pred_tfidf"] == "funerario"), ("e5", d["pred_e5"] == "funerario"),
                            ("ambos modelos", (d["pred_tfidf"] == "funerario") & (d["pred_e5"] == "funerario"))):
        g = mp.proveedores_por_anio(mp.preparar(d.assign(clase_final=np.where(mascara, "funerario", "otro"))))
        comparacion.append(g.assign(clasificacion=nombre))
    pd.concat(comparacion).to_csv(salida / "proveedores_hhi_por_clasificacion.csv", index=False, encoding="utf-8-sig")
    return f, pa, pd_, len(acierto)


if __name__ == "__main__":
    main()
