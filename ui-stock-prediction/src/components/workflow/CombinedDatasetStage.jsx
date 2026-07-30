import { useState } from 'react'
import { useDataAnalysis } from '../../hooks/useDataAnalysis'
import { postJson } from '../../utils/api'
import { cn } from '../../utils/cn'
import DataPreviewTable from '../data-analysis/DataPreviewTable'
import Button from '../Button'
import Icon from '../Icon'
import { StageError, StageLoading, StagePending } from './WorkflowStageCard'

const VARIANTS = [
  { value: 'finbert', label: 'Model B — FinBERT-LSTM (6 fitur)' },
  { value: 'baseline', label: 'Model A — OHLCV (5 fitur)' },
]

const SPLIT_MODES = [
  { value: 'random_search', label: 'Random Search (70/15/15)' },
  { value: 'manual', label: 'Training Manual (80/20)' },
]

function ToggleGroup({ options, value, onChange }) {
  return (
    <div className="inline-flex rounded-lg border border-slate-200 p-0.5">
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          onClick={() => onChange(opt.value)}
          className={cn(
            'rounded-md px-3 py-1.5 text-xs font-medium transition-colors',
            value === opt.value ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100',
          )}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}

function fmtRows(rowsIn, rowsOut) {
  if (rowsIn != null && rowsOut != null) return `${rowsIn.toLocaleString()} → ${rowsOut.toLocaleString()} baris`
  if (rowsOut != null) return `${rowsOut.toLocaleString()} baris`
  return null
}

function StepRow({ step }) {
  return (
    <li className="flex items-start justify-between gap-3 py-1.5 text-sm">
      <div>
        <span className="text-slate-700">{step.name}</span>
        {step.description && <p className="text-xs text-slate-400">{step.description}</p>}
      </div>
      {fmtRows(step.rows_in, step.rows_out) && (
        <span className="shrink-0 rounded bg-slate-50 border border-slate-200 px-2 py-0.5 font-mono text-xs text-slate-600">
          {fmtRows(step.rows_in, step.rows_out)}
        </span>
      )}
    </li>
  )
}

function ScalerTable({ trainMin, trainMax, featureCols }) {
  if (!featureCols?.length) return null
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50">
            <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Fitur</th>
            <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Train Min</th>
            <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Train Max</th>
          </tr>
        </thead>
        <tbody>
          {featureCols.map((col) => (
            <tr key={col} className="border-b border-slate-100 last:border-0">
              <td className="px-3 py-2 text-slate-600">{col}</td>
              <td className="px-3 py-2 font-mono text-slate-900">{trainMin?.[col] ?? '—'}</td>
              <td className="px-3 py-2 font-mono text-slate-900">{trainMax?.[col] ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function CombinedDatasetStage({ dailyReady }) {
  const [variant, setVariant] = useState('finbert')
  const [splitMode, setSplitMode] = useState('random_search')
  const [statusRefreshKey, setStatusRefreshKey] = useState(0)
  const [buildState, setBuildState] = useState({ loading: false, error: null })

  const query = `variant=${variant}&split_mode=${splitMode}`
  const pipelineSteps = useDataAnalysis(dailyReady ? `/data-analysis/combined/pipeline-steps?${query}` : null)
  const datasetStatus = useDataAnalysis(
    dailyReady ? `/data-analysis/combined/dataset-status?${query}&_r=${statusRefreshKey}` : null,
  )

  const steps = pipelineSteps.data?.steps ?? []
  const splitStep = steps.find((s) => s.order === 5)
  const cappingStep = steps.find((s) => s.order === 6)
  const scalerStep = steps.find((s) => s.order === 7)

  async function handleBuild() {
    setBuildState({ loading: true, error: null })
    try {
      await postJson(`/data-analysis/combined/build-dataset?${query}`)
      setStatusRefreshKey((k) => k + 1)
      setBuildState({ loading: false, error: null })
    } catch (err) {
      setBuildState({ loading: false, error: err.message })
    }
  }

  if (!dailyReady) {
    return <StagePending message="Menunggu tahap Agregasi Harian selesai dijalankan." />
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <ToggleGroup options={VARIANTS} value={variant} onChange={setVariant} />
        <ToggleGroup options={SPLIT_MODES} value={splitMode} onChange={setSplitMode} />
      </div>

      {pipelineSteps.loading && <StageLoading label="Memuat langkah preprocessing..." />}
      {pipelineSteps.error && <StageError message={pipelineSteps.error} />}

      {steps.length > 0 && (
        <ul className="divide-y divide-slate-100">
          {steps.map((step) => (
            <StepRow key={step.order} step={step} />
          ))}
        </ul>
      )}

      {splitStep?.detail && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {['train', 'val', 'test'].map((key) => (
            <div key={key} className="rounded-lg border border-slate-200 p-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{key}</p>
              <p className="mt-1 font-mono text-lg text-slate-900">
                {splitStep.detail[key]?.rows != null ? splitStep.detail[key].rows.toLocaleString() : '—'}
              </p>
              <p className="text-xs text-slate-500">{splitStep.detail[key]?.range || '—'}</p>
            </div>
          ))}
        </div>
      )}

      {cappingStep?.detail?.n_capped && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
          Jumlah nilai di-clip (capping outlier IQR): train {cappingStep.detail.n_capped.train
            ? Object.values(cappingStep.detail.n_capped.train).reduce((a, b) => a + b, 0)
            : 0}, val {cappingStep.detail.n_capped.val
            ? Object.values(cappingStep.detail.n_capped.val).reduce((a, b) => a + b, 0)
            : 0}, test {cappingStep.detail.n_capped.test
            ? Object.values(cappingStep.detail.n_capped.test).reduce((a, b) => a + b, 0)
            : 0}
        </div>
      )}

      {scalerStep?.detail && (
        <ScalerTable
          trainMin={scalerStep.detail.train_min}
          trainMax={scalerStep.detail.train_max}
          featureCols={pipelineSteps.data?.feature_cols}
        />
      )}

      {steps.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Cuplikan Data Siap Training (Setelah MinMax Scaling)
          </p>
          <DataPreviewTable path={`/data-analysis/combined/scaled-preview?n=10&split=train&${query}`} />
        </div>
      )}

      <div className="rounded-lg border border-slate-200 p-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-medium text-slate-900">Dataset Latih (Artifact)</p>
            {datasetStatus.loading && <p className="text-xs text-slate-400">Memeriksa status...</p>}
            {datasetStatus.data && (
              <p className="text-xs text-slate-500">
                {!datasetStatus.data.exists && 'Belum dibangun — Model Training akan menolak jalan sebelum ini dibangun.'}
                {datasetStatus.data.exists && datasetStatus.data.is_fresh && (
                  <>Dibangun {datasetStatus.data.built_at} — sinkron dengan data sumber saat ini.</>
                )}
                {datasetStatus.data.exists && !datasetStatus.data.is_fresh && (
                  <span className="text-amber-600">
                    Basi — data sumber berubah sejak dibangun ({datasetStatus.data.built_at}). Bangun ulang.
                  </span>
                )}
              </p>
            )}
          </div>
          <Button size="sm" variant="secondary" onClick={handleBuild} disabled={buildState.loading}>
            {buildState.loading ? (
              <Icon name="progress_activity" className="animate-spin text-base" />
            ) : (
              <Icon name="build" className="text-base" />
            )}
            Bangun Dataset Latih
          </Button>
        </div>
        {buildState.error && <StageError message={buildState.error} />}
      </div>
    </div>
  )
}
