import PlotlyChart from './PlotlyChart'
import { BASE_LAYOUT, CHART_COLORS } from '../../utils/chartTheme'
import { cn } from '../../utils/cn'

/**
 * data: [{ date, open, high, low, close }]
 * predicted (optional): [{ date, close }] — rendered as a dashed forecast line
 */
export default function PriceCandlestickChart({ data, predicted, height = 320, className }) {
  const traces = [
    {
      type: 'candlestick',
      x: data.map((d) => d.date),
      open: data.map((d) => d.open),
      high: data.map((d) => d.high),
      low: data.map((d) => d.low),
      close: data.map((d) => d.close),
      increasing: { line: { color: CHART_COLORS.emerald, width: 1 }, fillcolor: CHART_COLORS.emerald },
      decreasing: { line: { color: CHART_COLORS.crimson, width: 1 }, fillcolor: CHART_COLORS.crimson },
      name: 'Price',
    },
  ]

  if (predicted?.length) {
    traces.push({
      type: 'scatter',
      mode: 'lines',
      x: predicted.map((d) => d.date),
      y: predicted.map((d) => d.close),
      line: { color: CHART_COLORS.navy, width: 2, dash: 'dash' },
      name: 'Predicted',
    })
  }

  const layout = {
    ...BASE_LAYOUT,
    height,
    showlegend: false,
    xaxis: { ...BASE_LAYOUT.xaxis, rangeslider: { visible: false } },
  }

  return <PlotlyChart data={traces} layout={layout} className={cn(className)} />
}
