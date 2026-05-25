import { cn } from '../../lib/utils'

interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number        // 0-100
  variant?: 'default' | 'running' | 'done' | 'error'
  showLabel?: boolean
  ref?: React.Ref<HTMLDivElement>
}

const trackColor: Record<string, string> = {
  default: 'bg-[--color-primary]',
  running: 'bg-[--color-pipeline-running]',
  done:    'bg-[--color-pipeline-done]',
  error:   'bg-[--color-pipeline-error]',
}

export function Progress({
  value,
  variant = 'default',
  showLabel = false,
  className,
  ref,
  ...props
}: ProgressProps) {
  const clamped = Math.max(0, Math.min(100, value))

  return (
    <div ref={ref} className={cn('flex items-center gap-3', className)} {...props}>
      <div
        className="relative flex-1 h-2 rounded-full bg-[--color-surface-2] overflow-hidden"
        role="progressbar"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className={cn('h-full rounded-full transition-[width] duration-500', trackColor[variant])}
          style={{ width: `${clamped}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-xs tabular-nums text-[--color-muted-foreground] w-9 text-right">
          {clamped}%
        </span>
      )}
    </div>
  )
}
