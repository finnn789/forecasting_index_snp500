# Panduan Integrasi Frontend — Stock Direction Prediction

> **Untuk AI Agent Frontend.** Dokumen ini ditulis oleh tim backend sebagai kontrak
> tunggal yang WAJIB diikuti saat wiring UI ke API. Referensi field-level lengkap
> (request/response nyata tiap endpoint) ada di
> **`stock_prediction/code_plan/frontend_api_reference.md`** — baca itu untuk detail.
>
> Update terakhir: 2026-06-11 (mengikuti model klasifikasi arah harga).

---

## 0. TL;DR — yang WAJIB kamu tahu sebelum mulai

1. **Project ini sekarang KLASIFIKASI ARAH, bukan regresi harga.** Output model =
   `direction: "up"|"down"` + `probability_up` + `confidence`. **TIDAK ADA**
   `predicted_close`, `rmse/mae/mape`, atau `ensemble weight` lagi.
2. **Kode frontend yang ada SEKARANG SUDAH USANG** dan harus dikoreksi (lihat §6):
   - `src/types/prediction.ts` → masih model regresi lama (predictedClose, ensemble, rmse). **Ganti.**
   - `src/lib/api/endpoints.ts` → path salah (`/api/predict`, `/api/pipeline/*` tidak ada). **Ganti.**
3. **Semua response dibungkus envelope** `SuccessResponse` → ambil dari `.data`.
4. **Jujur soal performa model:** model saat ini **selalu menebak "up"** (AUC≈0.38–0.51,
   mendekati acak). UI WAJIB menampilkan confidence apa adanya + disclaimer (§5, §7).
5. **Single ticker = `GSPC`** (S&P 500). Data berhenti **2024-03-04**. Belum multi-ticker.

---

## 1. Base URL & Konfigurasi

- Backend FastAPI: `http://localhost:8000` (lihat `stock_prediction/server.py`, CORS sudah aktif).
- Set di `.env` frontend: `VITE_API_BASE_URL=http://localhost:8000`.
- Swagger referensi: `http://localhost:8000/docs`.

## 2. Kontrak Envelope (BERLAKU UNTUK SEMUA ENDPOINT)

Setiap response sukses:
```json
{
  "success": true,
  "message": "Deskripsi singkat",
  "meta": { "timestamp": "2026-06-11T...Z", "version": "1.0" },
  "data": { /* payload sebenarnya ADA DI SINI */ }
}
```
Error:
```json
{
  "success": false,
  "error": { "code": "MODEL_NOT_TRAINED", "message": "...", "detail": null },
  "meta": { "timestamp": "...", "version": "1.0" }
}
```
- **Selalu baca `response.data`.** Helper `src/lib/api/core/envelope.ts` (`ApiEnvelope<T>`, `isEnvelope`) sudah ada — pakai itu.
- **Error penting:** `404` + `error.code="MODEL_NOT_TRAINED"` muncul saat model belum dilatih.
  UI prediksi harus menangani ini (tampilkan empty-state "Model belum dilatih", bukan crash).
- HTTP status: `200` sukses, `404` data/model tak ada, `422` validasi, `500` server.

## 3. Peta Endpoint → Halaman → Komponen

| Halaman | Endpoint | Dipakai untuk |
|---|---|---|
| **PredictionPage** | `POST /api/v1/predict` | Kartu arah utama (direction/probability/confidence) |
| **PredictionPage** | `GET /api/v1/predict/model/status` | Trust panel: metrics, trained_at, is_available |
| **PredictionPage** | `GET /api/v1/predict/backtest?split=test` | Chart prediksi-vs-aktual + confusion matrix |
| **DashboardPage** | `GET /api/health`, `GET /api/status` | Badge uptime / status sistem |
| **StockDataPage** | `GET /api/v1/data/eda/stocks/time-series` | Chart harga (line/area) |
| **StockDataPage** | `GET /api/v1/data/eda/stocks/raw` | Tabel 10 baris terakhir OHLCV |
| **StockDataPage** | `GET /api/v1/data/eda/stocks/daily-returns` | Histogram/line return harian |
| **StockDataPage** | `GET /api/v1/data/eda/stocks/drawdown` | Area chart drawdown |
| **StockDataPage** | `GET /api/v1/data/eda/stocks/descriptive-stats`, `/summary` | Kartu statistik |
| **SentimentPage** | `GET /api/v1/data/eda/sentiment-distribution` | Pie/bar distribusi sentimen |
| **SentimentPage** | `GET /api/v1/data/eda/news-per-year`, `/news-per-day` | Bar/line volume berita |
| **SentimentPage** | `GET /api/v1/data/eda/headline-length` | Histogram panjang headline |
| **SentimentPage** | `GET /api/v1/sentiment/data/preview` | Tabel sampel sentimen harian (paginated manual) |
| **PipelinePage** | `GET /api/v1/sentiment/pipeline/status`, `/model/status` | Status pipeline & FinBERT |
| **PipelinePage** | `POST /api/v1/sentiment/pipeline/run` | Jalankan pipeline (SSE stream) |

## 4. Tipe TypeScript yang BENAR (ganti yang lama)

`src/types/prediction.ts` — GANTI TOTAL isinya jadi:
```ts
export interface PredictionRequest {
  ticker?: string   // default "GSPC"
}

export interface DirectionPrediction {
  ticker: string
  as_of_date: string          // tanggal data terakhir, ISO
  target_date: string         // tanggal yang diprediksi
  direction: 'up' | 'down'
  probability_up: number      // 0..1
  confidence: number          // 0..1 = max(p, 1-p)
  window: number              // 20
  features_used: string[]     // ["Open","High","Low","Close","Volume","sentiment_mean"]
  model_version: string | null
}

export interface ModelInfo {
  is_available: boolean
  artifact_path: string
  window: number | null
  features_used: string[]
  n_features: number | null
  metrics: {
    val_acc: number; val_f1: number; val_auc: number
    test_acc: number; test_f1: number; test_auc: number
  } | null
  trained_at: string | null
}

// Backtest (prediksi vs aktual)
export interface BacktestPoint {
  date: string
  close: number
  actual_direction: 'up' | 'down'
  predicted_direction: 'up' | 'down'
  probability_up: number
  correct: boolean
}
export interface ConfusionMatrix { tp: number; tn: number; fp: number; fn: number }
export interface BacktestResult {
  ticker: string
  window: number
  split: string
  n_samples: number
  metrics: Record<string, number>   // accuracy, precision, recall, f1, auc
  confusion_matrix: ConfusionMatrix
  points: BacktestPoint[]
}
```

> OHLCV (`OHLCVPoint` di `types/prediction.ts`) boleh dipertahankan untuk StockDataPage,
> tapi **pindahkan ke `types/stock.ts`**. Hapus `PredictionPoint`, `EnsembleWeight`,
> dan field regresi dari `PredictionResult` lama.

## 5. Output prediksi — cara menampilkan (PENTING & JUJUR)

`POST /api/v1/predict` body `{"ticker":"GSPC"}` → `data`:
```json
{
  "ticker": "GSPC", "as_of_date": "2024-03-04", "target_date": "2024-03-05",
  "direction": "up", "probability_up": 0.529, "confidence": 0.529,
  "window": 20, "features_used": ["Open","High","Low","Close","Volume","sentiment_mean"],
  "model_version": "2026-06-11T11:42:06Z"
}
```
Aturan UI:
- **Badge arah:** ↑ hijau / ↓ merah. Tapi jika `confidence < 0.55`, tambahkan label
  netral **"sinyal lemah"** dan jangan pakai warna pekat yang menyiratkan keyakinan tinggi.
- **Gauge `probability_up`:** tampilkan 0–100%, dengan garis acuan di 50% (random baseline).
- **Disclaimer wajib** (komponen `<ErrorAlert variant="info">` atau banner): _"Prediksi
  bersifat edukatif, bukan saran finansial. Akurasi model saat ini mendekati acak."_

## 6. Koreksi `endpoints.ts` (path lama SALAH)

Ganti `src/lib/api/endpoints.ts` agar sesuai backend nyata:
```ts
export const ENDPOINTS = {
  // Prediction
  PREDICT:            '/api/v1/predict',
  PREDICT_STATUS:     '/api/v1/predict/model/status',
  PREDICT_BACKTEST:   '/api/v1/predict/backtest',
  // System
  HEALTH:             '/api/health',
  STATUS:             '/api/status',
  // Stocks EDA
  STOCK_TIMESERIES:   '/api/v1/data/eda/stocks/time-series',
  STOCK_RAW:          '/api/v1/data/eda/stocks/raw',
  STOCK_RETURNS:      '/api/v1/data/eda/stocks/daily-returns',
  STOCK_DRAWDOWN:     '/api/v1/data/eda/stocks/drawdown',
  STOCK_DESC_STATS:   '/api/v1/data/eda/stocks/descriptive-stats',
  STOCK_SUMMARY:      '/api/v1/data/eda/stocks/summary',
  // Sentiment / News EDA
  SENTIMENT_DIST:     '/api/v1/data/eda/sentiment-distribution',
  NEWS_PER_YEAR:      '/api/v1/data/eda/news-per-year',
  NEWS_PER_DAY:       '/api/v1/data/eda/news-per-day',
  HEADLINE_LENGTH:    '/api/v1/data/eda/headline-length',
  SENTIMENT_PREVIEW:  '/api/v1/sentiment/data/preview',
  SENTIMENT_MODEL:    '/api/v1/sentiment/model/status',
  // Sentiment Pipeline
  PIPELINE_STATUS:    '/api/v1/sentiment/pipeline/status',
  PIPELINE_RUN:       '/api/v1/sentiment/pipeline/run',   // SSE (text/event-stream)
  // Feature engineering
  FE_COLUMNS:         '/api/v1/feature-engineering/columns',
  FE_INFO:            '/api/v1/feature-engineering/info',
  FE_PREVIEW:         '/api/v1/feature-engineering/preview',
} as const
```
> Catatan: endpoint `/api/pipeline/*` (status/run/stop/history/logs) yang dipakai
> `usePipelineStatus`/`pipeline.api.ts` saat ini **TIDAK ADA** di backend. Yang tersedia
> hanya **sentiment pipeline** di atas. Sesuaikan PipelinePage ke endpoint sentimen,
> atau pertahankan mock sampai backend pipeline umum dibuat.

## 7. Resep Chart (stack kamu: `recharts@3.8`, `lucide-react`, shadcn-style)

**a. Backtest — Prediksi vs Aktual** (`GET /predict/backtest?split=test` → `data.points[]`)
- `<LineChart>` dengan `<Line dataKey="close">` (harga aktual).
- Overlay titik benar/salah: `<Scatter>` atau custom `dot` yang warnanya dari `point.correct`
  (hijau=benar, merah=salah). x=`date`, y=`close`.
- Di samping: kartu **Confusion Matrix** (grid 2×2 dari `data.confusion_matrix`) +
  kartu metrik (`accuracy`, `f1`, `auc`). **Sorot** bahwa model selalu "up" (tn=0, fp>0).

**b. Harga historis** (`/stocks/time-series` → array {date, close, ...})
- `<AreaChart>`/`<LineChart>`, x=`date`, y=`close`. Highlight 20 hari terakhir (window model)
  dengan `<ReferenceArea>`.

**c. Distribusi sentimen** (`/sentiment-distribution` → `data.data[] {label,count,pct}`)
- `<PieChart>`/`<BarChart>` x=`label`, y=`count`. Warna: positive=hijau, negative=merah, neutral=abu.

**d. Volume berita per tahun** (`/news-per-year` → `data.data[] {year,count}`)
- `<BarChart>` x=`year`, y=`count`.

**e. Drawdown** (`/stocks/drawdown`)
- `<AreaChart>` area negatif (merah), x=`date`, y=`drawdown`.

> Untuk format angka/tanggal pakai `src/lib/format.ts` yang sudah ada. Untuk class
> conditional pakai `clsx` + `tailwind-merge` (`cn()` di `src/lib/utils.ts`).

## 8. Urutan kerja yang disarankan untuk Agent Frontend

1. Update `endpoints.ts` (§6) + tipe `prediction.ts` (§4). Hapus mock regresi lama.
2. Wire **PredictionPage**: kartu arah + gauge + trust panel + disclaimer (§5).
3. Wire **backtest chart** + confusion matrix (§7a) — ini "wow factor" demo.
4. Wire **StockDataPage** & **SentimentPage** ke EDA endpoint (data sudah lengkap).
5. **PipelinePage**: arahkan ke endpoint *sentiment pipeline* atau biarkan mock (§6 catatan).
6. Matikan `withMock` (`src/lib/api/core/mock.ts`) per modul setelah endpoint nyata terverifikasi.

## 9. Hal yang BELUM tersedia di backend (jangan diasumsikan ada)
- Multi-ticker (hanya GSPC).
- Prediksi multi-hari ke depan (hanya 1 hari: `target_date`).
- Riwayat prediksi tersimpan / endpoint `/predict/history`.
- Feature importance per fitur.
- Pipeline umum `/api/pipeline/*` (yang ada hanya sentiment pipeline).

Jika butuh salah satu di atas, minta ke tim backend dulu — jangan buat mock yang
menyiratkan fitur itu sudah jalan.
