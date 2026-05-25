import { cn } from '../../lib/utils'

interface SeparatorProps extends React.HTMLAttributes<HTMLDivElement> {
  orientation?: 'horizontal' | 'vertical'
  ref?: React.Ref<HTMLDivElement>
}

export function Separator({
  orientation = 'horizontal',
  className,
  ref,
  ...props
}: SeparatorProps) {
  return (
    <div
      ref={ref}
      role="separator"
      className={cn(
        'bg-[--color-border] shrink-0',
        orientation === 'horizontal' ? 'h-px w-full' : 'h-full w-px',
        className,
      )}
      {...props}
    />
  )
}
