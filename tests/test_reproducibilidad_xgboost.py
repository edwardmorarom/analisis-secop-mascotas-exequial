import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics import f1_score

from src.modelos import robustez


def _corrida():
    rng = np.random.default_rng(2026)
    x = csr_matrix(rng.random((200, 40)) * (rng.random((200, 40)) < 0.2))
    s = np.asarray(x[:, :3].sum(axis=1)).ravel() + rng.normal(0, 0.1, 200)
    y = np.digitize(s, [0.3, 0.8])
    modelo = robustez.xgb()
    modelo.fit(x[:150], y[:150])
    return f1_score(y[150:], modelo.predict(x[150:]), average="macro"), modelo.predict_proba(x[150:])


def test_xgboost_un_solo_hilo():
    assert robustez.xgb().get_params()["n_jobs"] == 1
    import os
    assert os.environ["OMP_NUM_THREADS"] == "1"


def test_dos_corridas_dan_el_mismo_f1():
    f1_a, p_a = _corrida()
    f1_b, p_b = _corrida()
    assert f1_a == f1_b
    assert np.array_equal(p_a, p_b)
