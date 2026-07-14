import PlotlyChart from '../charts/PlotlyChart'
import { BASE_LAYOUT, CHART_COLORS } from '../../utils/chartTheme'

function barTrace(entries) {
  return {
    type: 'bar',
    x: entries.map((e) => e.label),
    y: entries.map((e) => e.avg_return_pct),
    marker: {
      color: entries.map((e) => (e.avg_return_pct >= 0 ? CHART_COLORS.emerald : CHART_COLORS.crimson)),
    },
  }
}

function seasonalLayout(title) {
  return {
    ...BASE_LAYOUT,
    height: 320,
    bargap: 0.3,
    yaxis: { ...BASE_LAYOUT.yaxis, title: { text: 'Avg Daily Return (%)' } },
    xaxis: { ...BASE_LAYOUT.xaxis, title: { text: title } },
  }
}

export default function SeasonalityChart({ data }) {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Rata-rata Return per Bulan
        </p>
        <PlotlyChart data={[barTrace(data.monthly)]} layout={seasonalLayout('Bulan')} />
      </div>
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Rata-rata Return per Hari
        </p>
        <PlotlyChart data={[barTrace(data.weekday)]} layout={seasonalLayout('Hari')} />
      </div>
    </div>
  )
}
