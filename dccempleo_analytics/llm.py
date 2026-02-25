from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class OfferLabel(BaseModel):
    seniority: str = Field(default="UNKNOWN")
    offer_type: str = Field(default="JOB")
    tech_stack: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0)
    signals: list[str] = Field(default_factory=list)

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, value: Any) -> float:
        if isinstance(value, bool):
            return 1.0 if value else 0.0

        if isinstance(value, (int, float)):
            return cls._bound_confidence(float(value))

        if isinstance(value, str):
            lowered = value.strip().lower()
            text_map = {
                "high": 0.85,
                "medium": 0.6,
                "low": 0.35,
                "alta": 0.85,
                "media": 0.6,
                "baja": 0.35,
            }
            if lowered in text_map:
                return text_map[lowered]

            numeric_text = lowered.replace(",", ".").replace("%", "")
            try:
                return cls._bound_confidence(float(numeric_text))
            except ValueError:
                return 0.0

        return 0.0

    @staticmethod
    def _bound_confidence(value: float) -> float:
        if value < 0:
            return 0.0
        if value > 1:
            value = value / 100 if value <= 100 else 1.0
        return max(0.0, min(1.0, value))
