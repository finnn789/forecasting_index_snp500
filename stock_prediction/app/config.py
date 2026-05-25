"""
app/config.py — Konstanta dan konfigurasi global aplikasi.
"""

APP_TITLE = "Stock Market Prediction API"

APP_DESCRIPTION = """
## 📈 Stock Market Price Prediction System

API backend untuk sistem prediksi harga saham yang menggabungkan:

- **FinBERT** — Analisis sentimen berita & teks keuangan
- **LSTM (TensorFlow/Keras)** — Prediksi harga berbasis time-series historis

### Status Endpoint
Gunakan endpoint `/api/status` atau `/api/health` untuk memverifikasi
ketersediaan layanan sebelum mengonsumsi endpoint prediksi.

---
> **Note**: Endpoint pipeline data dan model prediksi akan tersedia pada versi berikutnya.
"""

APP_VERSION = "0.1.0"

APP_CONTACT = {
    "name": "Stock Prediction Dev Team",
    "email": "dev@stockpred.local",
}

APP_LICENSE = {
    "name": "MIT License",
    "url": "https://opensource.org/licenses/MIT",
}
