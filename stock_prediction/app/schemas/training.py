"""
app/schemas/training.py — Pydantic schemas untuk endpoint "API Training Live
Notebook 05" (training final LSTM terisolasi + hasil grid-search statis).

Event SSE (`start`/`epoch`/`done`/`error`) sengaja TIDAK divalidasi lewat
Pydantic model saat streaming (payload berupa dict biasa, lihat
models/lstm/notebook05_trainer.py) — skema di sini hanya dokumentatif untuk
request body dan endpoint grid-search-result (non-streaming, JSON biasa).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.prediction import BacktestPoint, ConfusionMatrix


# ---------------------------------------------------------------------------
# Request: POST /api/v1/train/notebook05
# ---------------------------------------------------------------------------

class TrainRequest(BaseModel):
    """Override hyperparameter training final. Semua opsional — default =
    best config hasil grid-search 144 kombinasi (notebook 05, §1.3)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "seq_len": 20,
                "hidden_size": 64,
                "num_layers": 2,
                "dropout": 0.4,
                "lr": 0.0005,
                "batch_size": 64,
                "epochs": 150,
                "early_stop": 30,
            }
        }
    )

    seq_len: int | None = None
    hidden_size: int | None = None
    num_layers: int | None = None
    dropout: float | None = None
    lr: float | None = None
    batch_size: int | None = None
    epochs: int | None = None
    early_stop: int | None = None


# ---------------------------------------------------------------------------
# Response: GET /api/v1/train/notebook05/grid-search-result
# ---------------------------------------------------------------------------

class GridConfigRow(BaseModel):
    """Satu baris konfigurasi hasil grid-search (statis, hardcode dari notebook)."""

    seq_len: int
    hidden_size: int
    num_layers: int
    dropout: float
    lr: float
    batch_size: int
    epochs: int
    early_stop: int
    val_f2: float


class BestConfig(BaseModel):
    """Konfigurasi terbaik — dipakai sebagai default training final
    (epochs/early_stop berbeda dari top_configs karena fase final vs
    grid-search, lihat catatan di notebook05_trainer.py)."""

    seq_len: int
    hidden_size: int
    num_layers: int
    dropout: float
    lr: float
    batch_size: int
    epochs: int
    early_stop: int


class GridSearchResultResponse(BaseModel):
    """Hasil grid-search 144 kombinasi (STATIS, hardcode — TIDAK dijalankan
    ulang server-side)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_combinations": 144,
                "best_val_f2": 0.811037,
                "best_config": {
                    "seq_len": 20,
                    "hidden_size": 64,
                    "num_layers": 2,
                    "dropout": 0.4,
                    "lr": 0.0005,
                    "batch_size": 64,
                    "epochs": 150,
                    "early_stop": 30,
                },
                "top_configs": [],
            }
        }
    )

    total_combinations: int
    best_val_f2: float
    best_config: BestConfig
    top_configs: list[GridConfigRow] = Field(
        description="Top 10 konfigurasi hasil grid-search, diurutkan val_f2 desc"
    )


# ---------------------------------------------------------------------------
# "Random Search Skripsi-Scoped" (notebook 07, Batasan Masalah BAB I) —
# POST /api/v1/train/skripsi/{ohlcv,finbert-lstm}, GET .../search-space
# ---------------------------------------------------------------------------

class SkripsiTrainRequest(BaseModel):
    """Override jumlah iterasi Random Search. Search space & window TIDAK
    dibuat configurable dari FE — tetap sesuai Batasan Masalah BAB I skripsi
    (lihat models/lstm/notebook07_trainer.py). Default n_iter = 20."""

    model_config = ConfigDict(json_schema_extra={"example": {"n_iter": 20}})

    n_iter: int | None = None


class SearchSpaceResponse(BaseModel):
    """Info statis search space Random Search (notebook 07, skripsi-scoped) —
    ditampilkan di FE sebagai kartu info, BUKAN hasil training (Random Search
    dijalankan LIVE, tidak ada hasil statis seperti grid-search notebook 05)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "hidden_size": [16, 32, 64, 128],
                "num_layers": [1, 2],
                "dropout_range": [0.2, 0.5],
                "optimizer": ["adam", "rmsprop", "sgd"],
                "activation": ["relu", "tanh", "sigmoid"],
                "lr_range": [0.0001, 0.01],
                "epochs": [30, 50, 80],
                "batch_size": [16, 32, 64],
                "n_iter": 20,
                "window": 10,
            }
        }
    )

    hidden_size: list[int]
    num_layers: list[int]
    dropout_range: list[float]
    optimizer: list[str]
    activation: list[str]
    lr_range: list[float]
    epochs: list[int]
    batch_size: list[int]
    n_iter: int
    window: int


# ---------------------------------------------------------------------------
# Halaman Prediction — hasil training notebook05 (persisted) + prediksi +
# backtest. Selaras dgn 2 varian training di atas (sentimen/ohlcv).
# ---------------------------------------------------------------------------

class Notebook05ResultResponse(BaseModel):
    """Hasil training notebook05 (varian sentimen/ohlcv) yang sudah dipersist
    di metadata.json — SELALU HTTP 200 (mirror `ModelInfoResponse` produksi),
    `is_available=False` kalau belum pernah training (BUKAN 404)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_available": True,
                "config": {"seq_len": 20, "hidden_size": 64},
                "feature_cols": ["Open", "High", "Low", "Close", "Volume", "sentiment_mean"],
                "metrics": {"accuracy": 0.62, "precision": 0.76, "recall": 1.0, "f1": 0.86, "f2": 0.93},
                "confusion_matrix": {"tp": 34, "tn": 0, "fp": 11, "fn": 0},
                "diagnosis": {
                    "overfitting": False,
                    "underfitting": False,
                    "fit_status": "GOOD_FIT",
                    "class_collapse": {"train": True, "val": True, "test": True},
                    "any_collapse": True,
                },
                "split_sizes": {
                    "train_rows": 1068, "val_rows": 229, "test_rows": 230,
                    "train_samples": 1058, "val_samples": 219, "test_samples": 220,
                },
                "trained_at": "2026-07-12T00:00:00+00:00",
                "best_epoch": 12,
                "best_val_f2": 0.8110,
            }
        }
    )

    is_available: bool
    config: dict | None = None
    feature_cols: list[str] | None = None
    metrics: dict | None = None
    confusion_matrix: dict | None = None
    diagnosis: dict | None = None
    split_sizes: dict | None = None
    trained_at: str | None = None
    best_epoch: int | None = None
    best_val_f2: float | None = None


class Notebook05PredictionResponse(BaseModel):
    """Prediksi arah harga hari berikutnya dari model notebook05 terlatih
    (varian sentimen/ohlcv), mirror `DirectionPredictionResponse` produksi."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "variant": "sentiment",
                "as_of_date": "2024-03-01",
                "target_date": "2024-03-02",
                "direction": "up",
                "probability_up": 0.67,
                "confidence": 0.67,
                "window": 20,
                "feature_cols": ["Open", "High", "Low", "Close", "Volume", "sentiment_mean"],
                "trained_at": "2026-07-12T00:00:00+00:00",
                "best_val_f2": 0.8110,
            }
        }
    )

    variant: Literal["sentiment", "ohlcv"]
    as_of_date: str
    target_date: str
    direction: Literal["up", "down"]
    probability_up: float = Field(..., ge=0, le=1)
    confidence: float = Field(..., ge=0, le=1)
    window: int
    feature_cols: list[str]
    trained_at: str | None = None
    best_val_f2: float | None = None


class Notebook05BacktestResponse(BaseModel):
    """Backtest model notebook05 terlatih (varian sentimen/ohlcv) pada data
    historis — mirror `BacktestResponse` produksi, reuse `BacktestPoint`/
    `ConfusionMatrix` (bentuknya identik)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "variant": "sentiment",
                "window": 20,
                "split": "test",
                "n_samples": 220,
                "metrics": {"accuracy": 0.61, "precision": 0.76, "recall": 0.97, "f1": 0.85, "auc": 0.52},
                "confusion_matrix": {"tp": 34, "tn": 0, "fp": 11, "fn": 1},
                "points": [
                    {
                        "date": "2024-01-19",
                        "close": 4839.81,
                        "actual_direction": "up",
                        "predicted_direction": "up",
                        "probability_up": 0.72,
                        "correct": True,
                    }
                ],
            }
        }
    )

    variant: Literal["sentiment", "ohlcv"]
    window: int
    split: str
    n_samples: int
    metrics: dict
    confusion_matrix: ConfusionMatrix
    points: list[BacktestPoint]


# ---------------------------------------------------------------------------
# Halaman Prediction — hasil Random Search skripsi-scoped (persisted) +
# prediksi + backtest. Model A (baseline, OHLCV) / Model B (finbert, OHLCV+
# sentimen). Field BEDA dari Notebook05*Response (tidak ada diagnosis/best_epoch,
# ada window/best_val_acc) — sengaja TIDAK reuse schema notebook05.
# ---------------------------------------------------------------------------

class Notebook07ResultResponse(BaseModel):
    """Hasil Random Search terakhir (persisted di metadata.json) — SELALU
    HTTP 200, `is_available=False` kalau belum pernah training (BUKAN 404)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_available": True,
                "config": {
                    "hidden_size": 64, "num_layers": 1, "dropout": 0.4576,
                    "optimizer": "adam", "activation": "sigmoid", "lr": 0.00353,
                    "epochs": 30, "batch_size": 16,
                },
                "feature_cols": ["Open", "High", "Low", "Close", "Volume"],
                "window": 10,
                "metrics": {"accuracy": 0.56, "precision": 0.56, "recall": 1.0, "f1": 0.717949},
                "confusion_matrix": {"tn": 0, "fp": 99, "fn": 0, "tp": 126},
                "best_val_f1": 0.619195,
                "best_val_acc": 0.44843,
                "split_sizes": {
                    "train_rows": 1085, "val_rows": 232, "test_rows": 234,
                    "train_samples": 1076, "val_samples": 223, "test_samples": 225,
                },
                "trained_at": "2026-07-14T13:06:56.717767+00:00",
            }
        }
    )

    is_available: bool
    config: dict | None = None
    feature_cols: list[str] | None = None
    window: int | None = None
    metrics: dict | None = None
    confusion_matrix: dict | None = None
    best_val_f1: float | None = None
    best_val_acc: float | None = None
    split_sizes: dict | None = None
    trained_at: str | None = None


class Notebook07PredictionResponse(BaseModel):
    """Prediksi arah harga hari berikutnya dari model Random Search terlatih
    (Model A: baseline / Model B: finbert)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "variant": "baseline",
                "as_of_date": "2024-03-01",
                "target_date": "2024-03-02",
                "direction": "up",
                "probability_up": 0.55,
                "confidence": 0.55,
                "window": 10,
                "feature_cols": ["Open", "High", "Low", "Close", "Volume"],
                "trained_at": "2026-07-14T13:06:56.717767+00:00",
                "best_val_f1": 0.619195,
            }
        }
    )

    variant: Literal["baseline", "finbert"]
    as_of_date: str
    target_date: str
    direction: Literal["up", "down"]
    probability_up: float = Field(..., ge=0, le=1)
    confidence: float = Field(..., ge=0, le=1)
    window: int
    feature_cols: list[str]
    trained_at: str | None = None
    best_val_f1: float | None = None


class Notebook07BacktestResponse(BaseModel):
    """Backtest model Random Search terlatih pada data historis — HANYA 4
    metrik (accuracy/precision/recall/f1) sesuai Batasan Masalah BAB I, reuse
    `BacktestPoint`/`ConfusionMatrix` (bentuknya identik notebook05)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "variant": "baseline",
                "window": 10,
                "split": "test",
                "n_samples": 225,
                "metrics": {"accuracy": 0.56, "precision": 0.56, "recall": 1.0, "f1": 0.717949},
                "confusion_matrix": {"tp": 126, "tn": 0, "fp": 99, "fn": 0},
                "points": [
                    {
                        "date": "2024-01-19",
                        "close": 4839.81,
                        "actual_direction": "up",
                        "predicted_direction": "up",
                        "probability_up": 0.55,
                        "correct": True,
                    }
                ],
            }
        }
    )

    variant: Literal["baseline", "finbert"]
    window: int
    split: str
    n_samples: int
    metrics: dict
    confusion_matrix: ConfusionMatrix
    points: list[BacktestPoint]
