import { cn } from '../utils/cn'

export default function PageContainer({ title, description, action, children, className }) {
  return (
    <div className={cn('space-y-6', className)}>
      {(title || action) && (
        <div className="flex items-start justify-between gap-4">
          <div>
            {title && <h2 className="text-lg font-semibold text-slate-900">{title}</h2>}
            {description && <p className="mt-1 text-sm text-slate-500">{description}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </div>
  )
}
