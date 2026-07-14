import PlotlyChart from './PlotlyChart'
import { CHART_COLORS } from '../../utils/chartTheme'
import { cn } from '../../utils/cn'

/**
 * label: string, value: string|number, delta: number (percent, signed)
 * sparkline (optional): number[] — mini trend line under the stat
 */
export default function StatCard({ label, value, delta, sparkline, className }) {
  const isPositive = typeof delta === 'number' ? delta >= 0 : null
  const trendColor = isPositive === false ? CHART_COLORS.crimson : CHART_COLORS.emerald

  const sparklineData = [
    {
      type: 'scatter',
      mode: 'lines',
      y: sparkline,
      line: { color: trendColor, width: 2 },
      fill: 'tozeroy',
      fillcolor: isPositive === false ? 'rgba(239, 68, 68, 0.08)' : 'rgba(16, 185, 129, 0.08)',
      hoverinfo: 'skip',
    },
  ]

  const sparklineLayout = {
    height: 56,
    margin: { l: 0, r: 0, t: 4, b: 4 },
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    xaxis: { visible: false, fixedrange: true },
    yaxis: { visible: false, fixedrange: true },
  }

  const sparklineConfig = { staticPlot: true }

  return (
    <div className={cn('rounded-lg border border-slate-200 bg-white p-6', className)}>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <div className="mt-2 flex items-end justify-between gap-4">
        <p className="font-mono text-2xl font-semibold text-slate-900">{value}</p>
        {typeof delta === 'number' && (
          <span
            className={cn(
              'font-mono text-sm font-medium',
              isPositive ? 'text-emerald-500' : 'text-red-500',
            )}
          >
            {isPositive ? '+' : ''}
            {delta.toFixed(2)}%
          </span>
        )}
      </div>
      {sparkline?.length > 0 && (
        <PlotlyChart
          data={sparklineData}
          layout={sparklineLayout}
          config={sparklineConfig}
          className="mt-3 h-14"
        />
      )}
    </div>
  )
}
