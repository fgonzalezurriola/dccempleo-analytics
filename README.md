# dccempleo-analytics

Dashboard de ofertas laborales tech en Chile basado en el canal [DCCEmpleoSinFiltro](https://t.me/DCCEmpleoSinFiltro).

## Estructura

```
/                           <- Astro frontend (Vercel auto-detecta)
├── src/                    <- Componentes React, layouts, pages, CSS
├── public/data/            <- JSON pre-computados (generados por pipeline)
├── astro.config.mjs
├── package.json
└── pipeline/               <- Todo el codigo Python
    ├── pyproject.toml
    ├── scripts/            <- Scraping, labeling, analisis, build
    ├── dccempleo_analytics/
    ├── baml_client/
    ├── baml_src/
    ├── tests/
    └── data/               <- Raw + processed data
```

## Frontend (Astro + React + ECharts)

```bash
npm install
npm run dev          # http://localhost:4321
npm run build        # genera dist/
```

## Pipeline Python

```bash
cd pipeline
cp .env.example .env
uv sync
```

### 1) Scrapear Telegram

```bash
uv run python scripts/scrape_telegram.py
```

### 2) Levantar servicios (2 terminales)

Terminal A:
```bash
OPENCODE_SERVER_PASSWORD=password opencode serve --hostname 127.0.0.1 --port 4099
```

Terminal B:
```bash
uv run python scripts/opencode_openai_proxy.py
```

### 3) Procesar con LLM

```bash
uv run python scripts/process_with_llm.py
```

Ejecuta labeling + analisis + generacion de datos web en `public/data/`.

### 4) Build estatico

```bash
uv run python scripts/build_web.py
```

Ejecuta `astro build` y genera `dist/` en la raiz del repo.

### 5) Pipeline completo

```bash
uv run python scripts/pipeline.py
```

Flags: `--skip-scrape`, `--skip-labeling`, `--skip-dist`.

## Deploy

Vercel detecta Astro automaticamente en la raiz. Solo conecta el repo.

Los JSON de `public/data/` deben estar generados antes del build (correr el pipeline primero).

## Stack

- **Astro** — generador de sitios estaticos
- **React** — componentes interactivos (islands)
- **ECharts** — graficos
- **Motion** (v12) — animaciones
- **Python** — scraping, labeling con LLM (BAML), analisis

## Notas

- Reglas de normalizacion y edge cases: `EDGE_CASES.md`
- Categoria dev-AI: Codex, Cursor, Claude Code, GitHub Copilot
