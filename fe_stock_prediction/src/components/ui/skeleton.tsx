import { cn } from '../../lib/utils'

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  ref?: React.Ref<HTMLDivElement>
}

export function Skeleton({ className, ref, ...props }: SkeletonProps) {
  return (
    <div
      ref={ref}
      className={cn(
        'animate-pulse rounded-[--radius-md] bg-[--color-surface-2]',
        className,
      )}
      {...props}
    />
  )
}
