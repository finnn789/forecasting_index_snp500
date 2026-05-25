from __future__ import annotations
import re
from pydantic import BaseModel, ConfigDict, field_validator

_TICKER_RE = re.compile(r"^[A-Z0-9.]{1,10}$")


class TickerSymbol(BaseModel):
    model_config = ConfigDict(frozen=True)
    symbol: str

    @field_validator("symbol", mode="before")
    @classmethod
    def _normalize(cls, v):
        if not isinstance(v, str):
            raise ValueError("symbol must be string")
        v_up = v.strip().upper()
        if not _TICKER_RE.match(v_up):
            raise ValueError(f"invalid ticker symbol: {v!r}")
        return v_up

    def __str__(self) -> str:
        return self.symbol


DEFAULT_TICKER = TickerSymbol(symbol="GSPC")
