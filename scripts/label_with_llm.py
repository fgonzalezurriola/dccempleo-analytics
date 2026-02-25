from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from _bootstrap import ensure_project_root_on_path

ensure_project_root_on_path()

from dccempleo_analytics.baml_runtime import (
    BamlRateLimitError,
    BamlRuntimeError,
    create_runtime,
    extract_offer,
    prepare_baml_env,
)
from dccempleo_analytics.llm import OfferLabel


def _pick_model() -> str:
    return os.environ.get("OPENCODE_MODEL", "opencode/minimax-m2.5-free")


def _load_latest_rows_by_message_id(output_path: Path) -> dict[int, dict[str, Any]]:
    if not output_path.exists():
        return {}
    latest: dict[int, dict[str, Any]] = {}
    with output_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
                message_id = row.get("message_id")
                if isinstance(message_id, int):
                    latest[message_id] = row
            except json.JSONDecodeError:
                continue
    return latest


def _offer_analysis_to_label(payload: Any) -> dict[str, Any]:
    seniority = str(getattr(payload, "seniority", "UNKNOWN"))
    offer_type = str(getattr(payload, "offer_type", "JOB"))
    if "." in seniority:
        seniority = seniority.split(".")[-1]
    if "." in offer_type:
        offer_type = offer_type.split(".")[-1]

    maybe_stack = getattr(payload, "tech_stack", [])
    tech_stack = [str(item).strip().lower() for item in maybe_stack if str(item).strip()]

    maybe_signals = getattr(payload, "signals", [])
    signals = [str(item).strip() for item in maybe_signals if str(item).strip()]

    maybe_confidence = getattr(payload, "confidence", 0.0)
    label = OfferLabel.model_validate(
        {
            "seniority": seniority,
            "offer_type": offer_type,
            "tech_stack": tech_stack,
            "confidence": maybe_confidence,
            "signals": signals,
        }
    )
    return label.model_dump()


def _is_rate_limit_message(text: str) -> bool:
    lowered = text.lower()
    patterns = (
        "free usage exceeded",
        "rate limit",
        "ratelimit",
        "too many requests",
        "status code: 429",
        "http 429",
        "insufficient credits",
    )
    return any(pattern in lowered for pattern in patterns)


class LabelingRateLimitError(RuntimeError):
    pass


async def _label_text(runtime: Any, ctx: Any, text: str) -> tuple[dict[str, Any] | None, str | None]:
    return await _label_text_with_retries(runtime=runtime, ctx=ctx, text=text)


async def _label_text_with_retries(
    runtime: Any,
    ctx: Any,
    text: str,
    retries: int = 2,
    retry_delay_seconds: float = 0.7,
    abort_on_rate_limit: bool = True,
) -> tuple[dict[str, Any] | None, str | None]:
    attempts = max(1, retries + 1)
    last_error: str | None = None

    for attempt in range(attempts):
        try:
            extracted = await extract_offer(runtime=runtime, ctx=ctx, text=text)
            return _offer_analysis_to_label(extracted), None
        except BamlRateLimitError as exc:
            raise LabelingRateLimitError(str(exc)) from exc
        except Exception as exc:
            last_error = f"{exc.__class__.__name__}: {exc}"
            if abort_on_rate_limit and _is_rate_limit_message(last_error):
                raise LabelingRateLimitError(last_error) from exc
            if attempt < attempts - 1:
                await asyncio.sleep(retry_delay_seconds * (attempt + 1))

    return None, (last_error or "unknown_error")


async def run_labeling(
    batch_size: int | None = None,
    delay_seconds: float | None = None,
    max_messages: int | None = None,
    stop_after_error_batches: int | None = None,
    retries: int | None = None,
    retry_delay_seconds: float | None = None,
) -> Path | None:
    load_dotenv(override=True)

    if batch_size is None:
        batch_size = int(os.environ.get("LABEL_BATCH_SIZE", "5"))
    if delay_seconds is None:
        delay_seconds = float(os.environ.get("LABEL_DELAY_SECONDS", "0.8"))
    if stop_after_error_batches is None:
        stop_after_error_batches = int(os.environ.get("LABEL_STOP_AFTER_ERROR_BATCHES", "3"))
    if retries is None:
        retries = int(os.environ.get("LABEL_RETRIES", "2"))
    if retry_delay_seconds is None:
        retry_delay_seconds = float(os.environ.get("LABEL_RETRY_DELAY_SECONDS", "0.7"))
    abort_on_rate_limit = os.environ.get("LABEL_ABORT_ON_RATE_LIMIT", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }
    retry_errors = os.environ.get("LABEL_RETRY_ERRORS", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }
    if max_messages is None:
        max_messages_env = int(os.environ.get("LABEL_MAX_MESSAGES", "0"))
        max_messages = max_messages_env if max_messages_env > 0 else None

    input_path = Path(os.environ.get("INPUT_PATH", "data/raw/telegram_export.jsonl"))
    output_path = Path(
        os.environ.get("LABELED_OUTPUT_PATH", "data/processed/labeled_messages.jsonl")
    )
    model_name = _pick_model()
    prepare_baml_env(model_name=model_name)

    if not input_path.exists():
        print(f"ERROR: labeling input not found: {input_path}")
        return None

    output_path.parent.mkdir(parents=True, exist_ok=True)
    latest_rows_by_id = _load_latest_rows_by_message_id(output_path)
    if retry_errors:
        processed_ids = {
            message_id
            for message_id, row in latest_rows_by_id.items()
            if str(row.get("status") or "").lower() == "labeled"
        }
    else:
        processed_ids = set(latest_rows_by_id)

    rows_to_process: list[dict[str, Any]] = []
    with input_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            message_id = row.get("message_id")
            text = str(row.get("text") or row.get("raw_text") or "").strip()
            if not isinstance(message_id, int) or message_id in processed_ids:
                continue
            if len(text) < 20:
                continue
            rows_to_process.append(row)

    if not rows_to_process:
        print("No new messages to label.")
        return output_path

    if max_messages is not None and max_messages > 0:
        rows_to_process = rows_to_process[:max_messages]

    proxy_base_url = os.environ.get("BAML_PROXY_BASE_URL", "")
    print(
        f"Labeling model={model_name} pending={len(rows_to_process)} "
        f"baml_proxy={proxy_base_url} retries={retries}"
    )

    try:
        runtime, ctx = create_runtime()
    except BamlRuntimeError as exc:
        raise RuntimeError(f"BAML setup error: {exc}") from exc

    consecutive_all_error_batches = 0
    total_labeled = 0
    total_error = 0

    with output_path.open("a", encoding="utf-8") as handle:
        for idx in range(0, len(rows_to_process), batch_size):
            batch = rows_to_process[idx : idx + batch_size]
            batch_results: list[tuple[dict[str, Any] | None, str | None]] = []
            for row in batch:
                try:
                    batch_results.append(
                        await _label_text_with_retries(
                            runtime=runtime,
                            ctx=ctx,
                            text=str(row.get("text") or row.get("raw_text") or ""),
                            retries=retries,
                            retry_delay_seconds=retry_delay_seconds,
                            abort_on_rate_limit=abort_on_rate_limit,
                        )
                    )
                except LabelingRateLimitError as exc:
                    raise RuntimeError(
                        "Labeling aborted due to detected rate limit. "
                        f"message_id={row.get('message_id')} error={exc}"
                    ) from exc

            batch_labeled = 0
            batch_error = 0
            batch_error_samples: list[tuple[int | None, str]] = []
            for row, result in zip(batch, batch_results):
                label, error_message = result
                if label:
                    batch_labeled += 1
                    total_labeled += 1
                else:
                    batch_error += 1
                    total_error += 1
                    if len(batch_error_samples) < 2:
                        batch_error_samples.append((row.get("message_id"), error_message or "unknown_error"))
                payload = {
                    **row,
                    "label": label,
                    "status": "labeled" if label else "error",
                    "error_message": error_message,
                    "model_name": model_name,
                }
                handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
            handle.flush()

            batch_number = (idx // batch_size) + 1
            batch_total = (len(rows_to_process) + batch_size - 1) // batch_size
            print(
                f"batch {batch_number}/{batch_total} done | "
                f"labeled={batch_labeled} error={batch_error} "
                f"(total labeled={total_labeled}, total error={total_error})"
            )
            if batch_error:
                for message_id, err in batch_error_samples:
                    print(f"ERROR sample | message_id={message_id} | {err}")

            if batch_labeled == 0:
                consecutive_all_error_batches += 1
            else:
                consecutive_all_error_batches = 0

            if (
                stop_after_error_batches > 0
                and consecutive_all_error_batches >= stop_after_error_batches
            ):
                first_sample = (
                    batch_error_samples[0][1] if batch_error_samples else "no error sample available"
                )
                raise RuntimeError(
                    "Labeling aborted: all messages failed in consecutive batches. "
                    f"Last error sample: {first_sample}. "
                    "Check BAML proxy/OpenCode auth-model settings before retrying."
                )

            await asyncio.sleep(delay_seconds)

    return output_path


def main() -> None:
    try:
        asyncio.run(run_labeling())
    except RuntimeError as exc:
        raise SystemExit(f"ERROR: {exc}") from exc


if __name__ == "__main__":
    main()
