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
