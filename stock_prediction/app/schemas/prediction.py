"""
app/schemas/prediction.py — Pydantic schemas untuk endpoint prediksi.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Backtest schemas
# ---------------------------------------------------------------------------


class BacktestPoint(BaseModel):
    """Satu titik data hasil backtest: tanggal, harga close, prediksi vs aktual."""

    date: str
    close: float
    actual_direction: Literal["up", "down"]
    predicted_direction: Literal["up", "down"]
    probability_up: float = Field(..., ge=0, le=1)
    correct: bool


class ConfusionMatrix(BaseModel):
    """Confusion matrix klasifikasi biner dengan kelas positif = 'up'."""

    tp: int
    tn: int
    fp: int
    fn: int


class BacktestResponse(BaseModel):
    """Hasil backtest model LSTM pada data historis."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ticker": "GSPC",
                "window": 20,
                "split": "test",
                "n_samples": 46,
                "metrics": {
                    "accuracy": 0.61,
                    "precision": 0.76,
                    "recall": 0.97,
                    "f1": 0.85,
                    "auc": 0.38,
                },
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

    ticker: str
    window: int
    split: str
    n_samples: int
    metrics: dict
    confusion_matrix: ConfusionMatrix
    points: list[BacktestPoint]


class PredictionRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ticker": "GSPC",
            }
        }
    )

    ticker: str = "GSPC"


class DirectionPredictionResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ticker": "GSPC",
                "as_of_date": "2024-03-01",
                "target_date": "2024-03-04",
                "direction": "up",
                "probability_up": 0.67,
                "confidence": 0.67,
                "window": 20,
                "features_used": [
                    "Open",
                    "High",
                    "Low",
                    "Close",
                    "Volume",
                    "sentiment_mean",
                ],
                "model_version": "2024-03-01T00:00:00",
            }
        }
    )

    ticker: str
    as_of_date: str
    target_date: str
    direction: Literal["up", "down"]
    probability_up: float = Field(..., ge=0, le=1)
    confidence: float = Field(..., ge=0, le=1)  # max(p, 1-p)
    window: int
    features_used: list[str]
    model_version: str | None = None


class ModelInfoResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_available": True,
                "artifact_path": "data/artifacts/lstm_weights",
                "window": 20,
                "features_used": [
                    "Open",
                    "High",
                    "Low",
                    "Close",
                    "Volume",
                    "sentiment_mean",
                ],
                "n_features": 6,
                "metrics": {
                    "val_acc": 0.58,
                    "val_f1": 0.57,
                    "val_auc": 0.61,
                    "test_acc": 0.56,
                    "test_f1": 0.55,
                    "test_auc": 0.60,
                },
                "trained_at": "2024-03-01T00:00:00",
            }
        }
    )

    is_available: bool
    artifact_path: str
    window: int | None = None
    features_used: list[str] = []
    n_features: int | None = None
    metrics: dict | None = None
    trained_at: str | None = None
