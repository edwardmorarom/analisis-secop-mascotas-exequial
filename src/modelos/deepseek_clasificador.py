import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

from src.etl.comun import RAIZ, cargar_config
from src.evaluacion.reglas_etiquetado import D20, D21
from src.modelos.datos_clasificacion import cargar, texto_contrato

N_EJEMPLOS = 8
MAX_CARACTERES_EJEMPLO = 260
CARACTERES_POR_TOKEN = (3.0, 3.5, 4.0)
TOKENS_SALIDA = 20
PRECIOS_USD_POR_MILLON = {"entrada_sin_cache": 0.30, "entrada_con_cache": 0.006, "salida": 1.20}
REGLAS_NUEVAS = [
    "Póliza de vida grupo con auxilio funerario → no_funerario (es una indemnización).",
    "Custodia y conservación de cuerpos NN o no reclamados → funerario; la custodia del cementerio como lugar es no_funerario.",
    "Infraestructura de salas de necropsia o de Medicina Legal → forense 1; una morgue sin necropsia → forense 0.",
    "Todo trabajo de búsqueda, identificación o información sobre personas desaparecidas, fosas o SIRDEC → forense 1.",
]
INSTRUCCION = (
    "Clasificas objetos de contratos públicos colombianos en tres clases: funerario, no_funerario o mixto, y marcas "
    "aparte forense (0 o 1). Responde solo un JSON con las claves \"etiqueta\" y \"forense\".\n\nCriterio:\n"
    + "\n".join(f"- {r}" for r in D20 + D21 + REGLAS_NUEVAS))


def elegir_ejemplos(d, semilla=2026):
    """Dos o tres casos cortos y claros por clase, más uno forense; se excluyen de la evaluación."""
    corto = d[d["texto"].str.len() <= MAX_CARACTERES_EJEMPLO]
    rng = np.random.default_rng(semilla)
    cupos = [("funerario", 0, 3), ("no_funerario", 0, 2), ("mixto", 0, 2), ("no_funerario", 1, 1)]
    ids = []
    for clase, forense, n in cupos:
        candidatos = corto[(corto["etiqueta"] == clase) & (corto["forense"] == forense) & ~corto["id_muestra"].isin(ids)]
        ids += list(rng.choice(candidatos["id_muestra"].values, min(n, len(candidatos)), replace=False))
    return d[d["id_muestra"].isin(ids)].sort_values("n")


def mensajes(ejemplos, texto):
    m = [{"role": "system", "content": INSTRUCCION}]
    for e in ejemplos.itertuples():
        m.append({"role": "user", "content": e.texto})
        m.append({"role": "assistant", "content": json.dumps({"etiqueta": e.etiqueta, "forense": int(e.forense)})})
    m.append({"role": "user", "content": texto})
    return m


def estimar(n_llamadas, caracteres_prefijo, caracteres_texto_total):
    """Costo en USD: el prefijo (instrucción y ejemplos) se factura sin caché una vez y con caché las demás."""
    p = PRECIOS_USD_POR_MILLON
    filas = []
    for cpt in CARACTERES_POR_TOKEN:
        prefijo, texto = caracteres_prefijo / cpt, caracteres_texto_total / cpt
        salida = n_llamadas * TOKENS_SALIDA * p["salida"] / 1e6
        con_cache = (prefijo + texto) * p["entrada_sin_cache"] / 1e6 + prefijo * (n_llamadas - 1) * p["entrada_con_cache"] / 1e6 + salida
        sin_cache = (prefijo * n_llamadas + texto) * p["entrada_sin_cache"] / 1e6 + salida
        filas.append({"caracteres_por_token": cpt, "tokens_prefijo": round(prefijo),
                      "tokens_entrada_totales": round(prefijo * n_llamadas + texto),
                      "costo_usd_con_cache": round(con_cache, 2), "costo_usd_sin_cache": round(sin_cache, 2)})
    return pd.DataFrame(filas)


HORAS_PICO_UTC = list(range(1, 4)) + list(range(6, 10))
REGISTRO = RAIZ / "logs" / "deepseek_evaluacion.jsonl"
ETIQUETAS_VALIDAS = {"funerario", "no_funerario", "mixto"}


def en_hora_pico(ahora=None):
    from datetime import datetime, timezone
    ahora = ahora or datetime.now(timezone.utc)
    return ahora.weekday() < 5 and ahora.hour in HORAS_PICO_UTC


def cliente():
    from dotenv import load_dotenv
    from openai import OpenAI
    load_dotenv()
    return OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url=cargar_config()["llm"]["base_url"])


def llamar(c, modelo, ejemplos, texto):
    r = c.chat.completions.create(model=modelo, messages=mensajes(ejemplos, texto), temperature=0, max_tokens=60,
                                  response_format={"type": "json_object"}, extra_body={"thinking": {"type": "disabled"}})
    u = r.usage
    return {"respuesta": r.choices[0].message.content, "modelo_devuelto": r.model,
            "tokens_entrada": u.prompt_tokens, "tokens_salida": u.completion_tokens,
            "tokens_cache_hit": getattr(u, "prompt_cache_hit_tokens", None),
            "tokens_cache_miss": getattr(u, "prompt_cache_miss_tokens", None)}


def interpretar(respuesta):
    try:
        j = json.loads(respuesta)
        etiqueta, forense = str(j["etiqueta"]).strip().lower(), int(j["forense"])
        return (etiqueta, forense) if etiqueta in ETIQUETAS_VALIDAS and forense in (0, 1) else (None, None)
    except (ValueError, KeyError, TypeError):
        return None, None


def costo_real(registros):
    p = PRECIOS_USD_POR_MILLON
    hit = sum(r.get("tokens_cache_hit") or 0 for r in registros)
    miss = sum(r.get("tokens_cache_miss") if r.get("tokens_cache_miss") is not None else r["tokens_entrada"] for r in registros)
    salida = sum(r["tokens_salida"] for r in registros)
    return {"llamadas": len(registros), "tokens_cache_hit": hit, "tokens_cache_miss": miss, "tokens_salida": salida,
            "costo_usd": (hit * p["entrada_con_cache"] + miss * p["entrada_sin_cache"] + salida * p["salida"]) / 1e6}


def evaluar(forzar_pico=False, trabajadores=6):
    from concurrent.futures import ThreadPoolExecutor
    from datetime import datetime, timezone
    if en_hora_pico() and not forzar_pico:
        raise SystemExit("Hora pico de DeepSeek (01-04 y 06-10 UTC entre semana): se pospone la corrida.")
    config = cargar_config()
    modelo = config["llm"]["modelo"]
    d = cargar()
    ejemplos = elegir_ejemplos(d)
    prueba = d[~d["id_muestra"].isin(ejemplos["id_muestra"])]
    REGISTRO.parent.mkdir(exist_ok=True)
    hechos = {}
    if REGISTRO.exists():
        for linea in REGISTRO.read_text(encoding="utf-8").splitlines():
            r = json.loads(linea)
            if "id_muestra" in r:
                hechos[r["id_muestra"]] = r
    else:
        REGISTRO.write_text(json.dumps({"encabezado": True, "modelo": modelo, "temperatura": 0, "thinking": "disabled",
                                        "instruccion": INSTRUCCION, "ejemplos": ejemplos["id_muestra"].tolist(),
                                        "inicio": datetime.now(timezone.utc).isoformat()}, ensure_ascii=False) + "\n",
                            encoding="utf-8")
    pendientes = [r for r in prueba.itertuples() if r.id_muestra not in hechos]
    c = cliente()

    def una(r):
        for intento in range(3):
            try:
                return {"id_muestra": r.id_muestra, **llamar(c, modelo, ejemplos, r.texto),
                        "momento_utc": datetime.now(timezone.utc).isoformat()}
            except Exception as e:
                error = str(e)[:200]
        return {"id_muestra": r.id_muestra, "error": error, "tokens_entrada": 0, "tokens_salida": 0}

    with ThreadPoolExecutor(trabajadores) as pool, REGISTRO.open("a", encoding="utf-8") as f:
        for resultado in pool.map(una, pendientes):
            f.write(json.dumps(resultado, ensure_ascii=False) + "\n")
            f.flush()
    return modelo


def cargar_resultados():
    registros = [json.loads(l) for l in REGISTRO.read_text(encoding="utf-8").splitlines()]
    return [r for r in registros if "id_muestra" in r]
