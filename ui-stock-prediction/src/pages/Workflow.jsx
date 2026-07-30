import { useEffect, useState } from 'react'
import PageContainer from '../layout/PageContainer'
import WorkflowStageCard, {
  StageLoading,
  StageError,
  StagePending,
} from '../components/workflow/WorkflowStageCard'
import CombinedDatasetStage from '../components/workflow/CombinedDatasetStage'
import { useDataAnalysis } from '../hooks/useDataAnalysis'
import { useSentimentPipelineStream } from '../hooks/useSentimentPipelineStream'
import { fetchJson } from '../utils/api'
import DataPreviewTable from '../components/data-analysis/DataPreviewTable'
import Button from '../components/Button'
import Icon from '../components/Icon'

const PIPELINE_STEP_LABELS = {
  loading_data: 'Membaca raw CSV',
  filtering: 'Memfilter rentang tanggal',
  loading_model: 'Memuat model FinBERT',
  model_ready: 'Model siap',
  inference: 'Scoring headline',
  aggregating: 'Mengagregasi harian',
  saving: 'Menyimpan file output',
  done: 'Selesai',
}

// Fetch yang cuma jalan kalau `path` tersedia — dipakai untuk endpoint yang
// mensyaratkan tahap sebelumnya sudah pernah dieksekusi (scoring-distribution
// butuh headlines_clean.csv, pipeline-steps butuh headlines_daily_sentiment.csv),
// supaya tidak memicu request yang pasti gagal saat prasyaratnya belum ada.
function useGatedFetch(path) {
  const [state, setState] = useState({ data: null, loading: Boolean(path), error: null })

  useEffect(() => {
    if (!path) {
      setState({ data: null, loading: false, error: null })
      return
    }
    const controller = new AbortController()
    setState({ data: null, loading: true, error: null })

    fetchJson(path, { signal: controller.signal })
      .then((data) => setState({ data, loading: false, error: null }))
      .catch((error) => {
        if (error.name === 'AbortError') return
        setState({ data: null, loading: false, error: error.message })
      })

    return () => controller.abort()
  }, [path])

  return state
}

export default function Workflow() {
  const [refreshKey, setRefreshKey] = useState(0)
  const sentimentStream = useSentimentPipelineStream()

  const stockRaw = useDataAnalysis('/data-analysis/stocks/raw-info')
  const sentimentRaw = useDataAnalysis('/data-analysis/sentiment/raw-info')
  const modelStatus = useDataAnalysis('/sentiment/model/status')
  const pipelineStatus = useDataAnalysis(`/sentiment/pipeline/status?_r=${refreshKey}`)

  // Sentiment pipeline (scoring + agregasi harian) dijalankan dalam satu job
  // backend — setelah selesai, paksa pipelineStatus fetch ulang supaya badge
  // Tahap 2/3 & data turunannya (scoringDist/pipelineSteps) ikut ter-update.
  useEffect(() => {
    if (sentimentStream.status === 'done') {
      setRefreshKey((k) => k + 1)
    }
  }, [sentimentStream.status])

  const cleanReady = pipelineStatus.data?.clean_file_exists ?? false
  const dailyReady = pipelineStatus.data?.daily_file_exists ?? false

  const scoringDist = useGatedFetch(cleanReady ? '/data-analysis/sentiment/scoring-distribution' : null)

  const baselineResult = useDataAnalysis('/train/skripsi/ohlcv/result')
  const finbertResult = useDataAnalysis('/train/skripsi/finbert-lstm/result')

  const trainingAvailable = Boolean(baselineResult.data?.is_available || finbertResult.data?.is_available)

  return (
    <PageContainer
      title="Alur Kerja Project"
      description="Ringkasan tiap tahap pipeline — dari data mentah hingga prediksi — diambil langsung dari status & hasil eksekusi backend."
    >
      <div>
        {/* 1. Data Mentah */}
        <WorkflowStageCard
          number={1}
          icon="storage"
          title="Data Mentah"
          description="OHLCV S&P 500 & headline berita mentah yang sudah tersedia di backend."
          status={{ label: 'Tersedia', tone: 'success' }}
        >
          {(stockRaw.loading || sentimentRaw.loading) && <StageLoading />}
          {stockRaw.error && <StageError message={stockRaw.error} />}
          {sentimentRaw.error && <StageError message={sentimentRaw.error} />}
          {stockRaw.data && sentimentRaw.data && (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">OHLCV Saham</p>
                <p className="mt-1 font-mono text-lg text-slate-900">
                  {stockRaw.data.total_rows.toLocaleString()} baris
                </p>
                <p className="text-xs text-slate-500">
                  {stockRaw.data.date_start} s/d {stockRaw.data.date_end}
                </p>
              </div>
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Headline Berita</p>
                <p className="mt-1 font-mono text-lg text-slate-900">
                  {sentimentRaw.data.total_rows.toLocaleString()} baris
                </p>
                <p className="text-xs text-slate-500">
                  {sentimentRaw.data.date_start} s/d {sentimentRaw.data.date_end}
                </p>
              </div>
            </div>
          )}

          {stockRaw.data && sentimentRaw.data && (
            <div className="space-y-4">
              <div>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Cuplikan OHLCV Mentah
                </p>
                <DataPreviewTable path="/data-analysis/stocks/raw-preview?n=10" />
              </div>
              <div>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Cuplikan Headline Mentah
                </p>
                <DataPreviewTable path="/data-analysis/sentiment/raw-preview?n=10" />
              </div>
            </div>
          )}
        </WorkflowStageCard>

        {/* 2. Sentiment Scoring */}
        <WorkflowStageCard
          number={2}
          icon="psychology"
          title="Sentiment Scoring (FinBERT)"
          description="Klasifikasi tiap headline (positive/negative/neutral) oleh model FinBERT."
          status={
            pipelineStatus.loading
              ? null
              : cleanReady
                ? { label: 'Sudah Dijalankan', tone: 'success' }
                : { label: 'Belum Dijalankan', tone: 'neutral' }
          }
        >
          {(modelStatus.loading || pipelineStatus.loading) && <StageLoading />}
          {modelStatus.error && <StageError message={modelStatus.error} />}
          {pipelineStatus.error && <StageError message={pipelineStatus.error} />}

          {modelStatus.data && (
            <p className="text-sm text-slate-600">
              Model FinBERT:{' '}
              <span className={modelStatus.data.is_available ? 'text-emerald-600' : 'text-red-600'}>
                {modelStatus.data.is_available ? 'siap dipakai' : 'tidak tersedia'}
              </span>{' '}
              ({modelStatus.data.source})
            </p>
          )}

          <div>
            <Button
              size="sm"
              variant="secondary"
              onClick={() => sentimentStream.run()}
              disabled={sentimentStream.status === 'running'}
            >
              {sentimentStream.status === 'running' ? (
                <Icon name="progress_activity" className="animate-spin text-base" />
              ) : (
                <Icon name="play_arrow" className="text-base" />
              )}
              Jalankan Sentiment Scoring
            </Button>
          </div>

          {sentimentStream.status === 'running' && (
            <div className="space-y-1.5">
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-slate-900 transition-all"
                  style={{ width: `${sentimentStream.pct}%` }}
                />
              </div>
              <p className="text-xs text-slate-500">
                {PIPELINE_STEP_LABELS[sentimentStream.step] ?? sentimentStream.step} ({sentimentStream.pct}%) —{' '}
                {sentimentStream.msg}
              </p>
            </div>
          )}

          {sentimentStream.status === 'error' && <StageError message={sentimentStream.error} />}

          {!pipelineStatus.loading && !cleanReady && sentimentStream.status !== 'running' && (
            <StagePending message="Sentiment pipeline belum pernah dijalankan — belum ada hasil klasifikasi headline." />
          )}

          {cleanReady && scoringDist.loading && <StageLoading />}
          {cleanReady && scoringDist.error && <StageError message={scoringDist.error} />}
          {cleanReady && scoringDist.data && (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Total Headline Discoring</p>
                <p className="mt-1 font-mono text-lg text-slate-900">
                  {scoringDist.data.total_headlines.toLocaleString()}
                </p>
              </div>
              {Object.entries(scoringDist.data.label_counts).map(([label, count]) => (
                <div key={label} className="rounded-lg border border-slate-200 p-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
                  <p className="mt-1 font-mono text-lg text-slate-900">
                    {count.toLocaleString()}{' '}
                    <span className="text-xs font-normal text-slate-500">
                      ({scoringDist.data.label_pct[label]?.toFixed(1)}%)
                    </span>
                  </p>
                </div>
              ))}
            </div>
          )}

          {cleanReady && (
            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                Tabel Hasil Sentiment Scoring
              </p>
              <DataPreviewTable path="/data-analysis/sentiment/clean-preview?n=10" />
            </div>
          )}
        </WorkflowStageCard>

        {/* 3. Agregasi Harian */}
        <WorkflowStageCard
          number={3}
          icon="calendar_month"
          title="Agregasi Harian"
          description="Skor tiap headline digabung jadi satu nilai sentiment_mean per hari."
          status={
            pipelineStatus.loading
              ? null
              : dailyReady
                ? { label: 'Sudah Dijalankan', tone: 'success' }
                : { label: 'Belum Dijalankan', tone: 'neutral' }
          }
        >
          {pipelineStatus.loading && <StageLoading />}
          {!pipelineStatus.loading && !dailyReady && (
            <StagePending message="Belum ada file agregasi harian — jalankan sentiment pipeline terlebih dahulu." />
          )}
          {dailyReady && pipelineStatus.data && (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Jumlah Hari Teragregasi</p>
                <p className="mt-1 font-mono text-lg text-slate-900">
                  {pipelineStatus.data.total_days?.toLocaleString() ?? '—'} hari
                </p>
              </div>
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Rentang Tanggal</p>
                <p className="mt-1 font-mono text-sm text-slate-900">
                  {pipelineStatus.data.date_range?.start ?? '—'} s/d {pipelineStatus.data.date_range?.end ?? '—'}
                </p>
              </div>
            </div>
          )}

          {dailyReady && (
            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                Tabel Hasil Agregasi Harian
              </p>
              <DataPreviewTable path="/sentiment/data/preview?page=1&page_size=10" />
            </div>
          )}
        </WorkflowStageCard>

        {/* 4. Penggabungan & Preprocessing (Penyedia Data Latih) */}
        <WorkflowStageCard
          number={4}
          icon="tune"
          title="Penggabungan & Preprocessing (Penyedia Data Latih)"
          description="Fitur return OHLCV + sentiment_mean → label horizon-5 → split kronologis → capping outlier → MinMax scaling → windowing. Mirror persis apa yang dipakai training — 'Bangun Dataset Latih' menyimpannya sebagai artifact yang dibaca Model Training."
          status={!dailyReady ? { label: 'Menunggu Agregasi', tone: 'neutral' } : null}
        >
          <CombinedDatasetStage dailyReady={dailyReady} />
        </WorkflowStageCard>

        {/* 5. Training Model */}
        <WorkflowStageCard
          number={5}
          icon="model_training"
          title="Training Model (Random Search)"
          description="Random Search LSTM-OHLCV (Model A) & FinBERT-LSTM (Model B) — hasil tersimpan terakhir."
          status={
            baselineResult.loading || finbertResult.loading
              ? null
              : trainingAvailable
                ? { label: 'Sudah Ditraining', tone: 'success' }
                : { label: 'Belum Ditraining', tone: 'neutral' }
          }
          linkTo="/"
          linkLabel="Buka halaman Model Training →"
        >
          {(baselineResult.loading || finbertResult.loading) && <StageLoading />}
          {baselineResult.error && <StageError message={baselineResult.error} />}
          {finbertResult.error && <StageError message={finbertResult.error} />}

          {!baselineResult.loading && !finbertResult.loading && !trainingAvailable && (
            <StagePending message="Belum ada hasil Random Search tersimpan untuk Model A maupun Model B." />
          )}

          {(baselineResult.data?.is_available || finbertResult.data?.is_available) && (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {[
                { label: 'Model A — LSTM-OHLCV', result: baselineResult.data },
                { label: 'Model B — FinBERT-LSTM', result: finbertResult.data },
              ].map(({ label, result }) => (
                <div key={label} className="rounded-lg border border-slate-200 p-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
                  {result?.is_available ? (
                    <>
                      <p className="mt-1 font-mono text-lg text-slate-900">
                        F1 {result.metrics?.f1?.toFixed(3) ?? '—'}
                      </p>
                      <p className="text-xs text-slate-500">Dilatih: {result.trained_at ?? '—'}</p>
                    </>
                  ) : (
                    <p className="mt-1 text-sm text-slate-400">Belum ditraining</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </WorkflowStageCard>

        {/* 6. Prediction */}
        <WorkflowStageCard
          number={6}
          icon="trending_up"
          title="Prediction"
          description="Prediksi arah harga hari berikutnya & backtest — dijalankan manual per model."
          status={
            trainingAvailable
              ? { label: 'Model Siap Diprediksi', tone: 'success' }
              : { label: 'Menunggu Training', tone: 'neutral' }
          }
          isLast
          linkTo="/predictions"
          linkLabel="Buka halaman Predictions →"
        >
          {!trainingAvailable && (
            <StagePending message="Belum ada model terlatih — jalankan tahap Training Model terlebih dahulu." />
          )}
          {trainingAvailable && (
            <p className="text-sm text-slate-600">
              Model terlatih tersedia. Buka halaman Predictions untuk menjalankan prediksi hari berikutnya atau backtest.
            </p>
          )}
        </WorkflowStageCard>
      </div>
    </PageContainer>
  )
}
