import React, { createContext, useContext, useState } from 'react'
import { cn, focusRing } from '../../lib/utils'

interface TabsContextType {
  value: string
  onValueChange: (value: string) => void
}

const TabsContext = createContext<TabsContextType | undefined>(undefined)

function useTabsContext() {
  const ctx = useContext(TabsContext)
  if (!ctx) {
    throw new Error('Tabs context not found — ensure TabsTrigger/TabsContent are inside Tabs')
  }
  return ctx
}

export interface TabsProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: string
  defaultValue?: string
  onValueChange?: (value: string) => void
  ref?: React.Ref<HTMLDivElement>
}

export function Tabs({
  value: controlledValue,
  defaultValue = '',
  onValueChange,
  children,
  className,
  ref,
  ...props
}: TabsProps) {
  const [internalValue, setInternalValue] = useState(defaultValue)
  const value = controlledValue !== undefined ? controlledValue : internalValue

  const handleValueChange = (newValue: string) => {
    if (controlledValue === undefined) {
      setInternalValue(newValue)
    }
    onValueChange?.(newValue)
  }

  return (
    <TabsContext.Provider value={{ value, onValueChange: handleValueChange }}>
      <div ref={ref} className={cn('w-full  ', className)} {...props}>
        {children}
      </div>
    </TabsContext.Provider>
  )
}

export interface TabsListProps extends React.HTMLAttributes<HTMLDivElement> {
  ref?: React.Ref<HTMLDivElement>
}

export function TabsList({ className, ref, ...props }: TabsListProps) {
  return (
    <div
      ref={ref}
      role="tablist"
      className={cn(
        '  rounded-[--radius-md] bg-[--color-surface-2] ',
        className,
      )}
      {...props}
    />
  )
}

export interface TabsTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  value: string
  ref?: React.Ref<HTMLButtonElement>
}

export function TabsTrigger({ value, className, ref, ...props }: TabsTriggerProps) {
  const { value: activeValue, onValueChange } = useTabsContext()
  const isActive = value === activeValue

  return (
    <button
      ref={ref}
      role="tab"
      aria-selected={isActive}
      type="button"
      onClick={() => onValueChange(value)}
      className={cn(
        'inline-flex items-center justify-center whitespace-nowrap rounded-[--radius-md] px-4 py-2 text-sm font-medium transition-all duration-200 cursor-pointer',
        focusRing,
        isActive
          ? 'bg-[--color-primary] text-[--color-primary-foreground] font-semibold shadow-sm border-t-2 border-[--color-primary]'
          : 'text-[--color-muted-foreground] hover:text-[--color-foreground] hover:bg-[--color-primary]/10',
        className,
      )}
      {...props}
    />
  )
}

export interface TabsContentProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string
  ref?: React.Ref<HTMLDivElement>
}

export function TabsContent({ value, className, ref, children, ...props }: TabsContentProps) {
  const { value: activeValue } = useTabsContext()

  if (value !== activeValue) {
    return null
  }

  return (
    <div
      ref={ref}
      role="tabpanel"
      className={cn('w-full animate-[tab-fade-in_0.15s_ease-out]', className)}
      {...props}
    >
      {children}
    </div>
  )
}
