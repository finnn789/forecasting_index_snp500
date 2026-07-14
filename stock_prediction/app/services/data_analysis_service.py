"""
app/services/data_analysis_service.py — Business logic untuk routes_data_analysis.py.

Mereplikasi alur analisis di:
  - notebooks/01_EDA_stock_data.ipynb    (saham ^GSPC — EDA + preprocessing)
  - notebooks/02_EDA_sentiment_data.ipynb (headline berita — EDA + FinBERT + agregasi)

Tahap "preprocessing" saham memakai StockPreprocessor produksi (bukan cell
MinMaxScaler eksploratif di notebook). Tahap "preprocessing" sentimen (cleaning
teks) mengikuti metodologi notebook — lihat catatan di masing-masing schema.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from app.core.exceptions import NotFoundError
from app.domain.value_objects import TickerSymbol
from app.helpers.serialization import format_iso_date
from app.repositories.provider import get_repositories
from app.schemas.data_analysis import (
    AnnualReturn,
    ClosingPricePoint,
    ColumnStats,
    CombinedMergeInfo,
    CombinedMergePreviewResponse,
    CombinedPipelineStepsResponse,
    CrashEvent,
    DailySentimentPoint,
    DrawdownPoint,
    Histogram,
    MethodComparisonPoint,
    MonthlySpread,
    NewsPerDayPoint,
    NewsPerYearItem,
    OhlcSpreadPoint,
    PipelineStep,
    PriceVolumePoint,
    ReturnPoint,
    RollingStatPoint,
    SeasonalReturn,
    SentimentClosingPriceResponse,
    SentimentDailyAggregationResponse,
    SentimentHeadlineLengthResponse,
    SentimentMethodComparisonResponse,
    SentimentNewsPerDayResponse,
    SentimentNewsPerYearResponse,
    SentimentPreprocessingResponse,
    SentimentRawInfo,
    SentimentRawPreviewResponse,
    SentimentScoringDistributionResponse,
    StockCorrelationResponse,
    StockCumulativeReturnDrawdownResponse,
    StockDailyReturnsResponse,
    StockDescriptiveStats,
    StockOhlcSpreadResponse,
    StockPreprocessingResponse,
    StockPreprocessingSide,
    StockPriceVolumeResponse,
    StockRawInfo,
    StockRawPreviewResponse,
    StockRollingStatsResponse,
    StockSeasonalityResponse,
    StockSummaryResponse,
    YearlyReturnBox,
)
from pipeline.feature_engineering.dataset_builder import FEATURE_COLS
from pipeline.preprocessing.stock_preprocessor import StockPreprocessor

_TICKER = TickerSymbol(symbol="GSPC")
_MIN_WORDS = 3
_WHITESPACE_RE = re.compile(r"\s+")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _none_if_nan(x) -> float | None:
    return None if pd.isna(x) else round(float(x), 6)


def _histogram(values: pd.Series, bins: int = 40) -> Histogram:
    counts, edges = np.histogram(values.dropna(), bins=bins)
    return Histogram(
        bin_edges=[round(float(e), 6) for e in edges],
        counts=[int(c) for c in counts],
    )


def _clean_headline(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", str(text).strip())


def _preview_rows(df: pd.DataFrame, n: int) -> list[dict]:
    """N baris pertama sebagai list of dict, siap di-serialize JSON.

    Kolom datetime diformat ISO string; NaN/NaT diubah jadi None (JSON null).
    """
    head = df.head(n).copy()
    for col in head.columns:
        if pd.api.types.is_datetime64_any_dtype(head[col]):
            head[col] = head[col].map(format_iso_date)
    head = head.where(pd.notnull(head), None)
    return head.to_dict(orient="records")


def _load_raw_stock() -> pd.DataFrame:
    return get_repositories()["stock"].load_raw(_TICKER)


def _load_raw_news_with_cp() -> pd.DataFrame:
    """Baca headline mentah TERMASUK kolom CP.

    NewsRepository.load_raw_headlines() membuang kolom CP — di sini kita baca
    langsung dari file karena endpoint closing-price butuh kolom itu.
    """
    path = get_repositories()["news"].raw_headlines_path()
    if not path.exists():
        raise NotFoundError(
            f"File headlines mentah tidak ditemukan: {path}",
            code="NEWS_DATA_NOT_FOUND",
        )
    return pd.read_csv(path, parse_dates=["Date"])


def _build_stock_frame() -> pd.DataFrame:
    """Enrichment progresif meniru notebook 01: return, MA, volatility, spread, drawdown."""
    df = _load_raw_stock().copy()
    df = df.sort_values("Date").reset_index(drop=True)
    df["Daily_Return"] = df["Close"].pct_change() * 100
    df["MA_20"] = df["Close"].rolling(20).mean()
    df["MA_50"] = df["Close"].rolling(50).mean()
    df["MA_200"] = df["Close"].rolling(200).mean()
    df["Vol_30"] = df["Daily_Return"].rolling(30).std()
    df["HL_Spread"] = df["High"] - df["Low"]
    df["OC_Spread"] = df["Close"] - df["Open"]
    df["Cum_Return"] = (1 + df["Daily_Return"] / 100).cumprod() - 1
    rolling_max = df["Close"].cummax()
    df["Drawdown"] = (df["Close"] - rolling_max) / rolling_max * 100
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["DayOfWeek"] = df["Date"].dt.day_name()
    return df


# ---------------------------------------------------------------------------
# Stock — notebooks/01_EDA_stock_data.ipynb
# ---------------------------------------------------------------------------

def get_stock_raw_info() -> StockRawInfo:
    df = _load_raw_stock()
    return StockRawInfo(
        total_rows=len(df),
        columns=df.columns.tolist(),
        date_start=format_iso_date(df["Date"].min()),
        date_end=format_iso_date(df["Date"].max()),
        missing_values={c: int(v) for c, v in df.isnull().sum().items()},
        duplicate_dates=int(df.duplicated(subset=["Date"]).sum()),
    )


def get_stock_raw_preview(n: int = 10) -> StockRawPreviewResponse:
    df = _load_raw_stock()
    return StockRawPreviewResponse(
        columns=df.columns.tolist(),
        n=min(n, len(df)),
        rows=_preview_rows(df, n),
    )


def get_stock_descriptive_stats() -> StockDescriptiveStats:
    df = _load_raw_stock()
    columns: dict[str, ColumnStats] = {}
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        s = df[col]
        mean = float(s.mean())
        std = float(s.std())
        columns[col] = ColumnStats(
            count=int(s.count()),
            mean=round(mean, 6),
            std=round(std, 6),
            min=float(s.min()),
            q25=float(s.quantile(0.25)),
            median=float(s.median()),
            q75=float(s.quantile(0.75)),
            max=float(s.max()),
            cv_pct=round(std / mean * 100, 2) if mean else 0.0,
        )
    return StockDescriptiveStats(columns=columns)


def get_stock_price_volume() -> StockPriceVolumeResponse:
    df = _build_stock_frame()
    points = [
        PriceVolumePoint(
            date=format_iso_date(row.Date), close=float(row.Close), volume=int(row.Volume)
        )
        for row in df.itertuples()
    ]
    crash_events = [
        CrashEvent(date="2020-03-23", label="COVID Low"),
        CrashEvent(date="2022-01-03", label="2022 Bear Market"),
    ]
    return StockPriceVolumeResponse(points=points, crash_events=crash_events)


def get_stock_daily_returns() -> StockDailyReturnsResponse:
    df = _build_stock_frame()
    valid = df.dropna(subset=["Daily_Return"])
    ret = valid["Daily_Return"]

    points = [
        ReturnPoint(date=format_iso_date(row.Date), return_pct=round(float(row.Daily_Return), 6))
        for row in valid.itertuples()
    ]

    max_gain_idx = ret.idxmax()
    max_loss_idx = ret.idxmin()

    yearly: list[YearlyReturnBox] = []
    for year, group in valid.groupby("Year"):
        s = group["Daily_Return"]
        yearly.append(
            YearlyReturnBox(
                year=int(year),
                min=float(s.min()),
                q1=float(s.quantile(0.25)),
                median=float(s.median()),
                q3=float(s.quantile(0.75)),
                max=float(s.max()),
            )
        )

    return StockDailyReturnsResponse(
        points=points,
        mean=round(float(ret.mean()), 6),
        std=round(float(ret.std()), 6),
        skewness=round(float(ret.skew()), 6),
        kurtosis=round(float(ret.kurt()), 6),
        max_gain_date=format_iso_date(df.loc[max_gain_idx, "Date"]),
        max_gain_pct=round(float(df.loc[max_gain_idx, "Daily_Return"]), 6),
        max_loss_date=format_iso_date(df.loc[max_loss_idx, "Date"]),
        max_loss_pct=round(float(df.loc[max_loss_idx, "Daily_Return"]), 6),
        histogram=_histogram(ret),
        yearly_boxplot=yearly,
    )


def get_stock_rolling_stats() -> StockRollingStatsResponse:
    df = _build_stock_frame()
    points = [
        RollingStatPoint(
            date=format_iso_date(row.Date),
            close=float(row.Close),
            ma_20=_none_if_nan(row.MA_20),
            ma_50=_none_if_nan(row.MA_50),
            ma_200=_none_if_nan(row.MA_200),
            volatility_30=_none_if_nan(row.Vol_30),
        )
        for row in df.itertuples()
    ]
    return StockRollingStatsResponse(points=points)


def get_stock_ohlc_spread() -> StockOhlcSpreadResponse:
    df = _build_stock_frame()
    points = [
        OhlcSpreadPoint(
            date=format_iso_date(row.Date),
            hl_spread=round(float(row.HL_Spread), 6),
            oc_spread=round(float(row.OC_Spread), 6),
        )
        for row in df.itertuples()
    ]

    monthly = df.groupby(df["Date"].dt.to_period("M"))["HL_Spread"].mean()
    monthly_spread = [
        MonthlySpread(month=str(period), avg_hl_spread=round(float(v), 6))
        for period, v in monthly.items()
    ]

    bullish = int((df["OC_Spread"] > 0).sum())
    bearish = int((df["OC_Spread"] <= 0).sum())
    total = bullish + bearish

    return StockOhlcSpreadResponse(
        points=points,
        monthly_avg_hl_spread=monthly_spread,
        bullish_days=bullish,
        bearish_days=bearish,
        bullish_pct=round(bullish / total * 100, 2) if total else 0.0,
        bearish_pct=round(bearish / total * 100, 2) if total else 0.0,
    )


def get_stock_correlation() -> StockCorrelationResponse:
    df = _build_stock_frame()
    cols = ["Open", "High", "Low", "Close", "Volume", "Daily_Return", "HL_Spread"]
    corr = df[cols].corr()
    matrix = [[round(float(v), 6) for v in row] for row in corr.values]
    return StockCorrelationResponse(columns=cols, matrix=matrix)


def get_stock_seasonality() -> StockSeasonalityResponse:
    df = _build_stock_frame()
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_ret = df.groupby("Month")["Daily_Return"].mean()
    monthly = [
        SeasonalReturn(label=month_names[m - 1], avg_return_pct=round(float(monthly_ret[m]), 6))
        for m in monthly_ret.index
    ]

    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    weekday_ret = df.groupby("DayOfWeek")["Daily_Return"].mean()
    weekday = [
        SeasonalReturn(label=d, avg_return_pct=round(float(weekday_ret[d]), 6))
        for d in weekday_order if d in weekday_ret.index
    ]

    return StockSeasonalityResponse(monthly=monthly, weekday=weekday)


def get_stock_cumulative_return_drawdown() -> StockCumulativeReturnDrawdownResponse:
    df = _build_stock_frame()
    points = [
        DrawdownPoint(
            date=format_iso_date(row.Date),
            cum_return_pct=round(float(row.Cum_Return) * 100, 6),
            drawdown_pct=round(float(row.Drawdown), 6),
        )
        for row in df.itertuples()
    ]
    total_return = float(df["Cum_Return"].iloc[-1]) * 100
    max_dd = float(df["Drawdown"].min())
    return StockCumulativeReturnDrawdownResponse(
        points=points,
        total_return_pct=round(total_return, 6),
        max_drawdown_pct=round(max_dd, 6),
    )


def get_stock_summary() -> StockSummaryResponse:
    df = _build_stock_frame()
    ret = df["Daily_Return"]

    total_return = float(df["Cum_Return"].iloc[-1]) * 100
    max_dd = float(df["Drawdown"].min())

    bullish = int((df["OC_Spread"] > 0).sum())
    bearish = int((df["OC_Spread"] <= 0).sum())
    total_days = bullish + bearish

    annual_ret = df.groupby("Year")["Daily_Return"].apply(lambda x: (1 + x / 100).prod() - 1) * 100
    annual_returns = [
        AnnualReturn(year=int(y), return_pct=round(float(r), 6)) for y, r in annual_ret.items()
    ]

    return StockSummaryResponse(
        total_trading_days=len(df),
        start_price=float(df["Close"].iloc[0]),
        end_price=float(df["Close"].iloc[-1]),
        cumulative_return_pct=round(total_return, 6),
        max_drawdown_pct=round(max_dd, 6),
        mean_daily_return_pct=round(float(ret.mean()), 6),
        annualized_volatility_pct=round(float(ret.std() * (252 ** 0.5)), 6),
        skewness=round(float(ret.skew()), 6),
        kurtosis=round(float(ret.kurt()), 6),
        bullish_days=bullish,
        bearish_days=bearish,
        bullish_pct=round(bullish / total_days * 100, 2) if total_days else 0.0,
        bearish_pct=round(bearish / total_days * 100, 2) if total_days else 0.0,
        annual_returns=annual_returns,
    )


def get_stock_preprocessing() -> StockPreprocessingResponse:
    df_raw = _load_raw_stock()
    df_clean = StockPreprocessor().clean(df_raw.copy())

    raw_dup_dates = int(df_raw.duplicated(subset=["Date"]).sum())
    raw_side = StockPreprocessingSide(
        total_rows=len(df_raw),
        columns=df_raw.columns.tolist(),
        missing_values={c: int(v) for c, v in df_raw.isnull().sum().items()},
        duplicate_dates=raw_dup_dates,
    )
    clean_side = StockPreprocessingSide(
        total_rows=len(df_clean),
        columns=df_clean.columns.tolist(),
        missing_values={c: int(v) for c, v in df_clean.isnull().sum().items()},
        duplicate_dates=int(df_clean.duplicated(subset=["Date"]).sum()),
    )
    columns_dropped = [c for c in df_raw.columns if c not in df_clean.columns]
    invalid_rows_dropped = max(0, (len(df_raw) - len(df_clean)) - raw_dup_dates)

    return StockPreprocessingResponse(
        raw=raw_side,
        clean=clean_side,
        columns_dropped=columns_dropped,
        invalid_rows_dropped=invalid_rows_dropped,
    )


# ---------------------------------------------------------------------------
# Sentiment — notebooks/02_EDA_sentiment_data.ipynb
# ---------------------------------------------------------------------------

def get_sentiment_raw_info() -> SentimentRawInfo:
    df = _load_raw_news_with_cp()
    return SentimentRawInfo(
        total_rows=len(df),
        columns=df.columns.tolist(),
        date_start=format_iso_date(df["Date"].min()),
        date_end=format_iso_date(df["Date"].max()),
        missing_values={c: int(v) for c, v in df.isnull().sum().items()},
        duplicate_rows=int(df.duplicated().sum()),
        duplicate_titles=int(df["Title"].duplicated().sum()),
        duplicate_title_date=int(df.duplicated(subset=["Title", "Date"]).sum()),
    )


def get_sentiment_raw_preview(n: int = 10) -> SentimentRawPreviewResponse:
    df = _load_raw_news_with_cp()
    return SentimentRawPreviewResponse(
        columns=df.columns.tolist(),
        n=min(n, len(df)),
        rows=_preview_rows(df, n),
    )


def get_news_per_year() -> SentimentNewsPerYearResponse:
    df = _load_raw_news_with_cp()
    year_counts = df.groupby(df["Date"].dt.year).size()
    data = [NewsPerYearItem(year=int(y), count=int(c)) for y, c in year_counts.items()]
    return SentimentNewsPerYearResponse(data=data, total=int(year_counts.sum()))


def get_news_per_day() -> SentimentNewsPerDayResponse:
    df = _load_raw_news_with_cp()
    per_day = df.groupby("Date").size()
    rolling_30 = per_day.rolling(30).mean()

    points = [
        NewsPerDayPoint(
            date=format_iso_date(d), count=int(c), rolling_30=_none_if_nan(rolling_30[d])
        )
        for d, c in per_day.items()
    ]

    return SentimentNewsPerDayResponse(
        points=points,
        mean=round(float(per_day.mean()), 4),
        median=float(per_day.median()),
        max_count=int(per_day.max()),
        max_date=format_iso_date(per_day.idxmax()),
        min_count=int(per_day.min()),
        min_date=format_iso_date(per_day.idxmin()),
    )


def get_headline_length() -> SentimentHeadlineLengthResponse:
    df = _load_raw_news_with_cp()
    char_len = df["Title"].str.len()
    word_len = df["Title"].str.split().str.len()

    return SentimentHeadlineLengthResponse(
        char_mean=round(float(char_len.mean()), 4),
        char_std=round(float(char_len.std()), 4),
        char_min=float(char_len.min()),
        char_max=float(char_len.max()),
        char_histogram=_histogram(char_len, bins=50),
        word_mean=round(float(word_len.mean()), 4),
        word_std=round(float(word_len.std()), 4),
        word_min=float(word_len.min()),
        word_max=float(word_len.max()),
        word_histogram=_histogram(word_len, bins=30),
    )


def get_sentiment_closing_price() -> SentimentClosingPriceResponse:
    df = _load_raw_news_with_cp()
    cp_daily = df.groupby("Date")["CP"].first()
    points = [
        ClosingPricePoint(date=format_iso_date(d), close=round(float(v), 6))
        for d, v in cp_daily.items()
    ]
    return SentimentClosingPriceResponse(points=points)


def get_sentiment_preprocessing() -> SentimentPreprocessingResponse:
    df = _load_raw_news_with_cp()
    raw_total = len(df)

    work = df[["Date", "Title"]].copy()
    work["Title"] = work["Title"].map(_clean_headline)
    work = work.dropna(subset=["Title"])
    work = work[work["Title"].str.len() > 0]

    before_dedup = len(work)
    work = work.drop_duplicates(subset=["Title", "Date"])
    dropped_duplicates = before_dedup - len(work)

    mask_short = work["Title"].str.split().str.len() < _MIN_WORDS
    dropped_short = int(mask_short.sum())
    work = work[~mask_short]

    return SentimentPreprocessingResponse(
        raw_total=raw_total,
        after_cleaning_total=len(work),
        dropped_duplicates=int(dropped_duplicates),
        dropped_short_headlines=dropped_short,
        min_words=_MIN_WORDS,
    )


def get_scoring_distribution() -> SentimentScoringDistributionResponse:
    df = get_repositories()["news"].load_clean_headlines()
    label_counts = df["sentiment_label"].value_counts()
    label_pct = df["sentiment_label"].value_counts(normalize=True) * 100

    return SentimentScoringDistributionResponse(
        total_headlines=len(df),
        label_counts={k: int(v) for k, v in label_counts.items()},
        label_pct={k: round(float(v), 2) for k, v in label_pct.items()},
        score_mean=round(float(df["sentiment_score"].mean()), 6),
        score_std=round(float(df["sentiment_score"].std()), 6),
        score_histogram=_histogram(df["sentiment_score"], bins=40),
    )


def get_daily_aggregation() -> SentimentDailyAggregationResponse:
    df = get_repositories()["news"].load_clean_headlines().copy()
    df["signed"] = df["sentiment_numeric"] * df["sentiment_score"]

    daily = df.groupby("Date")["signed"].mean().rename("sentiment_mean").reset_index()
    daily = daily.sort_values("Date").reset_index(drop=True)
    rolling_30 = daily.set_index("Date")["sentiment_mean"].rolling(30).mean()

    neutral_band = 0.05

    def _label(x: float) -> str:
        if x > neutral_band:
            return "positive"
        if x < -neutral_band:
            return "negative"
        return "neutral"

    daily["sentiment_label"] = daily["sentiment_mean"].map(_label)

    points = [
        DailySentimentPoint(
            date=format_iso_date(row.Date),
            sentiment_mean=round(float(row.sentiment_mean), 6),
            rolling_30=_none_if_nan(rolling_30[row.Date]),
        )
        for row in daily.itertuples()
    ]
    label_counts = daily["sentiment_label"].value_counts()

    return SentimentDailyAggregationResponse(
        points=points,
        histogram=_histogram(daily["sentiment_mean"], bins=50),
        label_counts={k: int(v) for k, v in label_counts.items()},
    )


def get_method_comparison() -> SentimentMethodComparisonResponse:
    df = get_repositories()["news"].load_clean_headlines().copy()
    df["signed"] = df["sentiment_numeric"] * df["sentiment_score"]

    weighted = df.groupby("Date")["signed"].mean()
    unweighted = df.groupby("Date")["sentiment_numeric"].mean()
    merged = pd.DataFrame({"weighted": weighted, "unweighted": unweighted}).dropna().reset_index()

    points = [
        MethodComparisonPoint(
            date=format_iso_date(row.Date),
            weighted=round(float(row.weighted), 6),
            unweighted=round(float(row.unweighted), 6),
        )
        for row in merged.itertuples()
    ]
    correlation = float(merged["weighted"].corr(merged["unweighted"])) if len(merged) > 1 else 0.0

    return SentimentMethodComparisonResponse(points=points, correlation=round(correlation, 6))


# ---------------------------------------------------------------------------
# Combined — OHLCV + sentiment_mean (mirrors dataset_builder.py::load_joined())
# ---------------------------------------------------------------------------

_OHLCV_COLS = ["Open", "High", "Low", "Close", "Volume"]
_WINDOW = 20
_TRAIN_END = "2022-12-31"
_VAL_END = "2023-12-31"


def _build_combined_frame() -> pd.DataFrame:
    """OHLCV (cleaned) inner-join sentiment_mean harian — replika logic
    pipeline/feature_engineering/dataset_builder.py::load_joined(), yang
    dipakai langsung oleh prediction_service.py untuk training & inference.
    """
    df_stock = StockPreprocessor().clean(_load_raw_stock().copy())
    df_sent = get_repositories()["sentiment"].load_daily_sentiment()

    df = pd.merge(
        df_stock[["Date"] + _OHLCV_COLS],
        df_sent[["Date", "sentiment_mean"]],
        on="Date",
        how="inner",
    )
    return df.sort_values("Date").reset_index(drop=True)


def get_combined_merge_info() -> CombinedMergeInfo:
    df_stock = StockPreprocessor().clean(_load_raw_stock().copy())
    df_sent = get_repositories()["sentiment"].load_daily_sentiment()
    df_merged = _build_combined_frame()

    rows_stock = len(df_stock)
    rows_merged = len(df_merged)

    return CombinedMergeInfo(
        rows_stock=rows_stock,
        rows_sentiment=len(df_sent),
        rows_merged=rows_merged,
        dropped_no_sentiment_match=rows_stock - rows_merged,
        coverage_pct=round(rows_merged / rows_stock * 100, 2) if rows_stock else 0.0,
        date_start=format_iso_date(df_merged["Date"].min()),
        date_end=format_iso_date(df_merged["Date"].max()),
        columns=df_merged.columns.tolist(),
    )


def get_combined_merge_preview(n: int = 10) -> CombinedMergePreviewResponse:
    df = _build_combined_frame()
    return CombinedMergePreviewResponse(
        columns=df.columns.tolist(),
        n=min(n, len(df)),
        rows=_preview_rows(df, n),
    )


def _split_range_detail(d: pd.DataFrame) -> dict:
    if len(d) == 0:
        return {"rows": 0, "range": ""}
    return {
        "rows": len(d),
        "range": f"{format_iso_date(d['Date'].min())} – {format_iso_date(d['Date'].max())}",
    }


def get_combined_pipeline_steps() -> CombinedPipelineStepsResponse:
    """Mirror ringan dataset_builder.py::build_dataset() (window=20, split default).

    HANYA pandas + sklearn MinMaxScaler — tanpa torch, tanpa windowing array
    sungguhan (langkah 7 hanya menghitung jumlah sampel per split).
    """
    steps: list[PipelineStep] = []

    # 1. Load & Clean OHLCV
    df_raw = _load_raw_stock()
    df_clean = StockPreprocessor().clean(df_raw.copy())
    columns_dropped = [c for c in df_raw.columns if c not in df_clean.columns]
    steps.append(PipelineStep(
        order=1,
        name="Load & Clean OHLCV",
        description="StockPreprocessor.clean(): drop kolom non-fitur, validasi, dedup, isi NaN",
        rows_in=len(df_raw),
        rows_out=len(df_clean),
        detail={"columns_dropped": columns_dropped},
    ))

    # 2. Load Sentimen Harian
    df_sent = get_repositories()["sentiment"].load_daily_sentiment()
    steps.append(PipelineStep(
        order=2,
        name="Load Sentimen Harian",
        description="headlines_daily_sentiment.csv — sentiment_mean per tanggal",
        rows_in=None,
        rows_out=len(df_sent),
        detail={
            "date_start": format_iso_date(df_sent["Date"].min()),
            "date_end": format_iso_date(df_sent["Date"].max()),
        },
    ))

    # 3. Inner Join on Date
    df_merged = _build_combined_frame()
    rows_clean = len(df_clean)
    rows_merged = len(df_merged)
    steps.append(PipelineStep(
        order=3,
        name="Inner Join on Date",
        description="Gabung OHLCV bersih + sentiment_mean; hari trading tanpa berita terbuang",
        rows_in=rows_clean,
        rows_out=rows_merged,
        detail={
            "coverage_pct": round(rows_merged / rows_clean * 100, 2) if rows_clean else 0.0,
            "dropped_no_sentiment_match": rows_clean - rows_merged,
        },
    ))

    # 4. Labeling
    df_labeled = df_merged.copy()
    df_labeled["label"] = (df_labeled["Close"].shift(-1) > df_labeled["Close"]).astype("float32")
    df_labeled = df_labeled.iloc[:-1].reset_index(drop=True)
    label_up_pct = round(float(df_labeled["label"].mean()) * 100, 2) if len(df_labeled) else 0.0
    steps.append(PipelineStep(
        order=4,
        name="Labeling",
        description="y = 1 jika Close[t+1] > Close[t]; baris terakhir dibuang (label NaN)",
        rows_in=rows_merged,
        rows_out=len(df_labeled),
        detail={
            "label_up_pct": label_up_pct,
            "label_down_pct": round(100 - label_up_pct, 2),
        },
    ))

    # 5. Split by Date (SEBELUM scaling)
    train_end_ts = pd.Timestamp(_TRAIN_END)
    val_end_ts = pd.Timestamp(_VAL_END)

    mask_train = df_labeled["Date"] <= train_end_ts
    mask_val = (df_labeled["Date"] > train_end_ts) & (df_labeled["Date"] <= val_end_ts)
    mask_test = df_labeled["Date"] > val_end_ts

    df_train = df_labeled[mask_train].reset_index(drop=True)
    df_val = df_labeled[mask_val].reset_index(drop=True)
    df_test = df_labeled[mask_test].reset_index(drop=True)

    n_labeled = len(df_labeled)
    steps.append(PipelineStep(
        order=5,
        name="Split by Date",
        description="train ≤ 2022-12-31 < val ≤ 2023-12-31 < test — split SEBELUM scaling",
        rows_in=n_labeled,
        rows_out=n_labeled,
        detail={
            "train": _split_range_detail(df_train),
            "val": _split_range_detail(df_val),
            "test": _split_range_detail(df_test),
        },
    ))

    # 6. MinMaxScaler (fit train-only, anti-leakage)
    scaler = MinMaxScaler()
    if len(df_train):
        scaler.fit(df_train[FEATURE_COLS].values.astype(np.float64))
        train_min = {c: round(float(v), 4) for c, v in zip(FEATURE_COLS, scaler.data_min_)}
        train_max = {c: round(float(v), 4) for c, v in zip(FEATURE_COLS, scaler.data_max_)}
    else:
        train_min = {}
        train_max = {}
    steps.append(PipelineStep(
        order=6,
        name="MinMaxScaler (fit train-only)",
        description="Anti-leakage: fit HANYA di train, transform ke semua split",
        rows_in=None,
        rows_out=None,
        detail={
            "feature_cols": FEATURE_COLS,
            "train_min": train_min,
            "train_max": train_max,
        },
    ))

    # 7. Windowing per-split (tanpa membangun array sungguhan)
    samples_train = max(0, len(df_train) - _WINDOW + 1)
    samples_val = max(0, len(df_val) - _WINDOW + 1)
    samples_test = max(0, len(df_test) - _WINDOW + 1)
    steps.append(PipelineStep(
        order=7,
        name="Windowing (W=20)",
        description="Sliding window per-split, tidak melintasi batas split; X[i] = fitur[i:i+20]",
        rows_in=None,
        rows_out=None,
        detail={
            "samples_train": samples_train,
            "samples_val": samples_val,
            "samples_test": samples_test,
            "shape": f"(N, {_WINDOW}, {len(FEATURE_COLS)})",
        },
    ))

    return CombinedPipelineStepsResponse(
        steps=steps,
        window=_WINDOW,
        feature_cols=FEATURE_COLS,
    )
