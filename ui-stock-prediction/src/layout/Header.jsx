import { useLocation } from 'react-router-dom'
import Icon from '../components/Icon'
import Input from '../components/Input'

const PAGE_TITLES = {
  '/': 'Prediksi',
  '/pipeline': 'Data Pipeline',
  '/data-analysis': 'Data Analysis',
  '/preprocessing': 'Data Preprocessing',
  '/training': 'Model Training',
  '/workflow': 'Alur Kerja',
  '/sentiment': 'Sentiment Analysis',
  '/settings': 'Settings',
}

export default function Header() {
  const { pathname } = useLocation()
  const title = PAGE_TITLES[pathname] ?? 'S&P Predictor'

  return (
    <header className="flex h-16 shrink-0 items-center justify-between gap-4 border-b border-slate-200 bg-white px-6">
      <h1 className="text-lg font-semibold text-slate-900">{title}</h1>

      <div className="flex flex-1 items-center justify-end gap-4">
        <div className="relative w-full max-w-xs">
          <Icon
            name="search"
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-lg text-slate-400"
          />
          <Input placeholder="Search ticker, model, report..." className="pl-9" />
        </div>

        <button
          type="button"
          className="flex size-10 items-center justify-center rounded text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900"
        >
          <Icon name="notifications" className="text-xl" />
        </button>
      </div>
    </header>
  )
}
