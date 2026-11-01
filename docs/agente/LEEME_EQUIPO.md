# Guía para Natalia y Harold: desarrollar el agente

Rama `agentes`. Todo en Windows con PowerShell. **Nunca peguen claves en el chat ni las escriban en archivos que se suben.**

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
```

`camelot` necesita Ghostscript instalado en el sistema (https://ghostscript.com/releases/gsdnld.html).

## 3. Claves (`.env`)

```powershell
Copy-Item .env.example .env
```

Abran `.env` y completen **su propia** clave de DeepSeek (`DEEPSEEK_API_KEY`, desde https://platform.deepseek.com). Las claves de Langfuse (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`) salen del paso siguiente. No necesitan las claves de Google ni de Socrata. `.env` no se sube (está en `.gitignore`).

## 4. Langfuse local con Docker

Necesitan Docker Desktop en marcha. Fuera de esta carpeta:

```powershell
git clone https://github.com/langfuse/langfuse.git
cd langfuse
docker compose up -d
```

Abran http://localhost:3000, creen un usuario, una organización y un proyecto, generen las claves del proyecto y cópienlas a `.env` (`LANGFUSE_HOST=http://localhost:3000`). Para apagarlo: `docker compose down`.

## 5. Paquete de datos

Edward les entrega `paquete_agente_AAAAMMDD.zip` (por un canal privado; no está en el repositorio). Descomprímanlo **en la raíz del repositorio**, de modo que queden `data/` y `SHA256SUMS.txt` junto a `config.yaml`:

```powershell
Expand-Archive -Path $HOME\Downloads\paquete_agente_AAAAMMDD.zip -DestinationPath . -Force
python -m src.agentes.verificar_paquete
```

Debe terminar con `faltantes: 0 | con otra huella: 0`. Si no, avisen a Edward antes de seguir. `data/` no se sube nunca.

## 6. Cómo empezar con Claude Code

Abran Claude Code en la carpeta del repositorio (rama `agentes`) y pídanle:

> Lee docs/agente/ESPECIFICACION.md y propón el plan de F6 antes de escribir código.

Claude Code carga solo `CLAUDE.md` y `src/agentes/CLAUDE.md`. Revisen el plan, ajústenlo y recién entonces autoricen que escriba código.

## 7. Reglas de la rama (resumen)

- Toda decisión de método va a `docs/decisiones_agente.md` (A01, A02…), en el mismo commit que la implementa.
- Los umbrales de la evaluación están fijados (A01). Cambiarlos después de ver resultados exige una enmienda registrada.
- No se toca `data/raw`, `src/etl`, `src/modelos`. Si necesitan un cambio ahí, anótenlo en `docs/agente/solicitudes.md`.
- Al terminar cada sesión: `pytest`, `git status` (nada de `data/`, `.env` ni trazas con datos) y `git push` de `agentes`.
- Formato de commit: `tipo(alcance): resumen`, con Qué, Por qué, Fuentes, Validación y Fase (D28).
