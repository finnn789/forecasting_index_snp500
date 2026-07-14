"""
app/api/v1/routes_training.py — Endpoint "API Training Live Notebook 05".

Expose training FINAL model LSTM (metodologi notebook 05) sebagai API
live-streamed (SSE), plus endpoint hasil grid-search STATIS (144 kombinasi,
tidak dijalankan ulang). Juga expose varian OHLCV-only (ablation study —
tanpa sentiment_mean, lihat `train_notebook05_ohlcv`). Artefak & kelas
TERISOLASI dari produksi — lihat models/lstm/notebook05_common.py.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.envelope import EnvelopeRoute
from app.helpers.sse import sse_response
from app.schemas.training import (
    GridSearchResultResponse,
    Notebook05BacktestResponse,
    Notebook05PredictionResponse,
    Notebook05ResultResponse,
    Notebook07BacktestResponse,
    Notebook07PredictionResponse,
    Notebook07ResultResponse,
    SearchSpaceResponse,
    SkripsiTrainRequest,
    TrainRequest,
)
from app.services import training_service

router = APIRouter(tags=["Model Training"], route_class=EnvelopeRoute)


@router.post(
    "/train/notebook05",
    summary="Training final LSTM (Server-Sent Events) — metodologi notebook 05",
    response_description="Stream SSE: type start/epoch/done/error",
)
async def train_notebook05(req: TrainRequest | None = None) -> StreamingResponse:
    """
    Jalankan training final `LSTMSoftmaxClassifier` (replikasi metodologi
    notebook 05, varian OHLCV+sentiment_mean) dan stream progress secara
    real-time via Server-Sent Events (text/event-stream).

    Model ini diketahui KOLAPS KELAS ("selalu menebak Up") — diagnosis
    class-collapse dihitung & dikembalikan apa adanya di event "done".

    Artefak disimpan TERISOLASI (`lstm_nb05_*`) — TIDAK menimpa artefak
    produksi (`direction_classifier.pt`/`scaler.joblib`/`metadata.json`).

    Setiap event adalah JSON satu baris:
    ```
    data: {"type": "start", ...}
    data: {"type": "epoch", ...}
    data: {"type": "done", ...}
    ```
    atau `{"type": "error", "message": "..."}` bila gagal.
    """
    body = req or TrainRequest()

    def work(emit: Callable[[dict], None]) -> None:
        training_service.run_training_stream(body, emit=emit)

    return sse_response(work)


@router.post(
    "/train/notebook05/ohlcv",
    summary="Training final LSTM (SSE) — varian OHLCV-only (ablation study)",
    response_description="Stream SSE: type start/epoch/done/error",
)
async def train_notebook05_ohlcv(req: TrainRequest | None = None) -> StreamingResponse:
    """
    Varian OHLCV-only (ablation study) dari training final `LSTMSoftmaxClassifier`
    — HANYA 5 fitur (Open, High, Low, Close, Volume), TANPA `sentiment_mean`.

    Hyperparameter default me-reuse `best_config` hasil grid-search 144
    kombinasi notebook 05 (varian sentimen) — grid-search 5-fitur ini sendiri
    TIDAK pernah dijalankan ulang. Tujuannya adalah ablation study terkontrol:
    satu-satunya variabel yang beda dari `POST /train/notebook05` adalah
    ada/tidaknya fitur `sentiment_mean`, untuk mengukur kontribusi nyatanya.

    Artefak disimpan TERISOLASI (`lstm_nb05_ohlcv_*`) — TIDAK menimpa artefak
    produksi maupun artefak varian sentimen (`lstm_nb05_*`).

    Event SSE identik dengan `POST /train/notebook05`:
    ```
    data: {"type": "start", ...}
    data: {"type": "epoch", ...}
    data: {"type": "done", ...}
    ```
    atau `{"type": "error", "message": "..."}` bila gagal.
    """
    body = req or TrainRequest()

    def work(emit: Callable[[dict], None]) -> None:
        training_service.run_training_stream_ohlcv(body, emit=emit)

    return sse_response(work)


@router.get(
    "/train/notebook05/grid-search-result",
    response_model=GridSearchResultResponse,
    openapi_extra={"x-message": "Hasil grid-search notebook 05 berhasil dimuat"},
)
def grid_search_result() -> GridSearchResultResponse:
    """Hasil grid-search 144 kombinasi (STATIS, hardcode dari notebook 05 —
    TIDAK dijalankan ulang)."""
    return training_service.get_grid_search_result()


# ---------------------------------------------------------------------------
# Halaman Prediction — hasil training notebook05 (persisted) + prediksi +
# backtest, per varian (sentimen/ohlcv). Sumber data pindah ke backend supaya
# tidak hilang saat React unmount (beda dari live SSE training di atas).
# ---------------------------------------------------------------------------

@router.get(
    "/train/notebook05/result",
    response_model=Notebook05ResultResponse,
    openapi_extra={"x-message": "Hasil training notebook05 (sentimen) berhasil dimuat"},
)
def notebook05_result() -> Notebook05ResultResponse:
    """Hasil training terakhir varian OHLCV+sentimen (persisted di metadata.json).
    `is_available=False` (bukan 404) kalau belum pernah training."""
    return training_service.get_notebook05_result("sentiment")


@router.get(
    "/train/notebook05/ohlcv/result",
    response_model=Notebook05ResultResponse,
    openapi_extra={"x-message": "Hasil training notebook05 (OHLCV-only) berhasil dimuat"},
)
def notebook05_ohlcv_result() -> Notebook05ResultResponse:
    """Varian OHLCV-only dari `GET /train/notebook05/result`."""
    return training_service.get_notebook05_result("ohlcv")


@router.post(
    "/train/notebook05/predict",
    response_model=Notebook05PredictionResponse,
    openapi_extra={"x-message": "Prediksi notebook05 (sentimen) berhasil dijalankan"},
)
def notebook05_predict() -> Notebook05PredictionResponse:
    """Prediksi arah harga hari berikutnya, varian OHLCV+sentimen, memakai
    model terlatih tersimpan (`lstm_nb05_best.pt`)."""
    return training_service.predict_notebook05("sentiment")


@router.post(
    "/train/notebook05/ohlcv/predict",
    response_model=Notebook05PredictionResponse,
    openapi_extra={"x-message": "Prediksi notebook05 (OHLCV-only) berhasil dijalankan"},
)
def notebook05_ohlcv_predict() -> Notebook05PredictionResponse:
    """Varian OHLCV-only dari `POST /train/notebook05/predict`."""
    return training_service.predict_notebook05("ohlcv")


@router.get(
    "/train/notebook05/backtest",
    response_model=Notebook05BacktestResponse,
    openapi_extra={"x-message": "Backtest notebook05 (sentimen) berhasil dijalankan"},
)
def notebook05_backtest(split: str = "test") -> Notebook05BacktestResponse:
    """Backtest model notebook05 terlatih (varian OHLCV+sentimen) pada split
    historis (default 'test')."""
    return training_service.backtest_notebook05("sentiment", split=split)


@router.get(
    "/train/notebook05/ohlcv/backtest",
    response_model=Notebook05BacktestResponse,
    openapi_extra={"x-message": "Backtest notebook05 (OHLCV-only) berhasil dijalankan"},
)
def notebook05_ohlcv_backtest(split: str = "test") -> Notebook05BacktestResponse:
    """Varian OHLCV-only dari `GET /train/notebook05/backtest`."""
    return training_service.backtest_notebook05("ohlcv", split=split)


# ---------------------------------------------------------------------------
# "Random Search Skripsi-Scoped" (notebook 07, Batasan Masalah BAB I skripsi)
# ---------------------------------------------------------------------------

@router.get(
    "/train/skripsi/search-space",
    response_model=SearchSpaceResponse,
    openapi_extra={"x-message": "Search space Random Search berhasil dimuat"},
)
def skripsi_search_space() -> SearchSpaceResponse:
    """Info statis search space Random Search (notebook 07) — TIDAK ada hasil
    statis seperti grid-search notebook 05, karena Random Search dijalankan LIVE
    tiap kali endpoint training di bawah dipanggil."""
    return training_service.get_skripsi_search_space()


@router.post(
    "/train/skripsi/ohlcv",
    summary="Random Search LSTM-OHLCV baseline (SSE) — Model A, skripsi-scoped",
    response_description="Stream SSE: type start/iteration_start/epoch/iteration_end/done/error",
)
async def train_skripsi_baseline(req: SkripsiTrainRequest | None = None) -> StreamingResponse:
    """
    Jalankan Random Search (replikasi `notebooks/07_LSTM_FinBERT_skripsi_scoped.ipynb`,
    Batasan Masalah BAB I skripsi) untuk **Model A — LSTM-OHLCV baseline** (5 fitur
    OHLCV, TANPA `sentiment_mean`) dan stream progress via Server-Sent Events.

    20 iterasi (default) — tiap iterasi melatih PENUH 1 konfigurasi hyperparameter
    hasil random sampling (TANPA early-stopping; `epochs` sendiri adalah salah satu
    hyperparameter yang di-*search*). Evaluasi akhir HANYA 4 metrik: Accuracy,
    Precision, Recall, F1-Score (sesuai Batasan Masalah — TIDAK ada AUC/F2/diagnosis
    class-collapse seperti varian notebook 05).

    Artefak disimpan sebagai `lstm_baseline_skripsi.*` — SAMA PERSIS dengan yang
    disimpan notebook 07 sendiri (interchangeable), TIDAK menimpa artefak produksi
    maupun varian notebook 05.

    Event SSE (JSON satu baris per event):
    ```
    data: {"type": "start", "total_iterations": 20, "search_space": {...}, ...}
    data: {"type": "iteration_start", "iteration": 1, "config": {...}}
    data: {"type": "epoch", "iteration": 1, "epoch": 1, "total_epochs": 50, ...}
    data: {"type": "iteration_end", "iteration": 1, "val_f1": 0.42, "is_new_best": true}
    data: {"type": "done", "best_config": {...}, "metrics": {...}, ...}
    ```
    atau `{"type": "error", "message": "..."}` bila gagal.
    """
    body = req or SkripsiTrainRequest()

    def work(emit: Callable[[dict], None]) -> None:
        training_service.run_skripsi_baseline_stream(body, emit=emit)

    return sse_response(work)


@router.post(
    "/train/skripsi/finbert-lstm",
    summary="Random Search FinBERT-LSTM (SSE) — Model B, skripsi-scoped",
    response_description="Stream SSE: type start/iteration_start/epoch/iteration_end/done/error",
)
async def train_skripsi_finbert(req: SkripsiTrainRequest | None = None) -> StreamingResponse:
    """
    Varian **Model B — FinBERT-LSTM** (6 fitur: OHLCV + `sentiment_mean`) dari
    Random Search skripsi-scoped. Identik dengan `POST /train/skripsi/ohlcv` di
    semua aspek lain (arsitektur, Random Search, evaluasi 4 metrik) — satu-satunya
    variabel yang beda adalah ada/tidaknya fitur `sentiment_mean`, untuk menjawab
    Hipotesa #4 BAB I (apakah FinBERT-LSTM mengungguli LSTM-OHLCV baseline).

    Artefak disimpan sebagai `finbert_lstm_skripsi.*`.

    Event SSE identik dengan `POST /train/skripsi/ohlcv`.
    """
    body = req or SkripsiTrainRequest()

    def work(emit: Callable[[dict], None]) -> None:
        training_service.run_skripsi_finbert_stream(body, emit=emit)

    return sse_response(work)


# ---------------------------------------------------------------------------
# Halaman Prediction — hasil Random Search skripsi-scoped (persisted) +
# prediksi + backtest, per varian (Model A: baseline / Model B: finbert).
# ---------------------------------------------------------------------------

@router.get(
    "/train/skripsi/ohlcv/result",
    response_model=Notebook07ResultResponse,
    openapi_extra={"x-message": "Hasil Random Search Model A (LSTM-OHLCV) berhasil dimuat"},
)
def skripsi_baseline_result() -> Notebook07ResultResponse:
    """Hasil Random Search terakhir Model A (LSTM-OHLCV baseline, persisted di
    metadata.json). `is_available=False` (bukan 404) kalau belum pernah training."""
    return training_service.get_notebook07_result("baseline")


@router.get(
    "/train/skripsi/finbert-lstm/result",
    response_model=Notebook07ResultResponse,
    openapi_extra={"x-message": "Hasil Random Search Model B (FinBERT-LSTM) berhasil dimuat"},
)
def skripsi_finbert_result() -> Notebook07ResultResponse:
    """Varian Model B (FinBERT-LSTM) dari `GET /train/skripsi/ohlcv/result`."""
    return training_service.get_notebook07_result("finbert")


@router.post(
    "/train/skripsi/ohlcv/predict",
    response_model=Notebook07PredictionResponse,
    openapi_extra={"x-message": "Prediksi Model A (LSTM-OHLCV) berhasil dijalankan"},
)
def skripsi_baseline_predict() -> Notebook07PredictionResponse:
    """Prediksi arah harga hari berikutnya, Model A (LSTM-OHLCV baseline),
    memakai model terlatih tersimpan (`lstm_baseline_skripsi.pt`)."""
    return training_service.predict_notebook07("baseline")


@router.post(
    "/train/skripsi/finbert-lstm/predict",
    response_model=Notebook07PredictionResponse,
    openapi_extra={"x-message": "Prediksi Model B (FinBERT-LSTM) berhasil dijalankan"},
)
def skripsi_finbert_predict() -> Notebook07PredictionResponse:
    """Varian Model B (FinBERT-LSTM) dari `POST /train/skripsi/ohlcv/predict`."""
    return training_service.predict_notebook07("finbert")


@router.get(
    "/train/skripsi/ohlcv/backtest",
    response_model=Notebook07BacktestResponse,
    openapi_extra={"x-message": "Backtest Model A (LSTM-OHLCV) berhasil dijalankan"},
)
def skripsi_baseline_backtest(split: str = "test") -> Notebook07BacktestResponse:
    """Backtest Model A (LSTM-OHLCV baseline) terlatih pada split historis
    (default 'test'). Hanya 4 metrik (accuracy/precision/recall/f1) sesuai
    Batasan Masalah BAB I."""
    return training_service.backtest_notebook07("baseline", split=split)


@router.get(
    "/train/skripsi/finbert-lstm/backtest",
    response_model=Notebook07BacktestResponse,
    openapi_extra={"x-message": "Backtest Model B (FinBERT-LSTM) berhasil dijalankan"},
)
def skripsi_finbert_backtest(split: str = "test") -> Notebook07BacktestResponse:
    """Varian Model B (FinBERT-LSTM) dari `GET /train/skripsi/ohlcv/backtest`."""
    return training_service.backtest_notebook07("finbert", split=split)
