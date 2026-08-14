import { useEffect, useState } from 'react'
import PageContainer from '../layout/PageContainer'
import Card, { CardHeader, CardTitle, CardContent } from '../components/Card'
import Button from '../components/Button'
import Icon from '../components/Icon'
import StatCard from '../components/charts/StatCard'
import PriceCandlestickChart from '../components/charts/PriceCandlestickChart'
import LatestNewsCard from '../components/dashboard/LatestNewsCard'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../components/ui/table'
import PredictionPanel, { NOTEBOOK07_METRIC_KEYS } from '../components/prediction/PredictionPanel'
import { useDataAnalysis } from '../hooks/useDataAnalysis'
import { useModelResult } from '../hooks/useModelResult'
import { useLivePredictStream } from '../hooks/useLivePredictStream'
import { fmtPct } from '../components/model-training/format'
import { cn } from '../utils/cn'

const LATEST_N = 30
const FINBERT_RESULT_PATH = '/train/skripsi/finbert-lstm/result'
const LIVE_PREDICT_PATH = '/live/predict/finbert-lstm'

const NOON_HOUR = 12
const NOON_REFRESH_STORAGE_KEY = 'dashboard_noon_refresh_date'

const VARIANTS = [
  {
    key: 'skripsi-baseline',
    label: 'LSTM',
    resultPath: '/train/skripsi/ohlcv/result',
    backtestPath: '/train/skripsi/ohlcv/backtest?split=test',
    backtestMetricKeys: NOTEBOOK07_METRIC_KEYS,
  },
  {
    key: 'skripsi-finbert',
    label: 'FinBERT-LSTM',
    resultPath: '/train/skripsi/finbert-lstm/result',
    backtestPath: '/train/skripsi/finbert-lstm/backtest?split=test',
    backtestMetricKeys: NOTEBOOK07_METRIC_KEYS,
  },
]

function todayDateStr() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function msUntilNextNoon() {
  const now = new Date()
  const noon = new Date(now.getFullYear(), now.getMonth(), now.getDate(), NOON_HOUR, 0, 0, 0)
  return noon > now ? noon - now : 0
}

const PIPELINE_STEPS = [
  { key: 'ohlcv', label: 'Fetch OHLCV', startEvent: 'fetching_ohlcv', doneEvent: 'fetching_ohlcv_done' },
  { key: 'news', label: 'Fetch Berita', startEvent: 'fetching_news', doneEvent: 'fetching_news_done' },
  { key: 'preprocess', label: 'Preprocessing', startEvent: 'preprocessing', doneEvent: 'preprocessing_done' },
  { key: 'infer', label: 'Inferensi', startEvent: 'inferring', doneEvent: 'done' },
]

function toChartData(rows) {
  return rows.map((r) => ({
    date: r.Date,
    open: r.Open,
    high: r.High,
    low: r.Low,
    close: r.Close,
  }))
}

function stepStatus(events, step) {
  if (events.some((e) => e.type === step.doneEvent)) return 'done'
  if (events.some((e) => e.type === step.startEvent)) return 'active'
  return 'pending'
}

function PipelineStepIndicator({ events }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {PIPELINE_STEPS.map((step) => {
        const status = stepStatus(events, step)
        const doneEventPayload = events.find((e) => e.type === step.doneEvent)
        return (
          <div
            key={step.key}
            className={cn(
              'rounded-lg border p-3 transition-colors',
              status === 'done' && 'border-emerald-200 bg-emerald-50',
              status === 'active' && 'border-blue-200 bg-blue-50',
              status === 'pending' && 'border-slate-200 bg-slate-50',
            )}
          >
            <div className="flex items-center gap-2">
              {status === 'active' && <Icon name="progress_activity" className="animate-spin text-base text-blue-600" />}
              {status === 'done' && <Icon name="check_circle" className="text-base text-emerald-600" />}
              {status === 'pending' && <Icon name="radio_button_unchecked" className="text-base text-slate-300" />}
              <p
                className={cn(
                  'text-xs font-semibold uppercase tracking-wide',
                  status === 'done' && 'text-emerald-700',
                  status === 'active' && 'text-blue-700',
                  status === 'pending' && 'text-slate-400',
                )}
              >
                {step.label}
              </p>
            </div>
            {doneEventPayload && (
              <p className="mt-1 text-xs text-slate-500">
                {step.key === 'ohlcv' && `${doneEventPayload.rows_fetched} baris (${doneEventPayload.date_start} → ${doneEventPayload.date_end})`}
                {step.key === 'news' && `${doneEventPayload.headlines_accumulated} headline terakumulasi`}
                {step.key === 'preprocess' &&
                  `${doneEventPayload.rows_available}/${doneEventPayload.window_required} baris siap · ${doneEventPayload.live_sentiment_days} hari sentimen live`}
                {step.key === 'infer' && 'selesai'}
              </p>
            )}
          </div>
        )
      })}
    </div>
  )
}

export default function Predictions() {
  const latest = useDataAnalysis(`/live/stocks/latest?n=${LATEST_N}`)
  const { result } = useModelResult(FINBERT_RESULT_PATH)
  const livePredict = useLivePredictStream(LIVE_PREDICT_PATH)
  const [newsRefreshKey, setNewsRefreshKey] = useState(0)
  const [activeVariant, setActiveVariant] = useState(VARIANTS[0].key)

  const refreshAll = () => {
    latest.refetch()
    setNewsRefreshKey((k) => k + 1)
  }

  // Auto-refresh sekali per hari setelah jam 12 siang (bukan polling terus-menerus):
  // kalau tab dibiarkan terbuka melewati jam 12, atau dibuka setelah jam 12 tapi
  // belum pernah fetch ulang hari itu, data live di-fetch ulang otomatis satu kali.
  useEffect(() => {
    const maybeRefresh = () => {
      const stamp = todayDateStr()
      if (new Date().getHours() >= NOON_HOUR && localStorage.getItem(NOON_REFRESH_STORAGE_KEY) !== stamp) {
        refreshAll()
        localStorage.setItem(NOON_REFRESH_STORAGE_KEY, stamp)
      }
    }

    maybeRefresh()
    const timeoutId = new Date().getHours() < NOON_HOUR ? setTimeout(maybeRefresh, msUntilNextNoon()) : null
    return () => clearTimeout(timeoutId)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [latest.refetch])

  const rows = latest.data?.rows ?? []
  const lastRow = rows[rows.length - 1]
  const prevRow = rows[rows.length - 2]
  const dailyChange =
    lastRow && prevRow ? ((lastRow.Close - prevRow.Close) / prevRow.Close) * 100 : null

  const isAvailable = Boolean(result.data?.is_available)
  const isRunning = livePredict.status === 'running'

  return (
    <PageContainer
      title="Prediksi"
      description="Data harga live S&P 500 (yfinance), berita terkini, prediksi arah harga 5 hari ke depan (live), serta prediksi & backtest per model dari hasil training tersimpan."
    >
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs text-slate-400">
          {latest.data?.fetched_at && `Terakhir fetch: ${latest.data.fetched_at}`}
        </p>
        <Button variant="secondary" size="sm" onClick={refreshAll} disabled={latest.loading}>
          {latest.loading ? (
            <Icon name="progress_activity" className="animate-spin text-base" />
          ) : (
            <Icon name="refresh" className="text-base" />
          )}
          Update Data & Berita
        </Button>
      </div>

      {latest.loading && (
        <div className="flex h-32 items-center justify-center gap-2 text-sm text-slate-400">
          <Icon name="progress_activity" className="animate-spin text-lg" />
          Mengambil data harga live...
        </div>
      )}

      {latest.error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
          <Icon name="error" className="text-lg" />
          {latest.error}
        </div>
      )}

      {rows.length > 0 && (
        <>
          <div className="grid grid-cols-3 gap-4">
            <StatCard
              label="Close Terakhir (Live)"
              value={lastRow.Close.toFixed(2)}
              delta={dailyChange ?? undefined}
              sparkline={rows.map((r) => r.Close)}
            />
            <StatCard label="Tanggal Terakhir" value={latest.data.latest_date} />
            <StatCard label="Volume Terakhir" value={lastRow.Volume.toLocaleString('id-ID')} />
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Harga OHLCV Live ({LATEST_N} Hari Terakhir)</CardTitle>
            </CardHeader>
            <CardContent>
              <PriceCandlestickChart data={toChartData(rows)} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Tabel Harga Terbaru</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="max-h-96 overflow-y-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Tanggal</TableHead>
                      <TableHead>Open</TableHead>
                      <TableHead>High</TableHead>
                      <TableHead>Low</TableHead>
                      <TableHead>Close</TableHead>
                      <TableHead>Volume</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {[...rows].reverse().map((r) => (
                      <TableRow key={r.Date}>
                        <TableCell className="font-mono">{r.Date}</TableCell>
                        <TableCell className="font-mono">{r.Open.toFixed(2)}</TableCell>
                        <TableCell className="font-mono">{r.High.toFixed(2)}</TableCell>
                        <TableCell className="font-mono">{r.Low.toFixed(2)}</TableCell>
                        <TableCell className="font-mono">{r.Close.toFixed(2)}</TableCell>
                        <TableCell className="font-mono">{r.Volume.toLocaleString('id-ID')}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </>
      )}

      <LatestNewsCard refreshKey={newsRefreshKey} />

      <Card>
        <CardHeader>
          <CardTitle>Prediksi Arah Harga 5 Hari ke Depan (Live)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {result.loading && (
            <div className="flex h-16 items-center gap-2 text-sm text-slate-400">
              <Icon name="progress_activity" className="animate-spin text-lg" />
              Memuat status model...
            </div>
          )}

          {result.data && !isAvailable && (
            <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500">
              <Icon name="info" className="text-lg" />
              Model FinBERT-LSTM belum pernah dilatih. Jalankan training di halaman Model Training terlebih dahulu.
            </div>
          )}

          {isAvailable && (
            <>
              <Button onClick={() => livePredict.start()} disabled={isRunning}>
                {isRunning ? (
                  <Icon name="progress_activity" className="animate-spin text-base" />
                ) : (
                  <Icon name="bolt" className="text-base" />
                )}
                Prediksi 5 Hari ke Depan (Fetch Live)
              </Button>

              {livePredict.events.length > 0 && <PipelineStepIndicator events={livePredict.events} />}

              {livePredict.status === 'error' && (
                <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
                  <Icon name="error" className="text-lg" />
                  {livePredict.error}
                </div>
              )}

              {livePredict.status === 'done' && livePredict.result && (
                <>
                  <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                    <div className="rounded border border-slate-200 p-3">
                      <p className="text-xs uppercase tracking-wide text-slate-400">Arah</p>
                      <p
                        className={cn(
                          'mt-1 font-mono text-xl font-semibold',
                          livePredict.result.direction === 'up' ? 'text-emerald-600' : 'text-red-600',
                        )}
                      >
                        {livePredict.result.direction === 'up' ? 'UP' : 'DOWN'}
                      </p>
                    </div>
                    <div className="rounded border border-slate-200 p-3">
                      <p className="text-xs uppercase tracking-wide text-slate-400">Probability Up</p>
                      <p className="mt-1 font-mono text-xl font-semibold text-slate-900">
                        {fmtPct(livePredict.result.probability_up)}
                      </p>
                    </div>
                    <div className="rounded border border-slate-200 p-3">
                      <p className="text-xs uppercase tracking-wide text-slate-400">Confidence</p>
                      <p className="mt-1 font-mono text-xl font-semibold text-slate-900">
                        {fmtPct(livePredict.result.confidence)}
                      </p>
                    </div>
                    <div className="rounded border border-slate-200 p-3">
                      <p className="text-xs uppercase tracking-wide text-slate-400">As Of → Target</p>
                      <p className="mt-1 font-mono text-sm font-semibold text-slate-900">
                        {livePredict.result.as_of_date} → {livePredict.result.target_date}
                      </p>
                    </div>
                  </div>
                  <p className="text-xs text-slate-400">
                    Window {livePredict.result.window} hari — {livePredict.result.live_sentiment_days ?? 0} hari di
                    antaranya punya sentimen berita live sungguhan, sisanya netral (0) karena cakupan berita live
                    terbatas.
                  </p>
                </>
              )}
            </>
          )}
        </CardContent>
      </Card>

      <div>
        <h3 className="text-sm font-semibold text-slate-900">Prediksi & Backtest per Model (Tersimpan)</h3>
        <p className="mt-1 text-xs text-slate-500">
          Prediksi hari berikutnya & backtest memakai model yang sudah ditraining dan tersimpan di backend. Lihat
          metrik & confusion matrix lengkapnya di halaman Model Training → tab "Hasil Training".
        </p>
      </div>

      <div className="flex gap-2 border-b border-slate-200">
        {VARIANTS.map((variant) => (
          <button
            key={variant.key}
            type="button"
            onClick={() => setActiveVariant(variant.key)}
            className={cn(
              'border-b-2 px-4 py-2 text-sm font-medium transition-colors',
              activeVariant === variant.key
                ? 'border-slate-900 text-slate-900'
                : 'border-transparent text-slate-400 hover:text-slate-600',
            )}
          >
            {variant.label}
          </button>
        ))}
      </div>

      {/*
        Semua panel dirender SEKALIGUS dan tetap mounted permanen — tab yang
        tidak aktif hanya disembunyikan lewat className, BUKAN conditional
        render, supaya hasil fetch/prediksi/backtest salah satu tab tidak
        hilang saat pindah tab (pola sama seperti ModelTraining.jsx).
      */}
      {VARIANTS.map((variant) => (
        <div key={variant.key} className={cn(activeVariant !== variant.key && 'hidden')}>
          <PredictionPanel
            resultPath={variant.resultPath}
            backtestPath={variant.backtestPath}
            backtestMetricKeys={variant.backtestMetricKeys}
          />
        </div>
      ))}
    </PageContainer>
  )
}
