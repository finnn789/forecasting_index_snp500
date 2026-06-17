from __future__ import annotations

import pandas as pd


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
