import { useLocation } from 'react-router-dom'
import { USE_MOCK } from '../../lib/constants'
import { Badge } from '../ui/badge'

const pageTitle: Record<string, string> = {
  '/':           'Dashboard',
  '/pipeline':   'Data Pipeline',
  '/prediction': 'Prediksi Saham',
  '/sentiment':  'Analisis Sentimen',
  '/logs':       'Log Sistem',
}

export function Header() {
  const { pathname } = useLocation()
  const title = pageTitle[pathname] ?? 'Stock Prediction'

  return (
    <header className="flex h-14 items-center justify-between border-b border-[--color-border] bg-[--color-surface] px-6">
      <h1 className="text-sm font-semibold text-[--color-foreground]">{title}</h1>
      <div className="flex items-center gap-2">
        {USE_MOCK && (
          <Badge variant="running" dot>Mock Mode</Badge>
        )}
      </div>
    </header>
  )
}
