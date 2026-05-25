# Project Context — Stock Prediction System

## Tujuan Project
Sistem prediksi harga saham yang menggabungkan:
- **FinBERT** (ProsusAI/finbert) → analisis sentimen berita keuangan
- **LSTM** (TensorFlow/Keras) → prediksi harga berbasis time-series OHLCV
- **Ensemble layer** → fusi weighted average dari kedua model
- **FastAPI** → REST API endpoint

## Dataset
- `data/raw/news/sp500_headlines_2008_2024.csv` — S&P 500 headlines, kolom: `Title`, `Date`, `CP`
- Filter aktif: tahun 2018–2024 (~13.422 baris setelah filter + dedup)
- Output notebook 02 tersimpan di:
  - `data/processed/sentiment/headlines_clean.csv` — per headline + skor FinBERT
  - `data/processed/sentiment/headlines_daily_sentiment.csv` — agregasi sentimen harian + CP

## FinBERT
- Model lokal di: `models/finbert/models--ProsusAI--finbert/snapshots/4556d13015211d73dccd3fdd39d39232506f3e43`
- Output: `sentiment_positive`, `sentiment_negative`, `sentiment_neutral`, `sentiment_label`, `sentiment_score` (pos−neg)
- Batch size default: 32

## Status Implementasi (per 2026-05-01)
| Layer | Status |
|-------|--------|
| FastAPI skeleton + middleware | ✅ Selesai |
| routes_general, routes_status | ✅ Selesai |
| schemas/status.py | ✅ Selesai |
| app/core/logging_config.py (sistem logging) | ✅ Selesai |
| technical_indicators.py | ✅ Selesai |
| sentiment_aggregator.py | ✅ Selesai |
| schemas/sentiment.py | ✅ Selesai |
| routes_data.py | ✅ Selesai |
| pipeline/preprocessing/stock_preprocessor.py | ✅ Selesai (cleaning only, scaler belum) |
| pipeline/preprocessing/text_preprocessor.py | ✅ Selesai |
| routes_prediction.py, routes_sentiment.py | 🔲 Belum |
| services/ | 🔲 Belum |
| models/lstm/, models/finbert/, models/combined/ | 🔲 Belum |

## Catatan stock_preprocessor.py (2026-05-01)
- Hanya menangani **cleaning** data OHLCV dari `data/raw/stocks/GSPC_2018_2024.csv`
- Step: drop kolom irrelevan → validasi kolom → sort Date → drop duplikat → ffill/bfill NaN → validasi nilai
- Output: `data/processed/stocks/{ticker}_clean.csv`
- **Scaler (MinMaxScaler) belum diimplementasikan** — akan ditambahkan di sesi berikutnya
- Entrypoint: `StockPreprocessor().run(csv_path, ticker)`

## Notebook yang Sudah Ada
- `notebooks/01_EDA_stock_data.ipynb` — EDA data OHLCV
- `notebooks/02_EDA_sentiment_data.ipynb` — EDA + preprocessing + FinBERT scoring (34 cells, sudah dijalankan)
