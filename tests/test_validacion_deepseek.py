import json

import pandas as pd

from src.modelos import validacion_deepseek as v


def escribir(ruta, filas):
    ruta.write_text("\n".join(json.dumps(f) for f in [{"encabezado": True}] + filas) + "\n", encoding="utf-8")


def resp(e):
    return json.dumps({"etiqueta": e, "forense": 0})


def test_votos_mayoria_empate_e_invalidas(tmp_path, monkeypatch):
    monkeypatch.setattr(v, "LOGS", tmp_path)
    d = pd.DataFrame({"clave": ["a", "b", "c", "d"]})
    r = {1: ["funerario", "mixto", "x", "funerario"], 2: ["funerario", "no_funerario", "x", "mixto"],
         3: ["no_funerario", "funerario", "x", "no_funerario"]}
    for k, etq in r.items():
        escribir(v.registro(k), [{"clave": c, "respuesta": resp(e) if e != "x" else "{}"} for c, e in zip(d["clave"], etq)])
    final, _, extra = v.votos(d)
    assert final == ["funerario", "mixto", "no_funerario", "funerario"]
    assert extra["respuestas_invalidas"] == 3
    assert extra["empates"] == 2
    assert extra["acuerdo_tres_corridas"] == 0.25
