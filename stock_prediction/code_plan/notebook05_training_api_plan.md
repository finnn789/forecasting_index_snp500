# Planning: API Training Live (Notebook 05) + UI "Model Training"

Status: **SELESAI DIEKSEKUSI** (2026-07-12) — via 2 agent Sonnet paralel + verifikasi end-to-end orchestrator. Detail hasil di `CLAUDE.md` (Log Keputusan 2026-07-12).
Tanggal: 2026-07-12.
Konteks permintaan user: ingin melihat proses training model (referensi metodologi notebook 03 & 05) langsung dari FE, bukan cuma hasil statis.

---

## 1. Latar belakang & keputusan scoping

### 1.1 Notebook 03 vs Notebook 05 — metodologi berbeda

| | Notebook 03 (v5) | Notebook 05 |
|---|---|---|
| Fitur | 10 (OHLCV + 5 indikator teknikal + sentiment+MA3) | 6 (OHLCV + sentiment_mean) — **sama persis dengan produksi sekarang** |
| Scaler | StandardScaler | MinMaxScaler |
| Split | Walk-forward rolling (WF_TRAIN_SIZE=400) | Kronologis 70/15/15 |
| Arsitektur | LSTM **mean-pooling**, ensemble 5 seed | LSTM **last-hidden-state** (persis `models/lstm/lstm_model.py` produksi) |
| Loss | BCEWithLogits | CrossEntropy + class-weight |
| Grid search | ~6 kombinasi | **144 kombinasi** (3×3×2×2×2×2) |
| Metrik utama | AUC (+ kalibrasi Platt, Youden's J) | F2-score + diagnosis overfit/class-collapse |

Catatan: notebook 04 (`04_Stats_Sentimen_Data.ipynb`) **BUKAN training** — isinya statistik EDA sentimen harian, lanjutan notebook 02. Tidak relevan untuk task ini.

### 1.2 Keputusan yang sudah dikonfirmasi user

1. **Grid search & walk-forward TIDAK dijalankan ulang secara live** — 144 kombinasi × hingga 150 epoch tidak realistis untuk 1 HTTP request. Grid search notebook 05 **sudah pernah dieksekusi** dan hasilnya (top-10 config) diambil sebagai data statis. Yang live-streamed hanya **training final** dengan hyperparameter terbaik yang sudah diketahui.
   - User punya CUDA terinstall — training akan otomatis pakai GPU kalau tersedia (`torch.cuda.is_available()`), jadi realistis untuk didemokan live meski epoch besar.
2. **Profil yang didukung: Notebook 05 SAJA dulu** (v5/notebook 03 menyusul di iterasi berikutnya). Alasan: notebook 05 pakai fitur & arsitektur yang SAMA PERSIS dengan produksi (`dataset_builder.py`, `lstm_model.py`) → banyak yang bisa di-reuse, jauh lebih cepat & aman dibangun.
3. **UI: halaman baru + tombol sidebar sendiri** "Model Training" — terpisah dari "Pipeline" (scope-nya data/sentiment pipeline) dan "Data Preprocessing".

### 1.3 Temuan penting dari hasil eksekusi asli notebook 05 (WAJIB ditampilkan jujur di UI)

Notebook 05 sudah pernah dieksekusi penuh (bukan draft kosong). Hasil grid search & training final asli:

**Hyperparameter terbaik (dari grid search 144 kombinasi, val F2=0.8110):**
```
seq_len=20, hidden_size=64, num_layers=2, dropout=0.4, lr=0.0005, batch_size=64, epochs=150, early_stop=30
```

**Split data:** Train 1086 hari, Val 233 hari, Test 233 hari (70/15/15 dari total setelah windowing).

**Hasil evaluasi test set (training final dgn config di atas):**
```
Accuracy   : 0.5587
Precision  : 0.5587
Recall     : 1.0000   ← mencurigakan, selalu 100%
F1-Score   : 0.7169
F2-Score   : 0.8636   ← metrik utama, TERLIHAT bagus
```

**TAPI — diagnosis class-collapse notebook itu sendiri mengungkap:**
- Train/Val/Test: recall kelas "Down" = 0% di semua split → model **selalu menebak "Up"**, tidak pernah memprediksi "Down".
- F2-Score tinggi itu **menyesatkan** (F2 sangat mudah "tertipu" recall=1.0 dari model yang cuma menebak 1 kelas terus).
- Ini **konsisten** dengan temuan lama yang sudah didokumentasikan di `CLAUDE.md` (2026-06-11: backtest produksi "model SELALU menebak up", AUC 0.38).

**Implikasi untuk implementasi:** ini BUKAN bug yang perlu diperbaiki di task ini (scope task = expose proses training, bukan improve akurasi model). Tapi API & UI **wajib** menghitung & menampilkan diagnosis class-collapse dengan jujur — jangan hanya menampilkan F2-score yang menyesatkan. Prinsip project: laporkan angka apa adanya, hindari p-hacking (sudah jadi pola berulang di catatan sesi `CLAUDE.md`).

---

## 2. Rancangan Backend

Semua isolated dari artefak produksi (`direction_classifier.pt`/`scaler.joblib`/`metadata.json` yang dipakai `/predict` endpoint TIDAK disentuh).

### 2.1 Model — `models/lstm/lstm_model.py`
Tambah varian 2-class (softmax + CrossEntropyLoss, sesuai notebook 05) — `LSTMDirectionClassifierV2` atau generalisasi `build_classifier(num_classes=...)`. Tidak mengubah default/behavior kelas produksi yang sudah ada (dipakai `predict_direction()`).

### 2.2 Trainer baru — `models/lstm/notebook05_trainer.py`
- Reuse `pipeline/feature_engineering/dataset_builder.py::load_joined()` untuk merge OHLCV + sentiment_mean (inner join, logic sudah identik dgn kebutuhan notebook 05).
- Split **kronologis berbasis persentase** 70/15/15 (BARU — beda dari split berbasis tanggal punya `build_dataset()` produksi).
- Windowing via `seq_len` (default 20, hasil grid search).
- `MinMaxScaler` fit-train-only pada 6 `FEATURE_COLS` (konsisten dgn keputusan scaling yang sudah dibahas & didokumentasikan sebelumnya).
- Class weight inverse-frequency (`compute_class_weights`, sesuai notebook).
- Training loop dengan callback `emit(event: dict)` dipanggil tiap epoch — pola yang sama seperti `app/helpers/sse.py::sse_response` (dipakai sentiment pipeline).
- Early stopping monitor val F2-score.
- Evaluasi final lengkap: confusion matrix (tn/fp/fn/tp), accuracy/precision/recall/f1/f2, diagnosis overfitting (gap train-test > 0.10) & underfitting (semua split < 0.55), **diagnosis class-collapse** (recall per kelas < 0.05 → flag collapse) — replikasi persis logic `diagnose_fit()` & `diagnose_class_collapse()` dari notebook.
- Simpan artefak terpisah: `data/artifacts/lstm_weights/lstm_nb05_best.pt` + `lstm_nb05_scaler.joblib` + `lstm_nb05_metadata.json` (nama mengikuti yang sudah dipakai notebook aslinya, tidak bentrok dengan artefak produksi).
- Default hyperparameter = konfigurasi terbaik hasil grid search (lihat §1.3), semua bisa di-override via parameter training.

### 2.3 Schema baru — `app/schemas/training.py`
- `TrainEpochEvent` — `{type:"epoch", epoch, total_epochs, train_loss, train_f2, val_loss, val_f2}`
- `TrainDoneEvent` / hasil akhir — `{type:"done", metrics:{accuracy,precision,recall,f1,f2}, confusion_matrix:{tn,fp,fn,tp}, diagnosis:{overfitting, underfitting, class_collapse:{train,val,test}}, artifact_paths:{...}}`
- `GridSearchResultResponse` — tabel top-10 config statis (hardcode dari hasil notebook di atas) + `best_config`.

### 2.4 Route baru — `app/api/v1/routes_training.py` (atau tambahkan section baru di file terkait)
- `POST /api/v1/train/notebook05` — SSE (`sse_response`), body = override hyperparameter opsional (default = best config §1.3).
- `GET /api/v1/train/notebook05/grid-search-result` — hasil statis grid search (TIDAK dijalankan ulang).

### 2.5 Service — `app/services/training_service.py`
Wiring route → `notebook05_trainer`. Ikuti pola `EnvelopeRoute` project untuk endpoint non-streaming; endpoint SSE mengikuti pola `routes_sentiment.py::run_pipeline()` yang sudah ada (return `StreamingResponse` langsung, skip `EnvelopeRoute`).

---

## 3. Rancangan Frontend

### 3.1 Halaman baru — `pages/ModelTraining.jsx`
- **Card "Grid Search (Hasil Sebelumnya)"** — tabel statis top-10 config dari `GET .../grid-search-result`, badge menandai best config.
- **Card "Training Final (Live)"** — form hyperparameter (prefilled dari best config, bisa diubah user) + tombol "Mulai Training" yang membuka koneksi SSE ke `POST /api/v1/train/notebook05`.
- **Live line chart** (reuse `PlotlyChart`) — train/val loss & train/val F2 per epoch, ter-update tiap event SSE.
- **Log panel** (pola mirip `Pipeline.jsx` Run Log) — tiap epoch event jadi 1 baris.
- **Setelah selesai (`done` event):** confusion matrix, metric cards (Accuracy/Precision/Recall/F1/F2), dan **box peringatan class-collapse** (amber/merah) kalau terdeteksi — WAJIB tampil jujur, bukan disembunyikan, sesuai §1.3.

### 3.2 Routing & Sidebar
- `Sidebar.jsx` — tombol baru "Model Training" (icon `model_training`), setelah "Data Preprocessing".
- `App.jsx` — route `/model-training`.
- `Header.jsx` — judul halaman baru.

---

## 4. Rencana eksekusi

Delegasi ke 2 agent Sonnet paralel (kontrak JSON/SSE event dikunci sama persis di kedua prompt, mengikuti pola orchestration yang sudah terbukti berhasil di task-task sebelumnya):
- **Agent A — Backend**: §2 lengkap + test.
- **Agent B — Frontend**: §3 lengkap + lint check.

Verifikasi akhir oleh orchestrator (Claude utama): jalankan training live sungguhan di browser, screenshot/baca hasil chart live update, konfirmasi box class-collapse muncul sesuai ekspektasi §1.3, pytest backend.

**Belum dieksekusi** — menunggu perintah "lanjut" dari user.
