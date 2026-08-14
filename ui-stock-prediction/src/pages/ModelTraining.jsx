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
import PersistedResultCard from '../components/model-training/PersistedResultCard'
import { useModelResult } from '../hooks/useModelResult'

const VARIANTS = [
  {
    key: 'skripsi-baseline',
    label: 'LSTM',
    endpoint: '/train/skripsi/ohlcv',
    manualEndpoint: '/train/skripsi/ohlcv/manual',
    resultPath: '/train/skripsi/ohlcv/result',
  },
  {
    key: 'skripsi-finbert',
    label: 'FinBERT-LSTM',
    endpoint: '/train/skripsi/finbert-lstm',
    manualEndpoint: '/train/skripsi/finbert-lstm/manual',
    resultPath: '/train/skripsi/finbert-lstm/result',
  },
]

const SECTIONS = [
  { key: 'training', label: 'Model Training' },
  { key: 'results', label: 'Hasil Training' },
]

const INITIAL_MANUAL_PREFILL = {
  'skripsi-baseline': { config: null, token: 0, source: null, trainedAt: null },
  'skripsi-finbert': { config: null, token: 0, source: null, trainedAt: null },
}

const INITIAL_RESULT_REFRESH = {
  'skripsi-baseline': 0,
  'skripsi-finbert': 0,
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
  const [activeSection, setActiveSection] = useState('training')
  const [activeVariant, setActiveVariant] = useState(VARIANTS[0].key)
  const [manualPrefill, setManualPrefill] = useState(INITIAL_MANUAL_PREFILL)
  const [resultRefreshKey, setResultRefreshKey] = useState(INITIAL_RESULT_REFRESH)

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

  // Prefill form Training Manual otomatis dari best_config Random Search
  // TERAKHIR yang sudah tersimpan (metadata.json), supaya user tidak perlu
  // menjalankan Random Search ulang tiap sesi hanya untuk mengisi form —
  // klik "Retrain dengan Best Config" (live) tetap menimpa ini kalau dipakai.
  useEffect(() => {
    const controller = new AbortController()

    VARIANTS.forEach((variant) => {
      fetchJson(variant.resultPath, { signal: controller.signal })
        .then((data) => {
          if (!data?.is_available || !data.config) return
          setManualPrefill((prev) => ({
            ...prev,
            [variant.key]: {
              config: data.config,
              token: prev[variant.key].token + 1,
              source: 'persisted',
              trainedAt: data.trained_at ?? null,
            },
          }))
        })
        .catch((error) => {
          if (error.name === 'AbortError') return
        })
    })

    return () => controller.abort()
  }, [])

  // Hasil Training persisted (metadata.json backend) per varian — dipakai tab
  // "Hasil Training". Refetch dipicu resultRefreshKey (di-bump lewat
  // handleVariantDone saat Random Search / Training Manual selesai) supaya
  // tab ini otomatis ikut ter-update tanpa reload halaman.
  const baseline = useModelResult(
    resultRefreshKey['skripsi-baseline']
      ? `${VARIANTS[0].resultPath}?_r=${resultRefreshKey['skripsi-baseline']}`
      : VARIANTS[0].resultPath,
  )
  const finbert = useModelResult(
    resultRefreshKey['skripsi-finbert']
      ? `${VARIANTS[1].resultPath}?_r=${resultRefreshKey['skripsi-finbert']}`
      : VARIANTS[1].resultPath,
  )
  const resultByVariant = { 'skripsi-baseline': baseline, 'skripsi-finbert': finbert }

  function handleVariantDone(variantKey) {
    setResultRefreshKey((prev) => ({ ...prev, [variantKey]: prev[variantKey] + 1 }))
  }

  const comparisonRows = useMemo(() => {
    const a = baseline.result.data
    const b = finbert.result.data
    if (!a?.is_available || !b?.is_available) return null
    return COMPARISON_METRICS.map((m) => {
      const av = a.metrics[m.key]
      const bv = b.metrics[m.key]
      return { label: m.label, a: av, b: bv, diff: bv - av }
    })
  }, [baseline.result.data, finbert.result.data])

  return (
    <PageContainer
      title="Model Training"
      description="Jalankan Random Search & Training Manual, lalu lihat Hasil Training (metrik, confusion matrix, perbandingan Model A vs Model B) yang tersimpan di backend."
    >
      <div className="flex gap-2 border-b border-slate-200">
        {SECTIONS.map((section) => (
          <button
            key={section.key}
            type="button"
            onClick={() => setActiveSection(section.key)}
            className={cn(
              'border-b-2 px-4 py-2 text-sm font-medium transition-colors',
              activeSection === section.key
                ? 'border-slate-900 text-slate-900'
                : 'border-transparent text-slate-400 hover:text-slate-600',
            )}
          >
            {section.label}
          </button>
        ))}
      </div>

      {/*
        Section "Model Training" & "Hasil Training" tetap mounted permanen
        (disembunyikan lewat className, bukan conditional render) dengan
        alasan sama seperti variant tabs di bawah: training SSE yang sedang
        berjalan tidak boleh ter-abort saat user pindah section.
      */}
      <div className={cn('space-y-6', activeSection !== 'training' && 'hidden')}>
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
                onDone={() => handleVariantDone(variant.key)}
                onUseBestConfig={(bestConfig) =>
                  setManualPrefill((prev) => ({
                    ...prev,
                    [variant.key]: {
                      config: bestConfig,
                      token: prev[variant.key].token + 1,
                      source: 'live',
                      trainedAt: null,
                    },
                  }))
                }
              />

              <div className="border-t border-slate-200 pt-6">
                <ManualTrainingPanel
                  endpoint={variant.manualEndpoint}
                  prefill={manualPrefill[variant.key]}
                  onDone={() => handleVariantDone(variant.key)}
                />
              </div>
            </div>
          )
        })}
      </div>

      <div className={cn('space-y-6', activeSection !== 'results' && 'hidden')}>
        {VARIANTS.map((variant) => (
          <PersistedResultCard key={variant.key} label={variant.label} state={resultByVariant[variant.key].result} />
        ))}

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
      </div>
    </PageContainer>
  )
}
