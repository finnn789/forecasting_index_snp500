"""
app/schemas/stocks.py — Inner schemas untuk Stock Data EDA (per-stage endpoints).

Mengikuti workflow 11 tahap EDA + feature engineering (lihat
code_plan/notebook_01_eda_stock_data_workflow.md). Setiap endpoint memakai
schema spesifik tahapnya.

CATATAN ENVELOPE: schema di sini adalah *inner* schema (isi `data` saja).
`EnvelopeRoute` otomatis membungkus ke `SuccessResponse{success, data, message, meta}`,
dan pagination ditaruh di `meta.pagination`. Jadi JANGAN menambahkan field
`success`/`message`/`meta`/`page`/`page_size` di sini.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ===== BUILDING BLOCKS (reusable) =====
class EDAStageBase(BaseModel):
    """Field konteks yang dipakai semua response EDA. Hilangkan boilerplate ticker/period."""

    ticker: str = Field(..., description="Stock ticker, mis. '^GSPC'")
    period: str = Field(..., description="Rentang data, mis. '2018-2024'")


class StatBlock(BaseModel):
    """
    Blok statistik deskriptif yang dapat dipakai ulang (harga, volume, return, dll).

    Untuk metrik berbasis persentase (mis. daily return), nilai-nilai di sini
    sudah dalam satuan persen (%).
    """

    min: float
    max: float
    mean: float
    std: float
    median: float | None = None
    cv_pct: float | None = Field(default=None, description="Coefficient of Variation: std/mean*100")
    skew: float | None = Field(default=None, description="Skewness (negatif = ekor kiri lebih panjang)")
    kurtosis: float | None = Field(default=None, description="Kurtosis (>3 = fat tails)")
    q25: float | None = Field(default=None, description="Quantile 25%")
    q75: float | None = Field(default=None, description="Quantile 75%")


# ===== STAGE 1-2: DATA INFO =====
class DataInfoResponse(EDAStageBase):
    """Stage 1-2: metadata dataset & hasil quality check."""

    total_rows: int = Field(..., description="Jumlah baris (trading days)")
    total_columns: int
    date_range: str = Field(..., description="'YYYY-MM-DD to YYYY-MM-DD'")
    columns: list[str]
    missing_values: dict[str, int] = Field(default_factory=dict, description="Missing count per kolom")
    duplicate_rows: int = 0
    data_quality_status: str = Field(default="clean", description="'clean' | 'warning' | 'error'")


# ===== STAGE 3: DESCRIPTIVE STATS =====
class DescriptiveStatsResponse(EDAStageBase):
    """Stage 3: statistik deskriptif OHLCV. Tiap field memakai StatBlock yang sama."""

    count_records: int = Field(..., description="Jumlah observasi yang dihitung")
    close: StatBlock | None = None
    open: StatBlock | None = None
    high: StatBlock | None = None
    low: StatBlock | None = None
    volume: StatBlock | None = None


# ===== STAGE 4: TIME SERIES (Close + Volume) =====
class TimeSeriesPoint(BaseModel):
    date: str = Field(..., description="ISO date: YYYY-MM-DD")
    close: float
    volume: float
    is_crash_event: bool = Field(default=False, description="Anotasi crash (COVID 2020, bear 2022)")


class TimeSeriesResponse(EDAStageBase):
    """Stage 4: deret Close + Volume untuk chart utama."""

    data: list[TimeSeriesPoint]


# ===== STAGE 5: DAILY RETURNS DISTRIBUTION =====
class ReturnPoint(BaseModel):
    date: str
    return_pct: float
    year: int = Field(..., description="Untuk grouping annual breakdown")


class AnnualReturn(BaseModel):
    """Statistik return per tahun."""

    year: int
    stats: StatBlock
    count_trading_days: int


class DailyReturnDistributionResponse(EDAStageBase):
    """Stage 5: distribusi daily return — agregat, deret, dan breakdown tahunan."""

    stats: StatBlock = Field(..., description="Stats agregat (satuan %)")
    time_series: list[ReturnPoint]
    annual_breakdown: list[AnnualReturn]


# ===== STAGE 6: MOVING AVERAGES & VOLATILITY =====
class MovingAveragePoint(BaseModel):
    date: str
    close: float
    ma_20: float | None = Field(default=None, description="null untuk 19 baris awal")
    ma_50: float | None = Field(default=None, description="null untuk 49 baris awal")
    ma_200: float | None = Field(default=None, description="null untuk 199 baris awal")
    volatility_30: float | None = Field(default=None, description="rolling vol 30 hari (%) — null 29 baris awal")


class MASnapshot(BaseModel):
    """Nilai MA terkini (untuk metric card)."""

    ma_20: float | None = None
    ma_50: float | None = None
    ma_200: float | None = None


class MovingAverageResponse(EDAStageBase):
    """Stage 6: price + MA(20/50/200) + rolling volatility."""

    data: list[MovingAveragePoint]
    snapshot: MASnapshot | None = Field(default=None, description="Nilai MA pada titik terakhir")


# ===== STAGE 7: OHLC SPREAD ANALYSIS =====
class OHLCSpreadPoint(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    hl_spread: float = Field(..., description="High - Low (intraday range)")
    oc_spread: float = Field(..., description="Close - Open (arah & magnitudo)")
    is_bullish: bool = Field(..., description="True jika Close > Open")


class MonthlySpread(BaseModel):
    month: str
    avg_spread: float


class OHLCSpreadSummary(BaseModel):
    avg_hl_spread: float
    std_hl_spread: float
    total_bullish_days: int
    total_bearish_days: int
    bullish_pct: float
    bearish_pct: float


class OHLCSpreadResponse(EDAStageBase):
    """Stage 7: analisis intraday range & arah (bullish/bearish)."""

    data: list[OHLCSpreadPoint]
    summary: OHLCSpreadSummary
    monthly_avg_spread: list[MonthlySpread] | None = None


# ===== STAGE 8: CORRELATION MATRIX =====
class CorrelationRow(BaseModel):
    """Satu baris matriks korelasi (keyed by feature — wajar berbentuk map)."""

    feature: str
    correlations: dict[str, float] = Field(..., description="{'Open': 1.0, 'High': 0.99, ...}")


class CorrelationPair(BaseModel):
    feature_a: str
    feature_b: str
    value: float


class CorrelationMatrixResponse(EDAStageBase):
    """Stage 8: matriks korelasi untuk heatmap + pasangan korelasi tinggi."""

    features: list[str]
    matrix: list[CorrelationRow]
    high_correlations: list[CorrelationPair] | None = Field(
        default=None, description="Pasangan dengan |korelasi| > threshold"
    )


# ===== STAGE 9: SEASONAL PATTERNS =====
class MonthlyPattern(BaseModel):
    month: str = Field(..., description="'January' ... 'December'")
    month_num: int = Field(..., ge=1, le=12)
    avg_return_pct: float
    count: int = Field(..., description="Jumlah observasi pada bulan ini")
    std_pct: float | None = None


class DayOfWeekPattern(BaseModel):
    day: str = Field(..., description="'Monday' ... 'Friday'")
    day_num: int = Field(..., ge=0, le=6, description="0=Monday ... 4=Friday")
    avg_return_pct: float
    count: int
    std_pct: float | None = None


class SeasonalPatternsResponse(EDAStageBase):
    """Stage 9: pola musiman bulanan & harian. Ekstrem diketik (bukan dict mentah)."""

    by_month: list[MonthlyPattern]
    by_day_of_week: list[DayOfWeekPattern]
    best_month: MonthlyPattern | None = None
    worst_month: MonthlyPattern | None = None
    best_day: DayOfWeekPattern | None = None
    worst_day: DayOfWeekPattern | None = None


# ===== STAGE 10: CUMULATIVE RETURN & DRAWDOWN =====
class DrawdownPoint(BaseModel):
    date: str
    cumulative_return_pct: float = Field(..., description="% return dari titik awal")
    peak_price: float = Field(..., description="Running peak close price")
    drawdown_pct: float = Field(..., description="% turun dari peak (negatif)")


class DrawdownMetrics(BaseModel):
    total_return_pct: float
    max_drawdown_pct: float
    max_drawdown_date: str
    days_to_recovery: int | None = None
    annualized_return_pct: float | None = None
    annualized_volatility_pct: float | None = None


class DrawdownResponse(EDAStageBase):
    """Stage 10: cumulative return & drawdown."""

    data: list[DrawdownPoint]
    metrics: DrawdownMetrics


# ===== STAGE 11: SUMMARY STATS =====
class AnnualPerformance(BaseModel):
    year: int
    open_price: float
    close_price: float
    return_pct: float
    max_drawdown_pct: float
    volatility_annualized_pct: float
    count_trading_days: int


class SummaryStatsResponse(EDAStageBase):
    """Stage 11: ringkasan akhir + breakdown per tahun."""

    overall_return_pct: float
    annualized_return_pct: float | None = None
    annualized_volatility_pct: float
    max_drawdown_pct: float
    total_trading_days: int
    annual_breakdown: list[AnnualPerformance]
    key_insights: list[str] | None = None


# ===== STAGE 12: PROCESSED STOCK DATA =====
class ProcessedStockRecord(BaseModel):
    """Satu baris processed dataset dengan engineered features (siap model/FE)."""

    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    daily_return: float | None = Field(default=None, description="pct_change() — null baris pertama")
    hl_spread: float
    oc_spread: float
    ma_20: float | None = None
    ma_50: float | None = None
    ma_200: float | None = None
    volatility_30: float | None = None


class ProcessedStockDataResponse(EDAStageBase):
    """
    Stage 12: processed dataset lengkap.
    Pagination DITANGANI envelope via `meta.pagination` — bukan field di sini.
    """

    data: list[ProcessedStockRecord]
