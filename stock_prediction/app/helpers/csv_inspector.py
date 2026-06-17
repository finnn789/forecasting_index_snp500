"""CSV file inspection & metadata extraction for processed data directories."""

from __future__ import annotations

import pandas as pd
from pathlib import Path

from app.core.exceptions import NotFoundError, ValidationError
from app.schemas.sentiment import ProcessedFileInfo

PROCESSED_DIR = Path("data/processed")
STOCKS_DIR = PROCESSED_DIR / "stocks"
SENTIMENT_DIR = PROCESSED_DIR / "sentiment"

VALID_SOURCES = {"stocks", "sentiment"}
SOURCE_DIR_MAP = {"stocks": STOCKS_DIR, "sentiment": SENTIMENT_DIR}


def validate_source(source: str) -> None:
    """Validate that source parameter is one of allowed values."""
    if source not in VALID_SOURCES:
        raise ValidationError(
            f"Parameter 'source' tidak valid: '{source}'. Pilihan: {sorted(VALID_SOURCES)}",
            code="INVALID_SOURCE"
        )


def build_file_info(path: Path) -> ProcessedFileInfo:
    """Extract metadata from a CSV file (columns, row count, date range)."""
    df = pd.read_csv(path, nrows=0)
    total_rows = sum(1 for _ in open(path)) - 1
    date_start = date_end = None
    if "Date" in df.columns:
        df_date = pd.read_csv(path, usecols=["Date"], parse_dates=["Date"])
        date_start = str(df_date["Date"].min().date())
        date_end = str(df_date["Date"].max().date())
    return ProcessedFileInfo(
        filename=path.name,
        path=str(path),
        total_rows=total_rows,
        columns=df.columns.tolist(),
        date_start=date_start,
        date_end=date_end
    )


def resolve_csv_path(source: str, file: str) -> Path:
    """Resolve and validate path to a CSV file in processed data directory."""
    validate_source(source)
    filename = file if file.endswith(".csv") else f"{file}.csv"
    path = SOURCE_DIR_MAP[source] / filename
    if not path.exists():
        raise NotFoundError(
            f"File '{filename}' tidak ditemukan di data/processed/{source}/. Jalankan pipeline preprocessing terlebih dahulu.",
            code="FILE_NOT_FOUND"
        )
    return path
