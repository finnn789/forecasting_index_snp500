"""
app/api/v1/routes_data_information.py — Endpoint tab "Data Information".

Mengekspos temuan diagnostik notebooks/11_diagnostic_data_analysis_horizon.ipynb
(pergeseran pola pasar, nilai di luar jangkauan normalisasi, arah hubungan yang
berbalik, sentimen reaktif, perbandingan dengan baseline sederhana) sebagai data
LIVE — dihitung ulang tiap request, bukan angka statis.

Handler tipis: logic ada di app/services/data_information_service.py. Pembungkusan
ke SuccessResponse otomatis via EnvelopeRoute (lihat app/core/envelope.py).
"""

from fastapi import APIRouter, Query

from app.core.envelope import EnvelopeRoute
from app.schemas.data_information import (
    BaselineComparisonResponse,
    DistributionDriftResponse,
    FeatureLabelCorrelationResponse,
    LabelBalanceResponse,
    ModelKey,
    RegimeOverviewResponse,
    ScalingRangeResponse,
    SentimentLagCorrelationResponse,
)
from app.services import data_information_service as svc

router = APIRouter(tags=["Data Information"], route_class=EnvelopeRoute)

# Query param horizon dideklarasikan sebagai int biasa (bukan Literal[1, 5]):
# FastAPI/Pydantic v2 pada versi yang dipakai project ini tidak meng-coerce query
# string ("1") ke Literal[int] — nilai yang tidak valid (bukan 1/5) divalidasi
# secara eksplisit di service layer (lihat data_information_service._validate_horizon).
_HORIZON_DESC = "Jarak hari prediksi — hanya 1 atau 5 yang valid"


@router.get(
    "/data-information/regime-overview",
    response_model=RegimeOverviewResponse,
    summary="Pergeseran Pola Pasar Antar Periode",
    description=(
        "Harga penutupan harian penuh + batas periode latih/validasi/uji + "
        "ringkasan perubahan harga & Up% label per periode."
    ),
    openapi_extra={"x-message": "Ringkasan pergeseran pola pasar berhasil dimuat"},
)
async def regime_overview(
    model: ModelKey = Query("joined", description="ohlcv = Model A, joined = Model B (FinBERT-LSTM)"),
    horizon: int = Query(1, description=_HORIZON_DESC),
) -> RegimeOverviewResponse:
    return svc.get_regime_overview(model, horizon)


@router.get(
    "/data-information/label-balance",
    response_model=LabelBalanceResponse,
    summary="Distribusi Arah Naik/Turun per Periode",
    description="Up%/Down% per periode untuk kedua model, plus Up% bergerak (jendela 60 hari) sepanjang waktu.",
    openapi_extra={"x-message": "Distribusi arah naik/turun berhasil dimuat"},
)
async def label_balance(
    horizon: int = Query(1, description=_HORIZON_DESC),
) -> LabelBalanceResponse:
    return svc.get_label_balance(horizon)


@router.get(
    "/data-information/scaling-range",
    response_model=ScalingRangeResponse,
    summary="Nilai di Luar Jangkauan Data Latihan",
    description=(
        "Per fitur: rentang hasil normalisasi data latih, persentase baris "
        "validasi/uji yang jatuh di luar [0,1], plus time series harga penutupan "
        "ternormalisasi."
    ),
    openapi_extra={"x-message": "Analisis rentang normalisasi berhasil dimuat"},
)
async def scaling_range(
    model: ModelKey = Query("joined", description="ohlcv = Model A, joined = Model B (FinBERT-LSTM)"),
    horizon: int = Query(1, description=_HORIZON_DESC),
) -> ScalingRangeResponse:
    return svc.get_scaling_range(model, horizon)


@router.get(
    "/data-information/feature-label-correlation",
    response_model=FeatureLabelCorrelationResponse,
    summary="Arah Hubungan Fitur vs Label yang Berbalik",
    description="Korelasi point-biserial per fitur per periode, dengan penanda arah hubungan yang berbalik.",
    openapi_extra={"x-message": "Analisis arah hubungan fitur berhasil dimuat"},
)
async def feature_label_correlation(
    model: ModelKey = Query("joined", description="ohlcv = Model A, joined = Model B (FinBERT-LSTM)"),
    horizon: int = Query(1, description=_HORIZON_DESC),
) -> FeatureLabelCorrelationResponse:
    return svc.get_feature_label_correlation(model, horizon)


@router.get(
    "/data-information/sentiment-lag-correlation",
    response_model=SentimentLagCorrelationResponse,
    summary="Sentimen Berita: Reaktif atau Memimpin Harga?",
    description="Korelasi skor sentimen harian vs return harga 0-10 hari ke depan, keseluruhan data & per periode.",
    openapi_extra={"x-message": "Analisis reaktivitas sentimen berhasil dimuat"},
)
async def sentiment_lag_correlation() -> SentimentLagCorrelationResponse:
    return svc.get_sentiment_lag_correlation()


@router.get(
    "/data-information/baseline-comparison",
    response_model=BaselineComparisonResponse,
    summary="Model vs Baseline Sederhana",
    description=(
        "Baseline Selalu-Mayoritas & Ikuti-Arah-Kemarin per periode/horizon/model, "
        "digabung dengan metrik model sungguhan dari artefak tersimpan."
    ),
    openapi_extra={"x-message": "Perbandingan model vs baseline berhasil dimuat"},
)
async def baseline_comparison() -> BaselineComparisonResponse:
    return svc.get_baseline_comparison()


@router.get(
    "/data-information/distribution-drift",
    response_model=DistributionDriftResponse,
    summary="Uji Perbedaan Distribusi (KS-test)",
    description="KS-statistic + p-value per fitur (data latih vs data uji) + histogram overlay.",
    openapi_extra={"x-message": "Uji perbedaan distribusi berhasil dimuat"},
)
async def distribution_drift(
    model: ModelKey = Query("joined", description="ohlcv = Model A, joined = Model B (FinBERT-LSTM)"),
    horizon: int = Query(1, description=_HORIZON_DESC),
) -> DistributionDriftResponse:
    return svc.get_distribution_drift(model, horizon)
