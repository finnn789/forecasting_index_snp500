from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator


class PredictionResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    ticker: str
    target_date: date
    direction: Literal["up", "down"]
    probability_up: float  # 0..1
    confidence: float  # 0..1 — max(probability_up, 1 - probability_up)

    @model_validator(mode="after")
    def _check_ranges(self) -> "PredictionResult":
        if not (0.0 <= self.probability_up <= 1.0):
            raise ValueError("probability_up must be in [0,1]")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("confidence must be in [0,1]")
        return self
