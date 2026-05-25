from __future__ import annotations
from datetime import date
from pydantic import BaseModel, ConfigDict, model_validator


class DateRange(BaseModel):
    model_config = ConfigDict(frozen=True)
    start: date
    end: date

    @model_validator(mode="after")
    def _check_order(self) -> "DateRange":
        if self.end < self.start:
            raise ValueError("end date must be >= start date")
        return self

    def contains(self, d: date) -> bool:
        return self.start <= d <= self.end

    @classmethod
    def from_settings(cls) -> "DateRange":
        from app.core.settings import settings
        from datetime import date as _date
        s = _date.fromisoformat(settings.data_filter_start)
        e = _date.fromisoformat(settings.data_filter_end)
        return cls(start=s, end=e)

    def to_pandas_query(self) -> tuple[str, str]:
        return (self.start.isoformat(), self.end.isoformat())
