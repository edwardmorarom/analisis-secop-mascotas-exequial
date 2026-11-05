import pandas as pd
import pytest

from src.modelos.grupos_hcpc import caracteristicas, descripcion, etiqueta, fmt, fv, grupos_reportados, recortar


def test_grupos_reportados_por_jaccard_y_tamano_con_nombres_por_tamano():
    estab = pd.DataFrame({"grupo": [1, 2, 3, 4], "contratos": [50, 900, 5, 45], "jaccard_medio": [0.9, 0.8, 0.99, 0.5]})
    tam = pd.DataFrame({"grupo": [1, 2, 3, 4], "pct": [5.0, 90.0, 0.5, 4.5]})
    r = grupos_reportados(estab, tam)
    assert r["grupo"].tolist() == [2, 1] and r["nombre"].tolist() == ["Grupo 1", "Grupo 2"]


def test_etiquetas_y_formatos():
    assert etiqueta("tipo_entidad=tipo_entidad_alcaldia_municipio") == "tipo_entidad: alcaldia_municipio"
    assert etiqueta("traslado=traslado_si") == "traslado: sí" and etiqueta("traslado=traslado_no") == "traslado: no"
    assert fmt(1234.5) == "1.234,5" and fv(float("inf")) == "∞" and fv(-float("inf")) == "−∞"
    assert recortar("a" * 300).endswith("…") and len(recortar("a" * 300)) == 181


def test_caracteristicas_filtra_por_v_y_ordena():
    v = pd.DataFrame({"grupo": [1, 1, 1, 2], "categoria": ["traslado=traslado_si", "tipo_entidad=tipo_entidad_x", "traslado=traslado_no", "a=a_b"],
                      "pct_de_la_categoria_en_el_grupo": [1.0] * 4, "pct_del_grupo_en_la_categoria": [80.0, 5.0, 20.0, 1.0],
                      "pct_global": [6.0, 4.0, 94.0, 1.0], "v_test": [float("inf"), 1.5, -float("inf"), 9.0], "p": [0] * 4})
    c = caracteristicas(v, 1)
    assert c["categoria"].tolist() == ["traslado: sí", "traslado: no"]


def test_descripcion_exige_categorias_sobrerrepresentadas():
    carac = pd.DataFrame({"categoria": ["tipo_entidad: alcaldia_municipio"], "pct_grupo": [99.3], "pct_total": [88.7], "v_test": [24.7]})
    with pytest.raises(ValueError):
        descripcion(5, carac)
