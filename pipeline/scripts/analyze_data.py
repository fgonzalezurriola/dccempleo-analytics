from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from _bootstrap import ensure_project_root_on_path

ensure_project_root_on_path()

from dccempleo_analytics.analysis import analyze_messages, generate_web_data, process_message


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _write_json(path: Path, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _keep_latest_row_per_message_id(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest_idx_by_id: dict[int, int] = {}
    for idx, row in enumerate(rows):
        message_id = row.get("message_id")
        if isinstance(message_id, int):
            latest_idx_by_id[message_id] = idx

    latest_indices = set(latest_idx_by_id.values())
    deduped: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        message_id = row.get("message_id")
        if isinstance(message_id, int):
            if idx in latest_indices:
                deduped.append(row)
            continue
        deduped.append(row)
    return deduped


def run_analysis() -> Path | None:
    load_dotenv(override=True)

    labeled_path = Path(
        os.environ.get("LABELED_OUTPUT_PATH", "data/processed/labeled_messages.jsonl")
    )
    raw_path = Path(os.environ.get("RAW_EXPORT_PATH", "data/raw/telegram_export.jsonl"))
    output_dir = Path(os.environ.get("PROCESSED_DIR", "data/processed"))

    input_path = labeled_path if labeled_path.exists() else raw_path
    if not input_path.exists():
        print(f"No existe input para analisis: {input_path}")
        return None

    source_rows = _read_jsonl(input_path)
    source_rows = _keep_latest_row_per_message_id(source_rows)
    messages = [process_message(row) for row in source_rows]
    insights = analyze_messages(messages, source_path=input_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    insights_path = output_dir / "insights.json"
    messages_path = output_dir / "messages_anonymized.jsonl"
    charts_path = output_dir / "charts.json"
    metrics_path = output_dir / "metrics.json"

    _write_json(insights_path, insights)
    _write_jsonl(messages_path, messages)
    _write_json(charts_path, insights["charts"])
    _write_json(metrics_path, {"kpis": insights["kpis"], "source": insights["source"]})

    # Generate pre-computed web data for Astro frontend (public/data at repo root)
    repo_root = Path(__file__).resolve().parents[2]
    default_web_data = str(repo_root / "public" / "data")
    web_data_dir = Path(os.environ.get("WEB_DATA_DIR", default_web_data))
    generate_web_data(messages, web_data_dir)

    print(f"Analisis listo: {insights_path}")
    return insights_path


def main() -> None:
    run_analysis()


if __name__ == "__main__":
    main()
