# Schema Metode Penelitian
## Prediksi Arah Harga S&P 500 dengan Fusi LSTM + FinBERT Sentiment

> ⚠️ **USANG (desain lama / v1–v3).** Dokumen ini menggambarkan rancangan awal
> (horizon-1, target `Close[t+1]>Close[t]`, LSTM 2-layer 64/32 + sigmoid/BCELoss,
> MinMaxScaler, 6 fitur OHLCV+sentiment_mean, split 2008–2019) yang **tidak lagi
> mencerminkan implementasi**. Untuk metodologi terkini (v5: horizon-5, 10 fitur
> stasioner, LSTM kecil + CrossEntropy, seed ensemble, rolling walk-forward,
> kalibrasi Platt, Youden's J, analisis sensitivitas) gunakan
> **[`metodologi_penelitian.md`](metodologi_penelitian.md)** dan
> **[`finbert_lstm_architecture.md`](finbert_lstm_architecture.md)**.
> File ini dipertahankan hanya sebagai jejak historis.

---

## SUMBER DATA MENTAH

```
┌─────────────────────────────────┐     ┌─────────────────────────────────────┐
│        DATA MENTAH #1           │     │          DATA MENTAH #2             │
│   OHLCV Harga Saham S&P 500     │     │    Berita Headline S&P 500          │
│                                 │     │                                     │
│  Sumber : Yahoo Finance / API   │     │  Sumber : sp500_headlines_           │
│  Format : CSV (per hari)        │     │           2008_2024.csv             │
│  Kolom  : Date, Open, High,     │     │  Kolom  : Title, Date, CP           │
│           Low, Close, Volume    │     │  Jumlah : ±19.127 headline          │
│  Frekuensi : Hari trading       │     │  Rentang: 2008 – 2024               │
│              (Senin–Jumat)      │     │  Frekuensi : Setiap hari            │
└────────────┬────────────────────┘     └──────────────┬──────────────────────┘
             │                                         │
             ▼                                         ▼
```

---

## TAHAP 1 — PREPROCESSING

```
┌─────────────────────────────────┐     ┌─────────────────────────────────────┐
│    PREPROCESSING OHLCV          │     │    PREPROCESSING TEKS               │
│                                 │     │                                     │
│  • Hapus baris NaN              │     │  • Strip whitespace                 │
│  • Parse kolom Date             │     │  • Collapse spasi ganda             │
│  • Sort ascending by Date       │     │  • Dedup (Title + Date sama)        │
│  • Hitung daily_return:         │     │  • Filter headline < 3 kata         │
│    (Close[t]-Close[t-1])        │     │  • Hapus kolom CP                   │
│    ────────────────────         │     │                                     │
│        Close[t-1]               │     │  Input  : 19.127 headline           │
│                                 │     │  Output : ±18.129 headline bersih   │
└────────────┬────────────────────┘     └──────────────┬──────────────────────┘
             │                                         │
             │                                         ▼
             │                         ┌─────────────────────────────────────┐
             │                         │    FINBERT SENTIMENT SCORING        │
             │                         │    (ProsusAI/finbert)               │
             │                         │                                     │
             │                         │  Model  : BERT fine-tuned keuangan  │
             │                         │  Input  : 1 headline → 1 prediksi  │
             │                         │  Output per headline:               │
             │                         │   • sentiment_label                 │
             │                         │     (positive / neutral / negative) │
             │                         │   • sentiment_score                 │
             │                         │     (confidence: 0.0 – 1.0)        │
             │                         │   • sentiment_numeric               │
             │                         │     (+1 / 0 / -1)                   │
             │                         └──────────────┬──────────────────────┘
             │                                        │
             │                                        ▼
```

---

## TAHAP 2 — AGREGASI SENTIMEN HARIAN

```
             │                         ┌─────────────────────────────────────┐
             │                         │   PROBABILITY-WEIGHTED AGGREGATION  │
             │                         │   (Metode Baru — per hari)          │
             │                         │                                     │
             │                         │  Step 1 — Hitung signed:            │
             │                         │    signed = sentiment_numeric        │
             │                         │             × sentiment_score        │
             │                         │    → range kontinu [-1.0, +1.0]     │
             │                         │    → berita yakin = bobot besar      │
             │                         │    → berita netral selalu = 0        │
             │                         │                                     │
             │                         │  Step 2 — groupby(Date):            │
             │                         │    sentiment_mean = mean(signed)     │
             │                         │    sentiment_pos  = prop(positive)   │
             │                         │    sentiment_neg  = prop(negative)   │
             │                         │    sentiment_neu  = prop(neutral)    │
             │                         │    headline_count = jumlah berita    │
             │                         │                                     │
             │                         │  Step 3 — Label harian:             │
             │                         │    mean >  0.05 → "positive"         │
             │                         │    mean < -0.05 → "negative"         │
             │                         │    else         → "neutral"          │
             │                         │                                     │
             │                         │  Step 4 — Fitur tambahan:           │
             │                         │    net_sentiment =                   │
             │                         │      sentiment_pos - sentiment_neg   │
             │                         │                                     │
             │                         │  Output: 1 baris per hari trading   │
             │                         │  File: headlines_daily_sentiment.csv│
             │                         └──────────────┬──────────────────────┘
             │                                        │
             ▼                                        ▼
```

---

## TAHAP 3 — MERGE & ALIGNMENT TEMPORAL

```
        ┌───────────────────────────────────────────────────────────────────┐
        │                  LEFT JOIN on Date                                │
        │                                                                   │
        │   OHLCV (hari trading) ←── Sentiment (semua hari)                │
        │                                                                   │
        │   Hari tanpa berita → fill: sentiment = 0.0, label = 'neutral'   │
        │   Weekend / libur bursa → tidak ada baris (hanya hari trading)   │
        └───────────────────────────────┬───────────────────────────────────┘
                                        │
                                        ▼
        ┌───────────────────────────────────────────────────────────────────┐
        │              PENANGANAN KAUSALITAS TEMPORAL  ⚠️                   │
        │                                                                   │
        │   Mengapa sentimen hari t-1, bukan hari t?                       │
        │                                                                   │
        │   Hari t-1                         Hari t                        │
        │   ────────────────────────         ──────────────────────────    │
        │   Berita terbit sepanjang hari  →  Pasar buka 09:30             │
        │   sentiment_mean dihitung          Investor sudah baca berita    │
        │   = nilai yang digunakan ────────► keputusan jual/beli           │
        │                                    → Close[t] bergerak           │
        │                                                                   │
        │   Jika pakai sentiment hari t:                                   │
        │   → RISIKO DATA LEAKAGE                                          │
        │   (berita bisa terbit sebagai RESPONS harga, bukan pemicu)      │
        │                                                                   │
        │   Solusi: sentiment_mean_lag1 = sentiment_mean.shift(1)          │
        └───────────────────────────────┬───────────────────────────────────┘
                                        │
                                        ▼
```

---

## TAHAP 4 — FEATURE ENGINEERING

```
        ┌───────────────────────────────────────────────────────────────────┐
        │                    FEATURE ENGINEERING                            │
        │                                                                   │
        │  Fitur Sentimen (dengan lag):                                    │
        │    sentiment_mean_lag1    → skor sentimen kemarin                │
        │    sentiment_pos_lag1     → proporsi positif kemarin             │
        │    sentiment_neg_lag1     → proporsi negatif kemarin             │
        │    net_sentiment_lag1     → (pos - neg) kemarin                  │
        │                                                                   │
        │  Fitur Harga (OHLCV):                                            │
        │    Open, High, Low, Close, Volume                                │
        │    daily_return           → % perubahan harga harian             │
        │    Close_lag1, lag3, lag5 → harga penutupan t-1, t-3, t-5       │
        │                                                                   │
        │  Fitur Rolling Sentimen:                                         │
        │    sentiment_mean_roll3   → rolling mean 3 hari                  │
        │    sentiment_mean_roll7   → rolling mean 7 hari                  │
        │    sentiment_std_roll3    → volatilitas sentimen 3 hari          │
        │                                                                   │
        │  TARGET (supervised learning):                                   │
        │    y = 1 jika Close[t+1] > Close[t]  (harga naik besok)        │
        │    y = 0 jika Close[t+1] ≤ Close[t]  (harga turun/flat)        │
        │                                                                   │
        │  Anti-leakage:                                                   │
        │    MinMaxScaler di-fit HANYA pada data training                  │
        │    → transform ke val/test pakai scaler yang sama               │
        └───────────────────────────────┬───────────────────────────────────┘
                                        │
                                        ▼
```

---

## TAHAP 5 — SPLIT DATASET (TIME-BASED)

```
        ┌───────────────────────────────────────────────────────────────────┐
        │              SPLIT BERDASARKAN URUTAN WAKTU                      │
        │              (BUKAN random shuffle — time-series)                │
        │                                                                   │
        │  ├──────────────────────────┬───────────────┬──────────────┤    │
        │  │       TRAIN (70%)        │   VAL (15%)   │  TEST (15%)  │    │
        │  │     2008 – 2019          │  2020 – 2021  │  2022 – 2024 │    │
        │  ├──────────────────────────┴───────────────┴──────────────┤    │
        │                                                                   │
        │  • Sliding window: 20 hari → 1 prediksi                         │
        │  • X shape: (samples, window=20, features=6+)                   │
        │  • y shape: (samples,)  → 0 atau 1                              │
        └───────────────────────────────┬───────────────────────────────────┘
                                        │
                                        ▼
```

---

## TAHAP 6 — MODEL (EARLY FUSION LSTM)

```
        ┌───────────────────────────────────────────────────────────────────┐
        │              EARLY FUSION LSTM (PyTorch)                         │
        │                                                                   │
        │  Arsitektur:                                                     │
        │                                                                   │
        │  Input Layer                                                     │
        │  [batch, window=20, features=6]                                  │
        │       │  OHLCV (5 fitur) + sentiment_mean (1 fitur)             │
        │       │  → digabung sejak awal (early fusion)                   │
        │       ▼                                                          │
        │  LSTM Layer 1  (hidden=64, dropout=0.2)                         │
        │       ▼                                                          │
        │  LSTM Layer 2  (hidden=32, dropout=0.2)                         │
        │       ▼                                                          │
        │  Fully Connected → 1 neuron                                     │
        │       ▼                                                          │
        │  Sigmoid Activation                                              │
        │       ▼                                                          │
        │  Output: probability_up ∈ [0, 1]                                │
        │                                                                   │
        │  Loss     : BCELoss (Binary Cross-Entropy)                      │
        │  Optimizer: Adam                                                 │
        │  Metric   : AUC-ROC, Accuracy, F1                               │
        │                                                                   │
        │  Artefak tersimpan:                                              │
        │   data/artifacts/lstm_weights/direction_classifier.pt           │
        │   data/artifacts/lstm_weights/scaler.joblib                     │
        │   data/artifacts/lstm_weights/metadata.json                     │
        └───────────────────────────────┬───────────────────────────────────┘
                                        │
                                        ▼
```

---

## TAHAP 7 — EVALUASI & OUTPUT

```
        ┌───────────────────────────────────────────────────────────────────┐
        │                      EVALUASI MODEL                              │
        │                                                                   │
        │  Backtest pada test set:                                         │
        │    • Confusion Matrix (TP, TN, FP, FN)                          │
        │    • Accuracy  = (TP + TN) / total                              │
        │    • Precision = TP / (TP + FP)                                 │
        │    • Recall    = TP / (TP + FN)                                 │
        │    • F1 Score  = 2 × (Precision × Recall) / (P + R)            │
        │    • AUC-ROC   = area under ROC curve                           │
        │                                                                   │
        │  Baseline perbandingan:                                          │
        │    • Always-up baseline (prediksi naik terus)                   │
        │    • Random baseline 50%                                         │
        └───────────────────────────────┬───────────────────────────────────┘
                                        │
                                        ▼
        ┌───────────────────────────────────────────────────────────────────┐
        │                    OUTPUT API (FastAPI)                           │
        │                                                                   │
        │  POST /api/v1/predict                                            │
        │    Input  : ticker, date range                                   │
        │    Output : direction (up/down), probability_up, confidence      │
        │                                                                   │
        │  GET  /api/v1/predict/backtest                                   │
        │    Output : prediksi vs aktual per hari + metrik                 │
        │                                                                   │
        │  GET  /api/v1/predict/model/status                               │
        │    Output : model loaded, AUC terakhir, tanggal training         │
        └───────────────────────────────────────────────────────────────────┘
```

---

## RINGKASAN ALUR KESELURUHAN

```
Data Mentah OHLCV ──────────────────────────────────────────────┐
                                                                 │
                                                                 ▼
Data Mentah Headline ──► Preprocessing ──► FinBERT Scoring      │
                                                  │              │
                                                  ▼              │
                             Agregasi Harian (probability-weighted)
                             + net_sentiment = pos - neg          │
                                                  │              │
                                                  ▼              ▼
                                         LEFT JOIN (Date) + LAG1 alignment
                                                  │
                                                  ▼
                                      Feature Engineering
                                      (lag, rolling, scaling)
                                                  │
                                                  ▼
                                    Split: Train / Val / Test
                                    (time-based, no shuffle)
                                                  │
                                                  ▼
                                    Early Fusion LSTM (PyTorch)
                                    OHLCV + sentiment_mean → input
                                                  │
                                                  ▼
                              Output: P(harga naik besok) ∈ [0,1]
                                                  │
                                                  ▼
                              Evaluasi: AUC-ROC, F1, Confusion Matrix
                                                  │
                                                  ▼
                                        FastAPI REST Endpoint
```

---

## CATATAN METODOLOGI KRITIS

| Aspek | Keputusan | Alasan |
|-------|-----------|--------|
| **Agregasi sentimen** | Probability-weighted (`signed = numeric × score`) | Lebih informatif dari integer; confidence FinBERT dimanfaatkan |
| **Lag sentimen** | `lag1` (sentimen t-1 → harga t) | Hindari data leakage; kausalitas benar (berita → reaksi pasar) |
| **Target** | Klasifikasi biner (arah naik/turun) | Lebih robust dari regresi harga mutlak |
| **Fitur harga** | `daily_return` bukan `Close` | `Close` non-stasioner → korelasi palsu (spurious) |
| **Split data** | Time-based (bukan random) | Data time-series tidak boleh di-shuffle |
| **Scaling** | MinMaxScaler fit di train saja | Hindari lookahead bias dari data val/test |
| **Framework model** | PyTorch (bukan TensorFlow) | TF tidak ter-install; PyTorch sudah ada via FinBERT dependency |
| **Dominasi netral** | Tambah `net_sentiment = pos - neg` | Lebih sensitif terhadap pergeseran pos/neg meski mean mendekati 0 |
