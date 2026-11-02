import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SCRIPT = RAIZ / "src/agentes/verificar_entorno.ps1"
POWERSHELL = shutil.which("powershell")
pytestmark = pytest.mark.skipif(POWERSHELL is None, reason="requiere Windows PowerShell")


def test_sintaxis_valida():
    r = subprocess.run(
        [POWERSHELL, "-NoProfile", "-Command",
         f"$e = $null; [void][System.Management.Automation.Language.Parser]::ParseFile('{SCRIPT}', [ref]$null, [ref]$e); "
         "if ($e.Count) { $e | ForEach-Object { $_.Message }; exit 1 }"],
        capture_output=True, text=True)
    assert r.returncode == 0, r.stdout


def test_solo_verifica_no_modifica():
    texto = SCRIPT.read_text(encoding="utf-8-sig")
    prohibidos = r"Set-Content|Add-Content|Out-File|Remove-Item|New-Item|Move-Item|Copy-Item|Install-|Start-Process|winget|choco|\bpip\s+install\b\s*[^\"']"
    codigo = "\n".join(l for l in texto.splitlines() if not l.strip().startswith("#"))
    sin_cadenas = re.sub(r'"[^"\n]*"', '""', codigo)
    assert not re.search(prohibidos, sin_cadenas)


def test_no_imprime_valores_del_env():
    env = RAIZ / ".env"
    if not env.exists():
        pytest.skip("no hay .env")
    secretos = []
    for linea in env.read_text(encoding="utf-8").splitlines():
        if "=" in linea and not linea.lstrip().startswith("#"):
            valor = linea.split("=", 1)[1].strip().strip("\"'")
            if len(valor) >= 8:
                secretos.append(valor)
    r = subprocess.run([POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPT)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    assert "Verificacion del entorno" in r.stdout and r.returncode in (0, 1)
    assert not any(s in r.stdout + r.stderr for s in secretos)
