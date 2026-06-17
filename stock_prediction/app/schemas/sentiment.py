"""
app/schemas/sentiment.py — Pydantic schemas untuk endpoint sentimen & feature engineering.
"""

from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Sentiment
# ---------------------------------------------------------------------------

class SentimentRequest(BaseModel):
    text: str = Field(..., min_length=3, description="Teks headline berita keuangan.")

    model_config = {
        "json_schema_extra": {
            "example": {"text": "Federal Reserve raises interest rates by 25 basis points"}
        }
    }


class SentimentResponse(BaseModel):
    text: str
    label: str = Field(..., description="Kelas dominan: positive | negative | neutral")
    score: float = Field(..., description="sentiment_score = positive − negative ∈ [−1, 1]")
    positive: float
    negative: float
    neutral: float

    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "Federal Reserve raises interest rates by 25 basis points",
                "label": "negative",
                "score": -0.42,
                "positive": 0.12,
                "negative": 0.54,
                "neutral": 0.34,
            }
        }
    }


# ---------------------------------------------------------------------------
# EDA — response schemas untuk endpoint data/eda/*
# ---------------------------------------------------------------------------

class NewsPerYearItem(BaseModel):
    year: int
    count: int


class NewsPerYearResponse(BaseModel):
    data: list[NewsPerYearItem]
    total: int
    plot_hint: str = "bar chart — x: year, y: count"


class NewsPerDayStats(BaseModel):
    mean: float
    max: int
    max_date: str
    min: int
    min_date: str
    plot_hint: str = "line chart — x: date, y: daily_count"


class HeadlineLengthStats(BaseModel):
    char_mean: float
    char_std: float
    char_min: float
    char_max: float
    word_mean: float
    word_std: float
    word_min: float
    word_max: float
    plot_hint: str = "histogram — title_len_char & title_len_word"


class SentimentDistributionItem(BaseModel):
    label: str
    count: int
    pct: float


class SentimentDistributionResponse(BaseModel):
    data: list[SentimentDistributionItem]
    sentiment_score_mean: float
    sentiment_score_std: float
    plot_hint: str = "bar chart — x: label, y: count"


class DatasetSummary(BaseModel):
    total_rows: int
    date_start: str
    date_end: str
    span_days: int
    # missing_title: int
    # missing_cp: int
    dtypes: dict[str, str]


# ---------------------------------------------------------------------------
# Feature Engineering
# ---------------------------------------------------------------------------

class ColumnGroups(BaseModel):
    """Pengelompokan kolom berdasarkan sumber data."""
    ohlcv: list[str] = Field(description="Kolom harga saham asli: Date, Open, High, Low, Close, Volume")
    sentiment: list[str] = Field(description="Kolom sentimen harian dari FinBERT")
    technical: list[str] = Field(description="Kolom indikator teknikal: EMA, RSI, MACD, BB, dll.")
    lag: list[str] = Field(description="Kolom lag features")
    rolling: list[str] = Field(description="Kolom rolling features")
    target: list[str] = Field(description="Kolom target untuk training LSTM")


class DataInfo(BaseModel):
    total_rows: int
    date_range: dict[str, str | None]
    column_groups: ColumnGroups
    missing_values: dict[str, int]


class FeatureEngineeringResponse(BaseModel):
    status: str
    data_info: DataInfo
    statistics: dict[str, Any]
    sentiment_distribution: dict[str, int]
    sample: list[dict[str, Any]] = Field(
        default_factory=list,
        description="5 baris pertama hasil feature engineering (preview)"
    )


# ---------------------------------------------------------------------------
# Feature Engineering — Read-Only (inspect data/processed/)
# ---------------------------------------------------------------------------

class ProcessedFileInfo(BaseModel):
    """Metadata satu file CSV di data/processed/."""
    filename: str = Field(description="Nama file beserta ekstensi, misal 'GSPC_2018_2024.csv'")
    path: str = Field(description="Path relatif dari root project")
    total_rows: int = Field(description="Jumlah baris data (tidak termasuk header)")
    columns: list[str] = Field(description="Daftar nama kolom")
    date_start: str | None = Field(None, description="Tanggal pertama jika ada kolom Date")
    date_end: str | None = Field(None, description="Tanggal terakhir jika ada kolom Date")


class ProcessedDataInfo(BaseModel):
    """Seluruh file yang tersedia di data/processed/, dikelompokkan per subdirektori."""
    stocks: list[ProcessedFileInfo] = Field(
        default_factory=list,
        description="File CSV di data/processed/stocks/"
    )
    sentiment: list[ProcessedFileInfo] = Field(
        default_factory=list,
        description="File CSV di data/processed/sentiment/"
    )
    total_files: int = Field(description="Total file CSV yang ditemukan")


class ColumnInfoResponse(BaseModel):
    """Skema kolom dari satu file CSV."""
    source: str = Field(description="Subdirektori sumber: 'stocks' atau 'sentiment'")
    filename: str = Field(description="Nama file yang dibaca")
    total_rows: int
    columns: list[str] = Field(description="Nama semua kolom")
    dtypes: dict[str, str] = Field(description="Tipe data setiap kolom (string Pandas dtype)")
    missing_values: dict[str, int] = Field(description="Jumlah nilai kosong per kolom")


class PreviewResponse(BaseModel):
    """N baris pertama dari satu file CSV."""
    source: str
    filename: str
    total_rows: int
    columns: list[str]
    rows: list[dict[str, Any]] = Field(description="Baris data dalam format list-of-dict")


# ---------------------------------------------------------------------------
# Sentiment Pipeline
# ---------------------------------------------------------------------------

class PreprocessRunResponse(BaseModel):
    status: str
    total_headlines: int
    total_days: int
    output_path: str
    duration_seconds: float
    date_range: dict[str, str | None]
    sample: list[dict[str, Any]]


class PipelineStatusResponse(BaseModel):
    clean_file_exists: bool
    daily_file_exists: bool
    total_headlines: int | None
    total_days: int | None
    date_range: dict[str, str | None]


class ModelStatusResponse(BaseModel):
    is_available: bool
    model_path: str
    source: str                          # "local_snapshot" | "local_dir" | "huggingface_hub"
    snapshot_path: str | None            # path snapshot aktif (jika HF cache format)
    required_files: dict[str, bool]      # config.json, pytorch_model.bin, tokenizer_config.json, vocab.txt
    model_size_mb: float | None          # total ukuran file di snapshot dir

class RawStocksResponse(BaseModel):
    """Skema baris tunggal dari file CSV stock data (GSPC_2018_2024.csv, dll)."""
    date: str = Field(description="Tanggal data: YYYY-MM-DD")
    open: float = Field(description="Harga pembukaan")
    high: float = Field(description="Harga tertinggi")
    low: float = Field(description="Harga terendah")
    close: float = Field(description="Harga penutupan")
    volume: int = Field(description="Volume transaksi")
    daily_return: float | None = Field(None, description="Perubahan harian dalam persen")
    hl_spread: float = Field(description="Selisih High - Low")
    oc_spread: float = Field(description="Selisih Open - Close")
    ma_20: float | None = Field(None, description="Moving Average 20 hari")
    ma_50: float | None = Field(None, description="Moving Average 50 hari")
    ma_200: float | None = Field(None, description="Moving Average 200 hari")
    volatility_30: float | None = Field(None, description="Volatilitas 30 hari")

    model_config = {
        "json_schema_extra": {
            "example": {
                "date": "2018-01-02",
                "open": 2683.73,
                "high": 2695.89,
                "low": 2682.36,
                "close": 2695.81,
                "volume": 3397430000,
                "daily_return": None,
                "hl_spread": 13.53,
                "oc_spread": 12.08,
                "ma_20": None,
                "ma_50": None,
                "ma_200": None,
                "volatility_30": None,
            }
        }
    }
