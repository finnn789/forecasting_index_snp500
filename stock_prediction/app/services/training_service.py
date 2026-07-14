"""app/services/training_service.py — Business logic untuk "API Training Live
Notebook 05" (varian OHLCV+sentiment_mean) dan varian OHLCV-only (ablation
study).

Di sinilah PERBEDAAN VARIAN ditentukan (feature_cols, loader data, nama
artefak) — masing-masing fungsi memilih parameter lalu memanggil
`run_notebook05_training()` (satu-satunya logic training, shared, di
`models/lstm/notebook05_common.py`) secara langsung.

Import LAZY (di dalam fungsi) agar torch tidak di-load saat module ini
di-import — konsisten dengan pola `prediction_service.py`.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from app.core.exceptions import NotFoundError
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


def get_grid_search_result() -> GridSearchResultResponse:
    """Kembalikan hasil grid-search 144 kombinasi (STATIS, hardcode dari
    notebook 05 — tidak dijalankan ulang)."""
    from models.lstm.notebook05_trainer import GRID_SEARCH_RESULT  # noqa: PLC0415

    return GridSearchResultResponse(**GRID_SEARCH_RESULT)


def run_training_stream(req: TrainRequest, emit: Callable[[dict], None]) -> None:
    """Varian OHLCV + sentiment_mean (existing, metodologi notebook 05).

    Dipanggil dari endpoint SSE — `run_notebook05_training()` sendiri sudah
    membungkus seluruh proses dalam try/except dan meng-emit event "error"
    bila gagal, jadi fungsi ini tidak perlu try/except tambahan.
    """
    from models.lstm.notebook05_common import run_notebook05_training  # noqa: PLC0415
    from models.lstm.notebook05_trainer import (  # noqa: PLC0415
        ARTIFACT_DIR,
        DEFAULT_CONFIG,
        METADATA_FILENAME,
        MODEL_FILENAME,
        SCALER_FILENAME,
    )
    from pipeline.feature_engineering.dataset_builder import FEATURE_COLS, load_joined  # noqa: PLC0415

    config = req.model_dump(exclude_none=True)
    run_notebook05_training(
        config=config,
        emit=emit,
        feature_cols=FEATURE_COLS,
        load_data_fn=load_joined,
        default_config=DEFAULT_CONFIG,
        artifact_dir=ARTIFACT_DIR,
        model_filename=MODEL_FILENAME,
        scaler_filename=SCALER_FILENAME,
        metadata_filename=METADATA_FILENAME,
    )


def run_training_stream_ohlcv(req: TrainRequest, emit: Callable[[dict], None]) -> None:
    """Varian OHLCV-only (ablation study — tanpa sentiment_mean).

    Reuse hyperparameter default hasil grid-search notebook 05 (`DEFAULT_CONFIG`)
    sebagai baseline — grid-search 5-fitur ini sendiri TIDAK pernah dijalankan
    ulang, sehingga ini adalah ablation yang terkontrol: satu-satunya variabel
    yang beda dari varian sentimen adalah ada/tidaknya fitur `sentiment_mean`.
    Artefak disimpan terisolasi dengan prefix `lstm_nb05_ohlcv_*`.
    """
    from models.lstm.notebook05_common import run_notebook05_training  # noqa: PLC0415
    from models.lstm.notebook05_trainer import ARTIFACT_DIR, DEFAULT_CONFIG  # noqa: PLC0415
    from pipeline.feature_engineering.dataset_builder import (  # noqa: PLC0415
        OHLCV_FEATURE_COLS,
        load_ohlcv_only,
    )

    config = req.model_dump(exclude_none=True)
    run_notebook05_training(
        config=config,
        emit=emit,
        feature_cols=OHLCV_FEATURE_COLS,
        load_data_fn=load_ohlcv_only,
        default_config=DEFAULT_CONFIG,
        artifact_dir=ARTIFACT_DIR,
        model_filename="lstm_nb05_ohlcv_best.pt",
        scaler_filename="lstm_nb05_ohlcv_scaler.joblib",
        metadata_filename="lstm_nb05_ohlcv_metadata.json",
    )


# ---------------------------------------------------------------------------
# Halaman Prediction — hasil training notebook05 (persisted) + prediksi +
# backtest, per varian (sentiment/ohlcv). Sama seperti run_training_stream*
# di atas, pemilihan varian (feature_cols/loader/nama artefak) ada di sini.
# ---------------------------------------------------------------------------

def _notebook05_variant_params(variant: Literal["sentiment", "ohlcv"]) -> dict:
    from models.lstm.notebook05_trainer import (  # noqa: PLC0415
        ARTIFACT_DIR,
        METADATA_FILENAME,
        MODEL_FILENAME,
        SCALER_FILENAME,
    )
    from pipeline.feature_engineering.dataset_builder import (  # noqa: PLC0415
        FEATURE_COLS,
        OHLCV_FEATURE_COLS,
        load_joined,
        load_ohlcv_only,
    )

    if variant == "sentiment":
        return {
            "feature_cols": FEATURE_COLS,
            "load_data_fn": load_joined,
            "artifact_dir": ARTIFACT_DIR,
            "model_filename": MODEL_FILENAME,
            "scaler_filename": SCALER_FILENAME,
            "metadata_filename": METADATA_FILENAME,
        }
    return {
        "feature_cols": OHLCV_FEATURE_COLS,
        "load_data_fn": load_ohlcv_only,
        "artifact_dir": ARTIFACT_DIR,
        "model_filename": "lstm_nb05_ohlcv_best.pt",
        "scaler_filename": "lstm_nb05_ohlcv_scaler.joblib",
        "metadata_filename": "lstm_nb05_ohlcv_metadata.json",
    }


def get_notebook05_result(variant: Literal["sentiment", "ohlcv"]) -> Notebook05ResultResponse:
    """Hasil training notebook05 yang sudah dipersist — SELALU 200,
    `is_available=False` kalau belum pernah training (mirror `ModelInfoResponse`)."""
    from models.lstm.notebook05_common import load_trained_notebook05  # noqa: PLC0415

    params = _notebook05_variant_params(variant)
    loaded = load_trained_notebook05(
        artifact_dir=params["artifact_dir"],
        model_filename=params["model_filename"],
        scaler_filename=params["scaler_filename"],
        metadata_filename=params["metadata_filename"],
    )
    if loaded is None:
        return Notebook05ResultResponse(is_available=False)

    meta = loaded["metadata"]
    return Notebook05ResultResponse(
        is_available=True,
        config=meta.get("config"),
        feature_cols=meta.get("feature_cols"),
        metrics=meta.get("metrics"),
        confusion_matrix=meta.get("confusion_matrix"),
        diagnosis=meta.get("diagnosis"),
        split_sizes=meta.get("split_sizes"),
        trained_at=meta.get("trained_at"),
        best_epoch=meta.get("best_epoch"),
        best_val_f2=meta.get("best_val_f2"),
    )


def predict_notebook05(variant: Literal["sentiment", "ohlcv"]) -> Notebook05PredictionResponse:
    """Prediksi arah harga hari berikutnya dari model notebook05 terlatih.

    Raises:
        NotFoundError: Jika model belum tersedia (belum dilatih) — endpoint ini
            genuinely tidak bisa jalan tanpa model, konsisten dgn pola
            `predict_direction()` produksi.
    """
    from models.lstm.notebook05_common import predict_latest_notebook05  # noqa: PLC0415

    params = _notebook05_variant_params(variant)
    result = predict_latest_notebook05(**params)
    if not result["trained"]:
        raise NotFoundError(
            "Model notebook05 belum tersedia. Latih model terlebih dahulu.",
            code="MODEL_NOT_TRAINED",
            detail=f"Artefak tidak ditemukan di {params['artifact_dir']}",
        )
    return Notebook05PredictionResponse(
        variant=variant,
        **{k: v for k, v in result.items() if k != "trained"},
    )


def backtest_notebook05(variant: Literal["sentiment", "ohlcv"], split: str = "test") -> Notebook05BacktestResponse:
    """Backtest model notebook05 terlatih pada split historis (default 'test').

    Raises:
        NotFoundError: Jika model belum tersedia (belum dilatih).
    """
    from models.lstm.notebook05_common import backtest_notebook05 as _backtest  # noqa: PLC0415

    params = _notebook05_variant_params(variant)
    result = _backtest(split=split, **params)
    if not result["trained"]:
        raise NotFoundError(
            "Model notebook05 belum tersedia. Latih model terlebih dahulu.",
            code="MODEL_NOT_TRAINED",
            detail=f"Artefak tidak ditemukan di {params['artifact_dir']}",
        )
    return Notebook05BacktestResponse(
        variant=variant,
        **{k: v for k, v in result.items() if k != "trained"},
    )


# ---------------------------------------------------------------------------
# "Random Search Skripsi-Scoped" (notebook 07, Batasan Masalah BAB I) —
# Model A (baseline, OHLCV saja) & Model B (FinBERT-LSTM, OHLCV+sentiment_mean).
# ---------------------------------------------------------------------------

def get_skripsi_search_space() -> SearchSpaceResponse:
    """Info statis search space Random Search (notebook 07) — TIDAK ada hasil
    statis seperti grid-search notebook 05, karena Random Search dijalankan LIVE."""
    from models.lstm.notebook07_trainer import N_ITER, SEARCH_SPACE, WINDOW  # noqa: PLC0415

    return SearchSpaceResponse(
        hidden_size=SEARCH_SPACE["hidden_size"],
        num_layers=SEARCH_SPACE["num_layers"],
        dropout_range=list(SEARCH_SPACE["dropout"]),
        optimizer=SEARCH_SPACE["optimizer"],
        activation=SEARCH_SPACE["activation"],
        lr_range=list(SEARCH_SPACE["lr"]),
        epochs=SEARCH_SPACE["epochs"],
        batch_size=SEARCH_SPACE["batch_size"],
        n_iter=N_ITER,
        window=WINDOW,
    )


def run_skripsi_baseline_stream(req: SkripsiTrainRequest, emit: Callable[[dict], None]) -> None:
    """Model A — LSTM-OHLCV baseline (skripsi-scoped, hanya 5 fitur OHLCV,
    TANPA sentiment_mean). Capping outlier: Volume saja (OHLC = 0 outlier,
    lihat EDA notebook 07)."""
    from models.lstm.notebook07_common import run_notebook07_training  # noqa: PLC0415
    from models.lstm.notebook07_trainer import (  # noqa: PLC0415
        ARTIFACT_DIR,
        BASELINE_FILES,
        N_ITER,
        SEARCH_SPACE,
        WINDOW,
    )
    from pipeline.feature_engineering.dataset_builder import (  # noqa: PLC0415
        OHLCV_FEATURE_COLS,
        load_ohlcv_only,
    )

    n_iter = req.n_iter if req.n_iter is not None else N_ITER
    run_notebook07_training(
        emit=emit,
        feature_cols=OHLCV_FEATURE_COLS,
        load_data_fn=load_ohlcv_only,
        capping_cols=["Volume"],
        search_space=SEARCH_SPACE,
        n_iter=n_iter,
        window=WINDOW,
        artifact_dir=ARTIFACT_DIR,
        model_filename=BASELINE_FILES["model"],
        scaler_filename=BASELINE_FILES["scaler"],
        metadata_filename=BASELINE_FILES["metadata"],
    )


def run_skripsi_finbert_stream(req: SkripsiTrainRequest, emit: Callable[[dict], None]) -> None:
    """Model B — FinBERT-LSTM (skripsi-scoped, 6 fitur OHLCV+sentiment_mean).
    Capping outlier: Volume & sentiment_mean."""
    from models.lstm.notebook07_common import run_notebook07_training  # noqa: PLC0415
    from models.lstm.notebook07_trainer import (  # noqa: PLC0415
        ARTIFACT_DIR,
        FINBERT_FILES,
        N_ITER,
        SEARCH_SPACE,
        WINDOW,
    )
    from pipeline.feature_engineering.dataset_builder import FEATURE_COLS, load_joined  # noqa: PLC0415

    n_iter = req.n_iter if req.n_iter is not None else N_ITER
    run_notebook07_training(
        emit=emit,
        feature_cols=FEATURE_COLS,
        load_data_fn=load_joined,
        capping_cols=["Volume", "sentiment_mean"],
        search_space=SEARCH_SPACE,
        n_iter=n_iter,
        window=WINDOW,
        artifact_dir=ARTIFACT_DIR,
        model_filename=FINBERT_FILES["model"],
        scaler_filename=FINBERT_FILES["scaler"],
        metadata_filename=FINBERT_FILES["metadata"],
    )


# ---------------------------------------------------------------------------
# Halaman Prediction — hasil Random Search skripsi-scoped (persisted) +
# prediksi + backtest, per varian (baseline/finbert). Sama seperti
# run_skripsi_*_stream di atas, pemilihan varian ada di sini.
# ---------------------------------------------------------------------------

def _notebook07_variant_params(variant: Literal["baseline", "finbert"]) -> dict:
    from models.lstm.notebook07_trainer import (  # noqa: PLC0415
        ARTIFACT_DIR,
        BASELINE_FILES,
        FINBERT_FILES,
    )
    from pipeline.feature_engineering.dataset_builder import (  # noqa: PLC0415
        FEATURE_COLS,
        OHLCV_FEATURE_COLS,
        load_joined,
        load_ohlcv_only,
    )

    if variant == "baseline":
        return {
            "feature_cols": OHLCV_FEATURE_COLS,
            "load_data_fn": load_ohlcv_only,
            "capping_cols": ["Volume"],
            "artifact_dir": ARTIFACT_DIR,
            "model_filename": BASELINE_FILES["model"],
            "scaler_filename": BASELINE_FILES["scaler"],
            "metadata_filename": BASELINE_FILES["metadata"],
        }
    return {
        "feature_cols": FEATURE_COLS,
        "load_data_fn": load_joined,
        "capping_cols": ["Volume", "sentiment_mean"],
        "artifact_dir": ARTIFACT_DIR,
        "model_filename": FINBERT_FILES["model"],
        "scaler_filename": FINBERT_FILES["scaler"],
        "metadata_filename": FINBERT_FILES["metadata"],
    }


def get_notebook07_result(variant: Literal["baseline", "finbert"]) -> Notebook07ResultResponse:
    """Hasil Random Search terakhir yang sudah dipersist — SELALU 200,
    `is_available=False` kalau belum pernah training."""
    from models.lstm.notebook07_common import load_trained_notebook07  # noqa: PLC0415

    params = _notebook07_variant_params(variant)
    loaded = load_trained_notebook07(
        artifact_dir=params["artifact_dir"],
        model_filename=params["model_filename"],
        scaler_filename=params["scaler_filename"],
        metadata_filename=params["metadata_filename"],
    )
    if loaded is None:
        return Notebook07ResultResponse(is_available=False)

    meta = loaded["metadata"]
    return Notebook07ResultResponse(
        is_available=True,
        config=meta.get("config"),
        feature_cols=meta.get("feature_cols"),
        window=meta.get("window"),
        metrics=meta.get("metrics"),
        confusion_matrix=meta.get("confusion_matrix"),
        best_val_f1=meta.get("best_val_f1"),
        best_val_acc=meta.get("best_val_acc"),
        split_sizes=meta.get("split_sizes"),
        trained_at=meta.get("trained_at"),
    )


def predict_notebook07(variant: Literal["baseline", "finbert"]) -> Notebook07PredictionResponse:
    """Prediksi arah harga hari berikutnya dari model Random Search terlatih.

    Raises:
        NotFoundError: Jika model belum tersedia (belum dilatih).
    """
    from models.lstm.notebook07_common import predict_latest_notebook07  # noqa: PLC0415

    params = _notebook07_variant_params(variant)
    result = predict_latest_notebook07(**params)
    if not result["trained"]:
        raise NotFoundError(
            "Model Random Search belum tersedia. Latih model terlebih dahulu.",
            code="MODEL_NOT_TRAINED",
            detail=f"Artefak tidak ditemukan di {params['artifact_dir']}",
        )
    return Notebook07PredictionResponse(
        variant=variant,
        **{k: v for k, v in result.items() if k != "trained"},
    )


def backtest_notebook07(variant: Literal["baseline", "finbert"], split: str = "test") -> Notebook07BacktestResponse:
    """Backtest model Random Search terlatih pada split historis (default 'test').

    Raises:
        NotFoundError: Jika model belum tersedia (belum dilatih).
    """
    from models.lstm.notebook07_common import backtest_notebook07 as _backtest  # noqa: PLC0415

    params = _notebook07_variant_params(variant)
    result = _backtest(split=split, **params)
    if not result["trained"]:
        raise NotFoundError(
            "Model Random Search belum tersedia. Latih model terlebih dahulu.",
            code="MODEL_NOT_TRAINED",
            detail=f"Artefak tidak ditemukan di {params['artifact_dir']}",
        )
    return Notebook07BacktestResponse(
        variant=variant,
        **{k: v for k, v in result.items() if k != "trained"},
    )
