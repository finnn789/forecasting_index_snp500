import PlotlyChart from '../charts/PlotlyChart'
import { BASE_LAYOUT, CHART_PALETTE, CHART_COLORS } from '../../utils/chartTheme'

const SERIES = [
  { key: 'overall', label: 'Seluruh data' },
  { key: 'train', label: 'Latih' },
  { key: 'val', label: 'Validasi' },
  { key: 'test', label: 'Uji' },
]

export default function SentimentLagContent({ data }) {
  const traces = SERIES.map((s, idx) => ({
    type: 'scatter',
    mode: 'lines+markers',
    name: s.label,
    x: data[s.key].map((p) => p.lag_days),
    y: data[s.key].map((p) => p.r),
    line: { color: CHART_PALETTE[idx], width: 1.6 },
    marker: { size: 5 },
  }))

  const layout = {
    ...BASE_LAYOUT,
    height: 340,
    legend: { orientation: 'h', y: -0.2 },
    xaxis: { ...BASE_LAYOUT.xaxis, title: { text: 'Jarak hari ke depan' } },
    yaxis: { ...BASE_LAYOUT.yaxis, title: { text: 'Korelasi dengan sentimen berita' } },
    shapes: [
      {
        type: 'line',
        xref: 'paper',
        x0: 0,
        x1: 1,
        yref: 'y',
        y0: 0,
        y1: 0,
        line: { color: CHART_COLORS.slate, dash: 'dash', width: 1 },
      },
    ],
  }

  return (
    <div className="space-y-4">
      <p className="text-xs text-slate-500">
        Jarak 0 hari = skor sentimen dibandingkan perubahan harga PADA HARI YANG SAMA. Jarak 1-10
        hari = dibandingkan perubahan harga BEBERAPA HARI SETELAHNYA. Korelasi tinggi hanya di
        jarak 0 hari menunjukkan sentimen mengikuti harga yang sudah terjadi, bukan memimpinnya.
      </p>
      <PlotlyChart data={traces} layout={layout} />
    </div>
  )
}
