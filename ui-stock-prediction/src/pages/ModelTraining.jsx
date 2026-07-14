import { useEffect, useMemo, useState } from 'react'
import PageContainer from '../layout/PageContainer'
import Card, { CardHeader, CardTitle, CardContent } from '../components/Card'
import Icon from '../components/Icon'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../components/ui/table'
import { fetchJson } from '../utils/api'
import { cn } from '../utils/cn'
import TrainingPanel, { CONFIG_KEYS, fmtNum, fmtPct } from '../components/model-training/TrainingPanel'
import RandomSearchPanel from '../components/model-training/RandomSearchPanel'

const GRID_TABLE_COLUMNS = [
  { key: 'seq_len', label: 'Seq Len' },
  { key: 'hidden_size', label: 'Hidden' },
  { key: 'num_layers', label: 'Layers' },
  { key: 'dropout', label: 'Dropout' },
  { key: 'lr', label: 'LR' },
  { key: 'batch_size', label: 'Batch' },
]

const VARIANTS = [
  { key: 'sentiment', label: 'NB05: OHLCV + Sentimen', kind: 'notebook05', endpoint: '/train/notebook05' },
  { key: 'ohlcv', label: 'NB05: OHLCV Saja (Ablation)', kind: 'notebook05', endpoint: '/train/notebook05/ohlcv' },
  { key: 'skripsi-baseline', label: 'Skripsi: LSTM-OHLCV', kind: 'skripsi', endpoint: '/train/skripsi/ohlcv' },
  { key: 'skripsi-finbert', label: 'Skripsi: FinBERT-LSTM', kind: 'skripsi', endpoint: '/train/skripsi/finbert-lstm' },
]

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

function isBestConfig(row, best) {
  if (!best) return false
  return CONFIG_KEYS.every((key) => row[key] === best[key])
}

function formatSpaceValue(value) {
  if (Array.isArray(value)) return value.join(', ')
  return String(value)
}

export default function ModelTraining() {
  const [gridState, setGridState] = useState({ data: null, loading: true, error: null })
  const [searchSpaceState, setSearchSpaceState] = useState({ data: null, loading: true, error: null })
  const [activeVariant, setActiveVariant] = useState(VARIANTS[0].key)
  const [skripsiResults, setSkripsiResults] = useState({ baseline: null, finbert: null })

  // Ambil hasil grid-search (statis, tidak dijalankan ulang dari FE). Hyperparameter
  // ini juga dipakai sebagai default utk varian OHLCV-only (ablation, lihat catatan di bawah).
  useEffect(() => {
    const controller = new AbortController()

    fetchJson('/train/notebook05/grid-search-result', { signal: controller.signal })
      .then((data) => setGridState({ data, loading: false, error: null }))
      .catch((error) => {
        if (error.name === 'AbortError') return
        setGridState({ data: null, loading: false, error: error.message })
      })

    return () => controller.abort()
  }, [])

  // Ambil search space Random Search skripsi-scoped (statis, info saja — Random
  // Search dijalankan LIVE, tidak ada hasil statis seperti grid-search notebook 05).
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

  const bestConfig = gridState.data?.best_config ?? null

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
      description="Latih model LSTM mengikuti metodologi Notebook 05, langsung dari browser via streaming SSE."
    >
      <Card>
        <CardHeader>
          <CardTitle>Grid Search (Hasil Sebelumnya)</CardTitle>
        </CardHeader>

        {gridState.loading && (
          <CardContent className="flex h-32 items-center justify-center gap-2 text-sm text-slate-400">
            <Icon name="progress_activity" className="animate-spin text-lg" />
            Memuat hasil grid-search...
          </CardContent>
        )}

        {gridState.error && (
          <CardContent>
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
              <Icon name="error" className="text-lg" />
              {gridState.error}
            </div>
          </CardContent>
        )}

        {gridState.data && (
          <>
            <div className="flex flex-wrap items-center gap-6 border-b border-slate-200 px-6 py-3 text-sm">
              <div>
                <span className="text-xs uppercase tracking-wide text-slate-400">Total Kombinasi</span>
                <p className="font-mono font-semibold text-slate-900">{gridState.data.total_combinations}</p>
              </div>
              <div>
                <span className="text-xs uppercase tracking-wide text-slate-400">Best Val F2</span>
                <p className="font-mono font-semibold text-slate-900">{fmtNum(gridState.data.best_val_f2)}</p>
              </div>
            </div>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    {GRID_TABLE_COLUMNS.map((col) => (
                      <TableHead key={col.key}>{col.label}</TableHead>
                    ))}
                    <TableHead>Val F2</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {gridState.data.top_configs.map((row, idx) => {
                    const best = idx === 0 || isBestConfig(row, gridState.data.best_config)
                    return (
                      <TableRow key={idx}>
                        {GRID_TABLE_COLUMNS.map((col) => (
                          <TableCell key={col.key} className="font-mono">
                            {row[col.key]}
                          </TableCell>
                        ))}
                        <TableCell className="font-mono font-semibold text-slate-900">
                          <div className="flex items-center gap-2">
                            {fmtNum(row.val_f2)}
                            {best && (
                              <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-600">
                                Best
                              </span>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </CardContent>
            <CardContent className="border-t border-slate-200 py-3 text-xs text-slate-500">
              Hyperparameter di atas juga dipakai sebagai default utk varian{' '}
              <span className="font-semibold text-slate-700">OHLCV Saja (Ablation)</span> — grid-search 5-fitur
              (tanpa <code className="font-mono">sentiment_mean</code>) tidak dijalankan ulang, supaya perbandingan
              antar varian adil (variabel terkontrol).
            </CardContent>
          </>
        )}
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Random Search — Search Space (Notebook 07, Skripsi Scoped)</CardTitle>
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
              Random Search dijalankan LIVE tiap kali tombol "Mulai Random Search" diklik di tab Skripsi di bawah —
              tidak ada hasil statis seperti tabel grid-search notebook 05, karena metodologi Batasan Masalah BAB I
              memang mensyaratkan Random Search (bukan Grid Search).
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
        Semua 4 panel (2 notebook05 + 2 skripsi) dirender SEKALIGUS dan tetap
        mounted permanen — tab yang tidak aktif hanya disembunyikan lewat
        className, BUKAN conditional render ({activeVariant === X && <Panel/>}).
        Alasan: conditional render akan unmount panel yang tidak aktif, yang
        berarti training SSE yang sedang berjalan di tab itu ter-abort
        (AbortController cleanup) dan seluruh progress (log epoch/iterasi, chart)
        hilang. Tujuan fitur ini adalah membandingkan training berdampingan yang
        bisa berjalan cukup lama, jadi identitas komponen harus tetap sama saat
        pindah tab.
      */}
      {VARIANTS.map((variant) => (
        <div key={variant.key} className={cn(activeVariant !== variant.key && 'hidden')}>
          {variant.kind === 'notebook05' ? (
            <TrainingPanel endpoint={variant.endpoint} bestConfig={bestConfig} />
          ) : (
            <RandomSearchPanel
              endpoint={variant.endpoint}
              onDone={(result) =>
                setSkripsiResults((prev) => ({
                  ...prev,
                  [variant.key === 'skripsi-baseline' ? 'baseline' : 'finbert']: result,
                }))
              }
            />
          )}
        </div>
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
    </PageContainer>
  )
}
