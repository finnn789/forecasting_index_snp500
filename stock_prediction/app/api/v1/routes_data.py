"""
app/api/v1/routes_data.py — Route EDA.

Handler tipis: cukup return schema inner. Pembungkusan ke SuccessResponse
ditangani otomatis oleh EnvelopeRoute (lihat app/core/envelope.py).
Pesan per-endpoint didefinisikan via openapi_extra={"x-message": "..."}.
"""

from fastapi import APIRouter

from app.core.envelope import EnvelopeRoute
from app.schemas.sentiment import (
    DatasetSummary,
    HeadlineLengthStats,
    NewsPerDayStats,
    NewsPerYearResponse,
    ProcessedDataInfo,
    RawStocksResponse,
    SentimentDistributionResponse,
)
from app.schemas.stocks import (
    DailyReturnDistributionResponse,
    DataInfoResponse,
    DescriptiveStatsResponse,
    DrawdownResponse,
    SummaryStatsResponse,
    TimeSeriesResponse,
)
from app.services import eda_service

router = APIRouter(tags=["Data & EDA"], route_class=EnvelopeRoute)


@router.get(
    "/data/eda/summary",
    response_model=DatasetSummary,
    summary="Statistik Dasar Dataset",
    description=(
        "Menampilkan statistik dasar dataset berita: jumlah baris, "
        "rentang tanggal, missing values, dan tipe data kolom."
    ),
    openapi_extra={"x-message": "Ringkasan dataset berhasil dimuat"},
)
async def eda_summary() -> DatasetSummary:
    return eda_service.get_dataset_summary()


@router.get(
    "/data/eda/news-per-year",
    response_model=NewsPerYearResponse,
    summary="Distribusi Berita per Tahun",
    description="Menghitung jumlah headline berita per tahun. Data siap digunakan sebagai bar chart.",
    openapi_extra={"x-message": "Distribusi berita per tahun berhasil dimuat"},
)
async def eda_news_per_year() -> NewsPerYearResponse:
    return eda_service.get_news_per_year()


@router.get(
    "/data/eda/news-per-day",
    response_model=NewsPerDayStats,
    summary="Statistik Jumlah Berita per Hari",
    description="Statistik agregasi jumlah headline per hari (mean, max, min) beserta petunjuk visualisasi.",
    openapi_extra={"x-message": "Statistik berita per hari berhasil dimuat"},
)
async def eda_news_per_day() -> NewsPerDayStats:
    return eda_service.get_news_per_day()


@router.get(
    "/data/eda/headline-length",
    response_model=HeadlineLengthStats,
    summary="Distribusi Panjang Headline",
    description="Statistik panjang headline dalam karakter dan kata. Data siap digunakan sebagai histogram.",
    openapi_extra={"x-message": "Statistik panjang headline berhasil dimuat"},
)
async def eda_headline_length() -> HeadlineLengthStats:
    return eda_service.get_headline_length()


@router.get(
    "/data/eda/sentiment-distribution",
    response_model=SentimentDistributionResponse,
    summary="Distribusi Label Sentimen",
    description=(
        "Menampilkan distribusi label sentimen (positive/negative/neutral) "
        "beserta statistik sentiment_score. Data siap digunakan sebagai bar chart."
    ),
    openapi_extra={"x-message": "Distribusi label sentimen berhasil dimuat"},
)
async def eda_sentiment_distribution() -> SentimentDistributionResponse:
    return eda_service.get_sentiment_distribution()


@router.get(
    "/data/eda/stocks-info-response",
    response_model=DataInfoResponse,
    summary="Informasi File Processed",
    description=(
        "Daftar file CSV yang sudah diproses di data/processed/, beserta "
        "metadata seperti jumlah baris, kolom, dan tipe data. Tidak ada eksekusi pipeline."
    ),
    openapi_extra={"x-message": "Informasi file processed berhasil dimuat"},
)
async def eda_stocks_info_response() -> DataInfoResponse:
    return eda_service.get_stocks_overview()


@router.get(
    "/data/eda/stocks/descriptive-stats",
    response_model=DescriptiveStatsResponse,
    summary="Statistik Deskriptif Saham",
    description=(
        "Statistik deskriptif OHLCV saham GSPC (min, max, mean, std, median, "
        "skewness, kurtosis, kuartil) untuk tiap kolom harga dan volume."
    ),
    openapi_extra={"x-message": "Statistik deskriptif saham berhasil dimuat"},
)
async def eda_stocks_descriptive_stats() -> DescriptiveStatsResponse:
    return eda_service.get_stocks_descriptive_stats()


@router.get(
    "/data/eda/stocks/time-series",
    response_model=TimeSeriesResponse,
    summary="Deret Waktu Harga & Volume",
    description=(
        "Deret waktu harga Close dan Volume saham GSPC, lengkap dengan anotasi "
        "crash event (COVID 2020, bear market 2022). Siap untuk chart utama."
    ),
    openapi_extra={"x-message": "Deret waktu saham berhasil dimuat"},
)
async def eda_stocks_time_series() -> TimeSeriesResponse:
    return eda_service.get_stocks_time_series()


@router.get(
    "/data/eda/stocks/daily-returns",
    response_model=DailyReturnDistributionResponse,
    summary="Distribusi Daily Return",
    description=(
        "Distribusi daily return saham GSPC: statistik agregat, deret waktu "
        "return, dan breakdown statistik per tahun."
    ),
    openapi_extra={"x-message": "Distribusi daily return berhasil dimuat"},
)
async def eda_stocks_daily_returns() -> DailyReturnDistributionResponse:
    return eda_service.get_stocks_daily_returns()


@router.get(
    "/data/eda/stocks/drawdown",
    response_model=DrawdownResponse,
    summary="Cumulative Return & Drawdown",
    description=(
        "Cumulative return dan drawdown saham GSPC beserta metrik ringkas "
        "(total return, max drawdown, annualized return & volatility)."
    ),
    openapi_extra={"x-message": "Data drawdown saham berhasil dimuat"},
)
async def eda_stocks_drawdown() -> DrawdownResponse:
    return eda_service.get_stocks_drawdown()


@router.get(
    "/data/eda/stocks/summary",
    response_model=SummaryStatsResponse,
    summary="Ringkasan Performa Saham",
    description=(
        "Ringkasan akhir performa saham GSPC: overall & annualized return, "
        "volatilitas, max drawdown, breakdown per tahun, dan key insights."
    ),
    openapi_extra={"x-message": "Ringkasan performa saham berhasil dimuat"},
)
async def eda_stocks_summary() -> SummaryStatsResponse:
    return eda_service.get_stocks_summary()

@router.get(
    "/data/eda/stocks/raw",
    response_model=list[RawStocksResponse],
    summary="Raw Stock Data GSPC",
    description="Seluruh baris data mentah saham GSPC dari file processed.",
    openapi_extra={"x-message": "Raw stock data berhasil dimuat"},
)
async def stocks_raw_response() -> list[RawStocksResponse]:
    return eda_service.get_raw_stocks()