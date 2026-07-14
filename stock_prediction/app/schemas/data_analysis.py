"""
app/schemas/data_analysis.py — Response schemas untuk app/api/v1/routes_data_analysis.py.

Merepresentasikan alur EDA & preprocessing di:
  - notebooks/01_EDA_stock_data.ipynb   (saham GSPC)
  - notebooks/02_EDA_sentiment_data.ipynb (headline berita + FinBERT)
"""

from typing import Any

from pydantic import BaseModel, Field


class Histogram(BaseModel):
    bin_edges: list[float]
    counts: list[int]


# ---------------------------------------------------------------------------
# Stock — notebooks/01_EDA_stock_data.ipynb
# ---------------------------------------------------------------------------

class StockRawInfo(BaseModel):
    total_rows: int
    columns: list[str]
    date_start: str
    date_end: str
    missing_values: dict[str, int]
    duplicate_dates: int
    plot_hint: str = "table — ringkasan struktur data mentah"


class StockRawPreviewResponse(BaseModel):
    columns: list[str]
    n: int
    rows: list[dict[str, Any]]
    plot_hint: str = "table — cuplikan baris pertama data OHLCV mentah"


class ColumnStats(BaseModel):
    count: int
    mean: float
    std: float
    min: float
    q25: float
    median: float
    q75: float
    max: float
    cv_pct: float = Field(description="Coefficient of variation = std/mean*100")


class StockDescriptiveStats(BaseModel):
    columns: dict[str, ColumnStats]
    plot_hint: str = "table — statistik deskriptif OHLCV"


class CrashEvent(BaseModel):
    date: str
    label: str


class PriceVolumePoint(BaseModel):
    date: str
    close: float
    volume: int


class StockPriceVolumeResponse(BaseModel):
    points: list[PriceVolumePoint]
    crash_events: list[CrashEvent]
    plot_hint: str = "dual-axis line+bar chart — x: date, y1: close, y2: volume"


class ReturnPoint(BaseModel):
    date: str
    return_pct: float


class YearlyReturnBox(BaseModel):
    year: int
    min: float
    q1: float
    median: float
    q3: float
    max: float


class StockDailyReturnsResponse(BaseModel):
    points: list[ReturnPoint]
    mean: float
    std: float
    skewness: float
    kurtosis: float
    max_gain_date: str
    max_gain_pct: float
    max_loss_date: str
    max_loss_pct: float
    histogram: Histogram
    yearly_boxplot: list[YearlyReturnBox]
    plot_hint: str = "line + histogram + boxplot per tahun — daily return (%)"


class RollingStatPoint(BaseModel):
    date: str
    close: float
    ma_20: float | None
    ma_50: float | None
    ma_200: float | None
    volatility_30: float | None


class StockRollingStatsResponse(BaseModel):
    points: list[RollingStatPoint]
    plot_hint: str = "line chart — close + MA20/50/200 (atas), volatility 30d (bawah)"


class MonthlySpread(BaseModel):
    month: str
    avg_hl_spread: float


class OhlcSpreadPoint(BaseModel):
    date: str
    hl_spread: float
    oc_spread: float


class StockOhlcSpreadResponse(BaseModel):
    points: list[OhlcSpreadPoint]
    monthly_avg_hl_spread: list[MonthlySpread]
    bullish_days: int
    bearish_days: int
    bullish_pct: float
    bearish_pct: float
    plot_hint: str = "line + bar + pie — HL spread, OC spread, proporsi bullish/bearish"


class StockCorrelationResponse(BaseModel):
    columns: list[str]
    matrix: list[list[float]]
    plot_hint: str = "heatmap — correlation matrix OHLCV + return + spread"


class SeasonalReturn(BaseModel):
    label: str
    avg_return_pct: float


class StockSeasonalityResponse(BaseModel):
    monthly: list[SeasonalReturn]
    weekday: list[SeasonalReturn]
    plot_hint: str = "bar chart — rata-rata return per bulan & per hari"


class DrawdownPoint(BaseModel):
    date: str
    cum_return_pct: float
    drawdown_pct: float


class StockCumulativeReturnDrawdownResponse(BaseModel):
    points: list[DrawdownPoint]
    total_return_pct: float
    max_drawdown_pct: float
    plot_hint: str = "area chart — cumulative return (atas), drawdown (bawah)"


class AnnualReturn(BaseModel):
    year: int
    return_pct: float


class StockSummaryResponse(BaseModel):
    total_trading_days: int
    start_price: float
    end_price: float
    cumulative_return_pct: float
    max_drawdown_pct: float
    mean_daily_return_pct: float
    annualized_volatility_pct: float
    skewness: float
    kurtosis: float
    bullish_days: int
    bearish_days: int
    bullish_pct: float
    bearish_pct: float
    annual_returns: list[AnnualReturn]
    plot_hint: str = "summary card + bar chart return tahunan"


class StockPreprocessingSide(BaseModel):
    total_rows: int
    columns: list[str]
    missing_values: dict[str, int]
    duplicate_dates: int


class StockPreprocessingResponse(BaseModel):
    raw: StockPreprocessingSide
    clean: StockPreprocessingSide
    columns_dropped: list[str]
    invalid_rows_dropped: int
    note: str = (
        "Mencerminkan pipeline/preprocessing/stock_preprocessor.py::StockPreprocessor "
        "(dipakai sistem sesungguhnya): drop kolom tidak relevan, validasi kolom, sort, "
        "dedup tanggal, forward/backward-fill NaN, drop baris tidak valid. "
        "TIDAK melakukan scaling (beda dari cell MinMaxScaler eksploratif di notebook 01)."
    )
    plot_hint: str = "before/after table — StockPreprocessor.clean()"


# ---------------------------------------------------------------------------
# Sentiment — notebooks/02_EDA_sentiment_data.ipynb
# ---------------------------------------------------------------------------

class SentimentRawInfo(BaseModel):
    total_rows: int
    columns: list[str]
    date_start: str
    date_end: str
    missing_values: dict[str, int]
    duplicate_rows: int
    duplicate_titles: int
    duplicate_title_date: int
    plot_hint: str = "table — ringkasan struktur data headline mentah"


class SentimentRawPreviewResponse(BaseModel):
    columns: list[str]
    n: int
    rows: list[dict[str, Any]]
    plot_hint: str = "table — cuplikan baris pertama data sentimen/headline mentah"


class NewsPerYearItem(BaseModel):
    year: int
    count: int


class SentimentNewsPerYearResponse(BaseModel):
    data: list[NewsPerYearItem]
    total: int
    plot_hint: str = "bar chart — x: year, y: count"


class NewsPerDayPoint(BaseModel):
    date: str
    count: int
    rolling_30: float | None


class SentimentNewsPerDayResponse(BaseModel):
    points: list[NewsPerDayPoint]
    mean: float
    median: float
    max_count: int
    max_date: str
    min_count: int
    min_date: str
    plot_hint: str = "line chart — jumlah berita per hari + rolling 30 hari"


class SentimentHeadlineLengthResponse(BaseModel):
    char_mean: float
    char_std: float
    char_min: float
    char_max: float
    char_histogram: Histogram
    word_mean: float
    word_std: float
    word_min: float
    word_max: float
    word_histogram: Histogram
    plot_hint: str = "histogram — panjang headline (karakter & kata)"


class ClosingPricePoint(BaseModel):
    date: str
    close: float


class SentimentClosingPriceResponse(BaseModel):
    points: list[ClosingPricePoint]
    plot_hint: str = "line chart — closing price S&P 500 (kolom CP di data berita)"


class SentimentPreprocessingResponse(BaseModel):
    raw_total: int
    after_cleaning_total: int
    dropped_duplicates: int
    dropped_short_headlines: int
    min_words: int
    note: str = (
        "Tahap cleaning ini mengikuti metodologi notebooks/02_EDA_sentiment_data.ipynb "
        "(normalisasi whitespace, buang duplikat Title+Date, filter headline < 3 kata). "
        "Pipeline produksi (sentiment_service.run_preprocessing_pipeline_stream) SAAT INI "
        "tidak menjalankan tahap cleaning ini — headline mentah langsung diberi skor FinBERT."
    )
    plot_hint: str = "before/after table — text cleaning"


class SentimentScoringDistributionResponse(BaseModel):
    total_headlines: int
    label_counts: dict[str, int]
    label_pct: dict[str, float]
    score_mean: float
    score_std: float
    score_histogram: Histogram
    plot_hint: str = "bar/pie + histogram — distribusi label & confidence FinBERT"


class DailySentimentPoint(BaseModel):
    date: str
    sentiment_mean: float
    rolling_30: float | None


class SentimentDailyAggregationResponse(BaseModel):
    points: list[DailySentimentPoint]
    histogram: Histogram
    label_counts: dict[str, int]
    note: str = (
        "sentiment_mean di sini dihitung ULANG langsung dari headline berskor "
        "(probability-weighted: signed = sentiment_numeric × sentiment_score), sesuai "
        "notebook 02. CATATAN: file data/processed/sentiment/headlines_daily_sentiment.csv "
        "yang disimpan pipeline produksi saat ini masih pakai metode LAMA (rata-rata "
        "sentiment_numeric tanpa bobot confidence) — belum diupgrade ke metode weighted."
    )
    plot_hint: str = "line chart + histogram — sentiment_mean harian (probability-weighted)"


class MethodComparisonPoint(BaseModel):
    date: str
    weighted: float
    unweighted: float


class SentimentMethodComparisonResponse(BaseModel):
    points: list[MethodComparisonPoint]
    correlation: float
    plot_hint: str = "scatter chart — perbandingan skor weighted vs unweighted per hari"


# ---------------------------------------------------------------------------
# Combined — OHLCV + sentiment_mean (mirrors dataset_builder.py::load_joined(),
# join yang sama persis dipakai prediction_service.py untuk training/inference)
# ---------------------------------------------------------------------------

class CombinedMergeInfo(BaseModel):
    rows_stock: int
    rows_sentiment: int
    rows_merged: int
    dropped_no_sentiment_match: int
    coverage_pct: float
    date_start: str
    date_end: str
    columns: list[str]
    note: str = (
        "Inner join pada kolom Date antara OHLCV (setelah StockPreprocessor.clean()) "
        "dan sentiment_mean harian — logic identik dengan "
        "pipeline/feature_engineering/dataset_builder.py::load_joined() yang dipakai "
        "langsung oleh model untuk training & inference."
    )
    plot_hint: str = "table — ringkasan hasil penggabungan OHLCV + sentiment_mean"


class CombinedMergePreviewResponse(BaseModel):
    columns: list[str]
    n: int
    rows: list[dict[str, Any]]
    plot_hint: str = "table — cuplikan baris pertama data gabungan OHLCV + sentiment_mean"


class PipelineStep(BaseModel):
    order: int
    name: str
    description: str
    rows_in: int | None
    rows_out: int | None
    detail: dict[str, Any]


class CombinedPipelineStepsResponse(BaseModel):
    steps: list[PipelineStep]
    window: int
    feature_cols: list[str]
    note: str = (
        "Mirror dataset_builder.build_dataset() dengan parameter default "
        "(window=20, train_end=2022-12-31, val_end=2023-12-31) — data yang "
        "sama persis dengan input training model."
    )
    plot_hint: str = "stepper — langkah preprocessing dataset gabungan"
