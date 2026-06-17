"""
app/api/v1/routes_prediction.py — Endpoint prediksi arah harga.

Menggunakan EnvelopeRoute — handler cukup return <InnerSchema>,
pembungkusan ke SuccessResponse dilakukan otomatis.
"""

from fastapi import APIRouter

from app.core.envelope import EnvelopeRoute
from app.schemas.prediction import BacktestResponse, DirectionPredictionResponse, ModelInfoResponse, PredictionRequest
from app.services import prediction_service

router = APIRouter(tags=["Prediction"], route_class=EnvelopeRoute)


@router.post(
    "/predict",
    response_model=DirectionPredictionResponse,
    openapi_extra={"x-message": "Prediksi arah harga berhasil"},
    summary="Prediksi arah harga S&P 500 hari berikutnya",
)
def predict(req: PredictionRequest) -> DirectionPredictionResponse:
    """
    Prediksi apakah harga S&P 500 akan naik atau turun besok.

    Menggunakan model LSTM yang telah dilatih dengan fusi fitur OHLCV + sentimen berita.
    Model harus sudah dilatih sebelum endpoint ini dapat digunakan.

    Returns:
        DirectionPredictionResponse: Arah prediksi, probabilitas, dan confidence.
    """
    return prediction_service.predict_direction(req.ticker)


@router.get(
    "/predict/model/status",
    response_model=ModelInfoResponse,
    openapi_extra={"x-message": "Status model prediksi berhasil dimuat"},
    summary="Cek status dan informasi model LSTM",
)
def model_status() -> ModelInfoResponse:
    """
    Cek apakah model LSTM sudah tersedia dan informasi metadata-nya.

    Membaca dari `data/artifacts/lstm_weights/metadata.json` jika ada.
    """
    return prediction_service.get_model_status()


@router.get(
    "/predict/backtest",
    response_model=BacktestResponse,
    openapi_extra={"x-message": "Backtest prediksi berhasil dimuat"},
    summary="Jalankan backtest model LSTM di data historis",
)
def backtest(split: str = "test") -> BacktestResponse:
    """
    Jalankan model LSTM yang sudah dilatih di data historis dan kembalikan
    pasangan prediksi-vs-aktual per tanggal beserta metrik evaluasi.

    Query params:
        split: Split data yang digunakan ('test' saja yang didukung saat ini).

    Returns:
        BacktestResponse berisi daftar titik prediksi, metrik (accuracy, precision,
        recall, f1, auc), dan confusion matrix.
    """
    return prediction_service.run_backtest(split)
