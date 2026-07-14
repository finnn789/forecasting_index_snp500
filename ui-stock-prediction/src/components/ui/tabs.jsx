import { createContext, useContext } from 'react'
import { cn } from '../../utils/cn'

const TabsContext = createContext(null)

function Tabs({ value, onValueChange, className, children }) {
  return (
    <TabsContext.Provider value={{ value, onValueChange }}>
      <div className={cn(className)}>{children}</div>
    </TabsContext.Provider>
  )
}

function TabsList({ className, children }) {
  return (
    <div className={cn('flex items-center gap-1 overflow-x-auto border-b border-slate-200', className)}>
      {children}
    </div>
  )
}

function TabsTrigger({ value, className, children }) {
  const ctx = useContext(TabsContext)
  const isActive = ctx?.value === value

  return (
    <button
      type="button"
      onClick={() => ctx?.onValueChange?.(value)}
      className={cn(
        'shrink-0 whitespace-nowrap border-b-2 px-3 py-2.5 text-sm font-medium transition-colors',
        isActive
          ? 'border-slate-900 text-slate-900'
          : 'border-transparent text-slate-500 hover:text-slate-700',
        className,
      )}
    >
      {children}
    </button>
  )
}

function TabsContent({ value, className, children }) {
  const ctx = useContext(TabsContext)
  if (ctx?.value !== value) return null

  return <div className={cn('mt-4', className)}>{children}</div>
}

export { Tabs, TabsList, TabsTrigger, TabsContent }
