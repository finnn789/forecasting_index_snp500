"""
app/schemas/live.py — Response schemas untuk app/api/v1/routes_live.py
(fitur "Prediksi Live" di Dashboard: fetch OHLCV+berita live via yfinance).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LiveStockLatestResponse(BaseModel):
    """OHLCV S&P 500 live (yfinance), tail N baris terbaru."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "columns": ["Date", "Open", "High", "Low", "Close", "Volume"],
                "n": 30,
                "rows": [
                    {"Date": "2026-07-31", "Open": 7462.13, "High": 7512.04, "Low": 7399.83, "Close": 7489.72, "Volume": 5391020000}
                ],
                "latest_date": "2026-07-31",
                "latest_close": 7489.72,
                "fetched_at": "2026-08-01T06:00:00Z",
            }
        }
    )

    columns: list[str]
    n: int
    rows: list[dict[str, Any]]
    latest_date: str
    latest_close: float
    fetched_at: str


class LiveHeadline(BaseModel):
    title: str
    date: str
    sentiment_label: str
    sentiment_score: float = Field(..., ge=0, le=1)


class LiveDailySentiment(BaseModel):
    date: str
    headline_count: int
    sentiment_mean: float
    sentiment_label: str


class LiveNewsLatestResponse(BaseModel):
    """Headline berita S&P 500 live (yfinance `.news`) + sentimen harian
    agregat (FinBERT, formula sama dengan data latih model — rata-rata
    sederhana `sentiment_numeric`). Cakupan berita live TERBATAS (biasanya
    hanya 1-2 hari kalender terakhir — yfinance tidak menyediakan arsip
    per-tanggal), ditandai jujur lewat jumlah hari di `daily_sentiment`."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "headlines": [
                    {
                        "title": "Amazon's surging cloud business is growing at a breakneck pace",
                        "date": "2026-07-31",
                        "sentiment_label": "positive",
                        "sentiment_score": 0.91,
                    }
                ],
                "daily_sentiment": [
                    {"date": "2026-07-31", "headline_count": 31, "sentiment_mean": 0.129, "sentiment_label": "neutral"}
                ],
                "accumulated_days": 6,
                "fetched_at": "2026-08-01T06:00:00Z",
            }
        }
    )

    headlines: list[LiveHeadline]
    daily_sentiment: list[LiveDailySentiment]
    accumulated_days: int = Field(
        ..., description="Total hari unik dengan sentimen live tersimpan (akumulasi lintas fetch/hari, bukan cuma fetch ini)"
    )
    fetched_at: str
