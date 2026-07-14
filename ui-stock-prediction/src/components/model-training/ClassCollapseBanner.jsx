import Icon from '../Icon'
import { cn } from '../../utils/cn'

/**
 * Banner peringatan class-collapse — reusable oleh TrainingPanel (hasil
 * training live SSE) dan PredictionPanel (hasil training persisted).
 */
export default function ClassCollapseBanner({ diagnosis }) {
  if (!diagnosis) return null

  const collapseSplits = Object.entries(diagnosis.class_collapse ?? {})
    .filter(([, collapsed]) => collapsed)
    .map(([split]) => split)
  const hasCollapse = Boolean(diagnosis.any_collapse) || collapseSplits.length > 0

  return (
    <div
      className={cn(
        'flex items-start gap-3 rounded-lg border p-4',
        hasCollapse ? 'border-red-200 bg-red-50' : 'border-emerald-200 bg-emerald-50',
      )}
    >
      <Icon
        name={hasCollapse ? 'warning' : 'check_circle'}
        className={cn('mt-0.5 text-xl', hasCollapse ? 'text-red-600' : 'text-emerald-600')}
      />
      <div className={cn('space-y-1 text-sm', hasCollapse ? 'text-red-700' : 'text-emerald-700')}>
        {hasCollapse ? (
          <>
            <p className="font-semibold">Peringatan: Model Mengalami Class Collapse</p>
            <p>
              Model hanya menebak satu kelas secara konsisten (recall salah satu kelas mendekati 0) pada
              split: <span className="font-mono font-semibold">{collapseSplits.join(', ') || '-'}</span>.
              Akibatnya, skor F2 yang tinggi bisa MENYESATKAN karena tidak mencerminkan kemampuan model
              membedakan kelas Up/Down yang sesungguhnya.
            </p>
          </>
        ) : (
          <p className="font-semibold">OK — Tidak Terdeteksi Class Collapse</p>
        )}
        <p>
          Status fit: <span className="font-mono font-semibold">{diagnosis.fit_status}</span>
          {' · '}
          Overfitting: <span className="font-mono font-semibold">{diagnosis.overfitting ? 'Ya' : 'Tidak'}</span>
          {' · '}
          Underfitting: <span className="font-mono font-semibold">{diagnosis.underfitting ? 'Ya' : 'Tidak'}</span>
        </p>
      </div>
    </div>
  )
}
