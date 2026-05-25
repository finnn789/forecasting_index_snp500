import { ChevronDown } from 'lucide-react'
import { cn, focusRing } from '../../lib/utils'
import { TICKERS } from '../../lib/constants'
import { Label } from '../ui/label'

interface TickerSelectorProps {
  value: string
  onChange: (value: string) => void
  id?: string
}

export function TickerSelector({ value, onChange, id = 'ticker' }: TickerSelectorProps) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>Kode Saham</Label>
      <div className="relative">
        <select
          id={id}
          value={value}
          onChange={e => onChange(e.target.value)}
          className={cn(
            'w-full appearance-none rounded-[--radius-md] border border-[--color-border]',
            'bg-[--color-surface] px-3 py-2 pr-9 text-sm text-[--color-foreground]',
            'disabled:cursor-not-allowed disabled:opacity-50',
            focusRing,
          )}
        >
          {TICKERS.map(t => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
        <ChevronDown className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-[--color-muted-foreground]" />
      </div>
    </div>
  )
}
