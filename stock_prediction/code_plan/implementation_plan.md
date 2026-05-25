# Implementation Plan — Stock Market Price Prediction

**Project:** Stock Market Price Prediction System  
**Tech Stack:** Python, FastAPI, TensorFlow (LSTM), FinBERT (HuggingFace Transformers)  
**Last Updated:** 2026-04-23

---

## 1. Tujuan Proyek

Membangun sistem prediksi harga saham yang menggabungkan dua pendekatan:
1. **FinBERT** → Analisis sentimen dari teks/berita keuangan
2. **LSTM (TensorFlow/Keras)** → Prediksi harga berdasarkan data time-series historis

Kedua output diintegrasikan melalui lapisan **Ensemble** kemudian di-serve melalui **FastAPI**.

---

## 2. Arsitektur Sistem

```
[Data Source]
     │
     ▼
[pipeline/ingestion]          ← Ambil data saham & berita
     │
     ▼
[pipeline/preprocessing]      ← Bersihkan & transformasi data
     │
     ▼
[pipeline/feature_engineering] ← Buat fitur teknikal & agregasi sentimen
     │
     ├──────────────────────────┐
     ▼                          ▼
[models/lstm]              [models/finbert]
  Prediksi Harga           Analisis Sentimen
     │                          │
     └──────────┬───────────────┘
                ▼
        [models/combined]      ← Ensemble / Fusion
                │
                ▼
          [app/FastAPI]        ← REST API Endpoint
```

---

## 3. Breakdown Komponen

### 3.1 `pipeline/` — Data Pipeline

| Modul | File | Tanggung Jawab |
|---|---|---|
| Ingestion | `ingestion/stock_fetcher.py` | Ambil data OHLCV (Open, High, Low, Close, Volume) dari sumber saham |
| Ingestion | `ingestion/news_fetcher.py` | Ambil headline/artikel berita keuangan |
| Preprocessing | `preprocessing/stock_preprocessor.py` | Normalisasi harga, handling NaN, buat window sequence untuk LSTM |
| Preprocessing | `preprocessing/text_preprocessor.py` | Cleaning text: lowercase, remove special char, tokenisasi untuk FinBERT |
| Feature Eng. | `feature_engineering/technical_indicators.py` | Hitung RSI, MACD, EMA, Bollinger Bands dari data OHLCV |
| Feature Eng. | `feature_engineering/sentiment_aggregator.py` | Gabungkan skor sentimen harian ke dataframe harga saham |
| Runner | `runner.py` | Orchestrate seluruh pipeline dari ingestion hingga feature engineering |

---

### 3.2 `models/` — Machine Learning Models

#### FinBERT (`models/finbert/`)
- **`finbert_model.py`**
  - Load pretrained model `ProsusAI/finbert` dari HuggingFace
  - Fungsi `predict_sentiment(text: str) -> dict` → mengembalikan label & skor
  - Label output: `positive`, `negative`, `neutral`
- **`finbert_trainer.py`** *(opsional)*
  - Fine-tuning FinBERT menggunakan dataset `financial_phrasebank.csv`
  - Fungsi `train(dataset_path, epochs, batch_size)`

#### LSTM (`models/lstm/`)
- **`lstm_model.py`**
  - Definisi arsitektur LSTM menggunakan `tensorflow.keras`
  - Arsitektur default: Input → LSTM(128) → Dropout → LSTM(64) → Dense(1)
  - Fungsi `build_model(input_shape) -> keras.Model`
- **`lstm_trainer.py`**
  - Training loop: `train(X_train, y_train, epochs, batch_size)`
  - Simpan model ke `data/artifacts/lstm_weights/`
- **`lstm_predictor.py`**
  - Load model dari artifacts
  - Fungsi `predict(X_input) -> np.array`

#### Ensemble (`models/combined/`)
- **`ensemble.py`**
  - Gabungkan output LSTM (prediksi harga) + FinBERT (skor sentimen)
  - Strategi: **Weighted Average** atau **Adjustment Factor**
  - Contoh: `final_price = lstm_price * (1 + sentiment_weight * sentiment_score)`

---

### 3.3 `app/` — FastAPI Backend

#### Endpoints (v1)

| Method | Path | Deskripsi |
|---|---|---|
| `POST` | `/api/v1/predict` | Input: ticker, tanggal → Output: prediksi harga |
| `POST` | `/api/v1/sentiment` | Input: teks berita → Output: sentimen & skor |
| `GET` | `/api/v1/data/history` | Ambil data historis harga suatu saham |

#### Schemas (Pydantic)
- **`schemas/prediction.py`**
  - `PredictionRequest`: `ticker: str`, `days_ahead: int`
  - `PredictionResponse`: `ticker`, `predicted_price`, `sentiment_score`, `confidence`
- **`schemas/sentiment.py`**
  - `SentimentRequest`: `text: str`
  - `SentimentResponse`: `label`, `score`

#### Services
- **`services/prediction_service.py`** → Orchestrate LSTM + FinBERT + Ensemble
- **`services/sentiment_service.py`** → Wrap FinBERT model untuk inference

---

### 3.4 `data/` — Penyimpanan Data

```
data/
├── raw/
│   ├── stocks/        ← File CSV/JSON harga saham mentah
│   └── news/          ← File teks berita mentah
├── processed/
│   ├── stocks/        ← Data saham setelah normalisasi & feature engineering
│   └── sentiment/     ← Skor sentimen per ticker per tanggal
└── artifacts/
    ├── lstm_weights/  ← File .h5 / SavedModel TensorFlow
    └── finbert_weights/ ← Fine-tuned FinBERT weights (opsional)
```

---

### 3.5 `notebooks/` — Eksperimen & EDA

| Notebook | Tujuan |
|---|---|
| `01_EDA_stock_data.ipynb` | Exploratory Data Analysis data harga saham |
| `02_EDA_sentiment_data.ipynb` | EDA data sentimen & distribusi label |
| `03_LSTM_experiment.ipynb` | Eksperimen arsitektur & hyperparameter LSTM |
| `04_FinBERT_experiment.ipynb` | Evaluasi FinBERT, fine-tuning experiment |

---

## 4. Urutan Pengerjaan (Roadmap)

```
Phase 1: Data Pipeline
  [x] Buat struktur folder
  [ ] Implementasi stock_fetcher.py
  [ ] Implementasi news_fetcher.py
  [ ] Implementasi stock_preprocessor.py
  [ ] Implementasi text_preprocessor.py
  [ ] Implementasi technical_indicators.py
  [ ] Implementasi sentiment_aggregator.py

Phase 2: Model Development
  [ ] Implementasi finbert_model.py
  [ ] Implementasi lstm_model.py
  [ ] Implementasi lstm_trainer.py
  [ ] Implementasi lstm_predictor.py
  [ ] Implementasi ensemble.py
  [ ] Training & evaluasi kedua model
  [ ] Fine-tuning FinBERT (opsional, pakai financial_phrasebank.csv)

Phase 3: FastAPI Backend
  [ ] Implementasi schemas
  [ ] Implementasi services
  [ ] Implementasi API routes/endpoints
  [ ] Integrasi dengan model
  [ ] Testing endpoint

Phase 4: Testing & Refinement
  [ ] Unit test pipeline
  [ ] Unit test models
  [ ] Integration test API
  [ ] Performance tuning
```

---

## 5. Dependensi Utama

```
# API
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
pydantic>=2.0.0
python-dotenv>=1.0.0

# ML / Deep Learning
tensorflow>=2.15.0
transformers>=4.38.0      # FinBERT (HuggingFace)
torch>=2.2.0              # Dependency transformers
datasets>=2.18.0          # HuggingFace datasets

# Data Processing
pandas>=2.2.0
numpy>=1.26.0
scikit-learn>=1.4.0
ta>=0.11.0                # Technical Analysis library

# Testing
pytest>=8.0.0
httpx>=0.27.0             # Testing FastAPI
```

---

## 6. Environment Variables (`.env`)

```env
# API Keys (akan ditentukan kemudian)
STOCK_API_KEY=
NEWS_API_KEY=

# Model Config
LSTM_MODEL_PATH=data/artifacts/lstm_weights/lstm_model.h5
FINBERT_MODEL_NAME=ProsusAI/finbert

# FastAPI
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
```

---

## 7. Catatan Teknis

- **FinBERT**: Pretrained model `ProsusAI/finbert` digunakan tanpa fine-tuning terlebih dahulu. Fine-tuning dengan `financial_phrasebank.csv` bisa dilakukan di Phase 2 sebagai peningkatan performa.
- **LSTM Framework**: Menggunakan **TensorFlow/Keras** (bukan PyTorch).
- **Ensemble Strategy**: Dimulai dengan strategi sederhana (weighted average), kemudian bisa ditingkatkan ke metode yang lebih kompleks.
- **Sumber Data**: Akan ditentukan kemudian oleh developer (yfinance / API berbayar / scraping).
