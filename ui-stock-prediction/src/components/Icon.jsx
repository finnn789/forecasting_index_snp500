import { cn } from '../utils/cn'

export default function Icon({ name, className, style, ...props }) {
  return (
    <span
      className={cn('material-symbols-outlined select-none leading-none', className)}
      style={style}
      aria-hidden="true"
      {...props}
    >
      {name}
    </span>
  )
}
