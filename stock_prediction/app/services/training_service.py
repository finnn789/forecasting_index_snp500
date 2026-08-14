"""app/services/training_service.py — Business logic untuk "Random Search
Skripsi-Scoped" (notebook 07, Batasan Masalah BAB I) — Model A (baseline,
OHLCV saja) & Model B (FinBERT-LSTM, OHLCV+sentiment_mean).

Import LAZY (di dalam fungsi) agar torch tidak di-load saat module ini
di-import — konsisten dengan pola `prediction_service.py`.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from app.core.exceptions import NotFoundError
from app.schemas.training import (
    ManualTrainRequest,
    Notebook07BacktestResponse,
    Notebook07PredictionResponse,
    Notebook07ResultResponse,
    SearchSpaceResponse,
    SkripsiTrainRequest,
)


# ---------------------------------------------------------------------------
# "Random Search Skripsi-Scoped" (notebook 07, Batasan Masalah BAB I) —
# Model A (baseline, OHLCV saja) & Model B (FinBERT-LSTM, OHLCV+sentiment_mean).
#
# Training MEMBACA dataset artifact (dibangun tombol "Bangun Dataset Latih" di
# halaman Workflow, `data_analysis_service.build_combined_dataset()`) — TIDAK
# lagi recompute dari raw CSV sendiri. Kalau artifact belum ada/basi, training
# dibatalkan sebelum sempat mulai (emit "error" dgn pesan jelas), supaya user
# tidak diam-diam melatih model dari data usang. Arsitektur "Data Provider":
# Workflow = satu-satunya sumber dataset siap-latih untuk training_service ini.
# ---------------------------------------------------------------------------

def _require_dataset_bundle(
    variant: Literal["baseline", "finbert"],
    split_mode: Literal["random_search", "manual"],
    emit: Callable[[dict], None],
):
    from models.lstm.notebook07_common import dataset_bundle_status, load_dataset_bundle  # noqa: PLC0415
    from models.lstm.notebook07_trainer import DATASET_ARTIFACT_DIR, dataset_prefix  # noqa: PLC0415

    prefix = dataset_prefix(variant, split_mode)
    status = dataset_bundle_status(DATASET_ARTIFACT_DIR, prefix)

    if not status["exists"]:
        emit({
            "type": "error",
            "message": (
                f"Dataset latih ({variant}/{split_mode}) belum dibangun. "
                "Klik 'Bangun Dataset Latih' di halaman Workflow terlebih dahulu."
            ),
        })
        return None
    if not status["is_fresh"]:
        emit({
            "type": "error",
            "message": (
                f"Dataset latih ({variant}/{split_mode}) basi — data sumber "
                "(headlines_daily_sentiment.csv atau GSPC_*.csv) berubah sejak "
                "dataset ini dibangun. Bangun ulang dataset di halaman Workflow "
                "sebelum training."
            ),
        })
        return None
    return load_dataset_bundle(DATASET_ARTIFACT_DIR, prefix)


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
    """Model A — LSTM-return baseline (skripsi-scoped, 5 fitur RETURN
    OHLCV — pct_change, TANPA sentiment_mean). Capping outlier: SEMUA kolom
    fitur (bukan cuma Volume) — lihat `load_return_features()`. Horizon=5
    (BUKAN 1) & seleksi F1-macro+threshold — deviasi Batasan Masalah BAB I
    disengaja per keputusan user 2026-07-28 (notebook 12), lihat CLAUDE.md.
    Baca dataset dari artifact (dibangun di Workflow) — lihat
    `_require_dataset_bundle()`."""
    from models.lstm.notebook07_common import run_notebook07_training  # noqa: PLC0415
    from models.lstm.notebook07_trainer import (  # noqa: PLC0415
        ARTIFACT_DIR,
        BASELINE_FILES,
        N_ITER,
        RETURN_HORIZON,
        SEARCH_SPACE,
        WINDOW,
    )
    from pipeline.feature_engineering.dataset_builder import (  # noqa: PLC0415
        RETURN_FEATURE_COLS_A,
        load_return_features,
    )

    bundle = _require_dataset_bundle("baseline", "random_search", emit)
    if bundle is None:
        return

    n_iter = req.n_iter if req.n_iter is not None else N_ITER
    seed = req.seed if req.seed is not None else 42
    run_notebook07_training(
        emit=emit,
        feature_cols=RETURN_FEATURE_COLS_A,
        load_data_fn=load_return_features,
        capping_cols=RETURN_FEATURE_COLS_A,
        search_space=SEARCH_SPACE,
        n_iter=n_iter,
        window=WINDOW,
        artifact_dir=ARTIFACT_DIR,
        model_filename=BASELINE_FILES["model"],
        scaler_filename=BASELINE_FILES["scaler"],
        metadata_filename=BASELINE_FILES["metadata"],
        horizon=RETURN_HORIZON,
        seed=seed,
        prebuilt_dataset=bundle,
    )


def run_skripsi_finbert_stream(req: SkripsiTrainRequest, emit: Callable[[dict], None]) -> None:
    """Model B — FinBERT-LSTM-return (skripsi-scoped, 6 fitur RETURN
    OHLCV+sentiment_mean). Capping outlier: SEMUA kolom fitur. Horizon=5 &
    seleksi F1-macro+threshold — sama deviasi seperti Model A, lihat docstring
    `run_skripsi_baseline_stream`. Baca dataset dari artifact — lihat
    `_require_dataset_bundle()`."""
    from models.lstm.notebook07_common import run_notebook07_training  # noqa: PLC0415
    from models.lstm.notebook07_trainer import (  # noqa: PLC0415
        ARTIFACT_DIR,
        FINBERT_FILES,
        N_ITER,
        RETURN_HORIZON,
        SEARCH_SPACE,
        WINDOW,
    )
    from pipeline.feature_engineering.dataset_builder import (  # noqa: PLC0415
        RETURN_FEATURE_COLS_B,
        load_return_features,
    )

    bundle = _require_dataset_bundle("finbert", "random_search", emit)
    if bundle is None:
        return

    n_iter = req.n_iter if req.n_iter is not None else N_ITER
    seed = req.seed if req.seed is not None else 42
    run_notebook07_training(
        emit=emit,
        feature_cols=RETURN_FEATURE_COLS_B,
        load_data_fn=load_return_features,
        capping_cols=RETURN_FEATURE_COLS_B,
        search_space=SEARCH_SPACE,
        n_iter=n_iter,
        window=WINDOW,
        artifact_dir=ARTIFACT_DIR,
        model_filename=FINBERT_FILES["model"],
        scaler_filename=FINBERT_FILES["scaler"],
        metadata_filename=FINBERT_FILES["metadata"],
        horizon=RETURN_HORIZON,
        seed=seed,
        prebuilt_dataset=bundle,
    )


# ---------------------------------------------------------------------------
# Training Manual (1-konfigurasi, fixed hyperparameter) — dipakai fitur
# "Training Manual" (input bebas) & "Retrain dengan Best Config" FE. Parameter
# varian (feature_cols/loader/capping/artifact filenames) SAMA PERSIS dengan
# run_skripsi_*_stream di atas — sengaja menimpa artefak resmi varian tsb.
# ---------------------------------------------------------------------------

def run_skripsi_baseline_manual_stream(req: ManualTrainRequest, emit: Callable[[dict], None]) -> None:
    """Training manual Model A — LSTM-return baseline (5 fitur RETURN OHLCV,
    horizon=5 — sama preprocessing dengan `run_skripsi_baseline_stream`).
    Split Train:Test dihitung LIVE sesuai `req.train_ratio` (0.6/0.7/0.8) —
    TIDAK lagi baca artifact Workflow (`_require_dataset_bundle`), karena
    preprocessing-nya ringan dan training manual butuh rasio fleksibel."""
    from models.lstm.notebook07_common import run_notebook07_manual_training  # noqa: PLC0415
    from models.lstm.notebook07_trainer import (  # noqa: PLC0415
        ARTIFACT_DIR,
        BASELINE_FILES,
        RETURN_HORIZON,
        WINDOW,
    )
    from pipeline.feature_engineering.dataset_builder import (  # noqa: PLC0415
        RETURN_FEATURE_COLS_A,
        load_return_features,
    )

    seed = req.seed if req.seed is not None else 42
    run_notebook07_manual_training(
        emit=emit,
        config=req.model_dump(exclude={"train_ratio", "seed"}),
        feature_cols=RETURN_FEATURE_COLS_A,
        load_data_fn=load_return_features,
        capping_cols=RETURN_FEATURE_COLS_A,
        window=WINDOW,
        artifact_dir=ARTIFACT_DIR,
        model_filename=BASELINE_FILES["model"],
        scaler_filename=BASELINE_FILES["scaler"],
        metadata_filename=BASELINE_FILES["metadata"],
        horizon=RETURN_HORIZON,
        seed=seed,
        train_ratio=req.train_ratio,
    )


def run_skripsi_finbert_manual_stream(req: ManualTrainRequest, emit: Callable[[dict], None]) -> None:
    """Training manual Model B — FinBERT-LSTM-return (6 fitur RETURN
    OHLCV+sentiment_mean, horizon=5 — sama preprocessing dengan
    `run_skripsi_finbert_stream`). Split Train:Test dihitung LIVE sesuai
    `req.train_ratio` (0.6/0.7/0.8) — TIDAK lagi baca artifact Workflow."""
    from models.lstm.notebook07_common import run_notebook07_manual_training  # noqa: PLC0415
    from models.lstm.notebook07_trainer import (  # noqa: PLC0415
        ARTIFACT_DIR,
        FINBERT_FILES,
        RETURN_HORIZON,
        WINDOW,
    )
    from pipeline.feature_engineering.dataset_builder import (  # noqa: PLC0415
        RETURN_FEATURE_COLS_B,
        load_return_features,
    )

    seed = req.seed if req.seed is not None else 42
    run_notebook07_manual_training(
        emit=emit,
        config=req.model_dump(exclude={"train_ratio", "seed"}),
        feature_cols=RETURN_FEATURE_COLS_B,
        load_data_fn=load_return_features,
        capping_cols=RETURN_FEATURE_COLS_B,
        window=WINDOW,
        artifact_dir=ARTIFACT_DIR,
        model_filename=FINBERT_FILES["model"],
        scaler_filename=FINBERT_FILES["scaler"],
        metadata_filename=FINBERT_FILES["metadata"],
        horizon=RETURN_HORIZON,
        seed=seed,
        train_ratio=req.train_ratio,
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
        RETURN_HORIZON,
    )
    from pipeline.feature_engineering.dataset_builder import (  # noqa: PLC0415
        RETURN_FEATURE_COLS_A,
        RETURN_FEATURE_COLS_B,
        load_return_features,
    )

    if variant == "baseline":
        return {
            "feature_cols": RETURN_FEATURE_COLS_A,
            "load_data_fn": load_return_features,
            "capping_cols": RETURN_FEATURE_COLS_A,
            "artifact_dir": ARTIFACT_DIR,
            "model_filename": BASELINE_FILES["model"],
            "scaler_filename": BASELINE_FILES["scaler"],
            "metadata_filename": BASELINE_FILES["metadata"],
            "horizon": RETURN_HORIZON,
        }
    return {
        "feature_cols": RETURN_FEATURE_COLS_B,
        "load_data_fn": load_return_features,
        "capping_cols": RETURN_FEATURE_COLS_B,
        "artifact_dir": ARTIFACT_DIR,
        "model_filename": FINBERT_FILES["model"],
        "scaler_filename": FINBERT_FILES["scaler"],
        "metadata_filename": FINBERT_FILES["metadata"],
        "horizon": RETURN_HORIZON,
    }


def get_notebook07_result(variant: Literal["baseline", "finbert"]) -> Notebook07ResultResponse:
    """Hasil Random Search terakhir yang sudah dipersist — SELALU 200,
    `is_available=False` kalau belum pernah training."""
    from models.lstm.notebook07_common import load_last_prediction, load_trained_notebook07  # noqa: PLC0415

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
        threshold=meta.get("threshold"),
        best_val_f1_macro=meta.get("best_val_f1_macro"),
        best_val_f1=meta.get("best_val_f1"),
        best_val_acc=meta.get("best_val_acc"),
        eval_split=meta.get("eval_split", "val"),
        split_sizes=meta.get("split_sizes"),
        trained_at=meta.get("trained_at"),
        seed=meta.get("seed"),
        last_prediction=load_last_prediction(
            artifact_dir=params["artifact_dir"],
            metadata_filename=params["metadata_filename"],
        ),
    )


def predict_notebook07(variant: Literal["baseline", "finbert"]) -> Notebook07PredictionResponse:
    """Prediksi arah harga hari berikutnya dari model Random Search terlatih.

    Raises:
        NotFoundError: Jika model belum tersedia (belum dilatih).
    """
    from models.lstm.notebook07_common import predict_latest_notebook07, save_last_prediction  # noqa: PLC0415

    params = _notebook07_variant_params(variant)
    result = predict_latest_notebook07(**params)
    if not result["trained"]:
        raise NotFoundError(
            "Model Random Search belum tersedia. Latih model terlebih dahulu.",
            code="MODEL_NOT_TRAINED",
            detail=f"Artefak tidak ditemukan di {params['artifact_dir']}",
        )
    save_last_prediction(
        result,
        artifact_dir=params["artifact_dir"],
        metadata_filename=params["metadata_filename"],
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
