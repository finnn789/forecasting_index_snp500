import React from 'react'
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

// Minimal Slot: clones the single child, merging parent props onto it.
// Child props take precedence except className which is merged via cn().
interface SlotProps {
  children: React.ReactNode
  className?: string
  ref?: React.Ref<unknown>
  [key: string]: unknown
}

function Slot({ children, className, ref, ...parentProps }: SlotProps) {
  const child = React.Children.only(children)
  if (!React.isValidElement(child)) {
    throw new Error('Slot requires a single valid React element as children')
  }
  const childEl = child as React.ReactElement<Record<string, unknown>>
  const mergedClassName = cn(className, childEl.props['className'] as string | undefined)
  return React.cloneElement(childEl, {
    ...parentProps,
    ...childEl.props,
    className: mergedClassName,
    ref,
  })
}

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  ref?: React.Ref<HTMLButtonElement>
  asChild?: boolean
  children?: React.ReactNode
}

export function Button({
  className,
  variant,
  size,
  ref,
  asChild = false,
  children,
  ...props
}: ButtonProps) {
  const computedClass = cn(buttonVariants({ variant, size, className }))

  if (asChild) {
    return (
      <Slot
        className={computedClass}
        ref={ref as React.Ref<unknown>}
        {...(props as Record<string, unknown>)}
      >
        {children}
      </Slot>
    )
  }

  return (
    <button
      ref={ref}
      className={computedClass}
      {...props}
    >
      {children}
    </button>
  )
}

export { buttonVariants }
