from __future__ import annotations
from datetime import date
from pydantic import BaseModel, ConfigDict, model_validator


class StockBar(BaseModel):
    model_config = ConfigDict(frozen=True)
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float

    @model_validator(mode="after")
    def _check_invariants(self) -> "StockBar":
        if self.volume < 0:
            raise ValueError("volume must be >= 0")
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high must be >= open/close/low")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low must be <= open/close/high")
        return self
