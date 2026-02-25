from __future__ import annotations

import json
import os
import re
import sys
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class Seniority(str, Enum):
    INTERN = "INTERN"
    TRAINEE = "TRAINEE"
    JUNIOR = "JUNIOR"
    MID_SENIOR = "MID_SENIOR"
    SENIOR = "SENIOR"
    MIXED = "MIXED"
    UNKNOWN = "UNKNOWN"


class OfferType(str, Enum):
    JOB = "JOB"
    PRACTICE = "PRACTICE"
    BOOTCAMP = "BOOTCAMP"
    COURSE = "COURSE"
    UNKNOWN = "UNKNOWN"


class OfferAnalysis(BaseModel):
    seniority: Seniority
    offer_type: OfferType
    tech_stack: list[str]
    confidence: float
    signals: list[str]


class BamlRuntimeError(RuntimeError):
    pass


class BamlRateLimitError(BamlRuntimeError):
    pass


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


def _iter_strings(node: Any) -> list[str]:
    values: list[str] = []
    if isinstance(node, str):
        values.append(node)
    elif isinstance(node, dict):
        for item in node.values():
            values.extend(_iter_strings(item))
    elif isinstance(node, list):
        for item in node:
            values.extend(_iter_strings(item))
    return values


def _normalize_seniority(value: Any) -> str:
    raw = str(value or "UNKNOWN").strip().upper().replace("-", "_")
    mapping = {
        "SEMI_SENIOR": "MID_SENIOR",
        "SEMISENIOR": "MID_SENIOR",
        "MID": "MID_SENIOR",
        "SR": "SENIOR",
    }
    normalized = mapping.get(raw, raw)
    if normalized in {item.value for item in Seniority}:
        return normalized
    return "UNKNOWN"


def _normalize_offer_type(value: Any) -> str:
    raw = str(value or "JOB").strip().upper().replace("-", "_")
    mapping = {
        "INTERNSHIP": "PRACTICE",
        "PRACTICA": "PRACTICE",
    }
    normalized = mapping.get(raw, raw)
    if normalized in {item.value for item in OfferType}:
        return normalized
    return "UNKNOWN"


def _coerce_offer_analysis(raw: dict[str, Any]) -> OfferAnalysis:
    tech_raw = raw.get("tech_stack")
    if isinstance(tech_raw, list):
        tech_stack = sorted({str(item).strip().lower() for item in tech_raw if str(item).strip()})
    elif isinstance(tech_raw, str):
        tech_stack = [part.strip().lower() for part in tech_raw.split(",") if part.strip()]
    else:
        tech_stack = []

    signals_raw = raw.get("signals")
    if isinstance(signals_raw, list):
        signals = [str(item).strip() for item in signals_raw if str(item).strip()]
    else:
        signals = []

    confidence_raw = raw.get("confidence", 0.0)
    if isinstance(confidence_raw, str):
        lowered = confidence_raw.strip().lower()
        confidence_map = {
            "high": 0.85,
            "medium": 0.6,
            "low": 0.35,
            "alta": 0.85,
            "media": 0.6,
            "baja": 0.35,
        }
        if lowered in confidence_map:
            confidence = confidence_map[lowered]
        else:
            numeric_text = lowered.replace(",", ".").replace("%", "")
            try:
                confidence = float(numeric_text)
            except ValueError:
                confidence = 0.0
    else:
        confidence = confidence_raw

    return OfferAnalysis.model_validate(
        {
            "seniority": _normalize_seniority(raw.get("seniority")),
            "offer_type": _normalize_offer_type(raw.get("offer_type")),
            "tech_stack": tech_stack,
            "confidence": confidence,
            "signals": signals,
        }
    )


def _recover_offer_from_debug(debug_message: str) -> OfferAnalysis | None:
    # Use BAML's internal trace to recover JSON outputs when structured parse fails by extra keys.
    text_candidates: list[str] = [debug_message]
    try:
        payload = json.loads(debug_message)
        text_candidates.extend(_iter_strings(payload))
    except Exception:
        pass

    for candidate in text_candidates:
        blocks = re.findall(
            r"```(?:json)?\s*(\{.*?\})\s*```",
            candidate,
            flags=re.DOTALL | re.IGNORECASE,
        )
        for block in reversed(blocks):
            try:
                parsed = json.loads(block)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict) and any(
                key in parsed for key in ("seniority", "offer_type", "tech_stack")
            ):
                try:
                    return _coerce_offer_analysis(parsed)
                except Exception:
                    continue

        # Fallback for non-fenced JSON objects in debug traces.
        object_candidates = re.findall(r"(\{(?:[^{}]|(?:\{[^{}]*\}))*\})", candidate, flags=re.DOTALL)
        for snippet in reversed(object_candidates):
            try:
                parsed = json.loads(snippet)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict) and any(
                key in parsed for key in ("seniority", "offer_type", "tech_stack")
            ):
                try:
                    return _coerce_offer_analysis(parsed)
                except Exception:
                    continue
    return None


def _default_baml_root() -> Path:
    return Path(__file__).resolve().parent.parent / "baml_src"


def prepare_baml_env(model_name: str) -> None:
    proxy_port = os.environ.get("OPENCODE_PROXY_PORT", "4100")
    default_proxy_url = f"http://127.0.0.1:{proxy_port}/v1"

    os.environ.setdefault("BAML_PROXY_BASE_URL", default_proxy_url)
    os.environ.setdefault("BAML_PROXY_API_KEY", "dummy")
    os.environ.setdefault("BAML_MODEL", model_name)


def create_runtime() -> tuple[Any, Any]:
    try:
        from baml_py import BamlRuntime
    except ImportError as exc:
        raise BamlRuntimeError(
            "BAML runtime not available. Run: uv sync (with baml-py installed)."
        ) from exc

    baml_root = _default_baml_root()
    if not baml_root.exists():
        raise BamlRuntimeError(f"BAML source directory not found: {baml_root}")

    runtime = BamlRuntime.from_directory(str(baml_root), os.environ.copy())
    ctx = runtime.create_context_manager()
    return runtime, ctx


async def extract_offer(runtime: Any, ctx: Any, text: str) -> OfferAnalysis:
    env_vars = os.environ.copy()
    try:
        # Newer baml_py versions require collectors/env_vars/tags.
        result = await runtime.call_function(
            "ExtractOffer",
            {"text": text},
            ctx,
            None,
            None,
            [],
            env_vars,
            {},
        )
    except TypeError:
        # Backward compatibility with older signatures.
        result = await runtime.call_function("ExtractOffer", {"text": text}, ctx, None, None)
    if not result.is_ok():
        debug_message = result.unstable_internal_repr()
        if _is_rate_limit_message(debug_message):
            raise BamlRateLimitError("BAML provider rate limit detected.")
        recovered = _recover_offer_from_debug(debug_message)
        if recovered is not None:
            return recovered
        raise BamlRuntimeError(f"BAML extraction failed: {debug_message[:500]}")

    try:
        current_module = sys.modules[__name__]
        try:
            parsed = result.cast_to(
                current_module,
                current_module,
                current_module,
                False,
                runtime,
            )
        except TypeError:
            parsed = result.cast_to(current_module, current_module)
    except Exception as exc:
        debug_message = result.unstable_internal_repr()
        raise BamlRuntimeError(
            "BAML cast failed; check schema/client configuration. "
            f"Debug: {debug_message[:500]}"
        ) from exc

    if isinstance(parsed, OfferAnalysis):
        return parsed

    if isinstance(parsed, dict):
        return OfferAnalysis.model_validate(parsed)

    try:
        payload = json.loads(result.unstable_internal_repr())
        if isinstance(payload, dict):
            for key in ("parsed_output", "parsed", "value"):
                candidate = payload.get(key)
                if isinstance(candidate, dict):
                    return OfferAnalysis.model_validate(candidate)
    except Exception:
        pass

    raise BamlRuntimeError(f"Unexpected BAML output type: {type(parsed).__name__}")
