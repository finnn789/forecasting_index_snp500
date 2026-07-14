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

## [2026-07-14] Notebook 07 — Implementasi Plan Skripsi-Scoped (LSTM vs FinBERT-LSTM)

### Status: NOTEBOOK DITULIS, BELUM DIEKSEKUSI
Melanjutkan rencana tersimpan `code_plan/skripsi_scoped_lstm_finbert_plan.md` (dipilih user
dari 2 plan pending, yang satu lagi — halaman Prediction FE+BE — masih menunggu).

### 5 Keputusan Terbuka — Dikonfirmasi User
1. Split train/val/test: **persentase kronologis 70/15/15** (bukan by-date cutoff produksi)
2. "Fungsi aktivasi" Random Search: **aktivasi FC-head** `{ReLU,Tanh,Sigmoid}` (bukan custom recurrent-activation LSTM)
3. Kriteria seleksi Random Search: **Val Accuracy**
4. Jumlah iterasi Random Search: **20** per model
5. Output LSTM: **last-timestep** (bukan mean-pooling v5) — user awalnya minta penjelasan trade-off lengkap sebelum memutuskan; direkomendasikan & dipilih karena konsisten model produksi + lebih defensible di sidang
6. (tambahan) Window size: **fixed 10**, tidak ikut di-search

### File Dibuat
`notebooks/07_LSTM_FinBERT_skripsi_scoped.ipynb` — dibuat via script generator nbformat
(bukan Jupyter MCP, demi hemat token) di scratchpad, lalu diverifikasi `nbformat.validate()`
+ `ast.parse()` tiap cell + scan larangan istilah (auc/walk_forward/ensemble/platt/youden
tidak boleh muncul di code cell). 24 cell (10 markdown + 14 code), semua belum dieksekusi.

Reuse: `dataset_builder.load_joined()`/`load_ohlcv_only()` (tidak reinvent). Model A=OHLCV-only
baseline, Model B=FinBERT-LSTM. Custom `FlexibleLSTMClassifier` (beda dari
`LSTMDirectionClassifier`/`LSTMSoftmaxClassifier` produksi — sengaja fleksibel utk Random
Search). Evaluasi HANYA Accuracy/Precision/Recall/F1. Artefak rencana simpan ke
`data/artifacts/lstm_weights/{lstm_baseline_skripsi,finbert_lstm_skripsi}.*` (belum
benar-benar tersimpan krn notebook belum dijalankan).

### Belum Dikerjakan
- Eksekusi notebook (disarankan via papermill/nbconvert headless, bukan Jupyter MCP cell-by-cell)
- Plan kedua yang masih pending: `code_plan/notebook05_prediction_page_plan.md` (halaman Prediction FE+BE)

## [2026-07-14] Notebook 07 — Iterasi EDA + Cleaning Outlier + Fix Training (user eksekusi sendiri)

User mengeksekusi notebook 07 sendiri di Jupyter-nya sendiri (bukan via Claude), lalu minta
Claude membaca & menganalisis output dari file `.ipynb` yang tersimpan.

### Temuan #1 — Class collapse total di run pertama
Model A (OHLCV): selalu prediksi "turun" (tn=99,fp=0,fn=126,tp=0, precision/recall/f1=0).
Model B (FinBERT-LSTM): selalu prediksi "naik" (tn=0,fp=97,fn=0,tp=124, recall=1.0 tapi itu
gejala collapse, bukan prestasi). 18-20 dari 20 iterasi Random Search collapse ke val_acc
identik → bukti model tidak belajar sama sekali, akurasi yg terlihat cuma refleksi base-rate
kelas mayoritas per split.

### Iterasi 2 — Tambah EDA (atas permintaan user) + Cleaning Outlier (Capping IQR)
Disisipkan "Bagian 1a — EDA" (missing values, gap tanggal, describe, deteksi outlier IQR +
boxplot, distribusi+skew/kurtosis, time series trend, correlation heatmap, korelasi
fitur-vs-label, label balance per split — semua plot disimpan ke file `eda07_*.png`, tidak
inline) dan "Bagian 1e — Cleaning Outlier" (capping IQR utk `Volume` & `sentiment_mean`,
bounds dihitung HANYA dari train, anti-leakage). **Semua BELUM dieksekusi oleh Claude** —
ditulis via script generator nbformat, HANYA disisipkan (cell lama yg sudah punya output
tetap dipertahankan utuh), user yang menjalankan & menganalisis sendiri.

**Temuan EDA krusial:** korelasi SEMUA fitur (Open/High/Low/Close/Volume/sentiment_mean)
terhadap label < |0.04| — bukti kuantitatif bahwa OHLCV mentah + sentimen mentah nyaris tidak
mengandung sinyal linier utk arah harga 1-hari. Label drift antar split (train naik 55%, val
45%, test 57%). Volume 97 outlier (6.35%), sentiment_mean 44 outlier (2.88%), OHLC = 0 outlier.

**Setelah cleaning dijalankan user:** Model A TIDAK BERUBAH SAMA SEKALI (confusion matrix
identik persis) — bukti capping Volume (korelasi paling lemah, -0.021) tidak berpengaruh.
Model B berubah dari full-collapse (recall=1.0, acc=0.561 "kebetulan" cocok base-rate test)
menjadi mixed-prediction jujur (acc=0.4615, di bawah tebak-acak) — **akurasi turun itu bukan
kemunduran, itu koreksi dari angka yang sebelumnya palsu/menyesatkan (ilusi collapse yg
kebetulan cocok base-rate test 56.5%)**.

### Analisis akar masalah yang disampaikan ke user
1. Non-stasioneritas harga OHLCV mentah (trend naik jangka panjang 2018→2024) membuat
   MinMaxScaler fit-train-only memetakan test-set ke wilayah scaled yg nyaris tak pernah
   dilihat model saat training — root cause utama, BUKAN outlier.
2. Tidak ada class-weighting di loss.
3. Kriteria seleksi Random Search (val accuracy) rentan tertipu label drift antar split.
4. Bug seed hardcode 42 di tiap iterasi Random Search (kurang variasi eksplorasi).
Rekomendasi diberi bertingkat risiko scope (return-transform OHLC/Volume = 🔴 risiko tinggi
vs Batasan Masalah "OHLCV mentah", sentiment_ma3 = 🟡 sedang [sudah pernah ditandai exceed di
`skripsi_scoped_lstm_finbert_plan.md`], class-weighting/kriteria-F1/fix-seed = 🟢 aman karena
murni prosedur training, bukan perubahan fitur).

### Keputusan user: implementasikan HANYA yang 🟢 aman (poin 4-6)
Diimplementasikan (belum dieksekusi, `outputs` di-reset kosong utk cell yg source-nya
berubah): (a) `pos_weight` di `BCEWithLogitsLoss` dihitung dari rasio kelas TRAIN; (b)
kriteria seleksi Random Search diganti Val Accuracy → **Val F1** (didokumentasikan di
markdown Bagian 3 dgn justifikasi: F1 tetap salah satu dari 4 metrik resmi BAB I, jadi
bukan penambahan metrik baru — hanya beda kriteria PEMILIHAN config); (c) fix bug seed,
`train_and_eval` kini dipanggil dgn `seed=seed_dasar+i` per iterasi (bukan hardcode 42).
Cell yang diubah: markdown Bagian 3 (dokumentasi), `train_and_eval`+`run_random_search`,
2 cell pemanggil (Model A seed=42, Model B seed=43). Cell evaluasi/perbandingan/simpan
artefak di bawahnya (Bagian 4-6) outputnya ikut di-reset kosong karena bergantung pada
`best_a`/`best_b` yang akan berubah — TIDAK diubah source-nya.

**Poin 1-3 (return-transform OHLC, volume relatif, sentiment_ma3) SENGAJA TIDAK dikerjakan**
— risiko scope terhadap Batasan Masalah BAB I ("OHLCV mentah"), user diarahkan konfirmasi ke
pembimbing dulu. **Ekspektasi yang dikomunikasikan ke user:** val_acc 70% untuk arah harian
S&P 500 melampaui state-of-the-art akademik (~52-57%, EMH); hasil rendah bahkan setelah fix
adalah temuan valid utk BAB IV/V, bukan kegagalan.

### Belum Dikerjakan (lanjutan)
- User belum menjalankan ulang notebook setelah fix poin 4-6 ini.
- Poin 1-3 menunggu konfirmasi pembimbing sebelum dikerjakan (kalau disetujui).
- Plan kedua yang masih pending: `code_plan/notebook05_prediction_page_plan.md`

## [2026-07-14] Fitur "Random Search Skripsi-Scoped" — BE+FE tab baru di Model Training

User minta notebook 07 diekspos ke `ui-stock-prediction` tab "Model Training" (pola sama
seperti notebook05 sebelumnya). Sebelum implementasi, user tanya trade-off arsitektur
(CrossEntropy+per-epoch SSE vs BCE+per-iterasi) — direkomendasikan **CrossEntropy + SSE
per-epoch** (lebih konsisten dgn UX notebook05 yg sudah ada, live feedback lebih kaya).
User setuju, minta notebook 07 diupdate dulu ke CrossEntropy SEBELUM lanjut BE/FE (supaya
notebook & demo API tetap 1 metodologi yg sama).

### 1. Update notebook 07 → CrossEntropy (2-class softmax)
`FlexibleLSTMClassifier` head diubah `Linear(16,1)`→`Linear(16,2)`; `train_and_eval`/
`evaluate_model` diubah dari `BCEWithLogitsLoss(pos_weight=...)`+sigmoid-threshold ke
`CrossEntropyLoss(weight=...)`+argmax (`compute_class_weights` inverse-frequency 2-kelas,
target di-cast `.long()`). Markdown Bagian 2 & docstring diupdate mencatat perubahan +
alasan (konsistensi dgn rencana BE/FE). Cell 39,40,43,45,47 (bergantung pd model lama)
di-reset kosong. Verifikasi: `nbformat.validate()` + `ast.parse()` 27 code cell OK.

### 2. Backend — 3 file baru + 3 file diedit (terisolasi penuh dari produksi & notebook05)
- **`models/lstm/lstm_model.py`**: tambah `FlexibleLSTMClassifier` (persis notebook 07 —
  last-timestep, aktivasi FC-head configurable {relu,tanh,sigmoid}, 2-class softmax) —
  beda dari `LSTMSoftmaxClassifier` (nb05) yg tak punya FC-head activation configurable.
- **`models/lstm/notebook07_trainer.py`** (baru): konstanta `SEARCH_SPACE`, `N_ITER=20`,
  `WINDOW=10`, nama artefak SAMA PERSIS dgn yg disimpan notebook 07 sendiri
  (`lstm_baseline_skripsi.*` / `finbert_lstm_skripsi.*`) — training via API atau notebook
  saling menimpa/kompatibel by design (dikonfirmasi user, bukan lupa).
- **`models/lstm/notebook07_common.py`** (baru): `run_notebook07_training()` — load+label+
  split 70/15/15+capping IQR (train-only)+scaling(train-only)+windowing(10)+Random Search
  n_iter loop. **SSE 3-level bersarang** (beda dari nb05 yg flat): `start` →
  [`iteration_start` → `epoch`×N → `iteration_end`] × n_iter → `done`/`error`. TANPA
  early-stop (epochs adl hyperparameter yg di-*search*, config jalan penuh).
- **`app/schemas/training.py`**: `SkripsiTrainRequest` (hanya override `n_iter`, search
  space/window TETAP fixed — bukan configurable dari FE, demi konsistensi BAB III),
  `SearchSpaceResponse`.
- **`app/services/training_service.py`**: `get_skripsi_search_space()`,
  `run_skripsi_baseline_stream()` (Model A, `load_ohlcv_only`, cap `["Volume"]`),
  `run_skripsi_finbert_stream()` (Model B, `load_joined`, cap `["Volume","sentiment_mean"]`).
- **`app/api/v1/routes_training.py`**: `GET /train/skripsi/search-space` (EnvelopeRoute),
  `POST /train/skripsi/ohlcv`, `POST /train/skripsi/finbert-lstm` (SSE).
- **Test baru**: `tests/test_api/test_training.py` — `TestSkripsiSearchSpaceEndpoint` +
  `TestTrainSkripsiBaselineStream` + `TestTrainSkripsiFinbertStream` (n_iter=1, ~7s/test
  krn epochs tak bisa di-override, cuma n_iter). **Verifikasi**: smoke test langsung
  (nested event start→iteration_start→epoch×N→iteration_end→done OK), `pytest` 190/191
  lulus (1 gagal = `test_default_ticker` pre-existing).

### 3. Frontend — 2 file baru + 1 file diedit
- **`hooks/useRandomSearchStream.js`** (baru): state `{totalIterations, currentIteration,
  currentConfig, currentEpochs (di-reset tiap iteration_start!), iterationHistory (terus
  bertambah), result}` — sengaja TIDAK simpan semua ~1000+ event epoch (20 iterasi × up to
  80 epoch), hanya epoch iterasi yg SEDANG jalan + ringkasan 1 baris/iterasi utk histori.
- **`components/model-training/RandomSearchPanel.jsx`** (baru): 2-tier progress bar
  ("Iterasi X/20" + "Epoch Y/N iterasi ini"), 2 chart live (Loss; Val Acc & F1) khusus
  iterasi berjalan, tabel Riwayat Iterasi (badge Best), 4 metric card (TANPA F2/diagnosis
  collapse — beda dari TrainingPanel nb05), confusion matrix, best config+artifact paths.
  Prop `onDone(result)` utk lift hasil ke parent (page tetap self-contained per pola nb05,
  tapi butuh cross-panel data utk card perbandingan).
- **`pages/ModelTraining.jsx`**: tambah card "Random Search — Search Space" (fetch
  sekali), `VARIANTS` array diperluas 2→4 (`kind: 'notebook05'|'skripsi'` menentukan
  render `TrainingPanel` vs `RandomSearchPanel`), state `skripsiResults{baseline,finbert}`
  diisi via `onDone` → card "Perbandingan Model A vs Model B" (Hipotesa #4 BAB I) muncul
  otomatis begitu KEDUA training selesai, dihitung client-side (tanpa endpoint baru). Pola
  "semua panel mounted permanen + `hidden` className" (bukan conditional render)
  dipertahankan utk 4 tab sekaligus — SSE tab tak aktif tidak ter-abort saat pindah tab.

### Verifikasi end-to-end (browser, server milik user — bukan yg dijalankan Claude)
`npm run lint`/`build` bersih (file baru saya; error lint di file lain — AnalysisPanel.jsx,
TrainingPanel.jsx, useDataAnalysis.js — SUDAH ADA sebelumnya/pre-existing, dikonfirmasi via
`git status` untracked, di luar scope). Live di browser: n_iter=1 kedua varian → progress
nested "Iterasi 1/1" + "Epoch 17/30" tampil real-time, chart update live, tabel Riwayat
Iterasi + badge Best + 4 metric card + confusion matrix + artifact paths
(`lstm_baseline_skripsi.*`/`finbert_lstm_skripsi.*`) semua benar. Card Perbandingan muncul
otomatis stlh Model B selesai (Accuracy 56%→43.89%, dst — dilaporkan apa adanya, TIDAK
disembunyikan meski Model B "kalah", sesuai prinsip anti p-hacking). Pindah tab bolak-balik
(NB05↔Skripsi) dikonfirmasi TIDAK me-reset progress/hasil (pola hidden-not-unmount).
Screenshot tool timeout di lingkungan ini (issue tooling, bukan kode) — verifikasi
dilakukan via `get_page_text`/`read_page` (DOM-level, terbukti cukup).
