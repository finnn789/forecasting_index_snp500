"""
app/api/v1/routes_data_analysis.py — Endpoint visualisasi analisis data.

Merepresentasikan setiap langkah alur di:
  - notebooks/01_EDA_stock_data.ipynb    (saham ^GSPC: raw -> EDA -> preprocessing)
  - notebooks/02_EDA_sentiment_data.ipynb (headline berita: raw -> EDA -> FinBERT -> agregasi)

Handler tipis: logic ada di app/services/data_analysis_service.py. Pembungkusan
ke SuccessResponse otomatis via EnvelopeRoute (lihat app/core/envelope.py).
"""

from fastapi import APIRouter, Query

from app.core.envelope import EnvelopeRoute
from app.schemas.data_analysis import (
    CombinedMergeInfo,
    CombinedMergePreviewResponse,
    CombinedPipelineStepsResponse,
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
    StockPriceVolumeResponse,
    StockRawInfo,
    StockRawPreviewResponse,
    StockRollingStatsResponse,
    StockSeasonalityResponse,
    StockSummaryResponse,
)
from app.services import data_analysis_service as svc

router = APIRouter(tags=["Data Analysis"], route_class=EnvelopeRoute)


# ---------------------------------------------------------------------------
# Stock — notebooks/01_EDA_stock_data.ipynb
# ---------------------------------------------------------------------------

@router.get(
    "/data-analysis/stocks/raw-info",
    response_model=StockRawInfo,
    summary="Info Data Saham Mentah",
    openapi_extra={"x-message": "Info data saham mentah berhasil dimuat"},
)
async def stocks_raw_info() -> StockRawInfo:
    return svc.get_stock_raw_info()


@router.get(
    "/data-analysis/stocks/raw-preview",
    response_model=StockRawPreviewResponse,
    summary="Cuplikan N Baris Pertama Data Saham Mentah",
    openapi_extra={"x-message": "Cuplikan data saham mentah berhasil dimuat"},
)
async def stocks_raw_preview(
    n: int = Query(10, ge=1, le=100, description="Jumlah baris pertama yang ditampilkan"),
) -> StockRawPreviewResponse:
    return svc.get_stock_raw_preview(n)


@router.get(
    "/data-analysis/stocks/descriptive-stats",
    response_model=StockDescriptiveStats,
    summary="Statistik Deskriptif OHLCV",
    openapi_extra={"x-message": "Statistik deskriptif saham berhasil dimuat"},
)
async def stocks_descriptive_stats() -> StockDescriptiveStats:
    return svc.get_stock_descriptive_stats()


@router.get(
    "/data-analysis/stocks/price-volume",
    response_model=StockPriceVolumeResponse,
    summary="Time Series Close & Volume",
    openapi_extra={"x-message": "Time series harga & volume berhasil dimuat"},
)
async def stocks_price_volume() -> StockPriceVolumeResponse:
    return svc.get_stock_price_volume()


@router.get(
    "/data-analysis/stocks/daily-returns",
    response_model=StockDailyReturnsResponse,
    summary="Distribusi Daily Return",
    openapi_extra={"x-message": "Distribusi daily return berhasil dimuat"},
)
async def stocks_daily_returns() -> StockDailyReturnsResponse:
    return svc.get_stock_daily_returns()


@router.get(
    "/data-analysis/stocks/rolling-stats",
    response_model=StockRollingStatsResponse,
    summary="Moving Average & Rolling Volatility",
    openapi_extra={"x-message": "Rolling statistics berhasil dimuat"},
)
async def stocks_rolling_stats() -> StockRollingStatsResponse:
    return svc.get_stock_rolling_stats()


@router.get(
    "/data-analysis/stocks/ohlc-spread",
    response_model=StockOhlcSpreadResponse,
    summary="Analisis OHLC Spread & Bullish/Bearish",
    openapi_extra={"x-message": "Analisis OHLC spread berhasil dimuat"},
)
async def stocks_ohlc_spread() -> StockOhlcSpreadResponse:
    return svc.get_stock_ohlc_spread()


@router.get(
    "/data-analysis/stocks/correlation",
    response_model=StockCorrelationResponse,
    summary="Correlation Matrix Fitur Saham",
    openapi_extra={"x-message": "Correlation matrix berhasil dimuat"},
)
async def stocks_correlation() -> StockCorrelationResponse:
    return svc.get_stock_correlation()


@router.get(
    "/data-analysis/stocks/seasonality",
    response_model=StockSeasonalityResponse,
    summary="Pola Musiman Return (Bulanan & Harian)",
    openapi_extra={"x-message": "Analisis musiman berhasil dimuat"},
)
async def stocks_seasonality() -> StockSeasonalityResponse:
    return svc.get_stock_seasonality()


@router.get(
    "/data-analysis/stocks/cumulative-return-drawdown",
    response_model=StockCumulativeReturnDrawdownResponse,
    summary="Cumulative Return & Drawdown",
    openapi_extra={"x-message": "Cumulative return & drawdown berhasil dimuat"},
)
async def stocks_cumulative_return_drawdown() -> StockCumulativeReturnDrawdownResponse:
    return svc.get_stock_cumulative_return_drawdown()


@router.get(
    "/data-analysis/stocks/summary",
    response_model=StockSummaryResponse,
    summary="Ringkasan Akhir EDA Saham",
    openapi_extra={"x-message": "Ringkasan EDA saham berhasil dimuat"},
)
async def stocks_summary() -> StockSummaryResponse:
    return svc.get_stock_summary()


@router.get(
    "/data-analysis/stocks/preprocessing",
    response_model=StockPreprocessingResponse,
    summary="Before/After Preprocessing Saham",
    description=(
        "Membandingkan data sebelum/sesudah StockPreprocessor.clean() "
        "(pipeline produksi) dijalankan."
    ),
    openapi_extra={"x-message": "Perbandingan preprocessing saham berhasil dimuat"},
)
async def stocks_preprocessing() -> StockPreprocessingResponse:
    return svc.get_stock_preprocessing()


# ---------------------------------------------------------------------------
# Sentiment — notebooks/02_EDA_sentiment_data.ipynb
# ---------------------------------------------------------------------------

@router.get(
    "/data-analysis/sentiment/raw-info",
    response_model=SentimentRawInfo,
    summary="Info Data Headline Mentah",
    openapi_extra={"x-message": "Info data headline mentah berhasil dimuat"},
)
async def sentiment_raw_info() -> SentimentRawInfo:
    return svc.get_sentiment_raw_info()


@router.get(
    "/data-analysis/sentiment/raw-preview",
    response_model=SentimentRawPreviewResponse,
    summary="Cuplikan N Baris Pertama Data Sentimen/Headline Mentah",
    openapi_extra={"x-message": "Cuplikan data sentimen mentah berhasil dimuat"},
)
async def sentiment_raw_preview(
    n: int = Query(10, ge=1, le=100, description="Jumlah baris pertama yang ditampilkan"),
) -> SentimentRawPreviewResponse:
    return svc.get_sentiment_raw_preview(n)


@router.get(
    "/data-analysis/sentiment/news-per-year",
    response_model=SentimentNewsPerYearResponse,
    summary="Distribusi Berita per Tahun",
    openapi_extra={"x-message": "Distribusi berita per tahun berhasil dimuat"},
)
async def sentiment_news_per_year() -> SentimentNewsPerYearResponse:
    return svc.get_news_per_year()


@router.get(
    "/data-analysis/sentiment/news-per-day",
    response_model=SentimentNewsPerDayResponse,
    summary="Distribusi Berita per Hari",
    openapi_extra={"x-message": "Distribusi berita per hari berhasil dimuat"},
)
async def sentiment_news_per_day() -> SentimentNewsPerDayResponse:
    return svc.get_news_per_day()


@router.get(
    "/data-analysis/sentiment/headline-length",
    response_model=SentimentHeadlineLengthResponse,
    summary="Distribusi Panjang Headline",
    openapi_extra={"x-message": "Distribusi panjang headline berhasil dimuat"},
)
async def sentiment_headline_length() -> SentimentHeadlineLengthResponse:
    return svc.get_headline_length()


@router.get(
    "/data-analysis/sentiment/closing-price",
    response_model=SentimentClosingPriceResponse,
    summary="Closing Price S&P 500 (kolom CP)",
    openapi_extra={"x-message": "Closing price berhasil dimuat"},
)
async def sentiment_closing_price() -> SentimentClosingPriceResponse:
    return svc.get_sentiment_closing_price()


@router.get(
    "/data-analysis/sentiment/preprocessing",
    response_model=SentimentPreprocessingResponse,
    summary="Before/After Text Cleaning Headline",
    description=(
        "Mengikuti metodologi cleaning teks di notebook 02 (normalisasi, dedup, "
        "filter headline pendek). Pipeline produksi saat ini belum menjalankan "
        "tahap ini — lihat field 'note' pada response."
    ),
    openapi_extra={"x-message": "Perbandingan text cleaning berhasil dimuat"},
)
async def sentiment_preprocessing() -> SentimentPreprocessingResponse:
    return svc.get_sentiment_preprocessing()


@router.get(
    "/data-analysis/sentiment/scoring-distribution",
    response_model=SentimentScoringDistributionResponse,
    summary="Distribusi Label & Skor FinBERT",
    description=(
        "Butuh headlines_clean.csv (hasil scoring FinBERT) sudah ada — jalankan "
        "POST /sentiment/pipeline/run terlebih dahulu jika belum."
    ),
    openapi_extra={"x-message": "Distribusi hasil scoring FinBERT berhasil dimuat"},
)
async def sentiment_scoring_distribution() -> SentimentScoringDistributionResponse:
    return svc.get_scoring_distribution()


@router.get(
    "/data-analysis/sentiment/daily-aggregation",
    response_model=SentimentDailyAggregationResponse,
    summary="Agregasi Sentimen Harian (Probability-Weighted)",
    description=(
        "Dihitung ulang langsung dari headline berskor (signed = numeric x score), "
        "bukan dibaca dari headlines_daily_sentiment.csv — lihat field 'note' pada response."
    ),
    openapi_extra={"x-message": "Agregasi sentimen harian berhasil dimuat"},
)
async def sentiment_daily_aggregation() -> SentimentDailyAggregationResponse:
    return svc.get_daily_aggregation()


@router.get(
    "/data-analysis/sentiment/method-comparison",
    response_model=SentimentMethodComparisonResponse,
    summary="Perbandingan Metode Weighted vs Unweighted",
    openapi_extra={"x-message": "Perbandingan metode agregasi berhasil dimuat"},
)
async def sentiment_method_comparison() -> SentimentMethodComparisonResponse:
    return svc.get_method_comparison()


# ---------------------------------------------------------------------------
# Combined — OHLCV + sentiment_mean (mirrors dataset_builder.py::load_joined())
# ---------------------------------------------------------------------------

@router.get(
    "/data-analysis/combined/merge-info",
    response_model=CombinedMergeInfo,
    summary="Info Penggabungan OHLCV + Sentiment Mean",
    description=(
        "Ringkasan hasil inner join OHLCV (setelah StockPreprocessor.clean()) dengan "
        "sentiment_mean harian — logic identik dengan dataset_builder.py::load_joined() "
        "yang dipakai model untuk training & inference."
    ),
    openapi_extra={"x-message": "Info penggabungan OHLCV + sentiment berhasil dimuat"},
)
async def combined_merge_info() -> CombinedMergeInfo:
    return svc.get_combined_merge_info()


@router.get(
    "/data-analysis/combined/merge-preview",
    response_model=CombinedMergePreviewResponse,
    summary="Cuplikan N Baris Pertama Data Gabungan OHLCV + Sentiment Mean",
    openapi_extra={"x-message": "Cuplikan data gabungan berhasil dimuat"},
)
async def combined_merge_preview(
    n: int = Query(10, ge=1, le=100, description="Jumlah baris pertama yang ditampilkan"),
) -> CombinedMergePreviewResponse:
    return svc.get_combined_merge_preview(n)


@router.get(
    "/data-analysis/combined/pipeline-steps",
    response_model=CombinedPipelineStepsResponse,
    summary="Langkah-Langkah Preprocessing Dataset Gabungan",
    description=(
        "Mencerminkan dataset_builder.py::build_dataset() (load & clean OHLCV, "
        "load sentimen, inner join, labeling, split by date, MinMaxScaler "
        "fit train-only, windowing) versi ringan — tanpa torch & tanpa array "
        "windowing sungguhan, hanya jumlah sampel."
    ),
    openapi_extra={"x-message": "Langkah preprocessing dataset gabungan berhasil dimuat"},
)
async def combined_pipeline_steps() -> CombinedPipelineStepsResponse:
    return svc.get_combined_pipeline_steps()
