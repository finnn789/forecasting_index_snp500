"""
app/api/v1/routes_live.py — Fitur "Prediksi Live" di Dashboard: fetch OHLCV +
headline S&P 500 live (yfinance, tanpa API key) untuk chart & daftar berita,
plus endpoint prediksi 5-hari-ke-depan yang menjalankan seluruh pipeline
(fetch -> preprocessing -> inference) secara live per klik. Lihat
`app/services/live_data_service.py` dan `app/services/live_prediction_service.py`.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.core.envelope import EnvelopeRoute
from app.helpers.sse import sse_response
from app.schemas.live import LiveNewsLatestResponse, LiveStockLatestResponse
from app.services import live_data_service, live_prediction_service

router = APIRouter(tags=["Live Prediction"], route_class=EnvelopeRoute)


@router.get(
    "/live/stocks/latest",
    response_model=LiveStockLatestResponse,
    summary="OHLCV S&P 500 Live (yfinance)",
    openapi_extra={"x-message": "Data OHLCV live berhasil dimuat"},
)
def live_stocks_latest(
    n: int = Query(30, ge=1, le=100, description="Jumlah baris terbaru yang ditampilkan"),
) -> LiveStockLatestResponse:
    return LiveStockLatestResponse(**live_data_service.get_live_stock_latest(n))


@router.get(
    "/live/news/latest",
    response_model=LiveNewsLatestResponse,
    summary="Headline Berita S&P 500 Live (yfinance) + Sentimen Harian",
    openapi_extra={"x-message": "Berita live berhasil dimuat"},
)
def live_news_latest(
    n: int = Query(10, ge=1, le=50, description="Jumlah headline terbaru yang ditampilkan"),
) -> LiveNewsLatestResponse:
    return LiveNewsLatestResponse(**live_data_service.get_live_news_latest(n))


@router.post(
    "/live/predict/finbert-lstm",
    summary="Prediksi Live 5 Hari ke Depan (fetch OHLCV+berita -> preprocessing -> inference, SSE)",
    response_description="Stream SSE: type start/fetching_ohlcv/fetching_ohlcv_done/fetching_news/"
    "fetching_news_done/preprocessing/preprocessing_done/inferring/done/error",
)
async def live_predict_finbert() -> StreamingResponse:
    """
    Jalankan seluruh pipeline "Prediksi Live" per klik: fetch OHLCV S&P 500 +
    headline berita live (yfinance, tanpa API key) -> preprocessing (FinBERT
    scoring, agregasi sentimen harian, return features) -> inference model
    FinBERT-LSTM terlatih (`finbert_lstm_skripsi.pt`) -> prediksi arah 5 hari
    ke depan.

    Event SSE (JSON satu baris per event):
    ```
    data: {"type": "start"}
    data: {"type": "fetching_ohlcv"}
    data: {"type": "fetching_ohlcv_done", "rows_fetched": 60, "date_start": "...", "date_end": "..."}
    data: {"type": "fetching_news"}
    data: {"type": "fetching_news_done", "headlines_accumulated": 50}
    data: {"type": "preprocessing"}
    data: {"type": "preprocessing_done", "days_joined": 2, "rows_available": 59, "live_sentiment_days": 1, "window_required": 20}
    data: {"type": "inferring"}
    data: {"type": "done", "as_of_date": "...", "target_date": "...", "direction": "up", "probability_up": 0.55, ...}
    ```
    atau `{"type": "error", "message": "..."}` bila model belum dilatih ATAU data
    live (OHLCV+berita gabungan) tidak cukup untuk membentuk 1 window (cakupan
    berita live yfinance terbatas — lihat docstring `live_data_service.py`).
    """
    def work(emit: Callable[[dict], None]) -> None:
        live_prediction_service.run_live_predict_stream(emit=emit)

    return sse_response(work)
