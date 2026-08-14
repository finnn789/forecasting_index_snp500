# Stock Market Price Prediction

Sistem prediksi harga pasar saham menggunakan kombinasi **FinBERT** (analisis sentimen) dan **LSTM** (prediksi time-series), di-serve melalui **FastAPI**.

## Tech Stack

- **Backend API**: FastAPI + Uvicorn
- **ML Framework**: TensorFlow/Keras (LSTM), HuggingFace Transformers (FinBERT)
- **Data Processing**: Pandas, NumPy, Scikit-learn

## Struktur Proyek

Lihat `code_plan/implementation_plan.md` untuk dokumentasi lengkap.

## Cara Menjalankan

```bash
# Install dependensi
pip install -r requirements.txt

# Jalankan API
./scripts/run_api.sh
```
