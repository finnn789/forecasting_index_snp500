"""
app/api/v1/routes_training.py — Endpoint "Random Search Skripsi-Scoped"
(notebook 07, Batasan Masalah BAB I skripsi).

Expose Random Search LIVE (SSE) untuk Model A (LSTM-OHLCV baseline) & Model B
(FinBERT-LSTM), plus endpoint hasil training tersimpan + prediksi + backtest
per varian. Artefak & kelas TERISOLASI dari produksi — lihat
models/lstm/notebook07_common.py.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.envelope import EnvelopeRoute
from app.helpers.sse import sse_response
from app.schemas.training import (
    ManualTrainRequest,
    Notebook07BacktestResponse,
    Notebook07PredictionResponse,
    Notebook07ResultResponse,
    SearchSpaceResponse,
    SkripsiTrainRequest,
)
from app.services import training_service

router = APIRouter(tags=["Model Training"], route_class=EnvelopeRoute)


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


@router.post(
    "/train/skripsi/ohlcv/manual",
    summary="Training Manual LSTM-OHLCV baseline (SSE) — Model A, 1 konfigurasi fixed",
    response_description="Stream SSE: type start/epoch/done/error",
)
async def train_skripsi_baseline_manual(req: ManualTrainRequest) -> StreamingResponse:
    """
    Latih **Model A — LSTM-OHLCV baseline** dengan 1 konfigurasi hyperparameter
    yang dikirim FE (input manual bebas, ATAU prefill dari `best_config` hasil
    `POST /train/skripsi/ohlcv`) — BUKAN Random Search, tidak ada sampling/seleksi.

    Event SSE flat (2 level, beda dari Random Search yang 3 level):
    ```
    data: {"type": "start", "config": {...}, ...}
    data: {"type": "epoch", "epoch": 1, "total_epochs": 30, ...}
    data: {"type": "done", "config": {...}, "final_val_f1": ..., "metrics": {...}, ...}
    ```
    atau `{"type": "error", "message": "..."}` bila gagal.

    **PENTING:** artefak disimpan ke nama file YANG SAMA dengan Random Search
    (`lstm_baseline_skripsi.*`) — training manual MENIMPA model resmi Model A,
    sehingga halaman Prediction (`.../result`, `.../predict`, `.../backtest`)
    otomatis merefleksikan model manual yang baru dilatih.
    """
    def work(emit: Callable[[dict], None]) -> None:
        training_service.run_skripsi_baseline_manual_stream(req, emit=emit)

    return sse_response(work)


@router.post(
    "/train/skripsi/finbert-lstm/manual",
    summary="Training Manual FinBERT-LSTM (SSE) — Model B, 1 konfigurasi fixed",
    response_description="Stream SSE: type start/epoch/done/error",
)
async def train_skripsi_finbert_manual(req: ManualTrainRequest) -> StreamingResponse:
    """Varian **Model B — FinBERT-LSTM** dari `POST /train/skripsi/ohlcv/manual`.
    Identik di semua aspek lain — hanya beda fitur (+`sentiment_mean`). Artefak
    disimpan ke `finbert_lstm_skripsi.*` (menimpa model resmi Model B)."""
    def work(emit: Callable[[dict], None]) -> None:
        training_service.run_skripsi_finbert_manual_stream(req, emit=emit)

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
