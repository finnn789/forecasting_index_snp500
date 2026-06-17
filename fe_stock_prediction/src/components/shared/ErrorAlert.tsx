import { AlertCircle, Info, X } from 'lucide-react'
import { cn } from '../../lib/utils'

interface ErrorAlertProps {
  message: string
  onDismiss?: () => void
  className?: string
  variant?: 'error' | 'info'
}

export function ErrorAlert({ message, onDismiss, className, variant = 'error' }: ErrorAlertProps) {
  const isError = variant === 'error'
  const isInfo = variant === 'info'

  return (
    <div
      role="alert"
      className={cn(
        'flex items-start gap-3 rounded-[--radius-lg] border px-4 py-3 text-sm',
        isError && 'border-[--color-destructive]/30 bg-[--color-destructive]/10 text-[--color-destructive]',
        isInfo && 'border-[--color-primary]/30 bg-[--color-primary]/10 text-[--color-primary]',
        className,
      )}
    >
      {isError && <AlertCircle className="mt-0.5 size-4 shrink-0" />}
      {isInfo && <Info className="mt-0.5 size-4 shrink-0" />}
      <p className="flex-1">{message}</p>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="shrink-0 hover:opacity-70 transition-opacity"
          aria-label="Tutup"
        >
          <X className="size-4" />
        </button>
      )}
    </div>
  )
}
