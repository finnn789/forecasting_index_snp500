import { cn, focusRing } from '../../lib/utils'

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string
  ref?: React.Ref<HTMLInputElement>
}

export function Input({ className, error, id, ref, ...props }: InputProps) {
  return (
    <div className="w-full">
      <input
        id={id}
        ref={ref}
        className={cn(
          'flex h-9 w-full rounded-[--radius-md] border border-[--color-border]',
          'bg-[--color-surface] px-3 py-2 text-sm text-[--color-foreground]',
          'placeholder:text-[--color-muted-foreground]',
          'disabled:cursor-not-allowed disabled:opacity-50',
          focusRing,
          error && 'border-[--color-destructive]',
          className,
        )}
        aria-invalid={!!error}
        aria-describedby={error && id ? `${id}-error` : undefined}
        {...props}
      />
      {error && (
        <p id={id ? `${id}-error` : undefined} className="mt-1 text-xs text-[--color-destructive]" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}
