import { forwardRef } from 'react'
import { cn } from '../utils/cn'

const Input = forwardRef(function Input({ className, type = 'text', ...props }, ref) {
  return (
    <input
      ref={ref}
      type={type}
      className={cn(
        'h-10 w-full rounded border border-slate-300 bg-white px-3 text-sm text-slate-900',
        'placeholder:text-slate-400 transition-colors',
        'focus:border-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900/10',
        'disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-400',
        className,
      )}
      {...props}
    />
  )
})

export default Input
