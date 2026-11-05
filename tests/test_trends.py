import pandas as pd

from src.etl.trends import cod_dpto, codigos_departamento, leer, serie_nacional, tabla_departamentos


def escribir(ruta, termino, filas, primera="Región"):
    ruta.write_text(f"Categoría: Todas las categorías\n\n{primera},{termino}: (21/10/21 - 21/10/26)\n" + "\n".join(filas) + "\n", encoding="utf-8")


def test_departamentos_detectables_y_termino_del_encabezado(tmp_path):
    escribir(tmp_path / "trends_funeraria_mascotas_subregion_x.csv", "funeraria de mascotas", ["Cauca,100", "Bogotá,69", "Amazonas,"])
    escribir(tmp_path / "trends_cremacion_mascotas_subregion_x.csv", "cementerio de mascotas", ["Cauca,50"])
    t = tabla_departamentos(tmp_path)
    f = t[t.termino == "funeraria de mascotas"].set_index("departamento")
    assert f.loc["Cauca", "interes_detectable"] and not f.loc["Amazonas", "interes_detectable"]
    assert f["termino_valido"].all() and f.loc["Bogotá", "cod_dpto"] == "11" and f.loc["Cauca", "cod_dpto"] == "19"
    c = t[t.termino == "cremación de mascotas"]
    assert not c["termino_valido"].any() and c["termino_encabezado"].iloc[0] == "cementerio de mascotas"


def test_codigos_de_departamento_con_alias():
    codigos = codigos_departamento()
    assert cod_dpto("San Andrés y Providencia", codigos) == "88"
    assert cod_dpto("Norte de Santander", codigos) == "54" and cod_dpto("Santander", codigos) == "68"
    assert cod_dpto("Valle del Cauca", codigos) == "76"


def test_serie_nacional_marca_semanas_con_interes(tmp_path):
    escribir(tmp_path / "trends_funeraria_mascotas_tiempo_x.csv", "funeraria de mascotas", ["2022-05-15,73", "2022-05-22,0"], primera="Semana")
    s = serie_nacional(tmp_path)
    assert s["interes_detectable"].tolist() == [True, False] and leer(tmp_path / "trends_funeraria_mascotas_tiempo_x.csv")[0] == "funeraria de mascotas"
