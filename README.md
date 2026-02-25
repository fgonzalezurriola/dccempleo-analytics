# dccempleo-analytics

Pipeline para:
1. Scrapear `DCCEmpleoSinFiltro`.
2. Etiquetar ofertas con BAML + OpenCode.
3. Generar dashboard estático en `dist/`.

## 1) Setup

```bash
cp .env.example .env
uv sync
```

Instalar OpenCode CLI:

```bash
curl -fsSL https://opencode.ai/install | bash
opencode models | grep free
```

## 2) Configurar `.env`

Variables mínimas a revisar:

- Telegram: `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE`
- Fecha de export: `EXPORT_SINCE=2023-01-01`
- Modelo: `OPENCODE_MODEL=opencode/trinity-large-preview-free`
- Password server: `OPENCODE_SERVER_PASSWORD=password`

Todo el comportamiento de labeling se controla por env vars (`LABEL_*`).
`--skip-build` se mantiene solo por compatibilidad y ya no es necesario.
Si una fila queda con `status=error`, por defecto se reintenta en corridas futuras (`LABEL_RETRY_ERRORS=1`).
Si se detecta rate limit del proveedor, el labeling aborta inmediatamente por defecto (`LABEL_ABORT_ON_RATE_LIMIT=1`).

## 3) Scrapear Telegram

```bash
uv run python scripts/scrape_telegram.py
```

Salida esperada: `data/raw/telegram_export.jsonl`

## 4) Levantar servicios (2 terminales)

Terminal A:

```bash
OPENCODE_SERVER_PASSWORD=password opencode serve --hostname 127.0.0.1 --port 4099
```

Terminal B:

```bash
uv run python scripts/opencode_openai_proxy.py
```

## 5) Procesar con LLM

Terminal C:

```bash
uv run python scripts/process_with_llm.py
```

Esto ejecuta:
- labeling (`data/processed/labeled_messages.jsonl`)
- análisis (`data/processed/insights.json`)

## 6) Build web (Reflex export)

```bash
uv run python scripts/build_web.py
```

## 7) Flujo combinado (opcional)

```bash
uv run python scripts/process_with_llm.py && uv run python scripts/build_web.py
```

## 8) Prueba corta (opcional)

```bash
LABEL_MAX_MESSAGES=5 LABEL_BATCH_SIZE=2 uv run python scripts/process_with_llm.py
```

## Deploy

Publica `dist/` como sitio estático (Vercel/Netlify/Nginx).

## Notas

- Reglas de normalización y edge cases: `EDGE_CASES.md`.
- Categoría dev-AI incluida: Codex, Cursor, Claude Code, GitHub Copilot.
