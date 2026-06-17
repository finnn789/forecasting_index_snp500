# Kontrak Modul — Model Klasifikasi Arah Harga (Sentiment + OHLCV)

> Dokumen kontrak yang WAJIB diikuti semua agent swarm. Tujuan: modul saling
> nyambung tanpa integrasi ulang. Jangan mengubah signature di bawah tanpa
> memberi tahu koordinator.

## Keputusan Desain (final, sudah di-approve user)

- **Tugas:** Klasifikasi biner arah harga besok. `y=1` jika `Close[t+1] > Close[t]`, else `0`.
- **Fusi:** Early fusion — `sentiment_mean` jadi kolom fitur bersama OHLCV (1 model).
- **Framework:** **PyTorch** (TensorFlow tidak terinstall; torch sudah ada).
- **Window:** default `20`, di-sweep `{10,20,30}` saat eksperimen.
- **Split:** time-series tanpa shuffle. train ≤ 2022-12-31 | val 2023 | test 2024.
- **Fitur:** `["Open","High","Low","Close","Volume","sentiment_mean"]` (6 fitur).
  Abaikan MA_20/50/200 & Volatility_30 sesuai instruksi user.
- **Scaling:** `MinMaxScaler` di-fit HANYA di train, transform val/test (anti-leakage).

## Sumber Data

- OHLCV: `data/processed/stocks/GSPC_2018_2024.csv` (kolom `Date,Open,High,Low,Close,Volume,...`)
- Sentimen: `data/processed/sentiment/headlines_daily_sentiment.csv` (kolom `Date,sentiment_mean,...`)
- Join: inner join on `Date` → 1528 baris, 2018-01-02..2024-03-04, 0 NaN sentiment.

## Artefak Output (disimpan di `data/artifacts/lstm_weights/`)

- `direction_classifier.pt`  — `state_dict` model PyTorch
- `scaler.joblib`            — MinMaxScaler hasil fit di train
- `metadata.json`            — `{feature_cols, window, n_features, hidden, metrics:{...}, trained_at, framework:"pytorch"}`

---

## Modul 1 — Data (`pipeline/feature_engineering/dataset_builder.py`) [AGENT: data]

```python
from dataclasses import dataclass
import numpy as np
from sklearn.preprocessing import MinMaxScaler

STOCK_CSV = "data/processed/stocks/GSPC_2018_2024.csv"
SENTIMENT_CSV = "data/processed/sentiment/headlines_daily_sentiment.csv"
FEATURE_COLS = ["Open", "High", "Low", "Close", "Volume", "sentiment_mean"]

@dataclass
class DatasetBundle:
    X_train: np.ndarray  # (N,W,6) float32
    y_train: np.ndarray  # (N,)   float32 {0,1}
    X_val:   np.ndarray
    y_val:   np.ndarray
    X_test:  np.ndarray
    y_test:  np.ndarray
    scaler:  MinMaxScaler
    feature_cols: list[str]
    window: int
    test_dates: list[str]    # tanggal target tiap sampel test (ISO)

def load_joined() -> "pd.DataFrame":
    """Inner-join OHLCV + sentiment by Date, sorted asc. Kolom: Date + FEATURE_COLS."""

def build_dataset(window: int = 20,
                  train_end: str = "2022-12-31",
                  val_end: str = "2023-12-31") -> DatasetBundle:
    """
    1. load_joined()
    2. label = (Close.shift(-1) > Close).astype(int); drop baris terakhir (label NaN)
    3. split by Date: train<=train_end, train_end<val<=val_end, test>val_end
    4. scaler.fit(train[FEATURE_COLS]) -> transform semua split
    5. windowing PER-SPLIT (tidak melintasi batas split):
       X[i]=feat[i:i+W], y[i]=label[i+W-1]
    return DatasetBundle
    """

def build_latest_window(window: int, scaler: MinMaxScaler) -> tuple[np.ndarray, str]:
    """
    Untuk inference: ambil `window` baris TERAKHIR dari load_joined(),
    transform pakai scaler, return (X[1,W,6] float32, as_of_date_iso).
    target_date = hari bursa berikutnya (boleh as_of_date + 1 hari kalender, string).
    """
```

Juga lengkapi `data_alignment.DataAligner.align()` (saat ini `NotImplementedError`)
sebagai inner-join sederhana on `Date` agar konsisten (opsional, jangan blokir Modul 1).

## Modul 2 — Model (`models/lstm/`) [AGENT: model]

`lstm_model.py`:
```python
import torch.nn as nn
class LSTMDirectionClassifier(nn.Module):
    def __init__(self, n_features: int, hidden: int = 64, num_layers: int = 2, dropout: float = 0.3):
        # LSTM(n_features,hidden,num_layers,batch_first=True,dropout) ->
        # ambil output timestep terakhir -> Linear(hidden,16)->ReLU->Dropout->Linear(16,1)
        # forward(x:(B,W,F)) -> logits (B,) TANPA sigmoid (pakai BCEWithLogitsLoss)
def build_classifier(n_features: int, **kw) -> LSTMDirectionClassifier: ...
```

`lstm_trainer.py`:
```python
ARTIFACT_DIR = "data/artifacts/lstm_weights"
def train(bundle, epochs=50, batch_size=32, lr=1e-3, patience=8, seed=42) -> dict:
    """
    BCEWithLogitsLoss + Adam. Early stopping on val AUC (atau val_loss).
    Simpan direction_classifier.pt, scaler.joblib, metadata.json.
    return metrics dict {val_acc,val_f1,val_auc,test_acc,test_f1,test_auc}.
    """
```

`lstm_predictor.py`:
```python
class DirectionPredictor:
    def __init__(self, artifact_dir: str = "data/artifacts/lstm_weights"): ...  # load model+scaler+meta
    @property
    def is_available(self) -> bool: ...
    def predict_proba(self, X: np.ndarray) -> np.ndarray: ...   # sigmoid(logits)
    def predict_latest(self) -> dict:
        """pakai dataset_builder.build_latest_window(window, scaler).
        return {probability_up: float, direction: 'up'|'down', confidence: float,
                as_of_date: str, target_date: str}"""
```

## Modul 3 — API (`app/`) [AGENT: api]

`schemas/prediction.py`:
```python
from typing import Literal
from pydantic import BaseModel, Field

class PredictionRequest(BaseModel):
    ticker: str = "GSPC"

class DirectionPredictionResponse(BaseModel):
    ticker: str
    as_of_date: str
    target_date: str
    direction: Literal["up", "down"]
    probability_up: float = Field(..., ge=0, le=1)
    confidence: float = Field(..., ge=0, le=1)   # max(p, 1-p)
    window: int
    features_used: list[str]
    model_version: str | None = None

class ModelInfoResponse(BaseModel):
    is_available: bool
    artifact_path: str
    window: int | None = None
    features_used: list[str] = []
    n_features: int | None = None
    metrics: dict | None = None
    trained_at: str | None = None
```

`services/prediction_service.py`:
```python
def get_model_status() -> ModelInfoResponse: ...
def predict_direction(ticker: str = "GSPC") -> DirectionPredictionResponse:
    # load DirectionPredictor; jika tidak available -> raise NotFoundError("MODEL_NOT_TRAINED", ...)
    # panggil predict_latest(); map ke DirectionPredictionResponse
```
Pakai `app.core.exceptions.NotFoundError` (lihat sentiment_service untuk pola).

`api/v1/routes_prediction.py`:
```python
from fastapi import APIRouter
from app.core.envelope import EnvelopeRoute
router = APIRouter(tags=["Prediction"], route_class=EnvelopeRoute)

@router.post("/predict", response_model=DirectionPredictionResponse,
             openapi_extra={"x-message": "Prediksi arah harga berhasil"})
def predict(req: PredictionRequest) -> DirectionPredictionResponse:
    return prediction_service.predict_direction(req.ticker)

@router.get("/predict/model/status", response_model=ModelInfoResponse,
            openapi_extra={"x-message": "Status model prediksi berhasil dimuat"})
def model_status() -> ModelInfoResponse:
    return prediction_service.get_model_status()
```
Daftarkan di `app/api/v1/__init__.py`:
```python
from app.api.v1.routes_prediction import router as prediction_router
api_router.include_router(prediction_router, prefix="/api/v1")
```

Update `app/domain/entities/prediction_result.py` → ganti ke klasifikasi:
field `direction: Literal["up","down"]`, `probability_up: float (0..1)`,
`confidence: float (0..1)`, hapus `predicted_close`/`lstm_weight`/`sentiment_weight`.

---

## Definition of Done

- [ ] `build_dataset(20)` jalan, shape `X_train (N,20,6)`, tidak ada NaN, no leakage.
- [ ] `train()` menghasilkan 3 artefak di `data/artifacts/lstm_weights/`.
- [ ] `GET /api/v1/predict/model/status` → 200, `is_available:true`.
- [ ] `POST /api/v1/predict` → 200, response sesuai `DirectionPredictionResponse` + envelope `SuccessResponse`.
- [ ] `pytest` hijau (test windowing, label, no-leakage, route).
