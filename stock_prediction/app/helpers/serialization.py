from __future__ import annotations

from typing import Any

import pandas as pd

ISO_DATE_FORMAT = "%Y-%m-%d"


def format_iso_date(value: Any) -> str:
    """Format sebuah date/Timestamp ke string ISO 'YYYY-MM-DD'.

    Menyatukan pemformatan tanggal yang sebelumnya diulang via
    `.strftime("%Y-%m-%d")` di banyak service.
    """
    return value.strftime(ISO_DATE_FORMAT)


def to_json_safe_record(record: dict) -> dict:
    """Convert a single record dict with numpy/datetime types to JSON-safe native Python types."""
    cleaned = {}
    for k, v in record.items():
        if hasattr(v, "item"):
            cleaned[k] = v.item()
        elif isinstance(v, float) and v != v:
            cleaned[k] = None
        elif hasattr(v, "isoformat"):
            cleaned[k] = str(v)
        else:
            cleaned[k] = v
    return cleaned


def to_json_safe_records(df: pd.DataFrame, n: int | None = None) -> list[dict]:
    """Convert DataFrame to list of JSON-safe dicts, optionally limiting to first n rows."""
    if n is not None:
        df = df.head(n)
    records = df.to_dict(orient="records")
    return [to_json_safe_record(record) for record in records]
