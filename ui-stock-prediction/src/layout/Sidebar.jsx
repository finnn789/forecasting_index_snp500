import { NavLink } from 'react-router-dom'
import Icon from '../components/Icon'
import { cn } from '../utils/cn'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: 'dashboard', end: true },
  { to: '/pipeline', label: 'Pipeline', icon: 'account_tree' },
  { to: '/data-analysis', label: 'Data Analysis', icon: 'info' },
  { to: '/preprocessing', label: 'Data Preprocessing', icon: 'cleaning_services' },
  { to: '/model-training', label: 'Model Training', icon: 'model_training' },
  { to: '/predictions', label: 'Predictions', icon: 'trending_up' },
  { to: '/sentiment', label: 'Sentiment', icon: 'newspaper' },
  { to: '/settings', label: 'Settings', icon: 'settings' },
  
]

export default function Sidebar() {
  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col border-r border-slate-200 bg-white">
      <div className="flex h-16 items-center gap-2.5 border-b border-slate-200 px-5">
        <div className="flex size-8 items-center justify-center rounded bg-slate-900">
          <Icon name="trending_up" className="text-lg text-white" />
        </div>
        <div>
          <p className="text-sm font-semibold leading-none text-slate-900">S&P Predictor</p>
          <p className="mt-1 text-[10px] leading-none text-slate-400">FinBERT + LSTM</p>
        </div>
      </div>

      <nav className="flex-1 space-y-0.5 px-3 py-4">
        {NAV_ITEMS.map(({ to, label, icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-slate-900 text-white'
                  : 'text-slate-500 hover:bg-slate-100 hover:text-slate-900',
              )
            }
          >
            <Icon name={icon} className="text-lg" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-slate-200 px-5 py-3">
        <p className="text-[10px] text-slate-400">S&P 500 Predictive Intelligence</p>
      </div>
    </aside>
  )
}
