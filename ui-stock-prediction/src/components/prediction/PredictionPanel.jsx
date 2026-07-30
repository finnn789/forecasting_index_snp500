import { useMemo } from 'react'
import Card, { CardHeader, CardTitle, CardContent } from '../Card'
import Button from '../Button'
import Icon from '../Icon'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../ui/table'
import MetricsCards from '../model-training/MetricsCards'
import ConfusionMatrixGrid from '../model-training/ConfusionMatrixGrid'
import ClassCollapseBanner from '../model-training/ClassCollapseBanner'
import { fmtNum, fmtPct } from '../model-training/format'
import { useModelResult } from '../../hooks/useModelResult'
import { cn } from '../../utils/cn'

// Random Search skripsi-scoped (notebook 07) — 4 metrik sesuai Batasan
// Masalah BAB I (tanpa F2/best_epoch).
export const NOTEBOOK07_METRIC_KEYS = [
  { key: 'accuracy', label: 'Accuracy', format: 'pct' },
  { key: 'precision', label: 'Precision', format: 'pct' },
  { key: 'recall', label: 'Recall', format: 'pct' },
  { key: 'f1', label: 'F1', format: 'pct' },
]

export const NOTEBOOK07_HEADER_STATS = [
  { key: 'best_val_f1', label: 'Best Val F1', format: 'num' },
  { key: 'best_val_acc', label: 'Best Val Acc', format: 'num' },
  { key: 'trained_at', label: 'Trained At', format: 'raw' },
]

function formatValue(value, format, digits) {
  if (format === 'pct') return fmtPct(value)
  if (format === 'num') return fmtNum(value, digits)
  return value ?? '-'
}

function buildEntries(metrics, keys) {
  if (!metrics) return []
  return keys.map(({ key, label, format, digits }) => ({
    label,
    value: formatValue(metrics[key], format, digits),
  }))
}

/**
 * Panel Prediction untuk satu varian model (Model A: baseline / Model B:
 * FinBERT-LSTM). Hasil training diambil dari backend (persisted di
 * metadata.json) — jadi tetap terlihat walau user sudah pindah halaman.
 */
export default function PredictionPanel({
  resultPath,
  predictPath,
  backtestPath,
  metricKeys,
  backtestMetricKeys,
  headerStats,
}) {
  const { result, predict, predictState, backtest, backtestState } = useModelResult(resultPath)

  const trainingMetricEntries = useMemo(
    () => buildEntries(result.data?.metrics, metricKeys),
    [result.data, metricKeys],
  )
  const backtestMetricEntries = useMemo(
    () => buildEntries(backtestState.data?.metrics, backtestMetricKeys),
    [backtestState.data, backtestMetricKeys],
  )

  const isAvailable = Boolean(result.data?.is_available)
  const evalSplitLabel = result.data?.eval_split === 'test' ? 'Test' : 'Val'

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Hasil Training (Persisted)</CardTitle>
        </CardHeader>

        {result.loading && (
          <CardContent className="flex h-32 items-center justify-center gap-2 text-sm text-slate-400">
            <Icon name="progress_activity" className="animate-spin text-lg" />
            Memuat hasil training...
          </CardContent>
        )}

        {result.error && (
          <CardContent>
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
              <Icon name="error" className="text-lg" />
              {result.error}
            </div>
          </CardContent>
        )}

        {result.data && !isAvailable && (
          <CardContent>
            <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500">
              <Icon name="info" className="text-lg" />
              Belum pernah training untuk varian ini. Jalankan training di halaman Model Training terlebih dahulu.
            </div>
          </CardContent>
        )}

        {isAvailable && (
          <CardContent className="space-y-4">
            <div className="flex flex-wrap items-center gap-6 text-sm">
              {headerStats.map((stat) => {
                const label = stat.key === 'best_val_f1' || stat.key === 'best_val_acc'
                  ? stat.label.replace('Val', evalSplitLabel)
                  : stat.label
                return (
                  <div key={stat.key}>
                    <span className="text-xs uppercase tracking-wide text-slate-400">{label}</span>
                    <p className="font-mono font-semibold text-slate-900">
                      {formatValue(result.data[stat.key], stat.format)}
                    </p>
                  </div>
                )
              })}
            </div>

            <MetricsCards entries={trainingMetricEntries} />
            <ConfusionMatrixGrid cm={result.data.confusion_matrix} />
            <ClassCollapseBanner diagnosis={result.data.diagnosis} />
          </CardContent>
        )}
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Prediksi Hari Berikutnya</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button onClick={() => predict(predictPath)} disabled={predictState.loading || !isAvailable}>
            {predictState.loading ? (
              <Icon name="progress_activity" className="animate-spin text-base" />
            ) : (
              <Icon name="bolt" className="text-base" />
            )}
            Prediksi Hari Berikutnya
          </Button>

          {predictState.error && (
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
              <Icon name="error" className="text-lg" />
              {predictState.error}
            </div>
          )}

          {predictState.data && (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <div className="rounded border border-slate-200 p-3">
                <p className="text-xs uppercase tracking-wide text-slate-400">Arah</p>
                <p
                  className={cn(
                    'mt-1 font-mono text-xl font-semibold',
                    predictState.data.direction === 'up' ? 'text-emerald-600' : 'text-red-600',
                  )}
                >
                  {predictState.data.direction === 'up' ? 'UP' : 'DOWN'}
                </p>
              </div>
              <div className="rounded border border-slate-200 p-3">
                <p className="text-xs uppercase tracking-wide text-slate-400">Probability Up</p>
                <p className="mt-1 font-mono text-xl font-semibold text-slate-900">
                  {fmtPct(predictState.data.probability_up)}
                </p>
              </div>
              <div className="rounded border border-slate-200 p-3">
                <p className="text-xs uppercase tracking-wide text-slate-400">Confidence</p>
                <p className="mt-1 font-mono text-xl font-semibold text-slate-900">
                  {fmtPct(predictState.data.confidence)}
                </p>
              </div>
              <div className="rounded border border-slate-200 p-3">
                <p className="text-xs uppercase tracking-wide text-slate-400">As Of → Target</p>
                <p className="mt-1 font-mono text-sm font-semibold text-slate-900">
                  {predictState.data.as_of_date} → {predictState.data.target_date}
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Backtest</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button onClick={() => backtest(backtestPath)} disabled={backtestState.loading || !isAvailable}>
            {backtestState.loading ? (
              <Icon name="progress_activity" className="animate-spin text-base" />
            ) : (
              <Icon name="play_arrow" className="text-base" />
            )}
            Jalankan Backtest
          </Button>

          {backtestState.error && (
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
              <Icon name="error" className="text-lg" />
              {backtestState.error}
            </div>
          )}

          {backtestState.data && (
            <>
              <MetricsCards entries={backtestMetricEntries} />
              <ConfusionMatrixGrid cm={backtestState.data.confusion_matrix} />

              <div className="max-h-96 overflow-y-auto rounded border border-slate-200">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Tanggal</TableHead>
                      <TableHead>Close</TableHead>
                      <TableHead>Aktual</TableHead>
                      <TableHead>Prediksi</TableHead>
                      <TableHead>Prob. Up</TableHead>
                      <TableHead>Benar?</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {backtestState.data.points.map((p) => (
                      <TableRow key={p.date}>
                        <TableCell className="font-mono">{p.date}</TableCell>
                        <TableCell className="font-mono">{p.close.toFixed(2)}</TableCell>
                        <TableCell className="font-mono uppercase">{p.actual_direction}</TableCell>
                        <TableCell className="font-mono uppercase">{p.predicted_direction}</TableCell>
                        <TableCell className="font-mono">{fmtPct(p.probability_up)}</TableCell>
                        <TableCell className={cn('font-mono', p.correct ? 'text-emerald-500' : 'text-red-500')}>
                          {p.correct ? 'Ya' : 'Tidak'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
