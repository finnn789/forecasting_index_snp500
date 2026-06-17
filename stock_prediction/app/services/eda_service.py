"""app/services/eda_service.py — Business logic untuk 5 endpoint EDA dataset berita."""

from __future__ import annotations

import logging
import math
from datetime import date

from app.domain.value_objects import TickerSymbol
from app.repositories.provider import get_repositories
from app.schemas.sentiment import (
    DatasetSummary,
    HeadlineLengthStats,
    NewsPerDayStats,
    NewsPerYearItem,
    NewsPerYearResponse,
    ProcessedDataInfo,
    ProcessedFileInfo,
    RawStocksResponse,
    SentimentDistributionItem,
    SentimentDistributionResponse,
)
from app.schemas.stocks import (
    AnnualPerformance,
    AnnualReturn,
    DataInfoResponse,
    DescriptiveStatsResponse,
    DailyReturnDistributionResponse,
    DrawdownMetrics,
    DrawdownPoint,
    DrawdownResponse,
    ReturnPoint,
    StatBlock,
    SummaryStatsResponse,
    TimeSeriesPoint,
    TimeSeriesResponse,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


def get_dataset_summary() -> DatasetSummary:
    """Hitung statistik dasar dataset headlines bersih."""
    logger.info("[EDA] Memuat ringkasan dataset...")

    df = get_repositories()["news"].load_clean_headlines()
    logger.info("[EDA] Dataset dimuat — %d baris", len(df))
    summary = DatasetSummary(
        total_rows=len(df),
        date_start=str(df["Date"].min().date()),
        date_end=str(df["Date"].max().date()),
        span_days=int((df["Date"].max() - df["Date"].min()).days),
        # missing_title=int(df["title_clean"].isnull().sum()),
        # missing_cp=int(df["CP"].isnull().sum()),
        dtypes={col: str(dtype) for col, dtype in df.dtypes.items()},
    )

    logger.info(
        "[EDA] Ringkasan selesai — %d baris, rentang %s s/d %s",
        summary.total_rows,
        summary.date_start,
        summary.date_end,
    )
    return summary


def get_news_per_year() -> NewsPerYearResponse:
    """Hitung jumlah headline berita per tahun."""
    logger.info("[EDA] Menghitung distribusi berita per tahun...")

    df = get_repositories()["news"].load_clean_headlines()
    df["Year"] = df["Date"].dt.year
    counts = df.groupby("Year").size().reset_index(name="count")

    items = [
        NewsPerYearItem(year=int(r["Year"]), count=int(r["count"]))
        for _, r in counts.iterrows()
    ]
    logger.info("[EDA] Distribusi per tahun selesai — %d tahun", len(items))

    return NewsPerYearResponse(data=items, total=len(df))


def get_news_per_day() -> NewsPerDayStats:
    """Hitung statistik agregasi jumlah headline per hari."""
    logger.info("[EDA] Menghitung statistik berita per hari...")

    df = get_repositories()["news"].load_clean_headlines()
    per_day = df.groupby("Date").size()

    stats = NewsPerDayStats(
        mean=round(float(per_day.mean()), 2),
        max=int(per_day.max()),
        max_date=str(per_day.idxmax().date()),
        min=int(per_day.min()),
        min_date=str(per_day.idxmin().date()),
    )

    logger.info(
        "[EDA] Statistik per hari selesai — mean=%.2f, max=%d, min=%d",
        stats.mean,
        stats.max,
        stats.min,
    )
    return stats


def get_headline_length() -> HeadlineLengthStats:
    """Hitung statistik panjang headline dalam karakter dan kata."""
    logger.info("[EDA] Menghitung distribusi panjang headline...")

    df = get_repositories()["news"].load_clean_headlines()
    df["len_char"] = df["Title"].str.len()
    df["len_word"] = df["Title"].str.split().str.len()

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

    logger.info(
        "[EDA] Panjang headline — char mean=%.2f, word mean=%.2f",
        stats.char_mean,
        stats.word_mean,
    )
    return stats


def get_sentiment_distribution() -> SentimentDistributionResponse:
    """Hitung distribusi label sentimen dan statistik sentiment_score."""
    logger.info("[EDA] Menghitung distribusi label sentimen...")

    df = get_repositories()["news"].load_clean_headlines()
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

    logger.info(
        "[EDA] Distribusi sentimen — %s",
        {i.label: i.count for i in items},
    )
    return result

def get_stocks_overview() -> DataInfoResponse:
    """Hitung ikhtisar data saham: jumlah baris, rentang tanggal, dan statistik dasar harga."""
    logger.info("[EDA] Menghitung ikhtisar data saham...")

    df = get_repositories()["stock"].load_processed(ticker=TickerSymbol(symbol="GSPC"))
    logger.info("[EDA] Data saham dimuat — %d baris", len(df))

    date_start = df["Date"].min().date()
    date_end = df["Date"].max().date()
    overview = {
        "period": f"{date_start} - {date_end}",
        "ticker": str(TickerSymbol(symbol="GSPC")),
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "date_range": f"{date_start} to {date_end}",
        "columns": df.columns.tolist(),
        "missing_values": df.isnull().sum().to_dict(),
        "duplicate_rows": int(df.duplicated().sum()),
        "data_quality_status": "clean" if df.isnull().sum().sum() == 0 else "warning",
    }

    logger.info(
        "[EDA] Ikhtisar data saham selesai — %d baris, rentang %s s/d %s",
        overview["total_rows"],
        date_start,
        date_end,
    )
    return DataInfoResponse(**overview)


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _nan_to_none(v: float) -> float | None:
    """Konversi NaN/Inf ke None agar kompatibel dengan Pydantic."""
    if v is None:
        return None
    try:
        if math.isnan(v) or math.isinf(v):
            return None
    except TypeError:
        return None
    return v


def _stat_block(series) -> StatBlock:
    """Buat StatBlock dari sebuah pandas Series (angka)."""
    s = series.dropna()
    mean_val = float(s.mean())
    std_val = float(s.std())

    cv: float | None = None
    if mean_val != 0 and not math.isnan(mean_val) and not math.isnan(std_val):
        cv = std_val / mean_val * 100

    return StatBlock(
        min=float(s.min()),
        max=float(s.max()),
        mean=mean_val,
        std=std_val,
        median=_nan_to_none(float(s.median())),
        cv_pct=_nan_to_none(cv),
        skew=_nan_to_none(float(s.skew())),
        kurtosis=_nan_to_none(float(s.kurtosis())),
        q25=_nan_to_none(float(s.quantile(0.25))),
        q75=_nan_to_none(float(s.quantile(0.75))),
    )


# Window crash events (inklusif)
_CRASH_WINDOWS = [
    (date(2020, 2, 20), date(2020, 4, 7)),   # COVID crash
    (date(2022, 1, 3),  date(2022, 10, 12)), # Bear market 2022
]


def _is_crash(d: date) -> bool:
    """Kembalikan True jika tanggal d berada dalam salah satu window crash."""
    for start, end in _CRASH_WINDOWS:
        if start <= d <= end:
            return True
    return False


# ---------------------------------------------------------------------------
# Stage 3: Descriptive Stats
# ---------------------------------------------------------------------------

def get_stocks_descriptive_stats() -> DescriptiveStatsResponse:
    """Hitung statistik deskriptif OHLCV data saham GSPC."""
    logger.info("[EDA] Menghitung statistik deskriptif saham (Stage 3)...")

    df = get_repositories()["stock"].load_processed(ticker=TickerSymbol(symbol="GSPC"))
    logger.info("[EDA] Data saham dimuat — %d baris", len(df))

    period = f"{df['Date'].min().year}-{df['Date'].max().year}"

    result = DescriptiveStatsResponse(
        ticker="GSPC",
        period=period,
        count_records=len(df),
        close=_stat_block(df["Close"]),
        open=_stat_block(df["Open"]),
        high=_stat_block(df["High"]),
        low=_stat_block(df["Low"]),
        volume=_stat_block(df["Volume"]),
    )

    logger.info(
        "[EDA] Statistik deskriptif selesai — Close mean=%.2f, Volume mean=%.0f",
        result.close.mean if result.close else 0,
        result.volume.mean if result.volume else 0,
    )
    return result


# ---------------------------------------------------------------------------
# Stage 4: Time Series
# ---------------------------------------------------------------------------

def get_stocks_time_series() -> TimeSeriesResponse:
    """Bangun deret waktu Close + Volume dengan anotasi crash event."""
    logger.info("[EDA] Membangun deret waktu saham (Stage 4)...")

    df = get_repositories()["stock"].load_processed(ticker=TickerSymbol(symbol="GSPC"))
    logger.info("[EDA] Data saham dimuat — %d baris", len(df))

    period = f"{df['Date'].min().year}-{df['Date'].max().year}"

    points: list[TimeSeriesPoint] = []
    for _, row in df.iterrows():
        d = row["Date"].date()
        points.append(
            TimeSeriesPoint(
                date=row["Date"].strftime("%Y-%m-%d"),
                close=float(row["Close"]),
                volume=float(row["Volume"]),
                is_crash_event=_is_crash(d),
            )
        )

    logger.info("[EDA] Deret waktu selesai — %d titik data", len(points))
    return TimeSeriesResponse(ticker="GSPC", period=period, data=points)


# ---------------------------------------------------------------------------
# Stage 5: Daily Returns Distribution
# ---------------------------------------------------------------------------

def get_stocks_daily_returns() -> DailyReturnDistributionResponse:
    """Hitung distribusi daily return saham GSPC beserta breakdown tahunan."""
    logger.info("[EDA] Menghitung distribusi daily return (Stage 5)...")

    df = get_repositories()["stock"].load_processed(ticker=TickerSymbol(symbol="GSPC"))
    logger.info("[EDA] Data saham dimuat — %d baris", len(df))

    period = f"{df['Date'].min().year}-{df['Date'].max().year}"

    # Agregat stats keseluruhan (hanya baris yang tidak NaN)
    r = df["Daily_Return"].dropna()
    overall_stats = _stat_block(r)

    # Time series — skip baris dengan Daily_Return NaN
    df_valid = df.dropna(subset=["Daily_Return"]).copy()
    time_series: list[ReturnPoint] = [
        ReturnPoint(
            date=row["Date"].strftime("%Y-%m-%d"),
            return_pct=float(row["Daily_Return"]),
            year=int(row["Date"].year),
        )
        for _, row in df_valid.iterrows()
    ]

    # Breakdown tahunan
    annual_breakdown: list[AnnualReturn] = []
    for year, grp in df_valid.groupby(df_valid["Date"].dt.year):
        annual_breakdown.append(
            AnnualReturn(
                year=int(year),
                stats=_stat_block(grp["Daily_Return"]),
                count_trading_days=len(grp),
            )
        )

    logger.info(
        "[EDA] Distribusi return selesai — mean=%.4f%%, std=%.4f%%, %d tahun",
        overall_stats.mean,
        overall_stats.std,
        len(annual_breakdown),
    )
    return DailyReturnDistributionResponse(
        ticker="GSPC",
        period=period,
        stats=overall_stats,
        time_series=time_series,
        annual_breakdown=annual_breakdown,
    )


# ---------------------------------------------------------------------------
# Stage 10: Drawdown
# ---------------------------------------------------------------------------

def get_stocks_drawdown() -> DrawdownResponse:
    """Hitung cumulative return dan drawdown saham GSPC."""
    logger.info("[EDA] Menghitung drawdown saham (Stage 10)...")

    df = get_repositories()["stock"].load_processed(ticker=TickerSymbol(symbol="GSPC"))
    logger.info("[EDA] Data saham dimuat — %d baris", len(df))

    period = f"{df['Date'].min().year}-{df['Date'].max().year}"

    close = df["Close"]
    peak = close.cummax()
    cum_return_pct = (close / close.iloc[0] - 1) * 100
    drawdown_pct = (close / peak - 1) * 100

    data: list[DrawdownPoint] = [
        DrawdownPoint(
            date=row["Date"].strftime("%Y-%m-%d"),
            cumulative_return_pct=float(cum_return_pct.iloc[i]),
            peak_price=float(peak.iloc[i]),
            drawdown_pct=float(drawdown_pct.iloc[i]),
        )
        for i, (_, row) in enumerate(df.iterrows())
    ]

    # Hitung metrik
    max_dd_idx = int(drawdown_pct.idxmin())
    max_dd_date = df.loc[max_dd_idx, "Date"].strftime("%Y-%m-%d")

    n = len(df)
    annualized_return = ((close.iloc[-1] / close.iloc[0]) ** (252 / n) - 1) * 100
    annualized_vol = float(df["Daily_Return"].dropna().std() * (252 ** 0.5))

    metrics = DrawdownMetrics(
        total_return_pct=float(cum_return_pct.iloc[-1]),
        max_drawdown_pct=float(drawdown_pct.min()),
        max_drawdown_date=max_dd_date,
        days_to_recovery=None,
        annualized_return_pct=float(annualized_return),
        annualized_volatility_pct=annualized_vol,
    )

    logger.info(
        "[EDA] Drawdown selesai — total return=%.2f%%, max drawdown=%.2f%%",
        metrics.total_return_pct,
        metrics.max_drawdown_pct,
    )
    return DrawdownResponse(ticker="GSPC", period=period, data=data, metrics=metrics)


# ---------------------------------------------------------------------------
# Stage 11: Summary Stats
# ---------------------------------------------------------------------------

def get_stocks_summary() -> SummaryStatsResponse:
    """Buat ringkasan performa saham GSPC beserta breakdown tahunan dan key insights."""
    logger.info("[EDA] Membuat ringkasan statistik saham (Stage 11)...")

    df = get_repositories()["stock"].load_processed(ticker=TickerSymbol(symbol="GSPC"))
    logger.info("[EDA] Data saham dimuat — %d baris", len(df))

    period = f"{df['Date'].min().year}-{df['Date'].max().year}"

    close = df["Close"]
    n = len(df)

    overall_return_pct = float((close.iloc[-1] / close.iloc[0] - 1) * 100)
    annualized_return_pct = float(((close.iloc[-1] / close.iloc[0]) ** (252 / n) - 1) * 100)
    annualized_volatility_pct = float(df["Daily_Return"].dropna().std() * (252 ** 0.5))

    # Max drawdown global
    peak_global = close.cummax()
    drawdown_global = (close / peak_global - 1) * 100
    max_drawdown_pct = float(drawdown_global.min())

    # Breakdown tahunan
    annual_breakdown: list[AnnualPerformance] = []
    for year, grp in df.groupby(df["Date"].dt.year):
        grp = grp.reset_index(drop=True)
        open_price = float(grp["Open"].iloc[0])
        close_price = float(grp["Close"].iloc[-1])
        ret_pct = float((close_price - open_price) / open_price * 100)

        # Max drawdown dalam tahun (peak relatif tahun itu)
        yr_close = grp["Close"]
        yr_peak = yr_close.cummax()
        yr_dd = (yr_close / yr_peak - 1) * 100
        yr_max_dd = float(yr_dd.min())

        yr_vol = float(grp["Daily_Return"].dropna().std() * (252 ** 0.5))

        annual_breakdown.append(
            AnnualPerformance(
                year=int(year),
                open_price=open_price,
                close_price=close_price,
                return_pct=ret_pct,
                max_drawdown_pct=yr_max_dd,
                volatility_annualized_pct=yr_vol,
                count_trading_days=len(grp),
            )
        )

    # Key insights
    best_year = max(annual_breakdown, key=lambda x: x.return_pct)
    worst_year = min(annual_breakdown, key=lambda x: x.return_pct)
    key_insights: list[str] = [
        f"Total return periode {period}: {overall_return_pct:.1f}%",
        f"Return tahunan maksimum: {best_year.return_pct:.1f}% pada tahun {best_year.year}",
        f"Tahun terburuk: {worst_year.return_pct:.1f}% pada tahun {worst_year.year}",
        f"Max drawdown: {max_drawdown_pct:.1f}%, volatilitas tahunan: {annualized_volatility_pct:.1f}%",
    ]

    logger.info(
        "[EDA] Ringkasan selesai — overall return=%.2f%%, annualized=%.2f%%, max_dd=%.2f%%",
        overall_return_pct,
        annualized_return_pct,
        max_drawdown_pct,
    )
    return SummaryStatsResponse(
        ticker="GSPC",
        period=period,
        overall_return_pct=overall_return_pct,
        annualized_return_pct=annualized_return_pct,
        annualized_volatility_pct=annualized_volatility_pct,
        max_drawdown_pct=max_drawdown_pct,
        total_trading_days=n,
        annual_breakdown=annual_breakdown,
        key_insights=key_insights,
    )


# ---------------------------------------------------------------------------
# Processed Data Info (Feature Engineering)
# ---------------------------------------------------------------------------

def get_processed_data_info() -> ProcessedDataInfo:
    """Scan folder data/processed/ dan kumpulkan metadata file CSV."""
    import os
    import pandas as pd
    from pathlib import Path

    logger.info("[FE] Memuat informasi file processed...")

    project_root = Path(__file__).parent.parent.parent
    processed_dir = project_root / "data" / "processed"

    stocks_files: list[ProcessedFileInfo] = []
    sentiment_files: list[ProcessedFileInfo] = []
    total_files = 0

    for source_type, target_list in [("stocks", stocks_files), ("sentiment", sentiment_files)]:
        source_dir = processed_dir / source_type
        if not source_dir.exists():
            logger.warning("[FE] Folder tidak ditemukan: %s", source_dir)
            continue

        for csv_file in source_dir.glob("*.csv"):
            try:
                df = pd.read_csv(csv_file)
                relative_path = f"data/processed/{source_type}/{csv_file.name}"

                date_start = None
                date_end = None
                if "Date" in df.columns or "date" in df.columns:
                    date_col = "Date" if "Date" in df.columns else "date"
                    try:
                        df[date_col] = pd.to_datetime(df[date_col])
                        date_start = str(df[date_col].min().date())
                        date_end = str(df[date_col].max().date())
                    except Exception:
                        pass

                file_info = ProcessedFileInfo(
                    filename=csv_file.name,
                    path=relative_path,
                    total_rows=len(df),
                    columns=df.columns.tolist(),
                    date_start=date_start,
                    date_end=date_end,
                )

                target_list.append(file_info)
                total_files += 1
                logger.info(
                    "[FE] File scanned: %s — %d rows, %d columns",
                    csv_file.name,
                    len(df),
                    len(df.columns),
                )

            except Exception as e:
                logger.error("[FE] Gagal membaca file %s: %s", csv_file.name, str(e))

    result = ProcessedDataInfo(
        stocks=stocks_files,
        sentiment=sentiment_files,
        total_files=total_files,
    )

    logger.info(
        "[FE] Informasi processed loaded — %d file stocks, %d file sentiment, total %d",
        len(stocks_files),
        len(sentiment_files),
        total_files,
    )
    return result


# ---------------------------------------------------------------------------
# Raw Stocks Data
# ---------------------------------------------------------------------------

def get_raw_stocks() -> list[RawStocksResponse]:
    """Ambil seluruh baris raw data saham GSPC dari file processed."""
    logger.info("[EDA] Memuat raw data saham GSPC...")

    df = get_repositories()["stock"].load_processed(ticker=TickerSymbol(symbol="GSPC"))
    df = df.tail(10)
    logger.info("[EDA] Data saham dimuat — %d baris", len(df))

    rows = [
        RawStocksResponse(
            date=str(row["Date"].date()),
            open=row["Open"],
            high=row["High"],
            low=row["Low"],
            close=row["Close"],
            volume=int(row["Volume"]),
            daily_return=_nan_to_none(float(row["Daily_Return"])),
            hl_spread=row["HL_Spread"],
            oc_spread=row["OC_Spread"],
            ma_20=_nan_to_none(float(row["MA_20"])),
            ma_50=_nan_to_none(float(row["MA_50"])),
            ma_200=_nan_to_none(float(row["MA_200"])),
            volatility_30=_nan_to_none(float(row["Volatility_30"])),
        )
        for _, row in df.iterrows()
    ]

    logger.info("[EDA] Raw stocks selesai — %d baris", len(rows))
    return rows