import { useEffect, useMemo, useState } from 'react'
import PageContainer from '../layout/PageContainer'
import Card, { CardHeader, CardTitle, CardContent } from '../components/Card'
import Icon from '../components/Icon'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../components/ui/table'
import { fetchJson } from '../utils/api'
import { cn } from '../utils/cn'
import { fmtPct } from '../components/model-training/format'
import RandomSearchPanel from '../components/model-training/RandomSearchPanel'
import ManualTrainingPanel from '../components/model-training/ManualTrainingPanel'

const VARIANTS = [
  {
    key: 'skripsi-baseline',
    label: 'LSTM',
    endpoint: '/train/skripsi/ohlcv',
    manualEndpoint: '/train/skripsi/ohlcv/manual',
  },
  {
    key: 'skripsi-finbert',
    label: 'FinBERT-LSTM',
    endpoint: '/train/skripsi/finbert-lstm',
    manualEndpoint: '/train/skripsi/finbert-lstm/manual',
  },
]

const INITIAL_MANUAL_PREFILL = {
  'skripsi-baseline': { config: null, token: 0 },
  'skripsi-finbert': { config: null, token: 0 },
}

const SEARCH_SPACE_ROWS = [
  { key: 'hidden_size', label: 'Hidden Size' },
  { key: 'num_layers', label: 'Jumlah Layer' },
  { key: 'dropout_range', label: 'Dropout' },
  { key: 'optimizer', label: 'Optimizer' },
  { key: 'activation', label: 'Aktivasi FC-Head' },
  { key: 'lr_range', label: 'Learning Rate' },
  { key: 'epochs', label: 'Epochs' },
  { key: 'batch_size', label: 'Batch Size' },
]

const COMPARISON_METRICS = [
  { key: 'accuracy', label: 'Accuracy' },
  { key: 'precision', label: 'Precision' },
  { key: 'recall', label: 'Recall' },
  { key: 'f1', label: 'F1-Score' },
]

function formatSpaceValue(value) {
  if (Array.isArray(value)) return value.join(', ')
  return String(value)
}

export default function ModelTraining() {
  const [searchSpaceState, setSearchSpaceState] = useState({ data: null, loading: true, error: null })
  const [activeVariant, setActiveVariant] = useState(VARIANTS[0].key)
  const [skripsiResults, setSkripsiResults] = useState({ baseline: null, finbert: null })
  const [manualPrefill, setManualPrefill] = useState(INITIAL_MANUAL_PREFILL)

  // Ambil search space Random Search skripsi-scoped (statis, info saja — Random
  // Search dijalankan LIVE, tidak ada hasil statis tersimpan).
  useEffect(() => {
    const controller = new AbortController()

    fetchJson('/train/skripsi/search-space', { signal: controller.signal })
      .then((data) => setSearchSpaceState({ data, loading: false, error: null }))
      .catch((error) => {
        if (error.name === 'AbortError') return
        setSearchSpaceState({ data: null, loading: false, error: error.message })
      })

    return () => controller.abort()
  }, [])

  const comparisonRows = useMemo(() => {
    const { baseline, finbert } = skripsiResults
    if (!baseline || !finbert) return null
    return COMPARISON_METRICS.map((m) => {
      const a = baseline.metrics[m.key]
      const b = finbert.metrics[m.key]
      return { label: m.label, a, b, diff: b - a }
    })
  }, [skripsiResults])

  return (
    <PageContainer
      title="Model Training"
      description="Jalankan Random Search dan bandingkan hasil model baseline (OHLCV) vs FinBERT-LSTM (OHLCV + Sentimen)."
    >
      <Card>
        <CardHeader>
          <CardTitle>Random Search — Search Space (Notebook 07)</CardTitle>
        </CardHeader>

        {searchSpaceState.loading && (
          <CardContent className="flex h-32 items-center justify-center gap-2 text-sm text-slate-400">
            <Icon name="progress_activity" className="animate-spin text-lg" />
            Memuat search space...
          </CardContent>
        )}

        {searchSpaceState.error && (
          <CardContent>
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
              <Icon name="error" className="text-lg" />
              {searchSpaceState.error}
            </div>
          </CardContent>
        )}

        {searchSpaceState.data && (
          <>
            <div className="flex flex-wrap items-center gap-6 border-b border-slate-200 px-6 py-3 text-sm">
              <div>
                <span className="text-xs uppercase tracking-wide text-slate-400">Jumlah Iterasi Default</span>
                <p className="font-mono font-semibold text-slate-900">{searchSpaceState.data.n_iter}</p>
              </div>
              <div>
                <span className="text-xs uppercase tracking-wide text-slate-400">Window</span>
                <p className="font-mono font-semibold text-slate-900">{searchSpaceState.data.window}</p>
              </div>
            </div>
            <CardContent className="p-0">
              <Table>
                <TableBody>
                  {SEARCH_SPACE_ROWS.map((row) => (
                    <TableRow key={row.key}>
                      <TableCell className="w-40 font-medium text-slate-600">{row.label}</TableCell>
                      <TableCell className="font-mono text-slate-900">
                        {formatSpaceValue(searchSpaceState.data[row.key])}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
            <CardContent className="border-t border-slate-200 py-3 text-xs text-slate-500">
              Random Search dijalankan LIVE tiap kali tombol "Mulai Random Search" diklik di tab di bawah, sesuai
              metodologi Batasan Masalah BAB I (Random Search, bukan Grid Search).
            </CardContent>
          </>
        )}
      </Card>

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
        Kedua panel dirender SEKALIGUS dan tetap mounted permanen — tab yang
        tidak aktif hanya disembunyikan lewat className, BUKAN conditional
        render ({activeVariant === X && <Panel/>}). Alasan: conditional render
        akan unmount panel yang tidak aktif, yang berarti training SSE yang
        sedang berjalan di tab itu ter-abort (AbortController cleanup) dan
        seluruh progress (log epoch/iterasi, chart) hilang. Tujuan fitur ini
        adalah membandingkan training berdampingan yang bisa berjalan cukup
        lama, jadi identitas komponen harus tetap sama saat pindah tab.
      */}
      {VARIANTS.map((variant) => {
        const datasetVariant = variant.key === 'skripsi-baseline' ? 'baseline' : 'finbert'
        return (
          <div key={variant.key} className={cn('space-y-6', activeVariant !== variant.key && 'hidden')}>
            <RandomSearchPanel
              endpoint={variant.endpoint}
              variant={datasetVariant}
              onDone={(result) =>
                setSkripsiResults((prev) => ({
                  ...prev,
                  [datasetVariant]: result,
                }))
              }
              onUseBestConfig={(bestConfig) =>
                setManualPrefill((prev) => ({
                  ...prev,
                  [variant.key]: { config: bestConfig, token: prev[variant.key].token + 1 },
                }))
              }
            />

            <div className="border-t border-slate-200 pt-6">
              <ManualTrainingPanel
                endpoint={variant.manualEndpoint}
                variant={datasetVariant}
                prefill={manualPrefill[variant.key]}
              />
            </div>
          </div>
        )
      })}

      {comparisonRows && (
        <Card>
          <CardHeader>
            <CardTitle>Perbandingan Model A (LSTM-OHLCV) vs Model B (FinBERT-LSTM)</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Metrik</TableHead>
                  <TableHead>Model A (LSTM-OHLCV)</TableHead>
                  <TableHead>Model B (FinBERT-LSTM)</TableHead>
                  <TableHead>Selisih (B - A)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {comparisonRows.map((row) => (
                  <TableRow key={row.label}>
                    <TableCell className="font-medium text-slate-700">{row.label}</TableCell>
                    <TableCell className="font-mono">{fmtPct(row.a)}</TableCell>
                    <TableCell className="font-mono">{fmtPct(row.b)}</TableCell>
                    <TableCell
                      className={cn(
                        'font-mono font-semibold',
                        row.diff > 0 ? 'text-emerald-600' : row.diff < 0 ? 'text-red-600' : 'text-slate-500',
                      )}
                    >
                      {row.diff > 0 ? '+' : ''}
                      {fmtPct(row.diff)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
          <CardContent className="border-t border-slate-200 py-3 text-xs text-slate-500">
            Menjawab Hipotesa #4 BAB I: apakah FinBERT-LSTM (OHLCV + sentimen) mengungguli LSTM-OHLCV baseline?
            Dilaporkan apa adanya — bukan berarti Model B harus menang (prinsip anti p-hacking, konsisten dengan
            notebook 07).
          </CardContent>
        </Card>
      )}
    </PageContainer>
  )
}
