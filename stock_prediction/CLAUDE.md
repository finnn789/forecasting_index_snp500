# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Stock market price prediction system combining **LSTM** (time-series) and **FinBERT** (news sentiment) models via an ensemble layer, served through a FastAPI REST API.

## Commands

```bash
# Install dependencies (use uv, the configured package manager)
uv sync
# or: pip install -r requirements.txt

# Run the API server (hot reload enabled by default)
./scripts/run_api.sh
# or: python server.py

# Run tests
pytest

# Run a single test file
pytest tests/test_api/test_routes.py -v

# Run data pipeline
./scripts/run_pipeline.sh
```

API available at `http://localhost:8000` — Swagger UI at `/docs`, ReDoc at `/redoc`.

## Architecture

Data flows through four layers:

```
[External APIs] → [pipeline/ingestion] → [pipeline/preprocessing]
                → [pipeline/feature_engineering]
                → [models/lstm] + [models/finbert]
                → [models/combined/ensemble.py]
                → [app/ FastAPI]
```

**Key packages:**
- `app/` — FastAPI backend: `config.py` (metadata), `core/state.py` (uptime tracking), `api/v1/` (routes), `schemas/` (Pydantic models), `services/` (business logic)
- `models/lstm/` — TensorFlow/Keras LSTM for OHLCV time-series
- `models/finbert/` — HuggingFace `ProsusAI/finbert` for financial news sentiment
- `models/combined/ensemble.py` — Weighted fusion of LSTM + sentiment scores
- `pipeline/` — Ingestion → preprocessing → feature engineering (technical indicators + sentiment aggregation)

**Entry point:** `server.py` — initializes FastAPI, registers routers, configures CORS and lifecycle events. `main.py` is a thin stub.

**Router registration:** `app/api/v1/__init__.py` aggregates all route modules.

## Current Implementation Status

The FastAPI skeleton and schemas are working. Most ML/pipeline files are **empty placeholders** awaiting implementation:

| Layer | Implemented | Empty |
|-------|------------|-------|
| API server + middleware | `server.py`, `app/core/state.py`, `app/config.py` | — |
| Schemas | `schemas/status.py` | `schemas/prediction.py`, `schemas/sentiment.py` |
| Routes | `routes_general.py`, `routes_status.py` | `routes_prediction.py`, `routes_sentiment.py`, `routes_data.py` |
| Services | — | `prediction_service.py`, `sentiment_service.py` |
| Models | — | All of `models/lstm/`, `models/finbert/`, `models/combined/` |
| Pipeline | — | All of `pipeline/` |

## Environment Configuration

Copy `.env.example` to `.env`:

```
STOCK_API_KEY=...
NEWS_API_KEY=...
LSTM_MODEL_PATH=data/artifacts/lstm_weights/
FINBERT_MODEL_NAME=ProsusAI/finbert
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
```

## Data

- `data/raw/news/sp500_headlines_2008_2024.csv` — S&P 500 news headlines (2008–2024), the primary training corpus for FinBERT sentiment
- `data/raw/stocks/` — OHLCV data (fetched at runtime via stock API)
- `data/artifacts/` — Saved model weights (LSTM and optional fine-tuned FinBERT)

## Implementation Plan

Detailed architecture decisions, data schemas, model specs, and endpoint contracts are documented in `code_plan/implementation_plan.md`. Read this before implementing any new component.

## Tech Stack

- Python 3.12, managed with `uv`
- FastAPI + Uvicorn + Pydantic v2
- TensorFlow (LSTM), PyTorch + HuggingFace Transformers (FinBERT)
- Pandas, NumPy, scikit-learn, `ta` (technical indicators)
- pytest + httpx for testing

## API Response Structure Format

**WAJIB:** Semua endpoint API harus menggunakan struktur response yang konsisten berikut. Jangan membuat response format ad-hoc di luar standar ini.

### Success Response

```json
{
  "success": true,
  "data": { ... },
  "message": "Deskripsi singkat hasil operasi",
  "meta": {
    "timestamp": "2026-05-04T10:00:00Z",
    "version": "1.0"
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Pesan error yang human-readable",
    "detail": "Detail teknis opsional (hanya di DEBUG mode)"
  },
  "meta": {
    "timestamp": "2026-05-04T10:00:00Z",
    "version": "1.0"
  }
}
```

### Paginated Response (untuk list/collection)

```json
{
  "success": true,
  "data": [ ... ],
  "message": "...",
  "meta": {
    "timestamp": "2026-05-04T10:00:00Z",
    "version": "1.0",
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 100,
      "total_pages": 5
    }
  }
}
```

### Aturan Implementasi

- Field `success` (bool) dan `meta.timestamp` **selalu ada** di setiap response.
- Field `data` hanya ada di success response; field `error` hanya ada di error response.
- `error.code` menggunakan format `SCREAMING_SNAKE_CASE` (contoh: `MODEL_NOT_LOADED`, `TICKER_NOT_FOUND`).
- HTTP status code harus sesuai: `200` sukses, `400` bad request, `404` not found, `422` validation error, `500` server error.
- Semua schema Pydantic response **wajib** mewarisi dari base class `BaseResponse` yang didefinisikan di `app/schemas/base.py`.
- Jangan pernah mengembalikan plain `dict`, string, atau Pydantic model tanpa wrapper `BaseResponse`.

### Contoh Base Schema (`app/schemas/base.py`)

```python
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")

class ResponseMeta(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = "1.0"

class BaseResponse(BaseModel, Generic[T]):
    success: bool
    message: str = ""
    meta: ResponseMeta = Field(default_factory=ResponseMeta)

class SuccessResponse(BaseResponse[T], Generic[T]):
    success: bool = True
    data: T

class ErrorDetail(BaseModel):
    code: str
    message: str
    detail: str | None = None

class ErrorResponse(BaseResponse[None]):
    success: bool = False
    error: ErrorDetail
```

---

## Working Rules (Claude Behavior)

### Konfirmasi Sebelum Eksekusi
**WAJIB:** Sebelum mengeksekusi tool apapun, tampilkan rencana eksekusi terlebih dahulu kepada user dan tunggu konfirmasi. Jangan langsung eksekusi tanpa persetujuan user. Format konfirmasi:
- Tool yang akan digunakan
- Parameter yang akan dikirim
- Tujuan / hasil yang diharapkan

### Manajemen Token Jupyter MCP
`mcp__jupyter__insert_execute_code_cell` mengonsumsi token sangat tinggi karena seluruh output (tabel, gambar base64, teks) masuk ke context window setiap kali cell dieksekusi. Pertimbangkan hal berikut:
- Gunakan `insert_cell` (tanpa eksekusi) untuk markdown cell
- Batasi jumlah cell yang dieksekusi sekaligus dalam satu giliran
- Untuk plot/visualisasi besar, pertimbangkan menyimpan ke file daripada menampilkan inline jika tidak diperlukan
- Pisahkan cell besar menjadi cell-cell kecil yang lebih terfokus

---

## Catatan Sesi & Preferensi Kolaborasi

Bagian ini diperbarui secara aktif selama sesi kerja. Claude wajib mencatat di sini setiap kali ada:
- Keputusan desain / arsitektur yang disepakati
- Preferensi atau instruksi baru dari user
- Konteks penting yang tidak tercakup di bagian lain CLAUDE.md

### Preferensi User
- Bahasa komunikasi: **Bahasa Indonesia**
- User ingin Claude mendokumentasikan hal-hal penting langsung di `CLAUDE.md` selama sesi berlangsung

### Log Keputusan
<!-- Tambahkan entri baru di sini dengan format: [YYYY-MM-DD] Deskripsi keputusan -->
- [2026-04-26] Inisialisasi section catatan sesi atas permintaan user
- [2026-05-04] Tambah standar API Response Structure Format — semua endpoint wajib pakai `SuccessResponse`/`ErrorResponse` dari `app/schemas/base.py`
- [2026-05-25] Refactor layering route: business logic dipindah dari `app/api/v1/routes_*.py` ke `app/services/` (eda_service, feature_service). Route kini tipis (deklarasi endpoint + delegasi). Util lintas-modul dipindah ke direktori baru `app/helpers/` (serialization, csv_inspector, sse). Loader data pakai repository (`NewsRepository`/`SentimentRepository`); exception pakai `DomainError` (bukan `HTTPException` mentah). Konsekuensi: error "data tidak ada" kini HTTP 404 (NotFoundError), sebelumnya 503.
- [2026-06-05] Hapus duplikasi & dead code hasil audit (`code_plan/api_audit_report.md`): endpoint duplikat `/data/eda/summary-statistics` dihapus; dead code `run_preprocessing_pipeline()` sinkron dihapus; `HTTPException` di `sentiment_service` diganti `NotFoundError`.
- [2026-06-05] **Pola Auto-Envelope**: dibuat `app/core/envelope.py` (`EnvelopeRoute`) — handler cukup `return <schema inner>`, pembungkusan ke `SuccessResponse` otomatis; pesan per-endpoint via `openapi_extra={"x-message": "..."}`; `StreamingResponse`/SSE & non-JSON otomatis di-skip. Route pakai `APIRouter(..., route_class=EnvelopeRoute)` dengan `response_model=<InnerSchema>` (bukan `SuccessResponse[...]`). Diterapkan ke `routes_data`, `routes_feature_engineering`, `routes_sentiment` (general/status belum). **Konvensi API baru:** ikuti pola ini — jangan wrap `SuccessResponse` manual di handler.
- [2026-06-05] **Provider repository tunggal**: dibuat `app/repositories/provider.py` (`get_repositories()` + `lru_cache`) menggantikan pola global `_repos`/`_get_repos()` yang sebelumnya diduplikasi di tiap service. `eda_service` & `sentiment_service` sudah migrasi. Service baru pakai `get_repositories()`.
- [2026-06-11] **Model prediksi arah harga (early fusion, PyTorch)**: dibangun model klasifikasi biner arah harga besok (`y=1 jika Close[t+1]>Close[t]`). Fitur = OHLCV + `sentiment_mean` (early fusion, 6 fitur; MA/Volatility diabaikan sesuai instruksi user). **Deviasi stack:** LSTM pakai **PyTorch**, BUKAN TensorFlow — TF tidak terinstall & tidak ada di `pyproject.toml`; torch 2.11 sudah jadi dependency FinBERT. File: `pipeline/feature_engineering/dataset_builder.py` (join+label+window+scaling, anti-leakage: MinMaxScaler fit di train saja, window=20 default), `models/lstm/{lstm_model,lstm_trainer,lstm_predictor}.py`, `app/services/prediction_service.py`, `app/api/v1/routes_prediction.py` (`POST /api/v1/predict` + `GET /api/v1/predict/model/status`, EnvelopeRoute). Entity `prediction_result.py` diubah ke klasifikasi (direction/probability_up/confidence). Artefak: `data/artifacts/lstm_weights/{direction_classifier.pt,scaler.joblib,metadata.json}`. Kontrak modul: `code_plan/direction_model_contract.md`. **Catatan hasil:** window sweep {10,20,30} → val_auc≈0.50–0.515 (mendekati acak, wajar utk arah harian); test set kecil (23 sampel, data berhenti 2024-03-04). Infrastruktur end-to-end jalan; akurasi model perlu iterasi (data lebih panjang, fitur tambahan, atau target horizon lebih panjang). **Bug pre-existing belum diperbaiki:** `tests/test_domain/test_value_objects.py::test_default_ticker` expect `TickerSymbol.DEFAULT` tapi kode pakai `DEFAULT_TICKER` (module var) — di luar scope, tidak disentuh.
- [2026-06-11] **Backtest endpoint + dokumentasi frontend**: tambah `GET /api/v1/predict/backtest?split=test` (`run_backtest()` di `prediction_service.py`; schema `BacktestPoint`/`ConfusionMatrix`/`BacktestResponse`) → prediksi-vs-aktual + confusion matrix + metrik utk visualisasi. **Temuan model:** backtest test set `tp=14,tn=0,fp=9,fn=0` — model SELALU menebak "up" (auc 0.38); baseline yg harus diperbaiki saat iterasi. Dokumen baru: `code_plan/frontend_api_reference.md` (23 endpoint, request/response nyata + envelope + saran recharts) dan `fe_stock_prediction/FRONTEND_AGENT_GUIDE.md` (panduan utk AI Agent Frontend). **Catatan frontend usang:** `fe_stock_prediction` masih wiring ke model regresi lama (`types/prediction.ts`, `endpoints.ts` path `/api/predict` & `/api/pipeline/*` yg tak ada) — koreksi ada di guide. Pipeline umum belum ada, hanya sentiment pipeline.
- [2026-06-15] **Notebook 03 v5 (PART A+B, via 2 agent Sonnet sekuensial)**: implementasi rancangan `notebook03-part-a-b-plan` (ruflo memory ns stock_prediction) ke `notebooks/03_LSTM_experiment.ipynb`. **PART A:** enrichment indikator teknikal stasioner via `compute_technical_indicators` (dihitung SEBELUM drop level OHLCV) → `FEATURE_COLS` jadi 10 (`ret_close,ret_volume,rsi_14,macd_hist,bb_bandwidth,volatility_20,close_vs_ema20,bb_pct_b,sentiment_mean,sentiment_mean_ma3`); `sentiment_neg` & `ret_open/high/low` dibuang; helper `scale_sequences()` StandardScaler fit TRAIN-only (anti-leakage), dipakai di tiap split. **PART B (anti-overfit):** `LSTMClassifier` default kecil hidden=32/1 layer/dropout=0.5; Adam `weight_decay=1e-4`; class weight inverse-frequency; `train_one()`+`ensemble_predict()` seed ensemble 5 model (eval test & walk-forward); kurva train-vs-val AUC; tabel baseline (LSTM vs always-Up vs random). Artefak v5: `direction_classifier_v5.pt` (list 5 state_dict) + `scaler_v5.joblib` + `metadata_v5.json`. Perbaikan kecil (Claude): propagasi `best_lr` dari grid ke pelatihan final. **CATATAN: notebook BELUM dieksekusi** (sesuai instruksi — hanya implementasi); semua cell `outputs=[]`/`execution_count=null`; tak ada draf Bab Tinjauan Pustaka.
- [2026-06-16] **Notebook 03 v5 — iterasi evaluasi + dok arsitektur**: (1) fix `inf` di `ret_volume` (Volume `^GSPC` ada 1 hari=0; `dropna` TIDAK buang inf → tambah `df.replace([inf,-inf],nan)` sebelum dropna di Cell 4). (2) Walk-forward expanding→**rolling-window** (`WF_TRAIN_SIZE=400`, `tr_lo=max(0,te_start-400)`) untuk lawan concept drift; tambah **kalibrasi Platt** (fit val) + **threshold tuning** + metrik lengkap (acc/prec/rec/f1) per fold. Hasil: mean AUC 0.5145→**0.5733±0.17**, fold 1–4 AUC 0.60–0.71 TAPI fold 2023–2024 tetap inversi (AUC 0.28) = sign-flip rezim momentum→kontrarian. (3) Threshold awal pakai F1 → kolaps "all-Up" (Recall=1.0, acc=base-rate, metrik menyesatkan) → **diganti Youden's J** (`tune_threshold` default `metric='youden'`, J=TPR−FPR). **AUC = metrik utama** (bebas threshold); ~0.57 selaras literatur (0.562) & EMH — defensible, jangan over-tune (p-hacking). Dok metodologi lengkap: `code_plan/finbert_lstm_architecture.md`. **FinBERT pipeline** (`scripts/regenerate_sentiment_weighted.py`): `signed_score=sentiment_numeric×sentiment_score` (prob-weighted), `sentiment_mean`=mean harian. Implementasi rolling+kalibrasi via agent Sonnet; fix inf & Youden oleh Claude utama.
- [2026-06-16] **Analisis sensitivitas WF + dok metodologi**: (1) walk-forward di-refactor jadi fungsi `run_walk_forward(...)` & kini pakai `best_params`/`best_lr` dari grid (bukan hardcode); tambah cell **analisis sensitivitas `WF_TRAIN_SIZE`** sweep {200,300,400,500,expanding} (via agent Sonnet). **Hasil:** mean AUC 0.51–0.60 (std 0.09–0.18) TAPI **pooled AUC 0.49–0.55** untuk semua setting → edge OOS konsisten ≈ tidak ada; mean≫pooled (mis. 200: mean 0.597 vs pooled 0.502) = sign-flip rezim. Kesimpulan jujur: sinyal lemah/regime-dependent/near-EMH, model BUKAN prediktor andal; kontribusi = metodologi + temuan. (2) `schema_metode_penelitian.md` ditandai **USANG** (desain v1–v3 horizon-1); dibuat **`code_plan/metodologi_penelitian.md`** (Bab 3 siap pakai, v5, dgn tabel sensitivitas + interpretasi pooled-vs-mean) + arsitektur di `finbert_lstm_architecture.md`. **Pesan ke user (berulang): berhenti tuning = hindari p-hacking; laporkan pooled AUC sebagai angka utama konservatif.**
- [2026-07-11] **API baru: `routes_data_analysis.py` — visualisasi analisis data ala notebook**. Dibuat atas permintaan user untuk menampilkan "setiap langkah alur" dari `notebooks/01_EDA_stock_data.ipynb` (saham ^GSPC) dan `notebooks/02_EDA_sentiment_data.ipynb` (headline + FinBERT) sebagai API — bukan resurrect grup EDA lama yang baru dihapus, tapi feature baru yang scope & isinya eksplisit mengikuti notebook. **20 endpoint** di bawah `/api/v1/data-analysis/{stocks,sentiment}/*`, arsitektur 3 file konsisten konvensi lama: `app/schemas/data_analysis.py` (schema + `plot_hint`, format JSON chart-ready — bukan gambar), `app/services/data_analysis_service.py` (logic), `app/api/v1/routes_data_analysis.py` (route tipis, `EnvelopeRoute`). **Stock (11 endpoint):** raw-info, descriptive-stats, price-volume, daily-returns, rolling-stats (MA20/50/200+vol30), ohlc-spread, correlation, seasonality, cumulative-return-drawdown, summary, preprocessing. **Sentiment (9 endpoint):** raw-info, news-per-year, news-per-day, headline-length, closing-price, preprocessing, scoring-distribution, daily-aggregation, method-comparison. **3 temuan penting soal notebook vs produksi** (diklarifikasi ke user sebelum implementasi): (1) endpoint `stocks/preprocessing` sengaja pakai `StockPreprocessor.clean()` produksi (drop kolom+validasi+dedup+NaN-fill, TANPA scaling), BUKAN cell MinMaxScaler eksploratif di notebook 01 (yang simpan ke file terpisah `GSPC_2018_2024_no_extended_feature.csv` yang tak dipakai training). (2) `sentiment/preprocessing` (text cleaning: normalisasi+dedup+filter<3kata) mengikuti metodologi notebook 02 — **pipeline produksi (`sentiment_service`) saat ini TIDAK menjalankan cleaning ini sama sekali**, headline mentah langsung ke FinBERT (didokumentasikan via field `note` di response). (3) **Temuan signifikan:** `sentiment/daily-aggregation` & `method-comparison` dihitung ULANG langsung dari `headlines_clean.csv` (probability-weighted, `signed=numeric×score`, sesuai notebook 02) — BUKAN dibaca dari `headlines_daily_sentiment.csv` produksi, karena `_aggregate_daily()` di `sentiment_service.py` ternyata **masih pakai metode LAMA** (rata-rata `sentiment_numeric` tanpa bobot confidence) yang notebook 02 sendiri sebut inferior. Pipeline produksi belum diupgrade ke metode weighted — di luar scope task ini, hanya didokumentasikan via `note` di response (kandidat perbaikan terpisah). **Verifikasi:** seluruh 20 endpoint dites live via `TestClient` (200 OK, angka summary saham cocok persis dgn kesimpulan notebook 01: cum return +90.33%, max drawdown -33.92%). Test baru ditambah ke `tests/test_api/test_envelope.py` (`TestDataAnalysisEndpoints`, parametrized). `pytest`: 183/184 lulus (1 gagal = bug pre-existing, di luar scope).
- [2026-07-11] **Pemangkasan API — hapus grup Data & EDA + Feature Engineering** (permintaan user setelah `fe_stock_prediction/` frontend dihapus dari working tree — endpoint itu awalnya dibuat untuk kebutuhan chart/inspeksi frontend yang sekarang sudah tidak ada). **Dihapus total:** `app/api/v1/routes_data.py`, `app/api/v1/routes_feature_engineering.py`, `app/services/eda_service.py`, `app/services/feature_service.py`, `app/helpers/csv_inspector.py`, `app/schemas/stocks.py`, `tests/tests_service/test_stocks_eda_routes.py`. **`app/schemas/sentiment.py`** dipangkas dari 20 class jadi 3 (`PreviewResponse`, `PipelineStatusResponse`, `ModelStatusResponse` — dipakai Sentiment Pipeline); 17 class lain dihapus (EDA/FE-only atau memang dead code yang tak pernah dipakai route manapun: `SentimentRequest`/`SentimentResponse`, `ColumnGroups`, `DataInfo`, `FeatureEngineeringResponse`, `PreprocessRunResponse`, dll). `app/api/v1/__init__.py` tak lagi registrasi `data_router`/`fe_router`. `tests/test_api/test_envelope.py` dipangkas (hapus `TestDataEdaEndpoints` & `TestFeatureEngineeringEndpoints`). **API v1 sekarang cuma 9 endpoint** (dari 25): General/Status (`/`, `/api/status`, `/api/health`) + Sentiment Pipeline (4) + Prediction (3). **Sengaja TIDAK dihapus** (di luar scope route/service/schema, biar tidak overreach): `app/repositories/stock_repository.py` (`StockRepository` kini tidak dipakai endpoint manapun, tapi masih bagian factory `get_default_repositories()` + ada test sendiri) dan `app/helpers/serialization.py::to_json_safe_records` (masih diuji langsung oleh `tests_service/test_feature_engineering_helpers.py`, yang isinya sebenarnya testing modul `pipeline/` lain). **Verifikasi:** `api_router` berhasil di-import (9 endpoint terdaftar), `pytest` 163/164 lulus (1 gagal = bug pre-existing `test_default_ticker`, sudah dicatat 2026-06-11, di luar scope). **Dokumen historis TIDAK diupdate** (referensi lama ke file yang sudah dihapus masih ada di `code_plan/api_audit_report.md` & `memory/*.md` — dibiarkan sebagai catatan historis, bukan dokumentasi aktif).
- [2026-07-11] **Pembersihan minor `app/api/v1/`** — cleanup non-breaking, verifikasi via `py_compile` + import `api_router` (25 route) + `pytest` (16/16 test_api lulus, 176/177 total lulus — 1 gagal adalah bug pre-existing `test_default_ticker` yang sudah dicatat 2026-06-11, di luar scope). (1) Hapus import tak terpakai `ProcessedDataInfo` di `routes_data.py`. (2) Rapikan urutan import `app/api/v1/__init__.py` (import `routes_sentiment`/`routes_prediction` sebelumnya di tengah file, dipindah ke atas bersama import lain). (3) **R5 (sisa audit `api_audit_report.md` 2026-06-04)**: `sentiment_service.get_daily_preview()` kini return `PreviewResponse` langsung (bukan `dict`) — instantiasi dipindah dari route ke service, sejajar pola `feature_service.get_preview()`; route `routes_sentiment.py::data_preview()` jadi delegasi tipis. (4) **R6**: tambah docstring pembeda `/sentiment/data/preview` vs `/feature-engineering/preview`. **Ditemukan tapi TIDAK diubah (butuh keputusan user):** `get_daily_preview()` lama menerima `page`/`page_size` tapi diam-diam DIBUANG oleh Pydantic (`PreviewResponse` tak punya field itu, extra='ignore' default) — jadi field itu selama ini tidak pernah benar-benar muncul di response meski endpoint menerima param tsb. Perilaku dipertahankan apa adanya (tidak breaking), tapi ini kandidat perbaikan kalau memang mau pagination metadata muncul di response. **Keputusan dibatalkan:** user awalnya minta standardisasi `async def` di `routes_sentiment.py`/`routes_prediction.py`, tapi dibatalkan setelah ditemukan bahwa service di baliknya (`predict_direction`, `run_backtest`, `get_pipeline_status`, dll) 100% sync-blocking (torch/pandas tanpa `await`) — mengubah ke `async def` akan memblokir event loop FastAPI alih-alih jalan di threadpool (regresi konkurensi). Handler tetap `def` sync sesuai kode asli.
- [2026-07-12] **Endpoint baru `combined/pipeline-steps` + tab frontend "Preprocessing" kategori Data Gabungan** (orchestrator Claude + 2 agent Sonnet paralel, kontrak JSON dikunci di prompt). **Backend:** `GET /api/v1/data-analysis/combined/pipeline-steps` — 7 langkah preprocessing dataset gabungan yang mirror `dataset_builder.build_dataset()` default (window=20, train_end=2022-12-31, val_end=2023-12-31): clean OHLCV → load sentimen → inner join → labeling → split by date → MinMaxScaler fit-train-only (data_min_/data_max_ per fitur) → windowing (hitung sampel saja, TANPA torch). Schema `PipelineStep`/`CombinedPipelineStepsResponse`; `FEATURE_COLS` di-import dari `dataset_builder` (single source of truth). Test parametrized ditambah; pytest 184/185 (1 gagal = `test_default_ticker` pre-existing). **Frontend (`ui-stock-prediction`):** kategori ke-3 "Data Gabungan (Input Model)" + tab Preprocessing → renderer `PipelineStepsView.jsx` (stepper vertikal, mini-card split, tabel min/max scaler, note amber, preview merge di bawah); `DataPreviewTable` diekstrak dari `SummaryTable.jsx` jadi komponen sendiri (reusable). Verifikasi end-to-end di browser: angka konsisten dgn training nyata (train 1241/val 244/test 42 baris; sampel window 1222/225/23 — test 23 cocok dgn catatan model 2026-06-11).
- [2026-07-12] **Fitur "API Training Live Notebook 05" + halaman FE "Model Training"** (orchestrator Claude + 2 agent Sonnet paralel, kontrak SSE/JSON dikunci identik di kedua prompt; rancangan: `code_plan/notebook05_training_api_plan.md`). Tujuan: expose proses TRAINING FINAL LSTM metodologi notebook 05 langsung dari FE via SSE (bukan hasil statis). Grid-search 144 kombinasi TIDAK dijalankan ulang — hasilnya (top-10, best val F2=0.8110) di-hardcode. **Backend (`stock_prediction`, terisolasi penuh dari produksi):** (1) `models/lstm/lstm_model.py` +`LSTMClassifierV2` (2-class softmax + CrossEntropy, last-hidden-state — kelas/`build_classifier` produksi tak disentuh). (2) `models/lstm/notebook05_trainer.py` BARU: reuse `dataset_builder.load_joined()`, split **kronologis persentase 70/15/15** (beda dari `build_dataset()` produksi yg split by-date), MinMaxScaler fit-train-only 6 FEATURE_COLS, class-weight inverse-freq, `ReduceLROnPlateau(mode=max, val_f2)`, early-stop monitor val F2, diagnosis overfit/underfit + **class-collapse per split** (recall kelas ≤0.05). Artefak terisolasi `lstm_nb05_{best.pt,scaler.joblib,metadata.json}` (produksi `direction_classifier.pt` dkk terverifikasi TIDAK berubah). (3) `app/schemas/training.py`, `app/services/training_service.py`, `app/api/v1/routes_training.py`: `POST /api/v1/train/notebook05` (SSE: event `start`→`epoch`×N→`done`/`error`) + `GET /api/v1/train/notebook05/grid-search-result` (EnvelopeRoute, statis). Event `done` berisi metrics+confusion_matrix+`diagnosis.class_collapse{train,val,test}`+artifact_paths. **Frontend (`ui-stock-prediction`):** halaman `pages/ModelTraining.jsx` + hook `useTrainingStream.js` (SSE via `fetch`+`ReadableStream` reader, bukan EventSource krn POST; AbortController cleanup) — card grid-search statis (badge Best), form hyperparameter prefilled best_config, 2 live PlotlyChart (loss & F2 per epoch), Run Log per event, metric cards, confusion matrix 2×2, dan **box peringatan class-collapse WAJIB tampil jujur** (amber/merah bila collapse — F2 tinggi disebut MENYESATKAN). Wiring Sidebar/App/Header (`/model-training`, icon `model_training`). **Verifikasi end-to-end (orchestrator, live di browser):** backend up, grid-search 200 OK, SSE training nyata pakai **CUDA**; split rows train 1068/val 229/test 230 (samples 1058/219/220 utk seq=10). Hasil (epoch minim): recall_up=1.0, tn=0, **`class_collapse={train,val,test}=true, any_collapse=true`** → box peringatan muncul benar, konsisten temuan lama "model selalu menebak Up". `pytest` 186/187 lulus (1 gagal = `test_default_ticker` pre-existing, di luar scope). `npm run lint`+`build` FE hijau. **Prinsip ditegakkan: laporkan angka apa adanya — F2=0.864 yg terlihat bagus TIDAK disembunyikan, class-collapse diekspos eksplisit.** Scope task = expose proses training, BUKAN memperbaiki akurasi model.
- [2026-07-13] **Varian training OHLCV-only (ablation study) + refactor konsolidasi shared training logic**. Tujuan: expose SSE training LSTM yang HANYA pakai 5 fitur OHLCV (tanpa `sentiment_mean`), untuk dibandingkan langsung dengan varian sentimen (`POST /train/notebook05`) — mengukur kontribusi nyata `sentiment_mean`. **Keputusan desain (2 putaran diskusi dgn user, plan mode):** (1) scope backend+frontend; (2) hyperparameter default REUSE `best_config` grid-search notebook05 (bukan grid-search baru) — ablation terkontrol, variabel tunggal yg beda cuma fitur; (3) **user menolak rencana awal** (file trainer baru `notebook05_ohlcv_trainer.py` per varian) — diminta re-desain supaya perbedaan varian (feature_cols/loader/nama artefak) ditentukan di **service layer**, bukan file `models/lstm/` baru per varian; (4) `LSTMClassifierV2` **di-rename** jadi `LSTMSoftmaxClassifier` (hapus akhiran "V2", dipakai bersama 2 varian, TANPA ubah arsitektur/perilaku — aman thd hasil val_f2=0.811 yg sudah tervalidasi). **Hasil refactor:** logic training (windowing, scaler, training loop, diagnosis) yg sebelumnya SATU salinan di `notebook05_trainer.py`, sekarang diekstrak jadi **`models/lstm/notebook05_common.py`** (`run_notebook05_training()`, generic lewat parameter `feature_cols`/`load_data_fn`/nama artefak) — SATU-SATUNYA salinan, dipakai kedua varian; `notebook05_trainer.py` dipangkas jadi konstanta saja (`DEFAULT_CONFIG`, `GRID_SEARCH_RESULT`, nama artefak varian sentimen), fungsi `train_notebook05()` dihapus (tak dibutuhkan lagi). **Loader baru:** `dataset_builder.py` + `OHLCV_FEATURE_COLS` + `load_ohlcv_only()` (baca `STOCK_CSV` saja, tanpa join sentimen; `FEATURE_COLS`/`load_joined()` produksi TIDAK disentuh). **Service layer** (`training_service.py`) kini tempat pemilihan varian: `run_training_stream()` (existing, sentimen) & `run_training_stream_ohlcv()` (baru) sama-sama memanggil `run_notebook05_training()` langsung dgn parameter beda — TIDAK ada file trainer baru di `models/lstm/`. **Endpoint baru:** `POST /api/v1/train/notebook05/ohlcv` (SSE, event contract identik, reuse `TrainRequest`+`sse_response()`); sengaja TIDAK ada endpoint `grid-search-result` utk varian ini (grid-search 5-fitur memang tak pernah dijalankan, tak dibuat seolah-olah ada). Artefak terisolasi: `lstm_nb05_ohlcv_{best.pt,scaler.joblib,metadata.json}`. **Frontend:** `useTrainingStream(endpoint)` diparameterisasi; komponen `TrainingPanel` diekstrak (`components/model-training/TrainingPanel.jsx`) dari `ModelTraining.jsx`; halaman kini render **KEDUA** `TrainingPanel` sekaligus (endpoint beda) dgn tab switcher yg toggle visibility via `className="hidden"` — **BUKAN** conditional render, supaya training SSE yg sedang jalan di tab tidak aktif TIDAK ter-abort/ke-reset saat pindah tab (langsung terkait prinsip unmount/Fiber yg dibahas user sebelumnya di sesi ini). **Verifikasi:** `pytest` 187/188 lulus (1 gagal = `test_default_ticker` pre-existing, di luar scope) + test SSE baru (`TestTrainNotebook05OhlcvStream`); end-to-end browser: training dijalankan di kedua tab, pindah tab terbukti TIDAK reset progress tab lain, artefak `lstm_nb05_ohlcv_*` terverifikasi tersimpan terpisah dari `lstm_nb05_*`. **Temuan konsisten pola lama:** varian OHLCV-only JUGA mengalami class-collapse (recall_up=1.0, val_f2=0.804) — box peringatan tampil jujur sesuai desain existing.
- [2026-07-13] **Rancangan disimpan (BELUM dieksekusi): notebook baru sesuai Batasan Masalah skripsi (BAB I)**. User membaca ulang BAB I skripsinya (`E:\SKRIPSI_ARIFIN\LIST_BAB_SKRIPSI\FIX_From_Pak_Eka\BAB_I_Muhammad Arifin_Rev_2.docx`, dibaca via MCP `markitdown`) dan menyadari notebook 03/06 (metodologi "v5": walk-forward 8-fold, AUC-ROC, ensemble 5-seed, kalibrasi Platt) **melebihi** Batasan Masalah skripsi yang eksplisit cuma minta 4 metrik (Accuracy/Precision/Recall/F1), horizon 1-hari (bukan 5-hari), fitur OHLCV+sentimen mentah (TANPA indikator teknikal RSI/MACD/BB), tuning via **Random Search** (bukan Grid Search), rentang data 2018-2024 (bukan 2008-2024), 2 model (LSTM-OHLCV baseline vs FinBERT-LSTM), dan **eksplisit TIDAK mencakup UI/deployment** (jadi `ui-stock-prediction` di luar scope penilaian skripsi, boleh tetap ada sbg demo). Rancangan notebook baru `07_LSTM_FinBERT_skripsi_scoped.ipynb` yang match 1:1 ke Batasan Masalah & Tujuan Khusus BAB I disimpan di `code_plan/skripsi_scoped_lstm_finbert_plan.md` — ada 5 keputusan terbuka yang perlu dikonfirmasi user saat delegasi (split ratio, interpretasi "fungsi aktivasi" utk PyTorch LSTM, kriteria seleksi Random Search, jumlah iterasi, last-timestep vs mean-pooling). **JANGAN diimplementasikan sampai user recall/minta eksekusi.**
- [2026-07-13] **Rancangan disimpan (BELUM dieksekusi): halaman Prediction tampilkan hasil training notebook05 + prediksi + backtest**. User ingin hasil training di halaman Model Training (yang hilang saat pindah tab/halaman karena cuma hidup di React state) bisa dilihat lagi & dipakai prediksi sungguhan di halaman Prediction (`pages/Predictions.jsx`, saat ini 100% mockup statis tanpa API call). Rancangan lengkap (backend: generalisasi `build_latest_window()`, fungsi inference+backtest baru di `notebook05_common.py`, 6 endpoint baru `/train/notebook05[/ohlcv]/{result,predict,backtest}`; frontend: extract komponen `MetricsCards`/`ConfusionMatrixGrid`/`ClassCollapseBanner` dari `TrainingPanel.jsx`, tulis ulang `Predictions.jsx` dgn tab switcher sama pola Model Training) disimpan di `code_plan/notebook05_prediction_page_plan.md` atas permintaan eksplisit user — **JANGAN diimplementasikan sampai user recall/minta eksekusi**.
- [2026-07-13] **Notebook baru `06_LSTM_experiment_2008_2024.ipynb` — replikasi metodologi v5 pada horizon 2008-2024**. Dibuat atas permintaan user untuk menguji apakah memperpanjang rentang data (2008-2024, ~16 tahun, mencakup GFC 2008 & COVID 2020) menghasilkan estimasi sinyal yang lebih robust dibanding notebook 03 (2018-2024, ~6 tahun). Data mentah 2008-2024 (`data/raw/stocks/GSPC_2008_2024.csv`, `data/processed/sentiment/headlines_daily_sentiment.csv`) sudah tersedia — tidak ada scraping ulang. **Keputusan disepakati user:** (1) set fitur SAMA PERSIS notebook 03 (10 fitur: 8 indikator teknikal stasioner + 2 sentimen, reuse `compute_technical_indicators()` dari `pipeline/feature_engineering/technical_indicators.py`, TIDAK menambah indikator baru — apples-to-apples, hindari p-hacking); (2) notebook ditulis LENGKAP dulu, **BELUM dieksekusi** (eksekusi jadi langkah terpisah, disarankan via nbconvert/papermill headless bukan cell-by-cell Jupyter MCP demi hemat token). **Struktur (33 cell, mirror notebook 03 + tambahan):** Bagian 0 (baru, gaya notebook 01) — overview data 2008-2024 (plot Close/Volume dgn penanda Lehman 2008 & COVID low, cek gap tanggal & coverage sentimen); Bagian 1 — load raw 2008-2024 → `StockPreprocessor.clean()` (reuse) → simpan ke `data/processed/stocks/GSPC_2008_2024.csv` (processed file baru, sebelumnya cuma ada utk 2018-2024) → merge sentimen → indikator teknikal; Bagian 2-3 — fitur/sequences/LSTMClassifier (arsitektur PERSIS sama, hidden=32/1 layer/dropout=0.5/mean-pooling); Bagian 4 — grid search **dijalankan ulang dari nol** (bukan reuse hyperparameter lama, karena distribusi data 16 tahun vs 6 tahun beda); Bagian 5 — evaluasi test-set ensemble 5-seed; Bagian 6/6b — walk-forward dgn **n_folds dinaikkan 5→8** dan sensitivity sweep `WF_TRAIN_SIZE` diperluas `[200,300,400,500,750,1000,expanding]` (sebelumnya cuma sampai 500) — rasional: data lebih panjang cukup utk fold lebih granular, menguji temuan "regime-dependent sign-flip" lintas lebih banyak rezim; Bagian 6c (baru, opsional, meminjam pola notebook 05) — baseline model tunggal (non-ensemble) dibanding ensemble 5-seed pada test-set slice yang sama; Bagian 7 — simpan artefak terisolasi `*_v6_2008_2024.*` (tidak menimpa `*_v5.*` maupun produksi). **Verifikasi dilakukan:** `nbformat.validate()` lulus, `ast.parse()` seluruh 33 cell code lulus tanpa syntax error, konfirmasi seluruh cell `outputs=[]`/`execution_count=None` (belum dieksekusi sesuai instruksi). **Ekspektasi dikomunikasikan jujur di markdown pembuka notebook:** data lebih panjang menambah keandalan statistik (bukan jaminan sinyal lebih mudah diprediksi) — prinsip anti p-hacking yang sama seperti notebook 03 tetap ditegakkan.
- [2026-07-12] **Keputusan scaling (dikonfirmasi ke user):** MinMaxScaler TETAP dilakukan SETELAH join (gabung raw → split by date → fit train-only), BUKAN per-sumber sebelum join — sklearn per-kolom independen jadi memisahkan scaler tidak mengubah hasil numerik, sementara scaling sebelum split = leakage. 1 artefak scaler = konsistensi inference. Revisit hanya kalau ganti metode normalisasi yang tidak per-kolom (row-wise/PCA).
- [2026-07-04] **Konsolidasi lapisan akses data ("satukan" repository)** — analisis codebase via agent Sonnet, lalu refactor tanpa perubahan perilaku (default config): (1) **`ArtifactRepository` dilengkapi** `load_metadata()/save_metadata()/metadata_path()` + `load_scaler()/save_scaler()/scaler_path()` (arg `filename=` opsional) — menutup celah yang bikin service bypass. (2) **`prediction_service.py`** tak lagi baca `metadata.json` manual via `json.loads` (3 tempat) → pakai `get_repositories()["artifact"].load_metadata()`; `_METADATA_FILE` & `import json` dihapus. (3) **`sentiment_service.py`** tak lagi resolve path via `os.environ["RAW_NEWS_CSV"/"SENTIMENT_PROCESSED_DIR"]` → pakai path-accessor repo baru (`NewsRepository.raw_headlines_path()/clean_headlines_path()`, `SentimentRepository.daily_sentiment_path()/daily_count_path()`); output save lewat `save_clean_headlines()`/`save_daily_sentiment()`; helper `_processed_dir()` dihapus. **Konsekuensi:** override path via env var TIDAK lagi dihormati (repository = sumber tunggal); default repo == nilai `.env.example` jadi lokasi identik. (4) **Helper tanggal bersama** `format_iso_date()` di `app/helpers/serialization.py` menggantikan `strftime("%Y-%m-%d")` yang tersebar (prediction_service + eda_service 4×). (5) **Bug laten diperbaiki:** `.env` lokal set `LSTM_MODEL_PATH=data/artifacts/lstm_weights/lstm_model.h5` (nama file `.h5` peninggalan TF) → `ArtifactRepository` menunjuk sub-dir `lstm_model.h5/` yang tak ada (dormant karena repo LSTM tak pernah dipakai). Factory `get_default_repositories()` kini normalisasi: jika `settings.lstm_model_path` punya suffix file → pakai direktori induk. **Batas arsitektur (sengaja):** `models/lstm/{lstm_trainer,lstm_predictor}.py` TETAP baca/tulis artefak langsung, TIDAK lewat `app/repositories` (agar `models/` tetap independen dari layer `app/`, hindari inversi dependensi). Verifikasi: 39 test (repositories/service/API) lulus + smoke test `get_model_status()`→is_available.
