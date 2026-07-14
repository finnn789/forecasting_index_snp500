import { usePlotlyChart } from '../../hooks/usePlotlyChart'
import { cn } from '../../utils/cn'

export default function PlotlyChart({ data, layout, config, className, style }) {
  const containerRef = usePlotlyChart({ data, layout, config })

  return <div ref={containerRef} className={cn('w-full', className)} style={style} />
}
