/**
 * Confusion matrix 2x2 (kelas positif = "up") — dipakai PredictionPanel
 * (hasil training persisted + backtest).
 */
export default function ConfusionMatrixGrid({ cm }) {
  if (!cm) return null

  return (
    <div className="inline-grid grid-cols-3 gap-px overflow-hidden rounded border border-slate-200 bg-slate-200 text-sm">
      <div className="bg-slate-50 p-3" />
      <div className="bg-slate-50 p-3 text-center font-semibold text-slate-600">Pred Down</div>
      <div className="bg-slate-50 p-3 text-center font-semibold text-slate-600">Pred Up</div>

      <div className="bg-slate-50 p-3 font-semibold text-slate-600">Actual Down</div>
      <div className="bg-white p-3 text-center font-mono">{cm.tn}</div>
      <div className="bg-white p-3 text-center font-mono">{cm.fp}</div>

      <div className="bg-slate-50 p-3 font-semibold text-slate-600">Actual Up</div>
      <div className="bg-white p-3 text-center font-mono">{cm.fn}</div>
      <div className="bg-white p-3 text-center font-mono">{cm.tp}</div>
    </div>
  )
}
