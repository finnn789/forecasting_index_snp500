# Log Keputusan Sesi

## [2026-04-26] Inisialisasi Feature Engineering

### Keputusan Arsitektur
- Feature engineering diimplementasikan di `pipeline/feature_engineering/`
- **Tidak ada folder baru** — semua file masuk ke folder yang sudah ada
- Setiap fungsi pipeline menerima DataFrame dan mengembalikan DataFrame

### Status: SELESAI [2026-04-26]

## [2026-04-26] Feature Extraction — sentiment_aggregator.py

### Status: SELESAI
Menambahkan fungsi ekstraksi fitur ke `pipeline/feature_engineering/sentiment_aggregator.py`:
- `encode_sentiment_label` — label string → numerik
- `add_lag_features` — lag columns untuk time-series
- `add_rolling_sentiment` — rolling mean/std sentimen (3 & 7 hari)
- `create_target` — kolom target return/direction untuk LSTM
- `extract_features` — orchestrator semua langkah ekstraksi
- `build_lstm_sequences` — sliding window array (samples, timesteps, features)
- `split_dataset` — time-based split train/val/test
- `save_features` — simpan ke data/processed/stocks/features.csv

## [2026-04-26] Sistem Logging Terpisah per Komponen

### Keputusan Arsitektur
- Folder `logs/` di root project, dibagi per komponen
- Konfigurasi terpusat di `app/core/logging_config.py`
- `RotatingFileHandler` — max 5MB per file, 3 backup
- Log juga tampil di console (stdout)
- Router logger otomatis berdasarkan nama modul: `pipeline.*`, `app.*`, `models.*`

### Struktur Log
- `logs/api/api.log` — FastAPI routes & request
- `logs/pipeline/pipeline.log` — ingestion, preprocessing, feature engineering
- `logs/models/models.log` — LSTM, FinBERT, ensemble
- `logs/app.log` — startup, shutdown, error umum

### File yang Dibuat/Diubah
1. `logs/api/.gitkeep`, `logs/pipeline/.gitkeep`, `logs/models/.gitkeep`
2. `app/core/logging_config.py` — setup_logging() terpusat
3. `server.py` — panggil setup_logging() di startup
4. `.gitignore` — abaikan *.log, keep .gitkeep

### Rencana Implementasi yang Disetujui
File yang akan ditulis (sesi ini):
1. `pipeline/feature_engineering/technical_indicators.py` — RSI, MACD, EMA-20/50, Bollinger Bands
2. `pipeline/feature_engineering/sentiment_aggregator.py` — merge sentiment harian ke OHLCV
3. `app/schemas/sentiment.py` — Pydantic schemas (SentimentRequest, SentimentResponse, FeatureEngineeringResponse)
4. `app/api/v1/routes_data.py` — endpoint EDA + feature engineering (response JSON)
5. `app/api/v1/__init__.py` — registrasi routes_data router

### Endpoint yang Akan Dibuat (routes_data.py)
- `GET /api/v1/data/eda/summary` — statistik dasar dataset
- `GET /api/v1/data/eda/news-per-year` — distribusi berita per tahun (JSON)
- `GET /api/v1/data/eda/news-per-day` — statistik berita per hari (JSON)
- `GET /api/v1/data/eda/sentiment-distribution` — distribusi label sentimen (JSON)
- `GET /api/v1/data/feature-engineering/run` — jalankan pipeline, kembalikan sample hasil

### Sumber Data untuk Feature Engineering
- Sentiment: `data/processed/sentiment/headlines_daily_sentiment.csv`
- OHLCV: akan di-fetch via yfinance (sesuai implementation_plan.md)
