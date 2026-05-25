import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '../../lib/utils'

const badgeVariants = cva(
  'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium',
  {
    variants: {
      variant: {
        default:     'bg-[--color-surface-2] text-[--color-foreground]',
        primary:     'bg-[--color-primary]/15 text-[--color-primary]',
        running:     'bg-[--color-pipeline-running]/15 text-[--color-pipeline-running]',
        done:        'bg-[--color-pipeline-done]/15 text-[--color-pipeline-done]',
        error:       'bg-[--color-pipeline-error]/15 text-[--color-pipeline-error]',
        idle:        'bg-[--color-surface-2] text-[--color-muted-foreground]',
        positive:    'bg-[--color-sentiment-pos]/15 text-[--color-sentiment-pos]',
        negative:    'bg-[--color-sentiment-neg]/15 text-[--color-sentiment-neg]',
        neutral:     'bg-[--color-surface-2] text-[--color-muted-foreground]',
      },
    },
    defaultVariants: { variant: 'default' },
  },
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {
  dot?: boolean
}

export function Badge({ className, variant, dot, children, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant, className }))} {...props}>
      {dot && (
        <span
          className={cn(
            'size-1.5 rounded-full bg-current',
            variant === 'running' && 'animate-[pulse-slow_2s_ease-in-out_infinite]',
          )}
        />
      )}
      {children}
    </span>
  )
}
