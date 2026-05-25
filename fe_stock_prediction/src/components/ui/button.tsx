import { cva, type VariantProps } from 'class-variance-authority'
import { cn, disabled, focusRing } from '../../lib/utils'

const buttonVariants = cva(
  [
    'inline-flex items-center justify-center gap-2 whitespace-nowrap',
    'rounded-[--radius-md] text-sm font-medium transition-colors cursor-pointer',
    focusRing, disabled,
  ],
  {
    variants: {
      variant: {
        default:     'bg-[--color-primary] text-[--color-primary-foreground] hover:opacity-90',
        outline:     'border border-[--color-border] bg-transparent text-[--color-foreground] hover:bg-[--color-surface-2]',
        ghost:       'bg-transparent text-[--color-foreground] hover:bg-[--color-surface-2]',
        destructive: 'bg-[--color-destructive] text-[--color-destructive-foreground] hover:opacity-90',
        secondary:   'bg-[--color-surface-2] text-[--color-foreground] hover:bg-[--color-border]',
        link:        'bg-transparent text-[--color-primary] underline-offset-4 hover:underline p-0 h-auto',
      },
      size: {
        sm:   'h-8  px-3 text-xs',
        md:   'h-9  px-4',
        lg:   'h-11 px-6 text-base',
        icon: 'size-9 p-0',
      },
    },
    defaultVariants: { variant: 'default', size: 'md' },
  },
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  ref?: React.Ref<HTMLButtonElement>
}

export function Button({ className, variant, size, ref, ...props }: ButtonProps) {
  return (
    <button
      ref={ref}
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}
