from src.agentes import verificar_paquete as vp


def test_verifica_correctos_faltantes_y_distintos(tmp_path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "a.txt").write_text("uno", encoding="utf-8")
    (tmp_path / "data" / "b.txt").write_text("dos", encoding="utf-8")
    sumas = tmp_path / "SHA256SUMS.txt"
    sumas.write_text(
        f"{vp.sha256(tmp_path / 'data' / 'a.txt')}  data/a.txt\n"
        f"{vp.sha256(tmp_path / 'data' / 'b.txt')}  data/b.txt\n"
        f"{'0' * 64}  data/c.txt\n", encoding="utf-8")
    (tmp_path / "data" / "b.txt").write_text("alterado", encoding="utf-8")
    correctos, faltantes, distintos = vp.verificar(sumas, tmp_path)
    assert correctos == ["data/a.txt"]
    assert faltantes == ["data/c.txt"]
    assert distintos == ["data/b.txt"]
    assert vp.main([str(sumas)]) == 1


def test_codigo_de_salida_cero_si_todo_coincide(tmp_path):
    (tmp_path / "x.txt").write_text("x", encoding="utf-8")
    sumas = tmp_path / "SHA256SUMS.txt"
    sumas.write_text(f"{vp.sha256(tmp_path / 'x.txt')}  x.txt\n", encoding="utf-8")
    assert vp.main([str(sumas)]) == 0
