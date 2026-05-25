# Frontend — Sistem Prediksi Harga Saham

Dashboard UI untuk sistem prediksi harga saham berbasis **FinBERT + LSTM + Ensemble**.  
Bagian dari proyek skripsi: *"Prediksi Harga Saham Menggunakan Analisis Sentimen Berita Keuangan dan Deep Learning"*

---

## Tech Stack

| Teknologi | Versi | Fungsi |
|-----------|-------|--------|
| React | 19 | UI framework |
| TypeScript | 6 | Type safety |
| Vite | 8 | Build tool & dev server |
| Tailwind CSS | 4 | Styling (CSS-first config) |
| React Router | 7 | Client-side routing |
| Recharts | 3 | Chart prediksi & sentimen |
| CVA | 0.7 | Component variant system |
| Lucide React | latest | Icon library |
| clsx + tailwind-merge | — | Class name utilities |

---

## Prasyarat

- Node.js ≥ 18
- npm ≥ 9
- Backend FastAPI berjalan di `http://localhost:8000` *(opsional, bisa pakai mock)*

---

## Memulai

```bash
# 1. Clone dan masuk ke direktori
cd fe_stock_prediction

# 2. Install dependensi
npm install

# 3. Salin file environment
cp .env.local.example .env.local   # atau buat manual, lihat bagian Env Variables

# 4. Jalankan dev server
npm run dev
```

Buka `http://localhost:5173` (atau port berikutnya jika sudah terpakai).

---

## Environment Variables

Buat file `.env.local` di root project:

```env
VITE_API_URL=http://localhost:8000
VITE_USE_MOCK=true
```

| Variabel | Default | Keterangan |
|----------|---------|------------|
| `VITE_API_URL` | `http://localhost:8000` | URL base FastAPI backend |
| `VITE_USE_MOCK` | `true` | `true` = data statis (tanpa backend), `false` = hit API nyata |

> **Mode Mock** aktif secara default. UI bisa dikembangkan dan dieksplorasi sepenuhnya tanpa menjalankan backend.

---

## Perintah NPM

```bash
npm run dev       # Dev server dengan HMR
npm run build     # Build produksi (TypeScript check + Vite bundle)
npm run preview   # Preview hasil build
npm run lint      # ESLint
```

---

## Struktur Direktori

```
src/
├── index.css                    # Tailwind v4 @theme tokens (design system)
├── main.tsx                     # Entry point
├── App.tsx                      # Root router
│
├── lib/
│   ├── utils.ts                 # cn(), focusRing, formatDate, formatDuration
│   ├── constants.ts             # Daftar ticker, pipeline stages, env flags
│   └── api/                     # ── SELURUH logika HTTP ada di sini ──
│       ├── client.ts            # apiFetch<T>() + ApiError class
│       ├── endpoints.ts         # Konstanta string endpoint
│       ├── pipeline.api.ts      # getPipelineStatus, runPipeline, stopPipeline, ...
│       ├── prediction.api.ts    # getPrediction
│       ├── sentiment.api.ts     # getSentiment
│       └── mock/                # Data statis (dipakai saat VITE_USE_MOCK=true)
│           ├── pipeline.mock.ts
│           ├── prediction.mock.ts
│           └── sentiment.mock.ts
│
├── types/
│   ├── pipeline.ts              # PipelineStatus, StageResult, RunLog, RunHistoryItem
│   ├── prediction.ts            # PredictionResult, OHLCVPoint, EnsembleWeight
│   └── sentiment.ts             # SentimentSummary, NewsItem, DailySentiment
│
├── hooks/
│   ├── usePipelineStatus.ts     # Polling status pipeline (interval configurable)
│   ├── usePrediction.ts         # POST predict + loading/error state
│   ├── useSentiment.ts          # Fetch sentimen per ticker
│   └── useSSE.ts                # Server-Sent Events untuk live log stream
│
├── components/
│   ├── ui/                      # Atom — design system murni, no business logic
│   │   ├── button.tsx           # 6 variant, 4 size (CVA)
│   │   ├── card.tsx             # Card + Header + Title + Description + Content + Footer
│   │   ├── badge.tsx            # 9 variant termasuk pipeline state & sentiment
│   │   ├── input.tsx            # Dengan error state + aria
│   │   ├── label.tsx
│   │   ├── progress.tsx         # 4 variant warna, animated
│   │   ├── skeleton.tsx         # Loading placeholder
│   │   ├── separator.tsx        # horizontal / vertical
│   │   └── tooltip.tsx          # CSS-only, 4 sisi
│   │
│   ├── layout/
│   │   ├── Sidebar.tsx          # Nav dengan NavLink aktif
│   │   ├── Header.tsx           # Judul dinamis per route + Mock badge
│   │   ├── MainLayout.tsx       # Shell: Sidebar + Header + <Outlet>
│   │   └── PageContainer.tsx    # Title/description/action header + children
│   │
│   ├── pipeline/
│   │   ├── PipelineControlPanel.tsx  # Tombol Run/Stop + progress bar
│   │   ├── StageStatusList.tsx       # Daftar StageCard
│   │   ├── StageCard.tsx             # Card satu tahap (expandable detail)
│   │   ├── LiveLogViewer.tsx         # Log streaming via SSE, auto-scroll
│   │   └── RunHistoryTable.tsx       # Tabel riwayat run pipeline
│   │
│   ├── prediction/
│   │   ├── TickerSelector.tsx        # Dropdown saham IDX
│   │   ├── PredictionForm.tsx        # Form ticker + tanggal
│   │   ├── PredictionChart.tsx       # Recharts: histori OHLCV + forecast + CI band
│   │   ├── EnsembleBreakdown.tsx     # Bobot LSTM vs FinBERT + confidence
│   │   └── PredictionResultCard.tsx  # Ringkasan harga + perubahan % + metrics
│   │
│   ├── sentiment/
│   │   ├── SentimentSummary.tsx      # Skor besar, distribusi bar, stat grid
│   │   ├── SentimentChart.tsx        # Recharts: stacked bar + garis skor rata-rata
│   │   └── NewsHeadlineList.tsx      # List berita + score bar + SentimentBadge
│   │
│   └── shared/
│       ├── StatusBadge.tsx      # PipelineStatusBadge + SentimentBadge (typed wrapper)
│       ├── ErrorAlert.tsx       # Alert error dismissible, aria role="alert"
│       ├── EmptyState.tsx       # Icon + title + description + action slot
│       └── LoadingOverlay.tsx   # Spinner + label, aria-busy
│
└── pages/
    ├── DashboardPage.tsx        # Stat cards overview + quick actions
    ├── PipelinePage.tsx         # Monitor pipeline lengkap
    ├── PredictionPage.tsx       # Form prediksi + chart + hasil ensemble
    ├── SentimentPage.tsx        # Analisis sentimen berita FinBERT
    └── LogsPage.tsx             # Tabel log dengan filter level
```

---

## Halaman & Fitur

### Dashboard (`/`)
Ringkasan sistem: status pipeline terkini, progress, prediksi terakhir, sentimen hari ini. Polling otomatis setiap 5 detik. Quick access ke semua halaman utama.

### Pipeline (`/pipeline`)
Monitor dan kontrol pipeline pemrosesan data secara real-time.

- **Kontrol:** tombol Run / Stop, refresh manual
- **Progress bar:** berwarna sesuai state (running=kuning, done=hijau, error=merah)
- **Tahapan:** 6 stage (Fetch → Clean → Sentiment → Feature Engineering → Train LSTM → Evaluasi), expandable detail per stage
- **Live Log:** streaming via Server-Sent Events, color-coded per level (INFO/WARNING/ERROR/DEBUG), auto-scroll
- **Riwayat Run:** tabel run sebelumnya dengan durasi dan keterangan error

### Prediksi (`/prediction`)
Prediksi harga penutupan saham menggunakan model ensemble.

- **Form:** pilih ticker (8 saham IDX) + tanggal target
- **Chart:** histori OHLCV 30 hari + garis forecast 7 hari + confidence band, garis pembatas histori/forecast
- **Hasil:** harga prediksi, perubahan % berwarna, metrics RMSE/MAE/MAPE
- **Ensemble Breakdown:** bar bobot LSTM vs FinBERT + indikator confidence (Tinggi/Sedang/Rendah)

### Sentimen (`/sentiment`)
Analisis sentimen berita keuangan dari model FinBERT.

- **Ticker switcher:** ganti ticker → re-fetch otomatis
- **Ringkasan:** skor rata-rata berwarna, badge dominant, tren (Membaik/Memburuk/Stabil), distribusi bar tricolor hari ini
- **Chart tren:** stacked bar jumlah berita (pos/neu/neg) + garis skor rata-rata harian, dual-axis
- **Berita terkini:** list dengan score bar vertikal, source, tanggal, SentimentBadge, skor numerik

### Log (`/logs`)
Tabel riwayat log dengan filter per level.

- Filter: ALL / INFO / WARNING / ERROR / DEBUG
- Kolom: waktu, level badge, tahap, pesan
- Counter entri tersaring vs total

---

## API Layer

Semua HTTP call **wajib** melewati `src/lib/api/`. Komponen dan hook tidak boleh fetch langsung.

```
Komponen / Hook
      ↓
  *.api.ts  ←→  mock/*.mock.ts  (VITE_USE_MOCK=true)
      ↓
  client.ts (apiFetch)
      ↓
  FastAPI Backend
```

### Switching Mock ↔ Real API

```env
# Pakai mock (default, tanpa backend)
VITE_USE_MOCK=true

# Pakai API nyata
VITE_USE_MOCK=false
VITE_API_URL=http://localhost:8000
```

Tidak ada perubahan kode komponen — hanya env var.

### Endpoint yang Digunakan

| Endpoint | Method | Fungsi |
|----------|--------|--------|
| `GET /api/pipeline/status` | GET | Status + tahapan pipeline aktif |
| `POST /api/pipeline/run` | POST | Jalankan pipeline baru |
| `POST /api/pipeline/stop` | POST | Hentikan pipeline aktif |
| `GET /api/pipeline/history` | GET | Riwayat run sebelumnya |
| `GET /api/pipeline/logs` | SSE | Stream log real-time |
| `POST /api/predict` | POST | Jalankan prediksi harga |
| `GET /api/sentiment?ticker=` | GET | Data sentimen per ticker |

---

## Design System

Design tokens didefinisikan di `src/index.css` menggunakan Tailwind CSS v4 CSS-first (`@theme {}`).

### Palet Warna (OKLCH)

```css
/* Surface */
--color-background  /* oklch(12% ...) — latar gelap utama */
--color-surface     /* oklch(17% ...) — sidebar, header   */
--color-surface-2   /* oklch(22% ...) — card sekunder     */

/* Brand */
--color-primary     /* biru teknis                         */

/* Pipeline State */
--color-pipeline-running  /* amber/kuning — berjalan       */
--color-pipeline-done     /* hijau — selesai               */
--color-pipeline-error    /* merah — error                 */
--color-pipeline-idle     /* abu — menunggu                */

/* Sentiment */
--color-sentiment-pos     /* hijau                         */
--color-sentiment-neg     /* merah                         */
--color-sentiment-neu     /* abu-biru                      */
```

### Komponen UI (Atoms)

Semua komponen di `src/components/ui/` adalah **pure presentational** — tidak ada state global, tidak ada fetch. Dibangun dengan CVA (Class Variance Authority) untuk variant yang type-safe.

```tsx
<Button variant="default | outline | ghost | destructive | secondary | link"
        size="sm | md | lg | icon" />

<Badge variant="default | primary | running | done | error | idle |
               positive | negative | neutral"
       dot={boolean} />

<Progress value={0-100}
          variant="default | running | done | error"
          showLabel={boolean} />

<Card>
  <CardHeader>
    <CardTitle />
    <CardDescription />
  </CardHeader>
  <CardContent />
  <CardFooter />
</Card>
```

---

## Hooks

| Hook | Parameter | Return |
|------|-----------|--------|
| `usePipelineStatus(intervalMs?)` | interval polling (default 3000ms) | `{ status, loading, error, refetch }` |
| `usePrediction()` | — | `{ result, loading, error, predict(req) }` |
| `useSentiment(ticker)` | kode saham | `{ data, loading, error }` |
| `useSSE(active)` | boolean aktif/tidak | `{ logs, connected }` |

---

## Saham yang Didukung (Mock)

| Ticker | Nama |
|--------|------|
| BBCA.JK | Bank Central Asia |
| BBRI.JK | Bank Rakyat Indonesia |
| TLKM.JK | Telkom Indonesia |
| ASII.JK | Astra International |
| BMRI.JK | Bank Mandiri |
| GOTO.JK | GoTo Group |
| UNVR.JK | Unilever Indonesia |
| ICBP.JK | Indofood CBP |

---

## Koneksi ke Backend

Backend (FastAPI) ada di `/home/skripsi_code/stock_prediction`.

```bash
# Jalankan backend (dari direktori backend)
uvicorn app.server:app --reload --port 8000

# Kemudian ubah .env.local frontend
VITE_USE_MOCK=false
```

Pastikan CORS di FastAPI mengizinkan `http://localhost:5173`.
