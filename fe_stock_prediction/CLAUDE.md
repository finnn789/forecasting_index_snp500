# CLAUDE.md — Frontend Stock Prediction (Skripsi)

## Ringkasan Proyek

Dashboard UI untuk sistem prediksi harga saham berbasis **FinBERT + LSTM + Ensemble**.
Backend: FastAPI (`/home/skripsi_code/stock_prediction`).
Frontend: **React 19 + Vite + Tailwind CSS v4** (CSS-first config).

---

## Arsitektur Direktori

```
src/
├── index.css              # Tailwind v4 @theme tokens + base styles
├── main.tsx
├── App.tsx                # Root router (react-router-dom)
│
├── lib/
│   ├── utils.ts           # cn(), focusRing helpers
│   ├── constants.ts       # Ticker list, stage labels, env flags
│   └── api/               # SELURUH logika HTTP ada di sini
│       ├── client.ts      # fetch/axios base config (base URL, headers, timeout)
│       ├── endpoints.ts   # Konstanta endpoint string
│       ├── pipeline.api.ts
│       ├── prediction.api.ts
│       ├── sentiment.api.ts
│       └── mock/          # Data statis tanpa koneksi API (dev/offline)
│           ├── pipeline.mock.ts
│           ├── prediction.mock.ts
│           └── sentiment.mock.ts
│
├── types/
│   ├── pipeline.ts        # PipelineStatus, StageEnum, RunLog, StageResult
│   ├── prediction.ts      # PredictionResult, EnsembleOutput, OHLCVPoint
│   └── sentiment.ts       # SentimentScore, NewsItem, DailySentiment
│
├── hooks/
│   ├── usePipelineStatus.ts   # Poll pipeline status (pakai mock jika offline)
│   ├── usePrediction.ts       # POST predict + loading state
│   └── useSSE.ts              # Server-Sent Events untuk live log stream
│
├── components/
│   ├── ui/                    # Atom — design system murni, no business logic
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── badge.tsx
│   │   ├── input.tsx
│   │   ├── label.tsx
│   │   ├── progress.tsx
│   │   ├── skeleton.tsx
│   │   ├── separator.tsx
│   │   └── tooltip.tsx
│   │
│   ├── layout/
│   │   ├── Sidebar.tsx
│   │   ├── Header.tsx
│   │   ├── MainLayout.tsx
│   │   └── PageContainer.tsx
│   │
│   ├── pipeline/
│   │   ├── PipelineControlPanel.tsx
│   │   ├── StageStatusList.tsx
│   │   ├── StageCard.tsx
│   │   ├── LiveLogViewer.tsx
│   │   └── RunHistoryTable.tsx
│   │
│   ├── prediction/
│   │   ├── TickerSelector.tsx
│   │   ├── PredictionForm.tsx
│   │   ├── PredictionChart.tsx
│   │   ├── EnsembleBreakdown.tsx
│   │   └── PredictionResultCard.tsx
│   │
│   ├── sentiment/
│   │   ├── SentimentSummary.tsx
│   │   ├── NewsHeadlineList.tsx
│   │   └── SentimentChart.tsx
│   │
│   └── shared/
│       ├── StatusBadge.tsx
│       ├── ErrorAlert.tsx
│       ├── LoadingOverlay.tsx
│       └── EmptyState.tsx
│
└── pages/
    ├── DashboardPage.tsx
    ├── PipelinePage.tsx
    ├── PredictionPage.tsx
    ├── SentimentPage.tsx
    └── LogsPage.tsx
```

---

## Aturan API Layer (`src/lib/api/`)

- **Semua** HTTP call wajib lewat `lib/api/`. Komponen dan hook TIDAK boleh fetch langsung.
- `client.ts` ekspos satu fungsi `apiFetch(path, options)` — base URL dari env var `VITE_API_URL`.
- Setiap file `*.api.ts` mengekspos fungsi-fungsi typed yang return `Promise<T>`.
- `mock/` folder berisi data statis yang mirip respons API nyata. Digunakan saat `VITE_USE_MOCK=true`.
- Switching mock ↔ real: ubah `VITE_USE_MOCK` di `.env.local`, tidak perlu ubah kode komponen.

## Environment Variables

```
VITE_API_URL=http://localhost:8000    # URL FastAPI backend
VITE_USE_MOCK=true                    # true = pakai mock data, false = hit API nyata
```

---

## Design Tokens (index.css)

Tailwind v4 CSS-first. Semua token ada di `@theme {}` di `index.css`.

Palet warna domain:
- `--color-pipeline-running` → kuning/amber  
- `--color-pipeline-done`    → hijau  
- `--color-pipeline-error`   → merah  
- `--color-pipeline-idle`    → abu  
- `--color-sentiment-pos`    → hijau  
- `--color-sentiment-neg`    → merah  
- `--color-sentiment-neu`    → abu-biru  

---

## Dependensi Utama

| Package | Versi | Fungsi |
|---------|-------|--------|
| react-router-dom | ^7 | Routing |
| class-variance-authority | ^0.7 | CVA variants |
| clsx | ^2 | Class merging |
| tailwind-merge | ^3 | Tailwind class conflict resolver |
| lucide-react | latest | Icons |
| recharts | ^2 | Chart prediksi & sentimen |

---

## Fase Implementasi

1. **Foundation** — index.css tokens, lib/utils, types/, lib/api/ (SELESAI: struktur dibuat)
2. **UI Atoms** — components/ui/
3. **Layout** — Sidebar, Header, MainLayout, routing
4. **Pipeline Page** — StageCard, LiveLogViewer, ControlPanel
5. **Prediction Page** — Form + Chart + EnsembleBreakdown
6. **Sentiment Page** — SentimentChart + NewsHeadlineList

---

## Keputusan Penting

- **Tidak pakai Redux/Zustand** — state lokal + hooks sudah cukup untuk skripsi
- **Recharts** dipilih atas Apex karena lebih ringan dan composable
- **Mock data by default** (`VITE_USE_MOCK=true`) — UI bisa dikembangkan tanpa backend nyata
- **React 19** — tidak pakai `forwardRef`, ref adalah prop biasa
- **Dark mode** — class-based via `@custom-variant dark`
