import { useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  GitBranch,
  TrendingUp,
  Newspaper,
  ScrollText,
  ChevronRight,
  ChevronDown,
  BarChart2,
} from 'lucide-react'
import { cn } from '../../lib/utils'

const navItems = [
  {
    label: 'Dashboard',
    icon: LayoutDashboard,
    children: [
      { to: '/overview/stocks', label: 'Data Saham', icon: BarChart2 },
      { to: '/overview/sentiment', label: 'Sentimen', icon: Newspaper },
    ],
  },
  { to: '/pipeline',   label: 'Pipeline',   icon: GitBranch       },
  { to: '/prediction', label: 'Prediksi',   icon: TrendingUp      },
  { to: '/sentiment',  label: 'Sentimen',   icon: Newspaper       },
  { to: '/logs',       label: 'Log',        icon: ScrollText      },
]

export function Sidebar() {
  const location = useLocation()
  const [dashboardOpen, setDashboardOpen] = useState(true)

  return (
    <aside className="flex h-screen w-56 flex-col border-r border-[--color-border] bg-[--color-surface]">
      {/* Logo */}
      <div className="flex h-14 items-center gap-2.5 border-b border-[--color-border] px-4">
        <div className="flex size-7 items-center justify-center rounded-[--radius-md] bg-[--color-primary]">
          <TrendingUp className="size-4 text-[--color-primary-foreground]" />
        </div>
        <div>
          <p className="text-sm font-semibold leading-none">StockPred</p>
          <p className="text-[10px] text-[--color-muted-foreground]">FinBERT + LSTM</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-3 px-2">
        <p className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-widest text-[--color-muted-foreground]">
          Menu
        </p>
        <ul className="space-y-0.5">
          {navItems.map((item) => {
            if ('children' in item && item.children) {
              return (
                <li key={item.label}>
                  <button
                    onClick={() => setDashboardOpen(!dashboardOpen)}
                    className={cn(
                      'flex w-full items-center gap-2.5 rounded-[--radius-md] px-3 py-2 text-sm transition-colors',
                      'text-[--color-muted-foreground] hover:bg-[--color-surface-2] hover:text-[--color-foreground]',
                    )}
                  >
                    <item.icon className="size-4 shrink-0" />
                    <span className="flex-1 text-left">{item.label}</span>
                    <ChevronDown className={cn(
                      'size-3 shrink-0 transition-transform',
                      dashboardOpen ? 'rotate-180' : '',
                    )} />
                  </button>
                  {dashboardOpen && (
                    <ul className="mt-0.5 space-y-0.5">
                      {item.children.map(({ to, label, icon: Icon }) => {
                        const isActive = location.pathname === to
                        return (
                          <li key={to}>
                            <NavLink
                              to={to}
                              className={cn(
                                'flex items-center gap-2.5 rounded-[--radius-md] px-3 py-2 pl-9 text-sm transition-colors',
                                isActive
                                  ? 'bg-[--color-primary]/15 text-[--color-primary] font-medium'
                                  : 'text-[--color-muted-foreground] hover:bg-[--color-surface-2] hover:text-[--color-foreground]',
                              )}
                            >
                              <Icon className="size-4 shrink-0" />
                              <span className="flex-1">{label}</span>
                              {isActive && <ChevronRight className="size-3 opacity-50" />}
                            </NavLink>
                          </li>
                        )
                      })}
                    </ul>
                  )}
                </li>
              )
            }

            const to = item.to
            return (
              <li key={to}>
                <NavLink
                  to={to}
                  end={to === '/'}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center gap-2.5 rounded-[--radius-md] px-3 py-2 text-sm transition-colors',
                      isActive
                        ? 'bg-[--color-primary]/15 text-[--color-primary] font-medium'
                        : 'text-[--color-muted-foreground] hover:bg-[--color-surface-2] hover:text-[--color-foreground]',
                    )
                  }
                >
                  {({ isActive }) => (
                    <>
                      <item.icon className="size-4 shrink-0" />
                      <span className="flex-1">{item.label}</span>
                      {isActive && <ChevronRight className="size-3 opacity-50" />}
                    </>
                  )}
                </NavLink>
              </li>
            )
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="border-t border-[--color-border] px-4 py-3">
        <p className="text-[10px] text-[--color-muted-foreground]">Skripsi 2024 · Mock Mode</p>
      </div>
    </aside>
  )
}
