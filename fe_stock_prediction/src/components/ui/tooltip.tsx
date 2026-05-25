import { cn } from '../../lib/utils'

interface TooltipProps {
  children: React.ReactNode
  content: string
  side?: 'top' | 'bottom' | 'left' | 'right'
  className?: string
}

const sideClass: Record<string, string> = {
  top:    'bottom-full left-1/2 -translate-x-1/2 mb-2',
  bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
  left:   'right-full top-1/2 -translate-y-1/2 mr-2',
  right:  'left-full top-1/2 -translate-y-1/2 ml-2',
}

export function Tooltip({ children, content, side = 'top', className }: TooltipProps) {
  return (
    <div className={cn('relative inline-flex group', className)}>
      {children}
      <span
        role="tooltip"
        className={cn(
          'pointer-events-none absolute z-50 whitespace-nowrap rounded-[--radius-md]',
          'bg-[--color-surface-2] border border-[--color-border]',
          'px-2.5 py-1 text-xs text-[--color-foreground] shadow-lg',
          'opacity-0 group-hover:opacity-100 transition-opacity duration-150',
          sideClass[side],
        )}
      >
        {content}
      </span>
    </div>
  )
}
