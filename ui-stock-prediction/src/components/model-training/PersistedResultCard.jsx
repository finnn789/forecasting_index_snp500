import Card, { CardHeader, CardTitle, CardContent } from '../Card'
import Icon from '../Icon'
import MetricsCards from './MetricsCards'
import ConfusionMatrixGrid from './ConfusionMatrixGrid'
import ClassCollapseBanner from './ClassCollapseBanner'
import { fmtNum, fmtPct } from './format'

const METRIC_KEYS = [
  { key: 'accuracy', label: 'Accuracy', format: 'pct' },
  { key: 'precision', label: 'Precision', format: 'pct' },
  { key: 'recall', label: 'Recall', format: 'pct' },
  { key: 'f1', label: 'F1', format: 'pct' },
]

const HEADER_STATS = [
  { key: 'best_val_f1', label: 'Best Val F1', format: 'num' },
  { key: 'best_val_acc', label: 'Best Val Acc', format: 'num' },
  { key: 'trained_at', label: 'Trained At', format: 'raw' },
]

function formatValue(value, format) {
  if (format === 'pct') return fmtPct(value)
  if (format === 'num') return fmtNum(value)
  return value ?? '-'
}

/**
 * Kartu Hasil Training (persisted di backend metadata.json) untuk satu
 * varian model — dipakai di halaman Model Training, tab "Hasil Training".
 * `state` mengikuti bentuk `result` dari useModelResult (data/loading/error).
 */
export default function PersistedResultCard({ label, state }) {
  const isAvailable = Boolean(state.data?.is_available)
  const evalSplitLabel = state.data?.eval_split === 'test' ? 'Test' : 'Val'

  const metricEntries = METRIC_KEYS.map((m) => ({
    label: m.label,
    value: formatValue(state.data?.metrics?.[m.key], m.format),
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle>Hasil Training (Persisted) — {label}</CardTitle>
      </CardHeader>

      {state.loading && (
        <CardContent className="flex h-32 items-center justify-center gap-2 text-sm text-slate-400">
          <Icon name="progress_activity" className="animate-spin text-lg" />
          Memuat hasil training...
        </CardContent>
      )}

      {state.error && (
        <CardContent>
          <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
            <Icon name="error" className="text-lg" />
            {state.error}
          </div>
        </CardContent>
      )}

      {state.data && !isAvailable && (
        <CardContent>
          <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500">
            <Icon name="info" className="text-lg" />
            Belum pernah training untuk varian ini — jalankan Random Search atau Training Manual di tab "Model
            Training".
          </div>
        </CardContent>
      )}

      {isAvailable && (
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-center gap-6 text-sm">
            {HEADER_STATS.map((stat) => {
              const statLabel =
                stat.key === 'best_val_f1' || stat.key === 'best_val_acc'
                  ? stat.label.replace('Val', evalSplitLabel)
                  : stat.label
              return (
                <div key={stat.key}>
                  <span className="text-xs uppercase tracking-wide text-slate-400">{statLabel}</span>
                  <p className="font-mono font-semibold text-slate-900">
                    {formatValue(state.data[stat.key], stat.format)}
                  </p>
                </div>
              )
            })}
          </div>

          <MetricsCards entries={metricEntries} />
          <ConfusionMatrixGrid cm={state.data.confusion_matrix} />
          <ClassCollapseBanner diagnosis={state.data.diagnosis} />
        </CardContent>
      )}
    </Card>
  )
}
