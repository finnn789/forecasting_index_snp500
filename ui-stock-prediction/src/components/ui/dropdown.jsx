import { useEffect, useRef, useState } from 'react'
import Icon from '../Icon'
import { cn } from '../../utils/cn'

export default function Dropdown({ value, onChange, options, className }) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef(null)

  useEffect(() => {
    function handleClickOutside(event) {
      if (rootRef.current && !rootRef.current.contains(event.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const selected = options.find((option) => option.value === value) ?? options[0]

  return (
    <div ref={rootRef} className={cn('relative', className)}>
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="flex w-full items-center justify-between gap-3 rounded border border-slate-300 bg-white px-3.5 py-2.5 text-left transition-colors hover:bg-slate-50"
      >
        <div className="flex items-center gap-2.5">
          {selected?.icon && <Icon name={selected.icon} className="text-lg text-slate-500" />}
          <div>
            <p className="text-sm font-medium text-slate-900">{selected?.label}</p>
            {selected?.description && (
              <p className="text-xs text-slate-500">{selected.description}</p>
            )}
          </div>
        </div>
        <Icon
          name="expand_more"
          className={cn('text-lg text-slate-400 transition-transform', open && 'rotate-180')}
        />
      </button>

      {open && (
        <div className="absolute z-10 mt-1.5 w-full overflow-hidden rounded-lg border border-slate-200 bg-white shadow-[0_4px_20px_rgba(15,23,42,0.08)]">
          {options.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => {
                onChange(option.value)
                setOpen(false)
              }}
              className={cn(
                'flex w-full items-start gap-2.5 px-3.5 py-2.5 text-left transition-colors hover:bg-slate-50',
                option.value === selected?.value && 'bg-slate-50',
              )}
            >
              {option.icon && <Icon name={option.icon} className="mt-0.5 text-lg text-slate-500" />}
              <div className="flex-1">
                <p className="text-sm font-medium text-slate-900">{option.label}</p>
                {option.description && (
                  <p className="text-xs text-slate-500">{option.description}</p>
                )}
              </div>
              {option.value === selected?.value && (
                <Icon name="check" className="mt-0.5 text-lg text-slate-900" />
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
