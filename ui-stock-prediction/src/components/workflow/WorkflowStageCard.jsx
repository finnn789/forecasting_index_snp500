import { Link } from 'react-router-dom'
import Card, { CardContent } from '../Card'
import Icon from '../Icon'
import { cn } from '../../utils/cn'

const TONE_STYLES = {
  success: 'bg-emerald-50 text-emerald-600',
  warning: 'bg-amber-50 text-amber-600',
  neutral: 'bg-slate-100 text-slate-500',
  error: 'bg-red-50 text-red-600',
}

export function StageLoading({ label = 'Memuat...' }) {
  return (
    <div className="flex items-center gap-2 text-sm text-slate-400">
      <Icon name="progress_activity" className="animate-spin text-base" />
      {label}
    </div>
  )
}

export function StageError({ message }) {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600">
      <Icon name="error" className="text-base" />
      {message}
    </div>
  )
}

export function StagePending({ message }) {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-500">
      <Icon name="hourglass_empty" className="text-base" />
      {message}
    </div>
  )
}

export default function WorkflowStageCard({
  number,
  icon,
  title,
  description,
  status,
  isLast,
  linkTo,
  linkLabel,
  children,
}) {
  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-900 font-mono text-sm text-white">
          {number}
        </div>
        {!isLast && <div className="mt-1 mb-1 w-px flex-1 border-l border-slate-200" />}
      </div>

      <Card className={cn('flex-1', !isLast && 'mb-6')}>
        <CardContent className="space-y-4 p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="flex items-start gap-3">
              <div className="flex size-9 shrink-0 items-center justify-center rounded bg-slate-100">
                <Icon name={icon} className="text-lg text-slate-600" />
              </div>
              <div>
                <p className="font-medium text-slate-900">{title}</p>
                <p className="text-sm text-slate-500">{description}</p>
              </div>
            </div>
            {status && (
              <span
                className={cn(
                  'shrink-0 rounded-full px-2 py-0.5 text-xs font-medium',
                  TONE_STYLES[status.tone] ?? TONE_STYLES.neutral,
                )}
              >
                {status.label}
              </span>
            )}
          </div>

          {children}

          {linkTo && (
            <Link
              to={linkTo}
              className="inline-flex items-center gap-1 text-sm font-medium text-slate-900 hover:underline"
            >
              {linkLabel ?? 'Lihat detail'}
              <Icon name="arrow_forward" className="text-base" />
            </Link>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
