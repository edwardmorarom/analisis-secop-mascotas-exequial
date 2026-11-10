"""D110: validación ampliada de DeepSeek frente a TF-IDF con las etiquetas humanas fuera de la muestra de 400.

python -m src.modelos.validacion_deepseek            # corre lo pendiente y reporta
python -m src.modelos.validacion_deepseek --informe  # solo recalcula métricas e informe con lo ya guardado
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from src.etl.comun import RAIZ, cargar_config, ruta
from src.evaluacion.metricas_ponderadas import fila_resumen
from src.modelos import deepseek_clasificador as ds
from src.modelos import etiquetas_humanas as eh
from src.modelos.clasificar_todos import predecir, universo
from src.modelos.comparar import regresion_logistica
from src.modelos.datos_clasificacion import CLASES, cargar
from src.modelos.tfidf_logistica import vectorizador

PRINCIPAL = ["validacion_60_revisada", "estrato_d_150", "humanitarios_40"]
SECUNDARIO = ["secop1_nuevos", "top_valor", "grupo5_revision", "adicionales_d81"]
CORRIDAS = 3
TOPE_USD = 1.50
LOGS = RAIZ / "logs"
INFORME = RAIZ / "docs" / "resultados" / "validacion_deepseek.md"


def registro(k):
    return LOGS / f"deepseek_validacion_343_r{k}.jsonl"


def conjunto(config):
    """Contratos con etiqueta humana que no están en la muestra de 400, con la jerarquía de D84."""
    t = eh.construir(config)
    m400 = t.loc[t["origen"] == "muestra_400", ["fuente", "llave"]]
    fuera = t.merge(m400.assign(_en400=1), on=["fuente", "llave"], how="left")
    fuera = fuera[fuera["_en400"].isna()].drop(columns="_en400")
    fuera = fuera[fuera["origen"].isin(PRINCIPAL + SECUNDARIO)]
    u = universo(config)[["fuente", "llave", "texto"]]
    d = fuera.merge(u, on=["fuente", "llave"], how="left", validate="one_to_one")
    assert d["texto"].notna().all(), "hay contratos etiquetados sin texto en el universo"
    d["clave"] = d["fuente"] + "|" + d["llave"].astype(str)
    return d.sort_values(["origen", "clave"]).reset_index(drop=True)


def pred_tfidf(config, d):
    muestra = cargar(config)
    v = vectorizador()
    modelo = regresion_logistica().fit(v.fit_transform(muestra["texto"]), muestra["etiqueta"])
    p = predecir(modelo, v.transform(d["texto"]))
    return [CLASES[i] for i in p.argmax(axis=1)]


def leer(k):
    f = registro(k)
    if not f.exists():
        return {}
    return {r["clave"]: r for r in map(json.loads, f.read_text(encoding="utf-8").splitlines()) if "clave" in r}


def gastado():
    regs = [r for k in range(1, CORRIDAS + 1) for r in leer(k).values() if "error" not in r]
    return ds.costo_real(regs)["costo_usd"] if regs else 0.0


def correr(config, d):
    modelo = config["llm"]["modelo"]
    ejemplos = ds.elegir_ejemplos(cargar(config))
    c = ds.cliente()
    LOGS.mkdir(exist_ok=True)
    for k in range(1, CORRIDAS + 1):
        hechos = leer(k)
        pendientes = [r for r in d.itertuples() if r.clave not in hechos or "error" in hechos[r.clave]]
        if not pendientes:
            continue
        estimado = gastado() + len(pendientes) * 0.0001
        if estimado > TOPE_USD:
            raise SystemExit(f"Tope de {TOPE_USD} USD: se detiene antes de la corrida {k} (estimado {estimado:.3f}).")

        def una(r):
            try:
                return {"clave": r.clave, **ds.llamar(c, modelo, ejemplos, r.texto),
                        "momento_utc": datetime.now(timezone.utc).isoformat()}
            except Exception as e:
                return {"clave": r.clave, "error": str(e)[:200], "tokens_entrada": 0, "tokens_salida": 0}

        with ThreadPoolExecutor(6) as pool, registro(k).open("a", encoding="utf-8") as f:
            if not hechos:
                f.write(json.dumps({"encabezado": True, "corrida": k, "modelo": modelo, "temperatura": 0,
                                    "thinking": "disabled", "ejemplos": ejemplos["id_muestra"].tolist(),
                                    "inicio": datetime.now(timezone.utc).isoformat()}, ensure_ascii=False) + "\n")
            for res in pool.map(una, pendientes):
                if res.get("modelo_devuelto") not in (None, modelo):
                    raise SystemExit(f"La API devolvió el modelo {res['modelo_devuelto']}, no {modelo}: se detiene.")
                f.write(json.dumps(res, ensure_ascii=False) + "\n")
                f.flush()


def votos(d):
    corridas, invalidas = [], 0
    for k in range(1, CORRIDAS + 1):
        h = leer(k)
        etq = []
        for cl in d["clave"]:
            r = h.get(cl, {})
            e, _ = ds.interpretar(r["respuesta"]) if "respuesta" in r else (None, None)
            invalidas += e is None
            etq.append(e)
        corridas.append(etq)
    c = np.array(corridas, dtype=object).T
    final, empates = [], 0
    for fila in c:
        val = [x for x in fila if x is not None]
        if not val:
            final.append("no_funerario")
            continue
        s = pd.Series(val).value_counts()
        if len(s) > 1 and s.iloc[0] == s.iloc[1]:
            empates += 1
            final.append(val[0])
        else:
            final.append(s.index[0])
    iguales = float(np.mean([len(set(f)) == 1 for f in c]))
    return final, c, {"respuestas_invalidas": int(invalidas), "empates": empates, "acuerdo_tres_corridas": iguales}


def metricas(d, preds, filtro):
    x = d[filtro]
    uno = np.ones(len(x))
    filas = []
    for nombre, p in preds.items():
        p = np.asarray(p)[filtro.values]
        f = fila_resumen(nombre, x["etiqueta"].values, p, uno, x["origen"].values)
        f["n"], f["funerarios"] = len(x), int((x["etiqueta"] == "funerario").sum())
        filas.append(f)
    return pd.DataFrame(filas).set_index("modelo")


def fmt(v, n=3):
    return f"{v:.{n}f}".replace(".", ",")


def informe(config, d, preds, extra, costo):
    proc = ruta(config, "processed")
    prin = d["origen"].isin(PRINCIPAL)
    tp, tt = metricas(d, preds, prin), metricas(d, preds, pd.Series(True, index=d.index))
    por_origen = pd.concat({o: metricas(d, preds, d["origen"] == o) for o in PRINCIPAL + SECUNDARIO if (d["origen"] == o).any()})
    tp.to_csv(proc / "tabla_validacion_343_principal.csv")
    tt.to_csv(proc / "tabla_validacion_343_todos.csv")
    por_origen.to_csv(proc / "tabla_validacion_343_por_origen.csv")
    d.drop(columns="texto").assign(pred_tfidf=preds["tfidf_logistica"], pred_deepseek=preds["deepseek_flash"]).to_parquet(
        proc / "predicciones_validacion_343.parquet", index=False)
    ganador = "deepseek_flash" if tp.loc["deepseek_flash", "f1_ic_bajo"] > tp.loc["tfidf_logistica", "f1_ic_alto"] else "tfidf_logistica"

    def linea(t, m):
        r = t.loc[m]
        return (f"| {m} | {int(r['n'])} | {int(r['funerarios'])} | {fmt(r['precision'])} | {fmt(r['sensibilidad'])} | "
                f"{fmt(r['f1'])} ({fmt(r['f1_ic_bajo'])}–{fmt(r['f1_ic_alto'])}) |")

    enc = "| Modelo | Contratos | Funerarios | Precisión | Sensibilidad | F1 (IC 95 %) |\n|---|---|---|---|---|---|"
    L = ["# Validación ampliada de DeepSeek frente a TF-IDF (D110)", "",
         f"Generado el {datetime.now(timezone.utc).date().isoformat()} con `python -m src.modelos.validacion_deepseek`. "
         "Métricas de la clase `funerario` sin ponderar, con bootstrap de 2.000 réplicas estratificado por origen (semilla 2026).", "",
         "## Conjunto principal (decide la regla de D110)", "",
         f"Lotes elegidos sin usar predicciones de ningún modelo: {', '.join(PRINCIPAL)}.", "", enc,
         linea(tp, "tfidf_logistica"), linea(tp, "deepseek_flash"), "",
         f"**Resultado de la regla:** {'DeepSeek reemplaza a TF-IDF' if ganador == 'deepseek_flash' else 'TF-IDF sigue como clasificador'} "
         f"(límite inferior de DeepSeek {fmt(tp.loc['deepseek_flash', 'f1_ic_bajo'])} frente a límite superior de TF-IDF "
         f"{fmt(tp.loc['tfidf_logistica', 'f1_ic_alto'])}).", "",
         "## Los 343 contratos (referencia; incluye lotes elegidos con predicciones del modelo)", "", enc,
         linea(tt, "tfidf_logistica"), linea(tt, "deepseek_flash"), "", "## Por origen", "",
         "| Origen | Modelo | Contratos | Funerarios | F1 | Precisión | Sensibilidad |", "|---|---|---|---|---|---|---|"]
    for (o, m), r in por_origen.iterrows():
        L.append(f"| {o} | {m} | {int(r['n'])} | {int(r['funerarios'])} | {fmt(r['f1'])} | {fmt(r['precision'])} | {fmt(r['sensibilidad'])} |")
    L += ["", "## Estabilidad de DeepSeek entre corridas", "",
          f"- Tres corridas con la misma instrucción y los mismos ocho ejemplos de D58; predicción final por mayoría.",
          f"- Contratos con la misma etiqueta en las tres corridas: {fmt(100 * extra['acuerdo_tres_corridas'], 1)} %.",
          f"- Respuestas inválidas: {extra['respuestas_invalidas']}; empates resueltos con la primera corrida: {extra['empates']}.",
          f"- Costo real de las tres corridas: {fmt(costo, 3)} USD.", "", "## Matrices de confusión del conjunto principal (filas: humano)", ""]
    for nombre, p in preds.items():
        ct = pd.crosstab(d.loc[prin, "etiqueta"], pd.Series(np.asarray(p)[prin.values], index=d.index[prin], name="modelo"))
        ct = ct.reindex(index=CLASES, columns=CLASES, fill_value=0)
        L += [f"**{nombre}**", "", "| humano \\ modelo | " + " | ".join(CLASES) + " |", "|---" * (len(CLASES) + 1) + "|"]
        L += [f"| {i} | " + " | ".join(str(v) for v in ct.loc[i]) + " |" for i in CLASES] + [""]
    INFORME.write_text("\n".join(L), encoding="utf-8")
    return ganador, tp


def main():
    config = cargar_config()
    d = conjunto(config)
    print(len(d), d["origen"].value_counts().to_dict())
    if "--informe" not in sys.argv:
        correr(config, d)
    final, _, extra = votos(d)
    preds = {"tfidf_logistica": pred_tfidf(config, d), "deepseek_flash": final}
    regs = [r for k in range(1, CORRIDAS + 1) for r in leer(k).values() if "error" not in r]
    ganador, tp = informe(config, d, preds, extra, ds.costo_real(regs)["costo_usd"] if regs else 0.0)
    print(tp.round(3).to_string())
    print("GANADOR:", ganador, "| costo USD:", round(gastado(), 4), "|", extra)


if __name__ == "__main__":
    main()
