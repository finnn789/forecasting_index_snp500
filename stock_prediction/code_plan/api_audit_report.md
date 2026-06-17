# Laporan Audit API v1 — Stock Prediction

**Tanggal:** 2026-06-04
**Metode:** Multi-agent swarm audit (3 Scout Haiku + 1 Auditor Sonnet, orchestrated)
**Scope:** Semua endpoint di `app/api/v1/` + service & schema terkait

---

## 1. Ringkasan Eksekutif

Total endpoint terdeteksi: **15 aktif** (1 file kosong: `routes_prediction.py`).

| Kategori Temuan | Jumlah |
|---|---:|
| Duplikasi eksak (endpoint identik) | 1 |
| Overlap fungsional (potensi konflik) | 3 |
| Inkonsistensi schema/pattern | 5 |
| File placeholder kosong | 2 (`routes_prediction.py`, `prediction_service.py`) |

**Verdict:** API v1 secara umum sudah mengikuti standar `SuccessResponse`/`BaseResponse`, namun ada **1 duplikasi eksak yang harus dihapus**, **dead code** di sentiment service, dan **inkonsistensi exception handling** yang melanggar keputusan refactor 2026-05-25.

---

## 2. Peta Lengkap Endpoint

### 2.1 General & Status (`routes_general.py`, `routes_status.py`)

| Method | Path | Function | Params | Service | Response |
|---|---|---|---|---|---|
| GET | `/` | `root()` | — | `app.config` | `SuccessResponse[APIInfo]` |
| GET | `/api/status` | `get_status()` | — | `core.state.get_uptime()` | `SuccessResponse[ServiceStatus]` |
| GET | `/api/health` | `health_check()` | — | — | `SuccessResponse[HealthCheck]` |

### 2.2 Data EDA (`routes_data.py`)

| Method | Path | Function | Params | Service | Response |
|---|---|---|---|---|---|
| GET | `/data/eda/summary` | `eda_summary()` | — | `eda_service.get_dataset_summary()` | `SuccessResponse[DatasetSummary]` |
| GET | `/data/eda/news-per-year` | `eda_news_per_year()` | — | `eda_service.get_news_per_year()` | `SuccessResponse[NewsPerYearResponse]` |
| GET | `/data/eda/news-per-day` | `eda_news_per_day()` | — | `eda_service.get_news_per_day()` | `SuccessResponse[NewsPerDayStats]` |
| GET | `/data/eda/headline-length` | `eda_headline_length()` | — | `eda_service.get_headline_length()` | `SuccessResponse[HeadlineLengthStats]` |
| GET | `/data/eda/sentiment-distribution` | `eda_sentiment_distribution()` | — | `eda_service.get_sentiment_distribution()` | `SuccessResponse[SentimentDistributionResponse]` |
| GET | `/data/eda/summary-statistics` ⚠️ | `eda_summary_statistics()` | `ticker` (**unused**) | `eda_service.get_dataset_summary()` | `SuccessResponse[DatasetSummary]` |

### 2.3 Feature Engineering (`routes_feature_engineering.py`)

| Method | Path | Function | Params | Service | Response |
|---|---|---|---|---|---|
| GET | `/feature-engineering/info` | `fe_info()` | — | `feature_service.get_processed_info()` | `SuccessResponse[ProcessedDataInfo]` |
| GET | `/feature-engineering/columns` | `fe_columns()` | `source`, `file` | `feature_service.get_columns()` | `SuccessResponse[ColumnInfoResponse]` |
| GET | `/feature-engineering/preview` | `fe_preview()` | `source`, `file`, `n` (1-50) | `feature_service.get_preview()` | `SuccessResponse[PreviewResponse]` |

### 2.4 Sentiment (`routes_sentiment.py`)

| Method | Path | Function | Params | Service | Response |
|---|---|---|---|---|---|
| POST | `/sentiment/pipeline/run` | `run_pipeline()` | `start_date`, `end_date`, `batch_size` | `sentiment_service.run_preprocessing_pipeline_stream()` | **SSE Stream** |
| GET | `/sentiment/pipeline/status` | `pipeline_status()` | — | `sentiment_service.get_pipeline_status()` | `SuccessResponse[PipelineStatusResponse]` |
| GET | `/sentiment/data/preview` | `data_preview()` | `page`, `page_size` | `sentiment_service.get_daily_preview()` | `SuccessResponse[PreviewResponse]` |
| GET | `/sentiment/model/status` | `model_status()` | — | `sentiment_service.get_model_status()` | `SuccessResponse[ModelStatusResponse]` |

### 2.5 Prediction (`routes_prediction.py`)

**Status:** File kosong (0 byte logic). `prediction_service.py` juga placeholder. Belum diimplementasikan sesuai roadmap di `implementation_plan.md`.

---

## 3. Matriks Duplikasi (Confirmed)

| Endpoint A | Endpoint B | Jenis | Bukti Code |
|---|---|---|---|
| `GET /data/eda/summary` | `GET /data/eda/summary-statistics` | **EXACT** | Keduanya memanggil `eda_service.get_dataset_summary()` tanpa argumen. `routes_data.py:27` vs `routes_data.py:90`. Response schema identik: `SuccessResponse[DatasetSummary]`. |
| `GET /feature-engineering/preview` | `GET /sentiment/data/preview` | **PARTIAL** | Keduanya pakai schema `PreviewResponse` (`schemas/sentiment.py:174`). FE-preview generic (path+source param); sentiment-preview hardcode `headlines_daily_sentiment.csv`. Klien bisa dapat data identik dari 2 endpoint berbeda. |

---

## 4. Overlap Fungsional (Berisiko Konflik)

| Endpoint A | Endpoint B | Apa yang Overlap | Risiko |
|---|---|---|---|
| `GET /feature-engineering/info` | `GET /sentiment/pipeline/status` | Keduanya scan metadata `data/processed/sentiment/`. `feature_service.py:41-68` vs `sentiment_service.py:316-358`. Metrik `total_headlines`, `total_days`, keberadaan file dilaporkan di kedua endpoint. | **Medium** |
| `GET /data/eda/sentiment-distribution` | `GET /sentiment/pipeline/status` | Keduanya membaca kolom `sentiment_label` dari CSV yang sama via `NewsRepository.load_clean_headlines()`. `eda_service.py:133` & `sentiment_service.py:330`. Tidak konflik data, tapi I/O duplikat. | **Low** |
| `GET /feature-engineering/preview?source=sentiment` | `GET /sentiment/data/preview` | FE-preview (`source=sentiment&file=headlines_daily_sentiment`) bisa menghasilkan output identik dengan sentiment data preview. | **Medium** |

---

## 5. Inkonsistensi Schema & Pattern

1. **Schema sentiment tidak inherit `BaseResponse`** — Seluruh class di `app/schemas/sentiment.py` (baris 14, 24, 50, 55, 61, 70, 82, 88, 95, 141, 151, 164, 174, 187, 197, 205) hanya inherit `BaseModel`. **Melanggar aturan CLAUDE.md** yang mewajibkan semua schema response wrap `BaseResponse`.

2. **Parameter `ticker` tidak digunakan** — `eda_summary_statistics(ticker: str)` di `routes_data.py:87` mendeklarasikan `ticker` sebagai required query param tetapi tidak pernah dipakai di body. Menjebak pemanggil.

3. **`sentiment_service` masih lempar `HTTPException` mentah** — `sentiment_service.py:86, 94, 107, 113, 367` pakai `HTTPException`, **melanggar keputusan refactor 2026-05-25** yang menetapkan exception harus pakai `DomainError`/`NotFoundError` dari `app.core.exceptions`. `feature_service.py:33` sudah benar.

4. **Dead code: `run_preprocessing_pipeline()` versi sinkron** — `sentiment_service.py:74-159` mendefinisikan versi non-stream, tapi tidak ada endpoint yang memanggilnya. `routes_sentiment.py:43` hanya pakai versi `_stream()`.

5. **Pola instantiasi `PreviewResponse` tidak konsisten** — `routes_sentiment.py:57-61` instansiasi dari `dict` via `**result`, sementara `feature_service.py:118` return object langsung. Rawan runtime error jika key dict berubah.

---

## 6. Rekomendasi Konsolidasi

### Prioritas Tinggi (Non-breaking)

| # | Action | File | Justifikasi |
|---|---|---|---|
| R1 | **Hapus endpoint `/data/eda/summary-statistics`** | `routes_data.py:77-91` | Exact duplicate dari `/summary`. Belum ada klien registered. |
| R2 | **Ganti `HTTPException` → `DomainError`/`NotFoundError`** | `sentiment_service.py:86,94,107,113,367` | Konsistensi dengan refactor 2026-05-25 (`feature_service.py:33` sudah pakai pola ini). |
| R3 | **Hapus dead code `run_preprocessing_pipeline()` sinkron** | `sentiment_service.py:74-159` | Tidak ada caller. Mengurangi beban maintenance ~85 baris. |
| R4 | **Refactor schema sentiment inherit `BaseResponse`** | `app/schemas/sentiment.py` (banyak baris) | Memenuhi aturan CLAUDE.md tentang response wrapper. |

### Prioritas Medium

| # | Action | File | Justifikasi |
|---|---|---|---|
| R5 | **Pindahkan instantiasi `PreviewResponse` ke service** | `sentiment_service.py:361` (`get_daily_preview`) | Return `PreviewResponse` langsung, bukan dict. Sejajar dengan `feature_service.get_preview()`. |
| R6 | **Tambahkan docstring pembeda** | `routes_feature_engineering.py` & `routes_sentiment.py` | Jelaskan eksplisit bahwa `/sentiment/data/preview` adalah shortcut ke file spesifik pipeline. |
| R7 | **Jika R1 ditolak:** ubah `ticker: str` → `ticker: str \| None = None` | `routes_data.py:87` | Hindari menjebak pemanggil dengan param required yang tidak dipakai. |

### Prioritas Rendah (Future Work)

| # | Action | Justifikasi |
|---|---|---|
| R8 | Implementasi `routes_prediction.py` + `prediction_service.py` | File masih kosong, blocker untuk endpoint inti `predict`. |
| R9 | Konsolidasikan logic scan `data/processed/sentiment/` ke satu helper | Hindari duplikat I/O antara `feature_service.get_processed_info()` & `sentiment_service.get_pipeline_status()`. |

---

## 7. Lampiran: Metodologi Swarm

```
Orchestrator (Sonnet/Opus)
│
├─ Scout-1 (Haiku) → routes_general.py + routes_status.py
├─ Scout-2 (Haiku) → routes_data.py + routes_feature_engineering.py + eda/feature services
├─ Scout-3 (Haiku) → routes_sentiment.py + routes_prediction.py + sentiment service & schema
│        ↓ (paralel, ~13 detik each)
└─ Auditor (Sonnet/Reviewer) → Cross-reference + verifikasi langsung ke source
         ↓ (~45 detik)
   Laporan final (file ini)
```

**Total token usage:** ~91k tokens (3 scout + 1 auditor).
**Durasi paralel:** ~13 detik (scout) + 45 detik (auditor) = ~58 detik wall-clock.

---

## 8. Next Action

Direkomendasikan eksekusi **R1–R4** dalam 1 PR (non-breaking, scope kecil), lalu **R5–R7** dalam PR terpisah. Implementasi prediction layer (R8) di PR mandiri sesuai `implementation_plan.md`.
