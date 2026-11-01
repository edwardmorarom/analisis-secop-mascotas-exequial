import json

import pandas as pd
import pytest

from src.etl import places
from src.etl.descargar_places import avance, correr

CFG = {"tamano_pagina": 20, "max_paginas": 3}
TERMINOS = ["cremación de mascotas", "funeraria de mascotas"]


def marco(n):
    return pd.DataFrame({
        "cod_divipola": [f"{i:05d}" for i in range(1, n + 1)],
        "minx": [float(i) for i in range(1, n + 1)], "miny": 0.0, "maxx": 100.0, "maxy": 1.0})


class ApiSimulada:
    def __init__(self, paginas_completas=False, falla_en=None):
        self.invocaciones = []
        self.paginas_completas = paginas_completas
        self.falla_en = falla_en

    def __call__(self, clave, peticion):
        self.invocaciones.append((peticion["locationRestriction"]["rectangle"]["low"]["longitude"],
                                  peticion["textQuery"], peticion.get("pageToken")))
        if self.falla_en and len(self.invocaciones) == self.falla_en:
            raise places.TopeDeLlamadas("HTTP 429 RESOURCE_EXHAUSTED")
        if self.paginas_completas:
            n = len(self.invocaciones)
            return {"places": [{"id": f"p{n}-{i}"} for i in range(20)], "nextPageToken": f"t{n}"}
        return {"places": [{"id": f"p{len(self.invocaciones)}"}]}


def test_corte_y_reanudacion_sin_repetir(tmp_path):
    registrados = []
    api1 = ApiSimulada()
    r1 = correr("k", marco(5), TERMINOS, CFG, tmp_path, corte=4, llamar=api1, registrar_archivo=registrados.append)
    assert r1["llamadas"] == 4 and len(api1.invocaciones) == 4
    assert r1["municipios_pendientes"] == 3 and "corte" in r1["motivo"]
    assert sorted(p.name for p in registrados) == ["places_00001.jsonl", "places_00002.jsonl"]
    assert not (tmp_path / "places_00003.jsonl").exists()

    api2 = ApiSimulada()
    r2 = correr("k", marco(5), TERMINOS, CFG, tmp_path, corte=100, llamar=api2)
    assert r2["motivo"] == "completa" and r2["municipios_pendientes"] == 0
    assert len(api2.invocaciones) == 6
    assert not set((x[0], x[1]) for x in api1.invocaciones) & set((x[0], x[1]) for x in api2.invocaciones)

    api3 = ApiSimulada()
    assert correr("k", marco(5), TERMINOS, CFG, tmp_path, corte=100, llamar=api3)["llamadas"] == 0
    assert api3.invocaciones == []


def test_cuota_agotada_no_reintenta_y_conserva_lo_guardado(tmp_path):
    registrados = []
    api = ApiSimulada(falla_en=3)
    r = correr("k", marco(3), TERMINOS, CFG, tmp_path, corte=100, llamar=api, registrar_archivo=registrados.append)
    assert len(api.invocaciones) == 3 and r["llamadas"] == 2 and "detenida" in r["motivo"]
    assert len(registrados) == 1 and not (tmp_path / "places_00002.jsonl").exists()
    guardado = (tmp_path / "places_00001.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(guardado) == 2 and json.loads(guardado[0])["termino"] == TERMINOS[0]

    api2 = ApiSimulada()
    r2 = correr("k", marco(3), TERMINOS, CFG, tmp_path, corte=100, llamar=api2)
    assert r2["municipios_pendientes"] == 0 and len(api2.invocaciones) == 4


def test_corte_en_medio_de_la_paginacion_retoma_desde_el_token(tmp_path):
    api1 = ApiSimulada(paginas_completas=True)
    r1 = correr("k", marco(1), ["x"], CFG, tmp_path, corte=2, llamar=api1)
    assert r1["llamadas"] == 2 and r1["municipios_pendientes"] == 1
    assert avance(tmp_path / "places_00001.jsonl")[("00001", "x")] == (3, "t2")

    api2 = ApiSimulada(paginas_completas=True)
    r2 = correr("k", marco(1), ["x"], CFG, tmp_path, corte=100, llamar=api2)
    assert r2["llamadas"] == 1 and api2.invocaciones[0][2] == "t2"
    assert r2["municipios_pendientes"] == 0


def test_clave_rechazada_detiene(tmp_path):
    def rechaza(clave, peticion):
        raise places.ClaveRechazada("HTTP 403")

    r = correr("k", marco(2), TERMINOS, CFG, tmp_path, corte=100, llamar=rechaza)
    assert r["motivo"].startswith("clave rechazada") and r["llamadas"] == 0


def test_llamar_trata_resource_exhausted_como_cuota(monkeypatch):
    class Respuesta:
        status_code = 403

        def json(self):
            return {"error": {"status": "RESOURCE_EXHAUSTED"}}

    monkeypatch.setattr(places.requests, "post", lambda *a, **k: Respuesta())
    with pytest.raises(places.TopeDeLlamadas):
        places.llamar("k", {})
