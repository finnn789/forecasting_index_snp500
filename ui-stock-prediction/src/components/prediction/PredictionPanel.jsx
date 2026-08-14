import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import Card, { CardHeader, CardTitle, CardContent } from '../Card'
import Button from '../Button'
import Icon from '../Icon'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../ui/table'
import MetricsCards from '../model-training/MetricsCards'
import ConfusionMatrixGrid from '../model-training/ConfusionMatrixGrid'
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
 * FinBERT-LSTM). Hasil training persisted (metrik/confusion matrix/diagnosis)
 * dipindah ke halaman Model Training (tab "Hasil Training") — di sini cuma
 * dipakai untuk gating tombol backtest.
 */
export default function PredictionPanel({
  resultPath,
  backtestPath,
  backtestMetricKeys,
}) {
  const { result, backtest, backtestState } = useModelResult(resultPath)

  const backtestMetricEntries = useMemo(
    () => buildEntries(backtestState.data?.metrics, backtestMetricKeys),
    [backtestState.data, backtestMetricKeys],
  )

  const isAvailable = Boolean(result.data?.is_available)

  return (
    <div className="space-y-6">
      {result.loading && (
        <div className="flex h-16 items-center gap-2 text-sm text-slate-400">
          <Icon name="progress_activity" className="animate-spin text-lg" />
          Memuat status model...
        </div>
      )}

      {result.error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
          <Icon name="error" className="text-lg" />
          {result.error}
        </div>
      )}

      {result.data && !isAvailable && (
        <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500">
          <Icon name="info" className="text-lg" />
          Belum pernah training untuk varian ini. Jalankan training di halaman{' '}
          <Link to="/training" className="font-medium underline">
            Model Training
          </Link>{' '}
          terlebih dahulu.
        </div>
      )}

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
