import PlotlyChart from '../charts/PlotlyChart'
import { BASE_LAYOUT, CHART_COLORS } from '../../utils/chartTheme'

const DAILY_BAR_LIMIT = 180

// A bar per trading day (1500+ for a multi-year range) is too dense to read —
// bars end up thinner than a pixel and merge into a solid block. Roll volume
// up to monthly totals once the series gets long; close just becomes the
// month-end value so both panels stay aligned on the same x-axis.
function resampleMonthly(points) {
  const buckets = new Map()

  for (const point of points) {
    const month = point.date.slice(0, 7)
    const bucket = buckets.get(month) ?? { date: `${month}-01`, close: point.close, volume: 0 }
    bucket.close = point.close
    bucket.volume += point.volume
    buckets.set(month, bucket)
  }

  return Array.from(buckets.values())
}

// Close (~thousands) and Volume (~billions) live on wildly different scales,
// so they're drawn as two stacked panels sharing one x-axis instead of being
// overlaid — overlaying flattens the smaller series and breaks tick labels.
export default function PriceVolumeChart({ data, height = 420 }) {
  const rawPoints = data.points
  const aggregated = rawPoints.length > DAILY_BAR_LIMIT
  const points = aggregated ? resampleMonthly(rawPoints) : rawPoints

  const dates = points.map((p) => p.date)
  const close = points.map((p) => p.close)
  const volumeBillions = points.map((p) => p.volume / 1e9)

  const traces = [
    {
      type: 'scatter',
      mode: 'lines',
      name: 'Close',
      x: dates,
      y: close,
      line: { color: CHART_COLORS.navy, width: 2 },
      yaxis: 'y',
    },
    {
      type: 'bar',
      name: aggregated ? 'Volume (monthly total)' : 'Volume',
      x: dates,
      y: volumeBillions,
      marker: { color: CHART_COLORS.slate },
      yaxis: 'y2',
    },
  ]

  const layout = {
    ...BASE_LAYOUT,
    height,
    showlegend: false,
    bargap: aggregated ? 0.3 : 0.1,
    margin: { l: 56, r: 16, t: 16, b: 32 },
    xaxis: { ...BASE_LAYOUT.xaxis },
    yaxis: { ...BASE_LAYOUT.yaxis, title: { text: 'Close' }, domain: [0.35, 1] },
    yaxis2: {
      ...BASE_LAYOUT.yaxis,
      title: { text: aggregated ? 'Volume (B) / month' : 'Volume (B)' },
      domain: [0, 0.25],
    },
  }

  return <PlotlyChart data={traces} layout={layout} />
}
