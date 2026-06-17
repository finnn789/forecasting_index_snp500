# Metodologi Penelitian
## Prediksi Arah Harga S&P 500 dengan Fusi FinBERT–LSTM

> Dokumen ini adalah **metodologi penelitian terkini (sesuai implementasi v5)**,
> siap dijadikan kerangka Bab Metodologi. Untuk detail teknis arsitektur, lihat
> [`finbert_lstm_architecture.md`](finbert_lstm_architecture.md).
>
> Catatan: `schema_metode_penelitian.md` menggambarkan desain **lama** (horizon-1,
> LSTM 2-layer sigmoid/BCE, MinMaxScaler) dan **tidak lagi mencerminkan kode**.
> Gunakan dokumen ini.

---

## 3.1 Jenis dan Pendekatan Penelitian

- **Jenis:** kuantitatif–eksperimental (terapan).
- **Pendekatan:** komputasional / *machine learning* dengan tugas **klasifikasi
  biner terbimbing** (*supervised binary classification*).
- **Objek:** indeks S&P 500 (^GSPC).
- **Tujuan:** menguji apakah peleburan (*fusion*) sinyal **sentimen berita
  keuangan** (via FinBERT) dengan **deret waktu harga** (via LSTM) dapat
  memprediksi **arah pergerakan harga 5 hari ke depan**.

## 3.2 Rumusan Masalah & Hipotesis

- **RM1:** Sejauh mana model fusi FinBERT–LSTM dapat memprediksi arah harga
  5-hari S&P 500 di luar sampel (*out-of-sample*)?
- **RM2:** Apakah hubungan sentimen→arah harga stabil lintas waktu, atau
  bergantung pada rezim pasar?
- **H0 (efficient market):** sentimen berita tidak memberi keunggulan prediktif
  yang konsisten (AUC OOS ≈ 0.5).
- **H1:** fusi sentimen memberi keunggulan tipis namun terukur (AUC > 0.5).

> Konteks: korelasi sentimen↔return **1-hari r≈0.02 (nol)** tetapi **5-hari
> r≈0.275** dan **MA3 5-hari r≈0.363** → horizon 5-hari dipilih sebagai satu-satunya
> sinyal yang dapat diandalkan.

## 3.3 Kerangka Penelitian (Research Framework)

```
        Berita Headline (CSV)                 Harga OHLCV ^GSPC (CSV)
                │                                     │
        Preprocessing teks                    Preprocessing harga
                │                                     │
        FinBERT scoring                       Indikator teknikal
        (label, score, numeric)               (RSI, MACD, BB, vol)
                │                                     │
        signed = numeric × score              Transform STASIONER
        Agregasi harian (mean)                (rasio/selisih/return)
                │                                     │
        sentiment_mean, MA3  ──shift(1)──►  LEFT JOIN (Date)  ◄── 8 fitur teknikal
                                                  │
                                    10 fitur stasioner / hari
                                                  │
                                Target = arah 5-hari (filter ±1%)
                                                  │
                            Sliding window 20 hari  +  scaling train-only
                                                  │
                                   LSTM (PyTorch) → P(Up)
                                                  │
                       Seed ensemble (5) → kalibrasi → threshold
                                                  │
              Evaluasi: split kronologis + ROLLING walk-forward + sensitivitas
                                                  │
                          Kesimpulan (AUC, pooled AUC, robustness)
```

## 3.4 Variabel Penelitian

**Variabel dependen (target):**
`y = 1` jika *return* 5-hari ke depan > 0, `y = 0` jika < 0. Hari dengan
|*return* 5-hari| < 1% dibuang (zona netral/sideways).

**Variabel independen (10 fitur, semua STASIONER):**

| # | Fitur | Definisi | Kelompok |
|---|---|---|---|
| 1 | `ret_close` | `Close.pct_change()` | Harga |
| 2 | `ret_volume` | `Volume.pct_change()` | Volume |
| 3 | `rsi_14` | RSI 14 (0–100) | Momentum |
| 4 | `macd_hist` | MACD − signal | Tren |
| 5 | `bb_bandwidth` | (upper−lower)/mid | Volatilitas |
| 6 | `volatility_20` | std(return) 20 hari | Volatilitas |
| 7 | `close_vs_ema20` | `Close/EMA20 − 1` | Tren |
| 8 | `bb_pct_b` | `(Close−lower)/(upper−lower)` | Posisi BB |
| 9 | `sentiment_mean` | sentimen harian (lag-1) | Sentimen |
| 10 | `sentiment_mean_ma3` | rolling-MA3 sentimen (lag-1) | Sentimen |

## 3.5 Data Penelitian

| Aspek | Harga (OHLCV) | Berita (Headline) |
|---|---|---|
| Sumber | `data/raw/stocks/GSPC_2018_2024.csv` | `data/raw/news/sp500_headlines_2008_2024.csv` |
| Periode | 2018–2024 | 2008–2024 (efektif beririsan 2018+) |
| Jumlah | 1.552 hari trading | ±19.000 headline |
| Kolom | Date, Open, High, Low, Close, Volume | Title, Date |

**Reduksi jumlah baris (transparan):** 1.552 hari → **1.531** (setelah warmup
indikator) → **951** (setelah filter ±1%, proporsi Up = 61,8% → tak seimbang,
ditangani *class weight*).

## 3.6 Tahapan Penelitian

1. **Pengumpulan data** OHLCV & headline.
2. **Preprocessing teks**: strip, dedup `(Title,Date)`, buang headline < 3 kata.
3. **FinBERT scoring** (`ProsusAI/finbert`): tiap headline → label
   (pos/neu/neg), `sentiment_score` (confidence), `sentiment_numeric` (±1/0).
4. **Agregasi sentimen harian** (*probability-weighted*):
   `signed = numeric × score`; `sentiment_mean` = mean harian; *neutral band* 0.05.
5. **Preprocessing harga + indikator teknikal** (`compute_technical_indicators`),
   lalu **transformasi stasioner** (level harga dibuang).
6. **Merge & alignment temporal**: *left join* per Date; sentimen di-**`shift(1)`**
   (anti *look-ahead*: hari *t* hanya melihat sentimen *t−1*); `inf`→`NaN`→`dropna`.
7. **Feature engineering & target**: 10 fitur stasioner; target arah 5-hari, filter ±1%.
8. **Windowing & scaling**: *sliding window* 20 hari; `StandardScaler`
   **fit train-only** (anti *leakage*) di setiap split.
9. **Pemodelan LSTM** (lihat §3.7).
10. **Strategi anti-overfitting**: kapasitas kecil, dropout 0.5, L2
    (`weight_decay=1e-4`), *class weight*, **seed ensemble 5 model**, *gradient
    clipping*, *early stopping*.
11. **Pelatihan & seleksi**: *grid search* (hidden/layer/dropout/lr/window)
    diseleksi by val AUC → `best_params`, `best_window`, `best_lr`.
12. **Evaluasi** (lihat §3.8).

## 3.7 Arsitektur Model (ringkas)

```
Input (batch, 20, 10)
  → LSTM(hidden=32, layers=1, batch_first)
  → mean-pooling sepanjang waktu → (batch, 32)
  → Dropout(0.5) → Linear(32→2) → softmax → P(Down), P(Up)
```
- *Framework*: **PyTorch** (TensorFlow tidak terpasang; torch sudah ada via FinBERT).
- *Loss*: `CrossEntropyLoss` dengan *class weight* inverse-frequency.
- Kapasitas sengaja kecil (data train per fold hanya ratusan sampel).

## 3.8 Protokol Evaluasi & Metrik

**a. Split kronologis** 70/15/15 (berbasis waktu, bukan acak).

**b. Rolling-window Walk-Forward (hakim utama).** 5 *fold*; tiap *fold* dilatih
hanya pada `WF_TRAIN_SIZE` sampel **terbaru** sebelum blok test
(`tr_lo = max(0, te_start − WF_TRAIN_SIZE)`). Alasan: melawan *concept drift*
(rezim pasar berubah). Konfigurasi model = `best_params`/`best_lr` dari grid.

**c. Kalibrasi & threshold (anti-leakage, hanya dari val):**
- **Kalibrasi Platt**: fit `LogisticRegression(p_val→y_val)`, transform p_test
  (monotonik → AUC tidak berubah, probabilitas lebih terkalibrasi).
- **Threshold Youden's J** (J = TPR − FPR) — dipilih, **bukan F1**, karena F1
  pada kelas tak seimbang mendorong prediksi kolaps "all-Up" sehingga
  Accuracy/F1 menyesatkan.

**d. Analisis sensitivitas** `WF_TRAIN_SIZE ∈ {200,300,400,500,expanding}`:
melaporkan **semua** hasil (uji *robustness*, anti *cherry-pick*).

**e. Baseline**: LSTM vs Always-Up vs Random.

**Metrik:**
- **AUC-ROC** = metrik utama (bebas *threshold*).
- **Pooled AUC** = AUC atas seluruh prediksi OOS digabung → agregat paling
  konservatif/jujur. Bila *mean per-fold* ≫ *pooled*, artinya antar-fold arahnya
  bertentangan (sign-flip rezim) → tidak ada *edge* global yang konsisten.
- Accuracy, Precision, Recall, F1 (pada threshold Youden's J), Confusion Matrix.

## 3.9 Hasil & Pembahasan

**Walk-forward (window=20, 5 fold, seed ensemble 5):** mean AUC bergerak di
kisaran **0.51–0.60** bergantung `WF_TRAIN_SIZE`, dengan **std besar (0.09–0.18)**
dan **pooled AUC 0.49–0.55**.

**Tabel sensitivitas `WF_TRAIN_SIZE`:**

| train_size | mean_auc | std_auc | mean_acc | mean_f1 | pooled_auc |
|---|---|---|---|---|---|
| 200 | 0.5966 | 0.0856 | 0.6029 | 0.7455 | **0.5020** |
| 300 | 0.5154 | 0.1738 | 0.6029 | 0.7455 | 0.5471 |
| 400 | 0.5723 | 0.1794 | 0.5711 | 0.6813 | 0.5417 |
| 500 | 0.5056 | 0.1829 | 0.4610 | 0.5272 | 0.4938 |
| expanding | 0.5800 | 0.1338 | 0.5341 | 0.6385 | 0.4945 |

**Interpretasi (penting & jujur):**
1. **Hasil rapuh.** `mean_auc` tidak monoton terhadap ukuran train dan ber-std
   besar → "yang terbaik" (200 @ 0.60) berpotensi kebetulan, bukan keunggulan.
2. **mean ≫ pooled.** Contoh train_size=200: mean 0.597 tetapi **pooled 0.502
   (≈ acak)**. Ini menandakan tiap *fold* punya struktur lokal, tetapi
   **antar-rezim arahnya saling membatalkan** → tidak ada *edge* OOS global.
3. **Pooled AUC bertahan ~0.49–0.55** untuk semua setting → keunggulan
   konsisten **sangat tipis / tidak ada**, selaras **EMH semi-kuat** dan
   literatur (LSTM+FinBERT ≈ AUC 0.562, efek "slight").
4. **Sign-flip rezim**: hubungan sentimen→return bersifat *momentum* (2022) lalu
   *kontrarian* (2023, "wall of worry"), menjelaskan *fold* yang inversi (AUC<0.5).
5. **Metrik threshold harus hati-hati** — gunakan AUC/pooled AUC sebagai dasar
   penilaian, bukan accuracy/F1 (rentan artefak kelas tak seimbang).

## 3.10 Kesimpulan & Keterbatasan

**Kesimpulan:** Sinyal sentimen→arah harga 5-hari S&P 500 bersifat **lemah,
bergantung rezim, dan mendekati batas pasar efisien** (pooled AUC ~0.50–0.55).
Model **bukan prediktor arah yang andal**. Kontribusi penelitian terletak pada
**(a) metodologi yang ketat & jujur** (early fusion, anti-leakage, seed ensemble,
rolling walk-forward, kalibrasi, Youden's J, analisis sensitivitas) dan
**(b) temuan empiris** bahwa keunggulan prediktif tidak bertahan lintas rezim.

**Keterbatasan:**
- Data uji per *fold* kecil (~93 sampel) → AUC *fold* tunggal *noisy*.
- Periode harga terbatas (2018–2024) → jumlah rezim sedikit.
- Sebagian sentimen bersifat **reaktif** (berita mengikuti harga).
- *Concept drift* tidak sepenuhnya teratasi oleh rolling window.

**Saran lanjutan:** horizon/target alternatif, fitur rezim eksplisit (volatilitas/
tren), atau model adaptif rezim — dengan disiplin menghindari *overfitting protokol*
(tidak menyetel hyperparameter sampai walk-forward "terlihat bagus").

## 3.11 Implementasi & Reproduksi

```bash
# 1) Regenerasi sentimen harian (FinBERT scoring — lama)
uv run python scripts/regenerate_sentiment_weighted.py

# 2) Notebook model: notebooks/03_LSTM_experiment.ipynb → Restart & Run All
#    Urutan kunci: Cell 1 (import) → 3–7 (data+fitur) → 10–11 (model+helper)
#    → 13–14 (grid) → 16 (kurva) → 18–19 (eval) → 21 (walk-forward)
#    → 23 (sensitivitas) → 25 (simpan artefak v5)
```

**Artefak (v5):** `direction_classifier_v5.pt`, `scaler_v5.joblib`,
`metadata_v5.json`, `lstm_train_val_auc_v5.png`,
`lstm_wf_trainsize_sensitivity_v5.png`, `lstm_confusion_dist.png`
(di `data/artifacts/...`).
