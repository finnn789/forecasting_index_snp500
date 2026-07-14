# Plan: Notebook Sesuai Batasan Masalah Skripsi (BAB I) — LSTM vs FinBERT-LSTM

> **Status: BELUM DIEKSEKUSI.** Disimpan atas permintaan user untuk didelegasikan nanti
> (kemungkinan ke sub-agent/sesi terpisah). Jangan mulai implementasi sebelum diminta.
>
> Sumber kebenaran scope: `E:\SKRIPSI_ARIFIN\LIST_BAB_SKRIPSI\FIX_From_Pak_Eka\BAB_I_Muhammad Arifin_Rev_2.docx`
> ("PREDIKSI PERGERAKAN INDEKS PASAR SAHAM BERDASARKAN SENTIMEN BERITA KEUANGAN DI YAHOO
> FINANCE MENGGUNAKAN MODEL FINBERT DAN LONG SHORT-TERM MEMORY").

## Context

Notebook 03 (`03_LSTM_experiment.ipynb`, metodologi "v5") dan turunannya (notebook 06,
horizon 2008-2024) dibangun sebagai riset EKSPLORATIF yang sengaja SANGAT ketat secara
metodologis (walk-forward rolling 8-fold, AUC-ROC sebagai metrik utama, ensemble 5-seed,
kalibrasi Platt, threshold tuning Youden's J, sensitivity analysis). Itu bagus untuk
mengeksplorasi batas kemampuan prediksi (EMH), TAPI **jauh melebihi** apa yang diminta
Batasan Masalah skripsi — yang eksplisit membatasi ke **4 metrik** (Accuracy, Precision,
Recall, F1-Score) tanpa walk-forward/AUC/ensemble/kalibrasi.

Selain evaluasi, ditemukan beberapa ketidakcocokan lain antara notebook 03/06 vs Batasan
Masalah skripsi:

| Aspek | Batasan Masalah Skripsi (BAB I) | Notebook 03/06 (v5) |
|---|---|---|
| Horizon prediksi | 1 hari (lag-1): label 1 jika Close[t] > Close[t-1] | 5 hari ke depan + filter buang zona netral ±1% |
| Fitur | OHLCV mentah + skor sentimen FinBERT harian (TANPA indikator teknikal RSI/MACD/BB) | 10 fitur (8 indikator teknikal stasioner + 2 sentimen) |
| Tuning hyperparameter | **Random Search**: units/layer, dropout rate, jenis optimizer, fungsi aktivasi, learning rate, epochs, batch size | Grid Search manual 5 kombinasi tetap, optimizer selalu Adam |
| Split evaluasi | Train/val/test biasa (tidak disebut walk-forward) | Walk-forward rolling 8-fold + sensitivity sweep |
| Rentang data | 2018-01-01 s.d. 2024-03-04 | Notebook 06 malah 2008-2024 |
| Jumlah model | Tepat 2: (a) LSTM murni OHLCV (baseline), (b) FinBERT-LSTM | (sudah sejalan secara konsep — sentimen vs non-sentimen) |
| Metrik evaluasi | HANYA Accuracy, Precision, Recall, F1-Score | + AUC-ROC, pooled/mean AUC, confusion matrix, class-collapse diagnosis |
| UI/Frontend | **Batasan Masalah eksplisit: TIDAK termasuk scope skripsi** | `ui-stock-prediction` (Model Training + rencana Prediction page) sudah dibangun — di luar scope skripsi, boleh tetap ada sbg demo tapi TIDAK perlu disentuh utk notebook ini |

**Tujuan notebook baru ini:** replikasi metodologi yang PERSIS sesuai Batasan Masalah &
Tujuan Khusus BAB I — supaya hasilnya langsung relevan untuk BAB III (Metodologi) dan
BAB IV (Hasil & Pembahasan) skripsi, tanpa kelebihan metodologis yang bisa dipertanyakan
dosen pembimbing/penguji ("kenapa pakai walk-forward padahal di proposal tidak disebut?").

## Rumusan Masalah & Hipotesa yang Harus Dijawab (dari BAB I, untuk konteks BAB IV nanti)

1. FinBERT dipakai zero-shot (`ProsusAI/finbert`, TANPA fine-tuning) untuk skor sentimen — **sudah ada**, reuse pipeline sentimen produksi (`sentiment_service`/`headlines_daily_sentiment.csv`).
2. LSTM dibangun dengan skor sentimen FinBERT sbg fitur tambahan — 2 model dibandingkan.
3. Kinerja FinBERT-LSTM diukur pakai Accuracy/Precision/Recall/F1.
4. **Hipotesa utama yang harus dijawab notebook ini**: apakah FinBERT-LSTM (OHLCV+sentimen) mengungguli LSTM murni (OHLCV saja) pada ke-4 metrik itu? Ini WAJIB ditampilkan sebagai perbandingan berdampingan yang eksplisit di akhir notebook.

## Rancangan Notebook Baru: `notebooks/07_LSTM_FinBERT_skripsi_scoped.ipynb`

### Bagian 1 — Data (reuse, TIDAK reinvent)
- OHLCV: `data/raw/stocks/GSPC_2018_2024.csv` → `StockPreprocessor.clean()` (reuse, sudah ada) — TIDAK perlu 2008-2024.
- Sentimen: `data/processed/sentiment/headlines_daily_sentiment.csv` (skor FinBERT harian, sudah ada, pre-trained tanpa fine-tuning — sesuai Batasan Masalah poin 4).
- Merge on Date, TANPA `compute_technical_indicators()` (Batasan Masalah tidak menyebut indikator teknikal — fitur cuma OHLCV mentah + skor sentimen).
- **Fitur Model A (baseline)**: `Open, High, Low, Close, Volume` (mirror `OHLCV_FEATURE_COLS` di `dataset_builder.py`, reuse konstanta itu).
- **Fitur Model B (FinBERT-LSTM)**: `Open, High, Low, Close, Volume, sentiment_mean` (mirror `FEATURE_COLS` di `dataset_builder.py`, reuse konstanta itu).
- Label: 1-hari horizon, `target = 1 jika Close[t+1] > Close[t] else 0` (TANPA filter zona netral — beda dari notebook 03 yg horizon=5 & threshold=0.01). Ini sesuai konvensi label produksi (`build_dataset()` di `dataset_builder.py` sudah pakai pola ini) — reuse logic label yang sama, jangan tulis ulang.
- Split: kronologis train/val/test (sarankan tetap sederhana — persentase 70/15/15 ATAU by-date seperti `build_dataset()` produksi; **keputusan terbuka**, didiskusikan saat delegasi — yang penting BUKAN walk-forward berulang, cukup SATU split tetap).
- Scaling: MinMaxScaler atau StandardScaler fit HANYA di train (anti-leakage tetap dipertahankan — ini prinsip metodologis universal, bukan "kelebihan", jadi tetap dipakai).

### Bagian 2 — Arsitektur LSTM (dipakai identik utk Model A & Model B, cuma `input_size` beda)
Model sederhana: `nn.LSTM` → ambil output (last timestep ATAU mean-pooling, pilih salah satu &
konsisten) → dense head → output biner. **Bukan** replika `LSTMSoftmaxClassifier` (2-class
softmax dari notebook05) atau `LSTMClassifier` v5 (mean-pooling dgn hidden=32 tetap) secara
kaku — arsitektur PERSIS-nya harus fleksibel karena akan di-*search* (lihat Bagian 3), bukan
hardcode satu konfigurasi.

### Bagian 3 — Hyperparameter Tuning: RANDOM SEARCH (bukan Grid Search)
Sesuai Batasan Masalah poin 4, search space mencakup:
- Jumlah units per layer (mis. sample dari {16,32,64,128})
- Jumlah layer (mis. {1,2})
- Dropout rate (mis. uniform 0.2–0.5)
- Jenis optimizer (mis. {Adam, RMSprop, SGD})
- Fungsi aktivasi (**catatan desain**: PyTorch `nn.LSTM` tidak native expose parameter
  "activation function" yang bisa diganti tanpa custom cell — kemungkinan besar yang
  dimaksud BAB I adalah aktivasi di dense/FC head setelah LSTM, mis. {ReLU, Tanh, Sigmoid}.
  **Keputusan terbuka**: konfirmasi ke user/pembimbing apakah ini cukup, atau perlu custom
  LSTMCell dgn recurrent-activation yg bisa diganti seperti di Keras. Direkomendasikan:
  interpretasi FC-head activation, karena itu yg paling natural & correct secara teknis di
  PyTorch tanpa over-engineering.)
- Learning rate (mis. log-uniform 1e-4–1e-2)
- Jumlah epochs (mis. {30,50,80})
- Batch size (mis. {16,32,64})

Jalankan **N iterasi random sampling** (mis. 15-20 kombinasi acak, bukan cartesian grid
penuh) dari search space di atas, untuk MASING-MASING model (A dan B) secara terpisah
(supaya hyperparameter optimal boleh beda antar model — best_config_A vs best_config_B).
Kriteria seleksi: val accuracy ATAU val F1 (**keputusan terbuka** — tentukan salah satu,
dokumentasikan alasannya di notebook karena BAB III skripsi perlu menjelaskan kriteria ini).

### Bagian 4 — Training Final & Evaluasi (HANYA 4 metrik, TIDAK LEBIH)
- Latih model final (A dan B) dengan best_config masing-masing hasil Random Search.
- Evaluasi test-set **HANYA**: Accuracy, Precision, Recall, F1-Score (`sklearn.metrics`).
- **TIDAK** menghitung/menampilkan AUC-ROC, confusion matrix visual, class-collapse
  diagnosis, atau metrik lain di luar 4 itu — supaya notebook match 1:1 dengan Tujuan
  Khusus BAB I (dosen penguji akan mencocokkan bab metodologi vs implementasi).
- Boleh tetap tampilkan confusion matrix RAW (tn/fp/fn/tp) sebagai pendukung angka
  precision/recall (lazim di BAB IV skripsi), tapi bukan sebagai "metrik tambahan".

### Bagian 5 — Perbandingan Model A vs Model B (menjawab Hipotesa #4 BAB I)
Tabel & narasi eksplisit: apakah Accuracy/Precision/Recall/F1 Model B (FinBERT-LSTM) >
Model A (LSTM-OHLCV)? Ini bagian PALING PENTING dari notebook — jawaban langsung ke
Rumusan Masalah #4 dan Hipotesa #4 BAB I. Laporkan apa adanya (kalau ternyata sentimen
TIDAK membantu, itu tetap temuan valid & harus dilaporkan jujur — prinsip anti p-hacking
yang sama seperti notebook-notebook sebelumnya, BUKAN berarti harus "diakali" supaya
Model B menang).

### Bagian 6 — Simpan Artefak
Nama terisolasi (mis. `lstm_baseline_skripsi.pt` / `finbert_lstm_skripsi.pt` + scaler +
metadata per model) — TIDAK menimpa artefak produksi atau notebook 03/05/06 manapun.

## Yang SENGAJA TIDAK Dikerjakan (di luar scope permintaan ini)
- Walk-forward validation, AUC-ROC, ensemble multi-seed, kalibrasi Platt, threshold tuning
  Youden's J, sensitivity sweep — semua ini bagus tapi bukan bagian dari Batasan Masalah
  BAB I. Kalau nanti pembimbing MEMINTA analisis tambahan itu di BAB IV/V (mis. sbg
  "keterbatasan penelitian" atau saran penelitian lanjutan), itu keputusan terpisah.
- Perubahan apa pun ke `ui-stock-prediction` (Batasan Masalah eksplisit: skripsi tidak
  mencakup UI/deployment).
- Perubahan ke rentang data 2008-2024 (notebook 06) — skripsi scope-nya 2018-2024 saja.

## Keputusan Terbuka (perlu dikonfirmasi user saat delegasi dimulai)
1. Split train/val/test: persentase kronologis (mis. 70/15/15) atau by-date seperti
   `build_dataset()` produksi?
2. Interpretasi "fungsi aktivasi" dalam Random Search: aktivasi FC-head (direkomendasikan)
   atau custom recurrent-activation LSTM?
3. Kriteria seleksi Random Search: val accuracy atau val F1?
4. Jumlah iterasi Random Search (disarankan 15-20, bisa disesuaikan kapasitas komputasi).
5. Last-timestep vs mean-pooling untuk output LSTM (notebook 03 pakai mean-pooling,
   produksi pakai last-timestep — pilih salah satu, dokumentasikan alasan di BAB III).

## Verifikasi (setelah notebook ditulis nanti)
1. `nbformat.validate()` + `ast.parse()` tiap cell code (pola sama seperti verifikasi notebook 06).
2. Cross-check isi notebook vs BAB I: tiap Rumusan Masalah & Tujuan Khusus harus ada
   cell yang menjawabnya secara eksplisit (baik lewat kode maupun markdown narasi).
3. Pastikan HANYA 4 metrik yang muncul di bagian evaluasi akhir (Accuracy/Precision/Recall/F1) — audit manual sebelum diserahkan.
