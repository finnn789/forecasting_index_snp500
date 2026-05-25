"""
app/api/v1/routes_data.py — Endpoint EDA dan Feature Engineering.

Semua endpoint membaca data yang sudah diproses (processed/) dan
mengembalikan respons JSON — tidak ada gambar inline.
"""

import logging
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException

from app.schemas.base import SuccessResponse
from app.schemas.sentiment import (
    ColumnGroups,
    DataInfo,
    DatasetSummary,
    FeatureEngineeringResponse,
    HeadlineLengthStats,
    NewsPerDayStats,
    NewsPerYearItem,
    NewsPerYearResponse,
    SentimentDistributionItem,
    SentimentDistributionResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Data & EDA"])

# ---------------------------------------------------------------------------
# Path konstanta
# ---------------------------------------------------------------------------
_SENTIMENT_DAILY = Path("data/processed/sentiment/headlines_daily_sentiment.csv")
_HEADLINES_CLEAN = Path("data/processed/sentiment/headlines_clean.csv")
_RAW_NEWS        = Path("data/raw/news/sp500_headlines_2008_2024.csv")


def _load_daily(path: Path = _SENTIMENT_DAILY) -> pd.DataFrame:
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail=f"File belum tersedia: {path}. Jalankan pipeline preprocessing terlebih dahulu.",
        )
    return pd.read_csv(path, parse_dates=["Date"])


def _load_clean(path: Path = _HEADLINES_CLEAN) -> pd.DataFrame:
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail=f"File belum tersedia: {path}. Jalankan pipeline preprocessing terlebih dahulu.",
        )
    return pd.read_csv(path, parse_dates=["Date"])


# ---------------------------------------------------------------------------
# EDA Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/data/eda/summary",
    response_model=SuccessResponse[DatasetSummary],
    summary="Statistik Dasar Dataset",
    description=(
        "Menampilkan statistik dasar dataset berita: jumlah baris, "
        "rentang tanggal, missing values, dan tipe data kolom."
    ),
)
async def eda_summary() -> SuccessResponse[DatasetSummary]:
    logger.info("[EDA] Memuat ringkasan dataset...")

    df = _load_clean()
    logger.info("[EDA] Dataset dimuat — %d baris", len(df))

    summary = DatasetSummary(
        total_rows=len(df),
        date_start=str(df["Date"].min().date()),
        date_end=str(df["Date"].max().date()),
        span_days=int((df["Date"].max() - df["Date"].min()).days),
        missing_title=int(df["title_clean"].isnull().sum()),
        missing_cp=int(df["CP"].isnull().sum()),
        dtypes={col: str(dtype) for col, dtype in df.dtypes.items()},
    )

    logger.info("[EDA] Ringkasan selesai — %d baris, rentang %s s/d %s",
                summary.total_rows, summary.date_start, summary.date_end)
    return SuccessResponse[DatasetSummary](data=summary, message="Ringkasan dataset berhasil dimuat")


@router.get(
    "/data/eda/news-per-year",
    response_model=SuccessResponse[NewsPerYearResponse],
    summary="Distribusi Berita per Tahun",
    description="Menghitung jumlah headline berita per tahun. Data siap digunakan sebagai bar chart.",
)
async def eda_news_per_year() -> SuccessResponse[NewsPerYearResponse]:
    logger.info("[EDA] Menghitung distribusi berita per tahun...")

    df = _load_clean()
    df["Year"] = df["Date"].dt.year
    counts = df.groupby("Year").size().reset_index(name="count")

    items = [NewsPerYearItem(year=int(r["Year"]), count=int(r["count"])) for _, r in counts.iterrows()]
    logger.info("[EDA] Distribusi per tahun selesai — %d tahun", len(items))

    result = NewsPerYearResponse(data=items, total=len(df))
    return SuccessResponse[NewsPerYearResponse](data=result, message="Distribusi berita per tahun berhasil dimuat")


@router.get(
    "/data/eda/news-per-day",
    response_model=SuccessResponse[NewsPerDayStats],
    summary="Statistik Jumlah Berita per Hari",
    description="Statistik agregasi jumlah headline per hari (mean, max, min) beserta petunjuk visualisasi.",
)
async def eda_news_per_day() -> SuccessResponse[NewsPerDayStats]:
    logger.info("[EDA] Menghitung statistik berita per hari...")

    df = _load_clean()
    per_day = df.groupby("Date").size()

    stats = NewsPerDayStats(
        mean=round(float(per_day.mean()), 2),
        max=int(per_day.max()),
        max_date=str(per_day.idxmax().date()),
        min=int(per_day.min()),
        min_date=str(per_day.idxmin().date()),
    )

    logger.info("[EDA] Statistik per hari selesai — mean=%.2f, max=%d, min=%d",
                stats.mean, stats.max, stats.min)
    return SuccessResponse[NewsPerDayStats](data=stats, message="Statistik berita per hari berhasil dimuat")


@router.get(
    "/data/eda/headline-length",
    response_model=SuccessResponse[HeadlineLengthStats],
    summary="Distribusi Panjang Headline",
    description="Statistik panjang headline dalam karakter dan kata. Data siap digunakan sebagai histogram.",
)
async def eda_headline_length() -> SuccessResponse[HeadlineLengthStats]:
    logger.info("[EDA] Menghitung distribusi panjang headline...")

    df = _load_clean()
    df["len_char"] = df["title_clean"].str.len()
    df["len_word"] = df["title_clean"].str.split().str.len()

    stats = HeadlineLengthStats(
        char_mean=round(float(df["len_char"].mean()), 2),
        char_std=round(float(df["len_char"].std()), 2),
        char_min=float(df["len_char"].min()),
        char_max=float(df["len_char"].max()),
        word_mean=round(float(df["len_word"].mean()), 2),
        word_std=round(float(df["len_word"].std()), 2),
        word_min=float(df["len_word"].min()),
        word_max=float(df["len_word"].max()),
    )

    logger.info("[EDA] Panjang headline — char mean=%.2f, word mean=%.2f",
                stats.char_mean, stats.word_mean)
    return SuccessResponse[HeadlineLengthStats](data=stats, message="Statistik panjang headline berhasil dimuat")


@router.get(
    "/data/eda/sentiment-distribution",
    response_model=SuccessResponse[SentimentDistributionResponse],
    summary="Distribusi Label Sentimen",
    description=(
        "Menampilkan distribusi label sentimen (positive/negative/neutral) "
        "beserta statistik sentiment_score. Data siap digunakan sebagai bar chart."
    ),
)
async def eda_sentiment_distribution() -> SuccessResponse[SentimentDistributionResponse]:
    logger.info("[EDA] Menghitung distribusi label sentimen...")

    df = _load_clean()
    counts = df["sentiment_label"].value_counts()
    total = len(df)

    items = [
        SentimentDistributionItem(
            label=label,
            count=int(cnt),
            pct=round(100 * cnt / total, 2),
        )
        for label, cnt in counts.items()
    ]

    result = SentimentDistributionResponse(
        data=items,
        sentiment_score_mean=round(float(df["sentiment_score"].mean()), 4),
        sentiment_score_std=round(float(df["sentiment_score"].std()), 4),
    )

    logger.info("[EDA] Distribusi sentimen — %s",
                {i.label: i.count for i in items})
    return SuccessResponse[SentimentDistributionResponse](data=result, message="Distribusi label sentimen berhasil dimuat")


# ---------------------------------------------------------------------------
# Feature Engineering Endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/data/feature-engineering/run",
    response_model=SuccessResponse[FeatureEngineeringResponse],
    summary="Jalankan Feature Engineering (Sentimen)",
    description=(
        "Menjalankan feature extraction dari data sentimen harian yang sudah diproses. "
        "Indikator teknikal (MACD, RSI, Bollinger Bands) TIDAK dihitung di sini — "
        "endpoint ini hanya memproses fitur sentimen. "
        "Data OHLCV asli diperlukan secara terpisah melalui stock_fetcher sebelum "
        "compute_technical_indicators() dapat dipanggil."
    ),
)
async def run_feature_engineering(ticker: str = "^GSPC") -> SuccessResponse[FeatureEngineeringResponse]:
    from pipeline.feature_engineering.sentiment_aggregator import (
        extract_features,
        get_feature_summary,
        load_daily_sentiment,
    )

    logger.info("[FE] Memulai feature engineering sentimen untuk ticker: %s", ticker)

    # 1. Muat data sentimen harian (output notebook 02)
    logger.info("[FE] Langkah 1/2 — Memuat data sentimen harian...")
    df_sentiment = load_daily_sentiment(_SENTIMENT_DAILY)

    # 2. Ekstraksi fitur dari data sentimen:
    #    encode label, lag, rolling, target
    #    Catatan: compute_technical_indicators() TIDAK dipanggil di sini karena
    #    membutuhkan data OHLCV asli (Open/High/Low/Close/Volume) dari stock_fetcher.
    logger.info("[FE] Langkah 2/2 — Ekstraksi fitur sentimen...")
    df_feat = extract_features(
        df_sentiment.rename(columns={"CP": "Close"}),
        lag_cols=["Close", "sentiment_mean"],
        lags=[1, 3, 5],
        roll_windows=[3, 7],
        target_horizon=1,
        target_mode="return",
    )

    # 3. Kelompokkan kolom berdasarkan sumber
    all_cols = df_feat.columns.tolist()
    _OHLCV_COLS      = ["Date", "Open", "High", "Low", "Close", "Volume"]
    _SENTIMENT_COLS  = ["headline_count", "sentiment_mean", "sentiment_pos",
                        "sentiment_neg", "sentiment_neu", "sentiment_label",
                        "sentiment_label_enc"]
    _TECHNICAL_COLS  = ["ema_20", "ema_50", "rsi_14", "macd", "macd_signal",
                        "macd_hist", "bb_mid", "bb_upper", "bb_lower",
                        "bb_bandwidth", "daily_return", "volatility_20"]

    col_groups = ColumnGroups(
        ohlcv     =[c for c in _OHLCV_COLS     if c in all_cols],
        sentiment =[c for c in _SENTIMENT_COLS  if c in all_cols],
        technical =[c for c in _TECHNICAL_COLS  if c in all_cols],
        lag       =[c for c in all_cols if "lag"  in c],
        rolling   =[c for c in all_cols if "roll" in c],
        target    =[c for c in all_cols if c == "target"],
    )

    # 4. Ringkasan
    logger.info("[FE] Membuat ringkasan akhir...")
    summary = get_feature_summary(df_feat)

    # 5. Sample rows — bersihkan tipe data agar JSON-serializable
    records = []
    for row in df_feat.head(5).to_dict(orient="records"):
        cleaned = {}
        for k, v in row.items():
            if hasattr(v, "item"):
                cleaned[k] = v.item()
            elif isinstance(v, float) and v != v:
                cleaned[k] = None
            elif hasattr(v, "isoformat"):
                cleaned[k] = str(v)
            else:
                cleaned[k] = v
        records.append(cleaned)

    logger.info("[FE] Feature engineering selesai — %d baris, %d kolom",
                summary["total_rows"], summary["total_columns"])

    result = FeatureEngineeringResponse(
        status="success",
        data_info=DataInfo(
            total_rows=summary["total_rows"],
            date_range=summary["date_range"],
            column_groups=col_groups,
            missing_values={k: int(v) for k, v in summary["missing_values"].items()},
        ),
        statistics=summary["statistics"],
        sentiment_distribution={k: int(v) for k, v in summary["sentiment_distribution"].items()},
        sample=records,
    )
    return SuccessResponse[FeatureEngineeringResponse](data=result, message="Feature engineering berhasil dijalankan")
