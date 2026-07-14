# Plan: Halaman Prediction — Tampilkan Hasil Training + Prediksi + Backtest (Notebook05)

> **Status: BELUM DIEKSEKUSI.** Disimpan atas permintaan user untuk di-recall nanti.
> Jangan mulai implementasi dari dokumen ini sampai user secara eksplisit meminta.

## Context

Setelah training di halaman Model Training selesai, hasilnya (metrics, confusion matrix,
diagnosis class-collapse) cuma hidup di React state `TrainingPanel` — begitu user pindah
halaman (unmount, sesuai pembahasan Fiber sebelumnya), semua itu hilang. User ingin hasil
training itu **persisten** dan bisa dilihat lagi di halaman **Prediction**, dan halaman itu
juga bisa dipakai untuk **menjalankan prediksi** sungguhan.

Solusinya bukan "simpan state React lebih lama" — melainkan sumber data harus pindah dari
state React ke **backend** (metadata JSON yang sudah disimpan tiap training selesai), lalu
Prediction page mengambilnya lewat API biasa. Ini otomatis solve masalah persistence karena
API call tidak peduli komponen mana yang mount/unmount.

**Riset yang sudah dikonfirmasi (2 Explore agent paralel):**
- Backend prediction (`/predict`, `/predict/model/status`, `/predict/backtest`) sudah lengkap
  tapi HANYA untuk model **produksi** (`direction_classifier.pt`, `LSTMDirectionClassifier`,
  6 fitur OHLCV+sentimen, split by-date). **Tidak ada** endpoint serupa untuk 2 varian
  notebook05 (`lstm_nb05_*` / `lstm_nb05_ohlcv_*`, arsitektur `LSTMSoftmaxClassifier`,
  split kronologis 70/15/15) — ini yang perlu dibangun baru.
- `pages/Predictions.jsx` saat ini **100% mockup statis**, tidak ada API call sama sekali —
  aman untuk ditulis ulang total tanpa breaking apa pun.
- Metadata JSON tiap training (`lstm_nb05_metadata.json` / `lstm_nb05_ohlcv_metadata.json`)
  sudah berisi semua yang dibutuhkan untuk ditampilkan ulang (config, feature_cols, metrics,
  confusion_matrix, diagnosis, split_sizes, trained_at, best_epoch, best_val_f2) — **sudah
  ada di disk** dari training yang dijalankan sesi ini, tidak perlu training ulang untuk testing.
- `build_latest_window()` (`dataset_builder.py`) di-hardcode ke `FEATURE_COLS`/`load_joined()`
  (varian sentimen produksi) — perlu digeneralisasi (pola SAMA seperti refactor
  `run_notebook05_training` sebelumnya: tambah parameter `feature_cols`/`load_data_fn`,
  default ke nilai lama supaya caller produksi TIDAK berubah perilaku).
- `LSTMSoftmaxClassifier` bisa direkonstruksi dari model .pt (berisi `model_state_dict` +
  `config` + `feature_cols`) — tidak perlu artefak tambahan.

**Keputusan yang sudah dikonfirmasi user:**
1. Tab switcher 2 varian (OHLCV+Sentimen / OHLCV Saja), sama seperti Model Training.
2. Sertakan JUGA section backtest (bukan cuma prediksi 1-hari), mirror `/predict/backtest` yang sudah ada untuk produksi.

## Backend (`stock_prediction`)

### 1. Generalisasi `build_latest_window()` — `pipeline/feature_engineering/dataset_builder.py`
Tambah parameter opsional `feature_cols: list[str] = FEATURE_COLS` dan
`load_data_fn: Callable[[], pd.DataFrame] = load_joined`, default sama seperti sebelumnya
(caller produksi `prediction_service.py` TIDAK perlu diubah, tidak ada perubahan perilaku).
`target_date` (as_of+1 hari) dihitung oleh caller baru (bukan mengubah return signature
fungsi ini — biar blast radius minimal terhadap kode produksi yang sudah ada).

### 2. Extract helper split di `models/lstm/notebook05_common.py`
Pecah bagian awal `run_notebook05_training()` (load data -> label -> split kronologis
70/15/15) jadi helper `_load_and_split(feature_cols, load_data_fn) -> (df_train, df_val, df_test)`
— dipakai ULANG oleh training (sudah ada) DAN backtest (baru) supaya logic split TIDAK
diduplikasi dua kali (konsisten dengan prinsip DRY yang sudah ditegakkan di refactor
sebelumnya).

### 3. Fungsi inference baru — `models/lstm/notebook05_common.py`
- `load_trained_notebook05(artifact_dir, model_filename, scaler_filename, metadata_filename) -> dict | None`
  — return `None` kalau metadata belum ada (belum pernah training); else load
  model_state_dict+config+feature_cols dari .pt, scaler dari .joblib, metadata dari .json,
  rekonstruksi `LSTMSoftmaxClassifier` siap pakai (`eval()` mode).
- `predict_latest_notebook05(*, feature_cols, load_data_fn, artifact_dir, model_filename,
  scaler_filename, metadata_filename) -> dict` — panggil `load_trained_notebook05()`, kalau
  `None` return `{"trained": False}`; else panggil `build_latest_window()` (feature_cols/
  load_data_fn sesuai varian), forward pass -> softmax -> P(Up)/direction/confidence,
  `target_date = as_of_date + 1 hari`. Return dict siap dipetakan ke schema response.
- `backtest_notebook05(*, feature_cols, load_data_fn, artifact_dir, model_filename,
  scaler_filename, metadata_filename, split='test') -> dict` — reuse `_load_and_split()` +
  scaler (transform saja, TIDAK fit ulang) + windowing (mirror `create_sequences`, tambah
  tracking tanggal dari `df_test['Date']` utk output per-titik) -> jalankan model -> per-titik
  prediksi vs aktual + confusion matrix + metrics (accuracy/precision/recall/f1/auc), mirror
  bentuk `BacktestResponse` yang sudah ada utk produksi.

### 4. Schema baru — `app/schemas/training.py`
- `Notebook05ResultResponse` (`is_available: bool`, lalu field lain optional: config, feature_cols, metrics, confusion_matrix, diagnosis, split_sizes, trained_at, best_epoch, best_val_f2) — mirror pola `ModelInfoResponse` produksi (selalu 200, `is_available=False` kalau belum training, BUKAN 404).
- `Notebook05PredictionResponse` (variant, as_of_date, target_date, direction, probability_up, confidence, window, feature_cols, trained_at, best_val_f2) — mirror `DirectionPredictionResponse` produksi.
- `Notebook05BacktestResponse` (variant, window, split, n_samples, metrics, confusion_matrix, points) — mirror `BacktestResponse` produksi.

### 5. Service — `app/services/training_service.py` (di sinilah pemilihan varian, pola sudah established)
- `get_notebook05_result(variant: Literal['sentiment','ohlcv'])`
- `predict_notebook05(variant)` — raise `NotFoundError(code='MODEL_NOT_TRAINED')` kalau belum training (konsisten dgn pola produksi `predict_direction()`, karena endpoint ini genuinely tidak bisa jalan tanpa model).
- `backtest_notebook05(variant, split='test')` — sama, raise kalau belum training.
Tiap fungsi ini lazy-import dari `notebook05_common.py` + pilih `feature_cols`/`load_data_fn`/
nama artefak yang sesuai varian (persis pola `run_training_stream`/`run_training_stream_ohlcv`
yang sudah ada).

### 6. Routes baru — `app/api/v1/routes_training.py` (EnvelopeRoute, bukan SSE)
| Endpoint | Varian |
|---|---|
| `GET /train/notebook05/result` | sentimen |
| `GET /train/notebook05/ohlcv/result` | ohlcv-only |
| `POST /train/notebook05/predict` | sentimen |
| `POST /train/notebook05/ohlcv/predict` | ohlcv-only |
| `GET /train/notebook05/backtest?split=test` | sentimen |
| `GET /train/notebook05/ohlcv/backtest?split=test` | ohlcv-only |

### 7. Test — `tests/test_api/test_training.py`
Tambah test class per endpoint baru, jalankan terhadap artefak yang **sudah ada di disk**
dari sesi ini (tidak perlu training ulang) — verifikasi `is_available=True`, bentuk response,
dan (untuk variant yang belum pernah ditest) skenario `is_available=False`/404 kalau file
artefak sengaja tidak ada.

## Frontend (`ui-stock-prediction`)

### 8. Extract komponen presentational reusable dari `TrainingPanel.jsx`
Pecah jadi 3 komponen kecil di `components/model-training/`: `MetricsCards`, `ConfusionMatrixGrid`,
`ClassCollapseBanner` — dipakai ULANG oleh `TrainingPanel` (live SSE, tidak berubah perilaku)
DAN oleh section baru di Prediction page (hasil persisted) supaya tidak duplikasi JSX.

### 9. Hook baru — `hooks/useNotebook05Result.js`
Mirror pola `useDataAnalysis.js` (AbortController, `fetchJson`) — fetch `GET .../result` on
mount per varian. Predict & backtest dipicu manual (tombol klik -> `fetchJson` POST/GET),
mirip pola `startTraining` di `useTrainingStream.js` (bukan auto-fetch).

### 10. Tulis ulang `pages/Predictions.jsx` (100% mockup lama dihapus, aman karena tidak ada wiring yang bergantung)
- Tab switcher "OHLCV + Sentimen" / "OHLCV Saja" (2 endpoint set berbeda, KEDUA konten tetap
  mounted permanen + `className="hidden"` untuk toggle — pola sama seperti Model Training,
  supaya hasil fetch/predict salah satu tab tidak hilang saat pindah tab).
- Per tab: card hasil training (pakai `MetricsCards`/`ConfusionMatrixGrid`/`ClassCollapseBanner`
  dari #8) atau state "belum pernah training" kalau `is_available=false`; tombol "Prediksi Hari
  Berikutnya" -> tampilkan direction/probability/confidence; section backtest (tabel prediksi
  vs aktual + confusion matrix + metrics, dari endpoint `/backtest`).
- Scope produksi (`/predict`, `/predict/model/status` untuk `direction_classifier.pt`) **TIDAK
  disentuh** — di luar scope permintaan user (fokus ke hasil training notebook05 yang baru saja
  dijalankan).

## Verifikasi
1. `pytest tests/test_api/test_training.py -v` — endpoint baru + lama tetap lulus.
2. Full `pytest` — pastikan generalisasi `build_latest_window()` tidak mengubah perilaku
   `predict_direction()`/`run_backtest()` produksi (default param sama).
3. End-to-end browser: buka `/predictions`, cek kedua tab menampilkan hasil training yang
   SUDAH ADA di disk (dari sesi ini), klik "Prediksi", klik backtest, pindah tab bolak-balik
   pastikan data tidak hilang (sama seperti verifikasi Model Training sebelumnya).
