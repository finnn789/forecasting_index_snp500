from __future__ import annotations
from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, model_validator

SentimentLabel = Literal["positive", "neutral", "negative"]


class SentimentScore(BaseModel):
    model_config = ConfigDict(frozen=True)
    positive: float
    negative: float
    neutral: float
    label: SentimentLabel
    score: float  # positive - negative, range [-1, 1]

    @model_validator(mode="after")
    def _check_probabilities(self) -> "SentimentScore":
        total = self.positive + self.negative + self.neutral
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"probabilities must sum to ~1.0, got {total:.4f}")
        if not (-1.0 - 1e-6 <= self.score <= 1.0 + 1e-6):
            raise ValueError("score must be in [-1, 1]")
        return self


class DailySentiment(BaseModel):
    model_config = ConfigDict(frozen=True)
    date: date
    score_mean: float
    score_positive: float
    score_negative: float
    label: SentimentLabel
