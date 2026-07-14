import PieChart from '../charts/PieChart'
import PlotlyChart from '../charts/PlotlyChart'
import StatCard from '../charts/StatCard'
import { BASE_LAYOUT, CHART_COLORS } from '../../utils/chartTheme'

const LABEL_COLORS = {
  positive: CHART_COLORS.emerald,
  neutral: CHART_COLORS.slate,
  negative: CHART_COLORS.crimson,
}

export default function DistributionView({ data }) {
  const labels = Object.keys(data.label_counts)
  const values = Object.values(data.label_counts)
  const colors = labels.map((label) => LABEL_COLORS[label] ?? CHART_COLORS.navy)

  const { bin_edges, counts } = data.score_histogram
  const binLabels = counts.map((_, i) => ((bin_edges[i] + bin_edges[i + 1]) / 2).toFixed(2))

  const histogramTrace = {
    type: 'bar',
    x: binLabels,
    y: counts,
    marker: { color: CHART_COLORS.navy },
  }

  const histogramLayout = {
    ...BASE_LAYOUT,
    height: 260,
    bargap: 0.05,
    xaxis: { ...BASE_LAYOUT.xaxis, title: { text: 'Confidence score' } },
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-4">
        <StatCard label="Total Headlines" value={data.total_headlines.toLocaleString()} />
        <StatCard label="Mean Score" value={data.score_mean.toFixed(3)} />
        <StatCard label="Std Dev" value={data.score_std.toFixed(3)} />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Label Distribution
          </p>
          <PieChart labels={labels} values={values} colors={colors} />
        </div>
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Confidence Score Histogram
          </p>
          <PlotlyChart data={[histogramTrace]} layout={histogramLayout} />
        </div>
      </div>
    </div>
  )
}
