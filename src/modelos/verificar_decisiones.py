"""Verifica que los archivos, módulos y commits citados en docs/decisiones.md (D84 en adelante) existan."""
import re
import subprocess
import sys

from src.etl.comun import RAIZ

EXT = r"(?:py|R|csv|parquet|md|xlsx|json|jsonl|pkl|rds|yaml|png|sha256|txt|pdf|docx)"
CARPETAS = ["", "data/processed/", "data/processed/resultados_secop/", "data/processed/resultados_secop/patrones/", "data/interim/", "data/raw/secop/",
            "docs/", "docs/resultados/", "docs/revision_f4/", "docs/etiquetado/", "src/modelos/", "src/etl/", "src/evaluacion/", "tests/", "data/raw/"]


def secciones(texto, desde=84):
    partes = re.split(r"(?m)^### D(\d+)\. ", texto)
    return {int(partes[i]): partes[i + 1] for i in range(1, len(partes) - 1, 2) if int(partes[i]) >= desde}


def candidatos(texto):
    rutas = set()
    for m in re.finditer(r"`([^`\n]+)`", texto):
        s = m.group(1).strip()
        if re.fullmatch(rf"[\w./\-*]+\.{EXT}", s) or re.fullmatch(r"src\.[\w.]+", s):
            rutas.add(s)
    return rutas


def existe(s):
    if s.startswith("src."):
        base = RAIZ / (s.replace(".", "/"))
        return base.with_suffix(".py").exists() or base.is_dir()
    if "*" in s:
        return any(RAIZ.glob(c + s) for c in CARPETAS)
    return any((RAIZ / (c + s)).exists() for c in CARPETAS)


def commit_existe(h):
    return subprocess.run(["git", "cat-file", "-e", f"{h}^{{commit}}"], cwd=RAIZ, capture_output=True).returncode == 0


def main(desde=84):
    texto = (RAIZ / "docs" / "decisiones.md").read_text(encoding="utf-8")
    faltan, commits_malos, total = [], [], 0
    for n, cuerpo in secciones(texto, desde).items():
        for s in sorted(candidatos(cuerpo)):
            total += 1
            if not existe(s):
                faltan.append((n, s))
        for h in set(re.findall(r"commit\s+`?([0-9a-f]{7,40})`?", cuerpo)):
            if not commit_existe(h):
                commits_malos.append((n, h))
    print(f"referencias revisadas: {total}")
    print("archivos o módulos que no existen:", faltan or "ninguno")
    print("commits que no existen:", commits_malos or "ninguno")
    return faltan, commits_malos


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 84)
