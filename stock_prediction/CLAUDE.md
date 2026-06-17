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
