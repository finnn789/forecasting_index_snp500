import PlotlyChart from '../charts/PlotlyChart'
import { BASE_LAYOUT, CHART_PALETTE } from '../../utils/chartTheme'

export default function TimeSeriesChart({ data, height = 360 }) {
  const points = data.points
  const seriesKeys = Object.keys(points[0] ?? {}).filter((key) => key !== 'date')

  const traces = seriesKeys.map((key, index) => ({
    type: 'scatter',
    mode: 'lines',
    name: key,
    x: points.map((p) => p.date),
    y: points.map((p) => p[key]),
    line: { color: CHART_PALETTE[index % CHART_PALETTE.length], width: 2 },
    yaxis: index === 0 ? 'y' : 'y2',
  }))

  const layout = {
    ...BASE_LAYOUT,
    height,
    showlegend: seriesKeys.length > 1,
    legend: { orientation: 'h', y: -0.15 },
    yaxis: { ...BASE_LAYOUT.yaxis, title: { text: seriesKeys[0] } },
    // Only include yaxis2 when it's actually used — Plotly's cleanLayout()
    // chokes on a `yaxis2` key that's present but `undefined`.
    ...(seriesKeys.length > 1 && {
      yaxis2: {
        ...BASE_LAYOUT.yaxis,
        title: { text: seriesKeys[1] },
        overlaying: 'y',
        side: 'right',
      },
    }),
  }

  return <PlotlyChart data={traces} layout={layout} />
}
