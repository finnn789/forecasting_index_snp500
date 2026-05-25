from __future__ import annotations
from datetime import date
from pydantic import BaseModel, ConfigDict, field_validator


class Headline(BaseModel):
    model_config = ConfigDict(frozen=True)
    date: date
    title: str
    source: str | None = None

    @field_validator("title")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be empty")
        return v.strip()
