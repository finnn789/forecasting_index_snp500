# Arsitektur & Metodologi Model FinBERT-LSTM

> Ringkasan metodologis sistem prediksi arah harga S&P 500 (^GSPC) yang
> menggabungkan **sentimen berita (FinBERT)** dan **deret waktu harga (LSTM)**
> via *early fusion*. Dokumen ini menjelaskan tiap komponen end-to-end agar
> metodologinya dapat dipahami untuk penulisan skripsi.
>
> Status: **v5** (notebook `notebooks/03_LSTM_experiment.ipynb`).
> Sumber kebenaran kode: notebook 03 + `scripts/regenerate_sentiment_weighted.py`
> + `pipeline/feature_engineering/technical_indicators.py`.

---

## 1. Gambaran Umum

Tujuan: klasifikasi **biner arah harga** — apakah harga S&P 500 **naik atau turun
dalam 5 hari ke depan**. Dua sumber informasi digabung:

```
                 ┌────────────────────────────┐
  Berita (CSV) → │  FinBERT (sentiment)        │ → sentiment_mean harian
                 └────────────────────────────┘            │
                                                            │  (early fusion:
                                                            │   gabung per-hari)
                 ┌────────────────────────────┐            ▼
  OHLCV (CSV)  → │  Indikator teknikal         │ →  10 fitur stasioner per hari
                 │  (RSI, MACD, BB, dst.)      │            │
                 └────────────────────────────┘            ▼
                                              ┌──────────────────────────────┐
                                              │  Sliding window (20 hari)      │
                                              │  → LSTM (PyTorch) → P(Up)      │
                                              └──────────────────────────────┘
                                                            │
                                  Evaluasi: walk-forward rolling + kalibrasi + threshold
```

**Catatan deviasi stack:** LSTM diimplementasikan dengan **PyTorch**, bukan
TensorFlow (TF tidak terpasang; `torch` sudah jadi dependency FinBERT).

---

## 2. Komponen A — Sentimen Berita (FinBERT)

Skrip otoritatif: `scripts/regenerate_sentiment_weighted.py`.
Pra-pemrosesan teks & inferensi: `pipeline/preprocessing/text_preprocessor.py`
(`TextPreprocessor`). Model: **`ProsusAI/finbert`** (snapshot lokal di
`models/finbert/models--ProsusAI--finbert/...`).

### 2.1 Sumber & pembersihan
- Input: `data/raw/news/sp500_headlines_2008_2024.csv` (~19k headline).
- Cleaning ringan (`clean_headlines`):
  - strip whitespace pada `Title`;
  - drop judul kosong / NaN;
  - drop duplikat `(Title, Date)`;
  - filter judul **< 3 kata**.

### 2.2 Skoring FinBERT
- Tiap headline → FinBERT menghasilkan **label** (`positive`/`neutral`/`negative`)
  + **`sentiment_score`** (probabilitas/confidence kelas terpilih).
- `sentiment_numeric` = encoding label: `positive → +1`, `neutral → 0`,
  `negative → -1`.
- Batch = 32, device auto (GPU `cuda:0` jika ada, jika tidak CPU).

### 2.3 Probability-weighted signed score (kunci metodologi)
Skor per-headline dibobot oleh keyakinannya:

```
signed_score = sentiment_numeric × sentiment_score
```

Artinya headline "negative" yang sangat yakin (score≈0.95) memberi kontribusi
≈ −0.95, sedangkan yang ragu (score≈0.55) hanya ≈ −0.55. Ini lebih halus
daripada sekadar menghitung jumlah label.

### 2.4 Agregasi harian (`aggregate_daily`)
Groupby `Date` menghasilkan (`data/processed/sentiment/headlines_daily_sentiment.csv`):

| Kolom | Definisi |
|---|---|
| `headline_count` | jumlah headline hari itu |
| `sentiment_mean` | **mean(`signed_score`)** hari itu — fitur sentimen utama |
| `sentiment_pos` / `sentiment_neg` / `sentiment_neu` | proporsi label per hari |
| `sentiment_label` | label harian via *neutral band* `|mean| < 0.05` |

---

## 3. Komponen B — Harga & Feature Engineering

Data OHLCV: `data/raw/stocks/GSPC_2018_2024.csv` (2018–2024).
Indikator: `pipeline/feature_engineering/technical_indicators.py`
(`compute_technical_indicators`).

### 3.1 Prinsip: fitur harus STASIONER
Level harga (Close, EMA, band BB) **tidak stasioner** dan menyesatkan LSTM.
Karena itu semua fitur dinyatakan sebagai **rasio / selisih / persentase**.
Indikator dihitung **sebelum** kolom level OHLCV di-drop, dan semuanya **causal**
(rolling/ewm ke belakang — tidak ada look-ahead).

### 3.2 Daftar 10 fitur (`FEATURE_COLS` v5)

| # | Fitur | Bentuk stasioner |
|---|---|---|
| 1 | `ret_close` | `Close.pct_change()` |
| 2 | `ret_volume` | `Volume.pct_change()` |
| 3 | `rsi_14` | RSI (0–100, sudah stasioner) |
| 4 | `macd_hist` | MACD − signal (selisih) |
| 5 | `bb_bandwidth` | (upper−lower)/mid (rasio) |
| 6 | `volatility_20` | std(return) 20 hari |
| 7 | `close_vs_ema20` | `Close/EMA20 − 1` |
| 8 | `bb_pct_b` | `(Close−lower)/(upper−lower)` |
| 9 | `sentiment_mean` | sentimen harian (di-`shift(1)`) |
| 10 | `sentiment_mean_ma3` | rolling-MA3 sentimen (di-`shift(1)`) |

> Fitur lama yang **dibuang** berbasis bukti korelasi/MI: `ret_open/high/low`
> (redundan dgn `ret_close`), `sentiment_neg`, `sentiment_pos`, `headline_count`.

### 3.3 Anti look-ahead pada sentimen
Seluruh kolom sentimen di-`shift(1)`: pada hari *t* model hanya "melihat"
sentimen hari *t−1*. `sentiment_mean_ma3` dihitung **sebelum** shift agar
smoothing berbasis data aktual, lalu ikut di-shift.

### 3.4 Penanganan nilai bermasalah
- Hari dengan `headline_count ≤ 2` → sentimen dinetralkan (0.0) karena estimasi
  tidak andal.
- `inf` (mis. `ret_volume` saat `Volume=0`) diganti `NaN` lalu di-`dropna`
  (**catatan penting:** `dropna` tidak membuang `inf`).

### 3.5 Target & windowing
- **Horizon = 5 hari**; `fwd_ret = Close.pct_change(5).shift(-5)`.
- **Filter zona netral ±1%**: buang hari `|fwd_ret| < 0.01` (sideways) → kelas
  lebih bersih & seimbang.
- Label: `target = 1 jika fwd_ret > 0, else 0`.
- *Sliding window* **20 hari** → `X` shape `(N, 20, 10)`.

> Dasar pemilihan horizon-5: korelasi sentimen↔return **1-hari r≈0.02 (nol)**,
> **5-hari r≈0.275**, **MA3↔5-hari r≈0.363** (sinyal terkuat).

### 3.6 Scaling anti-leakage
`scale_sequences()` mem-*fit* `StandardScaler` **hanya pada split train**, lalu
mentransform val/test. Helper ini dipakai konsisten di **setiap** tempat data
di-split (grid search, eval test, dan tiap fold walk-forward).

---

## 4. Arsitektur Model (`LSTMClassifier`, PyTorch)

```
Input (batch, 20, 10)
   │
   ├─ nn.LSTM(input=10, hidden=32, num_layers=1, batch_first=True)
   │
   ├─ mean-pooling sepanjang dimensi waktu  → (batch, 32)
   │
   ├─ Dropout(0.5)
   │
   └─ Linear(32 → 2)  → logits → softmax → P(Down), P(Up)
```

- **Sengaja berkapasitas kecil** (hidden 32, 1 layer) — data train per fold hanya
  ratusan sampel; model besar pasti overfit.
- Mean-pooling (bukan hanya hidden state terakhir) → lebih stabil.

---

## 5. Strategi Anti-Overfitting (PART B)

| Teknik | Detail | Tujuan |
|---|---|---|
| Kapasitas kecil | hidden=32, layers=1 | kurangi varians |
| Dropout 0.5 | di layer FC | regularisasi |
| L2 (`weight_decay=1e-4`) | Adam | regularisasi bobot |
| Class weight | inverse-frequency per split | cegah degenerate "selalu Up" |
| **Seed ensemble (5 model)** | rata-rata `P(Up)` 5 seed | turunkan varians prediksi |
| Gradient clipping | `max_norm=1.0` | stabilkan pelatihan |
| Early stopping | by val AUC, patience 7 | hindari over-training |
| `ReduceLROnPlateau` | mode=max, patience=3, factor=0.5 | adaptasi LR (tanpa arg `verbose` — dihapus di torch 2.x) |

---

## 6. Protokol Evaluasi

### 6.1 Split kronologis
70% train / 15% val / 15% test (berbasis urutan waktu, **bukan** shuffle).

### 6.2 Grid search
5 konfigurasi kapasitas kecil (`num_layers=1`, dropout 0.4–0.5, window 10/20/30,
lr 1e-3/5e-4). Pemilihan berdasarkan **val AUC**; `best_params`, `best_window`,
`best_lr` diteruskan ke pelatihan final.

### 6.3 Kurva Train vs Val AUC
Plot AUC train & val per epoch (bukti visual overfitting terkendali).

### 6.4 Evaluasi test (seed ensemble)
Latih 5 model (seed 0–4) → `ensemble_predict` (rata-rata `P(Up)`) → metrik test.

### 6.5 **Rolling-window Walk-Forward** (hakim utama)
- 5 fold *expanding* → diganti **rolling**: tiap fold dilatih hanya pada
  `WF_TRAIN_SIZE = 400` sampel **terbaru** sebelum blok test
  (`tr_lo = max(0, te_start − 400)`).
- **Alasan:** menyerang *concept drift*. Expanding window membuat model terjangkar
  ke rezim lama; rolling membuatnya adaptif ke rezim terkini.
- Tiap fold: scaling train-only → seed ensemble 5 model → prediksi test fold.
- **Konfigurasi model konsisten dengan grid:** `WF_CONFIG = best_params`,
  `WF_LR = best_lr`, `WF_WINDOW = best_window` (bukan di-hardcode).
- Logika WF dibungkus fungsi `run_walk_forward(wf_train_size, config, lr, window, ...)`
  (`wf_train_size=None` ⇒ expanding).

### 6.5b Analisis sensitivitas `WF_TRAIN_SIZE` (validasi, anti p-hacking)
Karena ukuran train rolling adalah hyperparameter yang dipilih manual, ada cell
**sweep `WF_TRAIN_SIZE ∈ {200, 300, 400, 500, expanding}`** yang melaporkan
mean/std AUC + pooled AUC untuk **semua** ukuran (bukan memilih yang terbaik).
Output: tabel `wf_sens_df` + plot `lstm_wf_trainsize_sensitivity_v5.png`, dan
tersimpan di `metadata_v5['walk_forward']['train_size_sensitivity']`. Ini bukti
robustness terhadap concept drift — bukan justifikasi cherry-pick.

### 6.6 Kalibrasi & threshold (anti-leakage, **hanya dari val**)
- **Kalibrasi Platt** (`calibrate_platt`): fit `LogisticRegression(p_val → y_val)`,
  transform `p_test`. Monotonik → **AUC tidak berubah**, tapi probabilitas
  terkalibrasi (pooled AUC & threshold lebih bermakna).
- **Threshold tuning Youden's J** (`tune_threshold`, default `metric='youden'`):
  pilih threshold yang memaksimalkan **J = TPR − FPR** pada val.
  - *Mengapa Youden's J, bukan F1:* pada kelas tak seimbang, F1 mendorong
    threshold runtuh ke prediksi **"all-Up"** (Recall=1.0, Precision=base-rate),
    sehingga Accuracy/F1 yang dilaporkan **menyesatkan**. Youden's J seimbang
    antara sensitivitas & spesifisitas → metrik mencerminkan diskriminasi nyata.

### 6.7 Tabel baseline
Bandingkan LSTM seed-ensemble vs **Always-Up** (AUC=0.5) vs **Random** (≈0.5),
metrik AUC + Accuracy.

---

## 7. Metrik & Hasil (ringkas)

- **AUC adalah metrik utama** (bebas threshold, jujur). Accuracy/Precision/Recall/F1
  dilaporkan pada threshold Youden's J dari val.
- Walk-forward rolling: **mean AUC ≈ 0.57 ± 0.17**. Fold 1–4 AUC ≈ 0.60–0.71
  (sinyal nyata di rezim 2021–2022), namun **fold 2023–2024 inversi (AUC < 0.5)**.
- Pooled AUC (prob terkalibrasi) ≈ 0.54.
- Selaras dengan benchmark literatur (LSTM+FinBERT ≈ AUC **0.562**, efek "slight").

---

## 8. Interpretasi & Keterbatasan (untuk Bab Pembahasan)

1. **Sinyal lemah & dekat batas EMH.** AUC ~0.57 OOS = edge tipis, konsisten
   dengan pasar semi-efisien. Bukan kegagalan — temuan yang defensible.
2. **Concept drift / sign-flip rezim.** Hubungan sentimen→return **momentum** di
   2022 (berita buruk → turun lanjut) **membalik jadi kontrarian** di 2023
   ("wall of worry"). Model satu-rezim salah arah → fold 2023 AUC < 0.5.
   Rolling window meringankan, tidak menghilangkan.
3. **Sentimen sebagian REAKTIF** (berita mengikuti harga) → plafon AUC realistis
   0.55–0.60, bukan lebih tinggi.
4. **Jangan over-claim metrik threshold.** Lihat catatan §6.6 — gunakan AUC.
5. **Data uji terbatas** (per fold ~93 sampel setelah filter ±1%).

---

## 9. Artefak (v5)

| File | Isi |
|---|---|
| `data/artifacts/lstm_weights/direction_classifier_v5.pt` | list 5 `state_dict` (seed ensemble) |
| `data/artifacts/lstm_weights/scaler_v5.joblib` | `StandardScaler` (fit train final) |
| `data/artifacts/lstm_weights/metadata_v5.json` | feature_cols, best_params, window, horizon, threshold, metrik test (+tuned), walk_forward (rolling + fold_metrics) |
| `data/artifacts/lstm_train_val_auc_v5.png` | kurva train vs val AUC |
| `data/artifacts/lstm_confusion_dist.png` | confusion matrix + distribusi P(Up) |

---

## 10. Reproduksi

```bash
# (1) Regenerasi sentimen harian (sekali, lama — FinBERT scoring)
uv run python scripts/regenerate_sentiment_weighted.py

# (2) Notebook model — Restart & Run All
#     notebooks/03_LSTM_experiment.ipynb  (urut dari Cell 1)
```

> Knob iterasi utama: `WF_TRAIN_SIZE` (coba 300/400/500) — terlalu kecil =
> underfit, terlalu besar = kembali terjangkar rezim lama. Hindari menyetel
> sampai WF "terlihat bagus" → itu *overfitting protokol validasi* (p-hacking).
