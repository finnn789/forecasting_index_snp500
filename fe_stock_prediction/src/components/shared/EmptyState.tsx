import type { LucideIcon } from 'lucide-react'
import { cn } from '../../lib/utils'

interface EmptyStateProps {
  icon?: LucideIcon
  title: string
  description?: string
  action?: React.ReactNode
  className?: string
}

export function EmptyState({ icon: Icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-3 py-12 text-center',
        className,
      )}
    >
      {Icon && (
        <div className="flex size-12 items-center justify-center rounded-full bg-[--color-surface-2]">
          <Icon className="size-6 text-[--color-muted-foreground]" />
        </div>
      )}
      <div className="space-y-1">
        <p className="text-sm font-medium text-[--color-foreground]">{title}</p>
        {description && (
          <p className="text-sm text-[--color-muted-foreground]">{description}</p>
        )}
      </div>
      {action}
    </div>
  )
}
