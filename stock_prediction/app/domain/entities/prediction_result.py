from __future__ import annotations
from datetime import date
from pydantic import BaseModel, ConfigDict, model_validator


class PredictionResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    ticker: str
    target_date: date
    predicted_close: float
    sentiment_score: float
    confidence: float  # 0..1
    lstm_weight: float
    sentiment_weight: float

    @model_validator(mode="after")
    def _check_ranges(self) -> "PredictionResult":
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("confidence must be in [0,1]")
        if not (-1.0 <= self.sentiment_score <= 1.0):
            raise ValueError("sentiment_score must be in [-1,1]")
        if abs(self.lstm_weight + self.sentiment_weight - 1.0) > 1e-6:
            raise ValueError("lstm_weight + sentiment_weight must == 1.0")
        return self
