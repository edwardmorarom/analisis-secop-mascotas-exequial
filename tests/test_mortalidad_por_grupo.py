import pandas as pd
import pytest

from src.etl.comun import RAIZ

CSV = RAIZ / "docs/resultados/mortalidad_por_grupo.csv"


@pytest.mark.skipif(not CSV.exists(), reason="requiere python -m src.modelos.mortalidad_por_grupo")
def test_perfil_mortalidad_total_y_cuantiles_ordenados():
    p = pd.read_csv(CSV)
    assert set(p["grupo"]) == {f"Grupo {i}" for i in range(1, 9)} | {"Total"}
    assert (p["contratos_grupo"][p["grupo"] == "Total"] == 4992).all()
    assert (p["p25"] <= p["mediana"]).all() and (p["mediana"] <= p["p75"]).all()
    assert (p["contratos_con_tasa"] <= p["contratos_grupo"]).all()
