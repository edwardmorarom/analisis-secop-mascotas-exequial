# Guía para Natalia y Harold: desarrollar el agente

Rama `agentes`. Todo en Windows con PowerShell. **Nunca peguen claves en el chat ni las escriban en archivos que se suben.**

**Sigue la hoja de ruta (`docs/agente/HOJA_DE_RUTA.md`); no empieces un hito sin aprobación del anterior.**

## 1. Clonar y cambiarse a la rama

```powershell
git clone https://github.com/edwardmorarom/analisis-secop-mascotas-exequial.git
cd analisis-secop-mascotas-exequial
git checkout agentes
git pull
```

Trabajen solo en `agentes`. No hagan merge a `main`: el agente entra por pull request revisado por Edward (D100).

## 2. Entorno de Python

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -c "import langfuse; print(langfuse.__version__)"
```

La última línea debe mostrar una versión **4.x** (A04). Si muestra 5.x, el servidor de Langfuse de esta guía no es compatible: corran `pip install -r requirements.txt` de nuevo (el archivo fija `langfuse>=4,<5`).

`camelot` necesita Ghostscript instalado en el sistema (https://ghostscript.com/releases/gsdnld.html).

## 3. Claves (`.env`)

```powershell
Copy-Item .env.example .env
```

Abran `.env` y completen **su propia** clave de DeepSeek (`DEEPSEEK_API_KEY`, desde https://platform.deepseek.com). Las claves de Langfuse (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`) salen del paso 5. No necesitan las claves de Google ni de Socrata. `.env` no se sube (está en `.gitignore`).

## 4. Comprobar Docker Desktop con WSL2

Langfuse corre en contenedores, así que antes del paso 5 verifiquen Docker. Con Docker Desktop abierto (el ícono de la ballena en la bandeja debe decir «Engine running»):

```powershell
wsl --status
wsl -l -v
docker version
docker run hello-world
```

Debe cumplirse:

- `wsl -l -v` lista al menos una distribución con `VERSION 2` (Docker Desktop crea `docker-desktop`).
- `docker version` muestra las secciones **Client** y **Server**. Si falta **Server**, Docker Desktop no está en marcha: ábranlo y esperen a que termine de iniciar.
- `docker run hello-world` termina con `Hello from Docker!`.

Si algo falla: en Docker Desktop, *Settings → General* debe tener activada la opción *Use the WSL 2 based engine*; actualicen WSL con `wsl --update`; y verifiquen que la virtualización esté habilitada en la BIOS. No sigan al paso 5 hasta que `hello-world` funcione.

## 5. Langfuse local con Docker (versión fijada, A04)

Se usa el servidor **Langfuse v3, etiqueta `v3.225.15`**, y el SDK de Python **4.x** (`langfuse>=4,<5`). No usen el SDK 5 ni el servidor v4 sin una enmienda de Edward: el SDK 5 exige servidor 4.59.0 o superior.

Fuera de la carpeta del repositorio:

```powershell
git clone https://github.com/langfuse/langfuse.git
cd langfuse
git checkout v3.225.15
```

Abran `docker-compose.yml` y hagan estos dos cambios (el archivo trae la etiqueta flotante `:3`, que cambiaría entre máquinas):

- `image: docker.io/langfuse/langfuse:3` → `image: docker.io/langfuse/langfuse:3.225.15`
- `image: docker.io/langfuse/langfuse-worker:3` → `image: docker.io/langfuse/langfuse-worker:3.225.15`

Cambien también los valores marcados `# CHANGEME` (al menos `SALT`, `NEXTAUTH_SECRET` y `ENCRYPTION_KEY`; esta última se genera con `openssl rand -hex 32` o, sin OpenSSL, en PowerShell con `$b = New-Object byte[] 32; [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b); -join ($b | ForEach-Object { $_.ToString('x2') })`). No expongan los puertos fuera de su equipo.

```powershell
docker compose up -d
docker compose logs -f langfuse-web
```

Esperen 2 o 3 minutos hasta ver `Ready` en el registro (salgan con Ctrl+C). Abran http://localhost:3000, creen un usuario, una organización y un proyecto, generen las claves del proyecto y cópienlas a `.env` (`LANGFUSE_HOST=http://localhost:3000`). Comprobación rápida: http://localhost:3000/api/public/health debe responder con el estado `OK`. Para apagarlo: `docker compose down`.

## 6. Paquete de datos

Edward les entrega `paquete_agente_AAAAMMDD.zip` (por un canal privado; no está en el repositorio). Descomprímanlo **en la raíz del repositorio**, de modo que queden `data/` y `SHA256SUMS.txt` junto a `config.yaml`:

```powershell
Expand-Archive -Path $HOME\Downloads\paquete_agente_AAAAMMDD.zip -DestinationPath . -Force
python -m src.agentes.verificar_paquete
```

Debe terminar con `faltantes: 0 | con otra huella: 0`. Si no, avisen a Edward antes de seguir. `data/` no se sube nunca.

## 7. Cómo empezar con Claude Code

Abran Claude Code en la carpeta del repositorio (rama `agentes`) y pídanle:

> Lee docs/agente/ESPECIFICACION.md y docs/agente/HOJA_DE_RUTA.md y propón el plan del hito H1 antes de escribir código.

Claude Code carga solo `CLAUDE.md` y `src/agentes/CLAUDE.md`. Revisen el plan, ajústenlo y recién entonces autoricen que escriba código. Al terminar cada hito, pidan revisión a Edward (punto de control de la hoja de ruta).

## 8. Reglas de la rama (resumen)

- Toda decisión de método va a `docs/decisiones_agente.md` (A01, A02…), en el mismo commit que la implementa.
- Los umbrales de la evaluación están fijados (A01). Cambiarlos después de ver resultados exige una enmienda registrada.
- No se toca `data/raw`, `src/etl`, `src/modelos`. Si necesitan un cambio ahí, anótenlo en `docs/agente/solicitudes.md`.
- Al terminar cada sesión: `pytest`, `git status` (nada de `data/`, `.env` ni trazas con datos) y `git push` de `agentes`.
- Formato de commit: `tipo(alcance): resumen`, con Qué, Por qué, Fuentes, Validación y Fase (D28).
