# dccempleo-analytics

Dashboard estatico de ofertas laborales tech en Chile, construido con Astro + React y alimentado por un pipeline en Python.

Fuente principal: canal publico [DCCEmpleoSinFiltro](https://t.me/DCCEmpleoSinFiltro).

## Que hace este proyecto

- Extrae publicaciones desde Telegram.
- Etiqueta seniority, tipo de oferta y stack tecnologico con LLM.
- Genera JSON precomputados para visualizacion web.
- Publica un sitio estatico optimizado para SEO (sitemap, robots, canonical, OG, JSON-LD).

## Stack

- Frontend: Astro, React, ECharts, Motion.
- Data pipeline: Python 3.12, Telethon, Pydantic, BAML.
- Package managers: pnpm (frontend) y uv (pipeline Python).

## Estructura del repo

```text
/                           # Astro frontend
|-- src/
|-- public/
|   |-- data/               # JSON listos para el dashboard
|-- astro.config.mjs
|-- package.json
|-- pipeline/               # pipeline de datos
|   |-- scripts/            # scraping, labeling, analisis
|   |-- dccempleo_analytics/
|   |-- baml_src/
|   |-- baml_client/
|   |-- tests/
|   |-- data/               # raw + processed (ignorado en git)
|   |-- .env.example
|   `-- pyproject.toml
`-- LICENSE
```

## Requisitos

- Node.js 20+
- pnpm 10+
- Python 3.12+
- uv

## Quickstart (solo dashboard)

Si ya existe `public/data/` en tu rama, solo necesitas frontend:

```bash
pnpm i
pnpm dev
```

Build local:

```bash
pnpm build
```

## Pipeline de datos (end-to-end)

### 1) Setup Python

```bash
cd pipeline
cp .env.example .env
uv sync
```

### 2) Scrapear Telegram

```bash
uv run python scripts/scrape_telegram.py
```

### 3) Levantar servicios para labeling (2 terminales)

Terminal A:

```bash
OPENCODE_SERVER_PASSWORD=password opencode serve --hostname 127.0.0.1 --port 4099
```

Terminal B:

```bash
uv run python scripts/opencode_openai_proxy.py
```

### 4) Labeling + analisis

```bash
uv run python scripts/label_with_llm.py
uv run python scripts/analyze_data.py
```

Esto actualiza:

- `pipeline/data/processed/*`
- `public/data/*`

Nota: el labeling puede demorar bastante por rate limits. El proceso se puede reanudar.

### 5) Build web

En la raiz del repo:

```bash
pnpm build
```

### Comando integrado (opcional)

```bash
uv run python scripts/pipeline.py --skip-dist
```

Flags disponibles: `--skip-scrape`, `--skip-labeling`, `--skip-dist`.

El script legacy `scripts/process_with_llm.py` se mantiene solo por compatibilidad.

## Deploy (Vercel)

### Opcion recomendada (simple)

1. Generar `public/data` localmente (pipeline).
2. Commit/push de codigo + `public/data`.
3. Importar repo en Vercel.
4. Configuracion:
   - Build command: `pnpm build`
   - Output directory: `dist`
5. Definir variable de entorno:
   - `SITE_URL=https://tu-dominio.com`

Con eso quedan correctos canonical, sitemap y robots.

### Archivos SEO generados

- `dist/sitemap-index.xml`
- `dist/robots.txt`

## Open source checklist

- Licencia MIT: `LICENSE`.
- Secrets fuera de git (`pipeline/.env` esta ignorado).
- Datos crudos/temporales fuera de git (`pipeline/data/` ignorado).
- Build artifacts fuera de git (`dist/` ignorado).

## Tests

Pipeline:

```bash
cd pipeline
uv run python -m unittest
```

Frontend build check:

```bash
pnpm build
```

## Variables de entorno importantes

En `pipeline/.env.example`:

- Telegram: `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE`.
- OpenCode/BAML: `OPENCODE_*`, `BAML_*`.
- Control de labeling: `LABEL_*`.
- Paths: `RAW_EXPORT_PATH`, `LABELED_OUTPUT_PATH`, `PROCESSED_DIR`.

En deploy frontend:

- `SITE_URL` (recomendado para canonical/sitemap consistentes).