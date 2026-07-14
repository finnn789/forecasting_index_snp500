import Card, { CardContent } from '../Card'

/**
 * Grid kartu metrik reusable — dipakai TrainingPanel (hasil training live SSE)
 * dan PredictionPanel (hasil training persisted + backtest). Caller yang
 * memformat `value` (mis. via fmtPct/fmtNum) supaya komponen ini tetap murni
 * presentational.
 */
export default function MetricsCards({ entries }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
      {entries.map((m) => (
        <Card key={m.label}>
          <CardContent className="p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{m.label}</p>
            <p className="mt-1 font-mono text-xl font-semibold text-slate-900">{m.value}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
