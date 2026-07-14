import { cn } from '../utils/cn'

function Card({ className, children, ...props }) {
  return (
    <div
      className={cn('rounded-lg border border-slate-200 bg-white', className)}
      {...props}
    >
      {children}
    </div>
  )
}

function CardHeader({ className, children, ...props }) {
  return (
    <div
      className={cn(
        'flex items-center justify-between border-b border-slate-200 px-6 py-4',
        className,
      )}
      {...props}
    >
      {children}
    </div>
  )
}

function CardTitle({ className, children, ...props }) {
  return (
    <h3
      className={cn(
        'text-xs font-semibold uppercase tracking-wide text-slate-500',
        className,
      )}
      {...props}
    >
      {children}
    </h3>
  )
}

function CardContent({ className, children, ...props }) {
  return (
    <div className={cn('p-6', className)} {...props}>
      {children}
    </div>
  )
}

Card.Header = CardHeader
Card.Title = CardTitle
Card.Content = CardContent

export default Card
export { CardHeader, CardTitle, CardContent }
