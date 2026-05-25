import { cn } from '../../lib/utils'

type DivProps = React.HTMLAttributes<HTMLDivElement> & { ref?: React.Ref<HTMLDivElement> }

export function Card({ className, ref, ...props }: DivProps) {
  return (
    <div
      ref={ref}
      className={cn(
        'rounded-[--radius-lg] border border-[--color-border] bg-[--color-card] text-[--color-card-foreground]',
        className,
      )}
      {...props}
    />
  )
}

export function CardHeader({ className, ref, ...props }: DivProps) {
  return (
    <div ref={ref} className={cn('flex flex-col gap-1.5 p-5', className)} {...props} />
  )
}

export function CardTitle({
  className,
  ref,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement> & { ref?: React.Ref<HTMLHeadingElement> }) {
  return (
    <h3
      ref={ref}
      className={cn('text-base font-semibold leading-none tracking-tight', className)}
      {...props}
    />
  )
}

export function CardDescription({
  className,
  ref,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement> & { ref?: React.Ref<HTMLParagraphElement> }) {
  return (
    <p
      ref={ref}
      className={cn('text-sm text-[--color-muted-foreground]', className)}
      {...props}
    />
  )
}

export function CardContent({ className, ref, ...props }: DivProps) {
  return <div ref={ref} className={cn('p-5 pt-0', className)} {...props} />
}

export function CardFooter({ className, ref, ...props }: DivProps) {
  return (
    <div ref={ref} className={cn('flex items-center p-5 pt-0', className)} {...props} />
  )
}
