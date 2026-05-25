import { Loader2 } from 'lucide-react'
import { cn } from '../../lib/utils'

interface LoadingOverlayProps {
  label?: string
  className?: string
}

export function LoadingOverlay({ label = 'Memuat...', className }: LoadingOverlayProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-3 py-12',
        className,
      )}
      aria-busy="true"
      aria-label={label}
    >
      <Loader2 className="size-6 animate-spin text-[--color-primary]" />
      <p className="text-sm text-[--color-muted-foreground]">{label}</p>
    </div>
  )
}
