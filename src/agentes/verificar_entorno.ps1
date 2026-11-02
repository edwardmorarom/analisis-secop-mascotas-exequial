# Verifica el entorno del agente en Windows. Solo lee: no instala ni modifica nada.
# Uso (desde la raiz del repositorio):  powershell -ExecutionPolicy Bypass -File src\agentes\verificar_entorno.ps1

param([string]$LangfuseHost = "")

$ErrorActionPreference = "Continue"
$raiz = Resolve-Path (Join-Path $PSScriptRoot "..\..")
# Versiones fijadas en A05 (docs/decisiones_agente.md); una prueba comprueba que coinciden con A05, requirements.txt y LEEME_EQUIPO.md
$versionServidorFijada = "4.72.0"
$servidorMinimoSdk = "4.59.0"
$versionSdkMayor = 5
$variablesNecesarias = @("DEEPSEEK_API_KEY", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST")

$resultados = New-Object System.Collections.ArrayList
$faltas = New-Object System.Collections.ArrayList

function Registrar($estado, $nombre, $detalle, $accion) {
    [void]$resultados.Add([pscustomobject]@{ Estado = $estado; Nombre = $nombre; Detalle = $detalle })
    if ($estado -eq "FALTA") { [void]$faltas.Add("${nombre}: $accion") }
}

function Salida-Limpia($texto) {
    # wsl.exe escribe en UTF-16: se quitan los caracteres nulos
    return (($texto | Out-String) -replace "`0", "")
}

# 1. Windows
try {
    $so = Get-CimInstance Win32_OperatingSystem
    $build = [int]$so.BuildNumber
    if ($build -ge 19041) {
        Registrar "OK" "Windows" "$($so.Caption) (version $($so.Version), compilacion $build)" ""
    } else {
        Registrar "FALTA" "Windows" "$($so.Caption), compilacion $build" "WSL2 requiere Windows 10 compilacion 19041 o superior; actualice Windows"
    }
} catch {
    Registrar "FALTA" "Windows" "no se pudo leer la version" "ejecute este script en Windows con PowerShell"
}

# 2. WSL2
$wsl = Get-Command wsl.exe -ErrorAction SilentlyContinue
if (-not $wsl) {
    Registrar "FALTA" "WSL2" "wsl.exe no existe" "active WSL (wsl --install, en una consola de administrador) y reinicie"
} else {
    $lista = Salida-Limpia (& wsl.exe -l -v 2>&1)
    $codigo = $LASTEXITCODE
    $distros2 = @($lista -split "`r?`n" | Where-Object { $_ -match "\s2\s*$" })
    if ($codigo -eq 0 -and $distros2.Count -gt 0) {
        Registrar "OK" "WSL2" "$($distros2.Count) distribucion(es) con VERSION 2" ""
    } elseif ($codigo -eq 0) {
        Registrar "FALTA" "WSL2" "WSL esta instalado pero ninguna distribucion usa VERSION 2" "abra Docker Desktop (crea docker-desktop en WSL2) o convierta una distribucion con wsl --set-version <nombre> 2"
    } else {
        Registrar "FALTA" "WSL2" "wsl -l -v no respondio" "ejecute wsl --update y revise que la virtualizacion este habilitada en la BIOS"
    }
}

# 3. Docker
$docker = Get-Command docker.exe -ErrorAction SilentlyContinue
if (-not $docker) {
    Registrar "FALTA" "Docker" "docker.exe no existe" "instale Docker Desktop con el motor WSL 2"
} else {
    $servidor = (& docker.exe version --format "{{.Server.Version}}" 2>$null | Out-String).Trim()
    if ($LASTEXITCODE -eq 0 -and $servidor) {
        Registrar "OK" "Docker" "responde (servidor $servidor)" ""
    } else {
        Registrar "FALTA" "Docker" "el cliente existe pero el servidor no responde" "abra Docker Desktop y espere a que diga Engine running"
    }
}

# 4. .env (solo nombres, nunca valores)
$envRuta = Join-Path $raiz ".env"
$valores = @{}
if (-not (Test-Path $envRuta)) {
    Registrar "FALTA" ".env" "no existe en la raiz del repositorio" "copie .env.example a .env y complete las claves"
} else {
    foreach ($linea in Get-Content $envRuta -Encoding UTF8) {
        if ($linea -match "^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$" -and -not $linea.TrimStart().StartsWith("#")) {
            $valores[$Matches[1]] = $Matches[2].Trim('"').Trim("'")
        }
    }
    $sinValor = @($variablesNecesarias | Where-Object { -not $valores.ContainsKey($_) -or [string]::IsNullOrWhiteSpace($valores[$_]) })
    if ($sinValor.Count -eq 0) {
        Registrar "OK" ".env" "existe y tiene las $($variablesNecesarias.Count) variables necesarias" ""
    } else {
        Registrar "FALTA" ".env" "sin valor: $($sinValor -join ', ')" "complete esas variables en .env (las de Langfuse salen de la interfaz de Langfuse)"
    }
    $ignorado = & git -C $raiz check-ignore -q ".env" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Registrar "FALTA" ".env ignorado por git" ".env no esta en .gitignore" "agregue .env a .gitignore: las claves no se suben"
    }
}

# 5. Langfuse
$host_ = "http://localhost:3000"
if ($valores.ContainsKey("LANGFUSE_HOST") -and $valores["LANGFUSE_HOST"]) { $host_ = $valores["LANGFUSE_HOST"].TrimEnd("/") }
if ($LangfuseHost) { $host_ = $LangfuseHost.TrimEnd("/") }
try {
    $r = Invoke-WebRequest -Uri "$host_/api/public/health" -UseBasicParsing -TimeoutSec 8
    $info = $r.Content | ConvertFrom-Json
    if ($info.status -eq "OK") {
        $numerica = if ("$($info.version)" -match "^(\d+\.\d+\.\d+)") { [version]$Matches[1] } else { $null }
        if (-not $numerica) {
            Registrar "AVISO" "Langfuse" "responde en $host_ pero no informa su version; la fijada es $versionServidorFijada (A05)" ""
        } elseif ($numerica -lt [version]$servidorMinimoSdk) {
            Registrar "FALTA" "Langfuse" "responde con la version $($info.version); el SDK $versionSdkMayor exige $servidorMinimoSdk o superior" "levante el servidor $versionServidorFijada (LEEME_EQUIPO.md, paso 5)"
        } elseif ($numerica -ne [version]$versionServidorFijada) {
            Registrar "AVISO" "Langfuse" "responde en $host_ con la version $($info.version); la fijada es $versionServidorFijada (A05)" ""
        } else {
            Registrar "OK" "Langfuse" "responde en $host_ (version $($info.version))" ""
        }
    } else {
        Registrar "FALTA" "Langfuse" "respondio con estado $($info.status)" "revise docker compose logs langfuse-web"
    }
} catch {
    Registrar "FALTA" "Langfuse" "no responde en $host_" "en la carpeta de langfuse ejecute docker compose up -d y espere 2 o 3 minutos"
}

# 6. Python y SDK de Langfuse del entorno virtual (A05: Python 3.11 o superior y SDK 5.x)
$py = Join-Path $raiz ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Registrar "FALTA" "Entorno Python" ".venv no existe" "python -m venv .venv y pip install -r requirements.txt"
} else {
    $pv = (& $py -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null | Out-String).Trim()
    if ($pv -match "^(\d+)\.(\d+)$" -and ([int]$Matches[1] -gt 3 -or ([int]$Matches[1] -eq 3 -and [int]$Matches[2] -ge 11))) {
        Registrar "OK" "Python (.venv)" "version $pv" ""
    } else {
        Registrar "FALTA" "Python (.venv)" "version '$pv'; el SDK 5 exige 3.11 o superior" "cree el entorno con Python 3.11 o superior"
    }
    $v = (& $py -c "import langfuse; print(langfuse.__version__)" 2>$null | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $v) {
        Registrar "FALTA" "SDK langfuse" "no se pudo importar" "pip install -r requirements.txt"
    } elseif ($v -match "^$versionSdkMayor\.") {
        Registrar "OK" "SDK langfuse" "version $v (A05)" ""
    } else {
        Registrar "FALTA" "SDK langfuse" "version $v; A05 exige $versionSdkMayor.x (servidor $servidorMinimoSdk o superior)" "pip install -r requirements.txt"
    }
}

# Resumen
Write-Host ""
Write-Host "Verificacion del entorno del agente" -ForegroundColor Cyan
foreach ($x in $resultados) {
    $color = switch ($x.Estado) { "OK" { "Green" } "AVISO" { "Yellow" } default { "Red" } }
    Write-Host ("[{0,-5}] {1,-22} {2}" -f $x.Estado, $x.Nombre, $x.Detalle) -ForegroundColor $color
}
Write-Host ""
if ($faltas.Count -eq 0) {
    Write-Host "No falta nada." -ForegroundColor Green
    exit 0
}
Write-Host "Falta ($($faltas.Count)):" -ForegroundColor Red
$i = 1
foreach ($f in $faltas) { Write-Host "  $i. $f"; $i++ }
exit 1
