"""
app/schemas/training.py — Pydantic schemas untuk endpoint "Random Search
Skripsi-Scoped" (notebook 07, Batasan Masalah BAB I skripsi).

Event SSE (`start`/`iteration_start`/`epoch`/`iteration_end`/`done`/`error`)
sengaja TIDAK divalidasi lewat Pydantic model saat streaming (payload berupa
dict biasa) — skema di sini hanya dokumentatif untuk request body dan
endpoint hasil/prediksi/backtest (non-streaming, JSON biasa).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.prediction import BacktestPoint, ConfusionMatrix


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


class ManualTrainRequest(BaseModel):
    """Training 1-konfigurasi (fixed hyperparameter) — dipakai fitur "Training
    Manual" (input bebas) dan "Retrain dengan Best Config" (prefill dari hasil
    Random Search). Berbeda dari `SkripsiTrainRequest`: SEMUA hyperparameter
    wajib dikirim FE, TIDAK ada sampling/pencarian. Validasi hanya batas wajar
    (positif, dropout<1) — nilai TIDAK dibatasi ke pilihan diskrit search space
    Random Search (sesuai keputusan: input manual bersifat bebas)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "hidden_size": 64, "num_layers": 1, "dropout": 0.3,
                "optimizer": "adam", "activation": "relu", "lr": 0.001,
                "epochs": 30, "batch_size": 32,
            }
        }
    )

    hidden_size: int = Field(..., gt=0)
    num_layers: int = Field(..., gt=0)
    dropout: float = Field(..., ge=0, lt=1)
    optimizer: Literal["adam", "rmsprop", "sgd"]
    activation: Literal["relu", "tanh", "sigmoid"]
    lr: float = Field(..., gt=0)
    epochs: int = Field(..., gt=0)
    batch_size: int = Field(..., gt=0)


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
# Halaman Prediction — hasil Random Search skripsi-scoped (persisted) +
# prediksi + backtest. Model A (baseline, OHLCV) / Model B (finbert, OHLCV+
# sentimen).
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
                "eval_split": "val",
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
    threshold: float | None = None
    best_val_f1_macro: float | None = None
    best_val_f1: float | None = None
    best_val_acc: float | None = None
    eval_split: Literal["val", "test"] | None = None
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
