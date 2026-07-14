import { cn } from '../utils/cn'

export default function Navbar({ brand, items = [], actions, className }) {
  return (
    <header
      className={cn(
        'flex h-16 items-center justify-between border-b border-slate-200 bg-white px-6',
        className,
      )}
    >
      <div className="flex items-center gap-8">
        {brand && (
          <span className="text-lg font-bold tracking-tight text-slate-900">{brand}</span>
        )}
        <nav className="flex h-16 items-center gap-6">
          {items.map((item) => (
            <a
              key={item.label}
              href={item.href ?? '#'}
              className={cn(
                'flex h-full items-center border-b-2 text-sm font-medium transition-colors',
                item.active
                  ? 'border-slate-900 text-slate-900'
                  : 'border-transparent text-slate-500 hover:text-slate-700',
              )}
            >
              {item.label}
            </a>
          ))}
        </nav>
      </div>
      {actions && <div className="flex items-center gap-3">{actions}</div>}
    </header>
  )
}
