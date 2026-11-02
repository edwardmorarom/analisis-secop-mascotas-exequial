import json
import re
import shutil
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SCRIPT = RAIZ / "src/agentes/verificar_entorno.ps1"
POWERSHELL = shutil.which("powershell")
requiere_powershell = pytest.mark.skipif(POWERSHELL is None, reason="requiere Windows PowerShell")


def texto_script():
    return SCRIPT.read_text(encoding="utf-8-sig")


def constante(nombre):
    m = re.search(rf'\${nombre}\s*=\s*"?([\w.]+)"?', texto_script())
    assert m, nombre
    return m.group(1)


def ejecutar(*args):
    return subprocess.run([POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPT), *args],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)


def servidor_langfuse(version):
    class Salud(BaseHTTPRequestHandler):
        def do_GET(self):
            cuerpo = json.dumps({"status": "OK", "version": version}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), Salud)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def test_versiones_del_script_coinciden_con_a05():
    servidor, minimo, sdk = constante("versionServidorFijada"), constante("servidorMinimoSdk"), int(constante("versionSdkMayor"))
    decisiones = (RAIZ / "docs/decisiones_agente.md").read_text(encoding="utf-8")
    a05 = decisiones[decisiones.index("### A05."):]
    a05 = a05.split("\n### A", 1)[0]
    assert f"etiqueta `v{servidor}`" in a05
    assert f"`langfuse>={sdk},<{sdk + 1}`" in a05
    assert f"servidor {minimo} o superior" in a05
    assert f"langfuse>={sdk},<{sdk + 1}" in (RAIZ / "requirements.txt").read_text(encoding="utf-8").split()
    leeme = (RAIZ / "docs/agente/LEEME_EQUIPO.md").read_text(encoding="utf-8")
    for esperado in (f"git checkout v{servidor}", f"docker.io/langfuse/langfuse:{servidor}",
                     f"docker.io/langfuse/langfuse-worker:{servidor}", f"`langfuse>={sdk},<{sdk + 1}`"):
        assert esperado in leeme


@requiere_powershell
def test_sintaxis_valida():
    r = subprocess.run(
        [POWERSHELL, "-NoProfile", "-Command",
         f"$e = $null; [void][System.Management.Automation.Language.Parser]::ParseFile('{SCRIPT}', [ref]$null, [ref]$e); "
         "if ($e.Count) { $e | ForEach-Object { $_.Message }; exit 1 }"],
        capture_output=True, text=True)
    assert r.returncode == 0, r.stdout


@requiere_powershell
def test_solo_verifica_no_modifica():
    prohibidos = r"Set-Content|Add-Content|Out-File|Remove-Item|New-Item|Move-Item|Copy-Item|Install-|Start-Process|winget|choco"
    codigo = "\n".join(l for l in texto_script().splitlines() if not l.strip().startswith("#"))
    assert not re.search(prohibidos, re.sub(r'"[^"\n]*"', '""', codigo))


@requiere_powershell
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
    r = ejecutar()
    assert "Verificacion del entorno" in r.stdout and r.returncode in (0, 1)
    assert not any(s in r.stdout + r.stderr for s in secretos)


@requiere_powershell
@pytest.mark.parametrize("version_servidor, estado", [
    (None, "OK"),
    ("4.71.0", "AVISO"),
    ("4.58.9", "FALTA"),
    ("3.225.15", "FALTA"),
])
def test_compara_la_version_del_servidor_con_a05(version_servidor, estado):
    version = version_servidor or constante("versionServidorFijada")
    srv = servidor_langfuse(version)
    try:
        r = ejecutar("-LangfuseHost", f"http://127.0.0.1:{srv.server_port}")
    finally:
        srv.shutdown()
    linea = next(l for l in r.stdout.splitlines() if " Langfuse " in l)
    assert linea.startswith(f"[{estado:<5}]"), linea
    assert version in linea
