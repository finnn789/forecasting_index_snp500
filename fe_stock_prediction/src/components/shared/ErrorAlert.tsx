import { AlertCircle, X } from 'lucide-react'
import { cn } from '../../lib/utils'

interface ErrorAlertProps {
  message: string
  onDismiss?: () => void
  className?: string
}

export function ErrorAlert({ message, onDismiss, className }: ErrorAlertProps) {
  return (
    <div
      role="alert"
      className={cn(
        'flex items-start gap-3 rounded-[--radius-lg] border border-[--color-destructive]/30',
        'bg-[--color-destructive]/10 px-4 py-3 text-sm text-[--color-destructive]',
        className,
      )}
    >
      <AlertCircle className="mt-0.5 size-4 shrink-0" />
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
