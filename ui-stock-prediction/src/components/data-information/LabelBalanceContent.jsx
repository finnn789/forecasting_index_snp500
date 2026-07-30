import PlotlyChart from '../charts/PlotlyChart'
import { BASE_LAYOUT, CHART_PALETTE, CHART_COLORS } from '../../utils/chartTheme'
import { SPLIT_ORDER, SPLIT_LABEL } from './shared'

function barTraces(models) {
  return models.map((m, idx) => ({
    type: 'bar',
    name: m.model_label,
    x: SPLIT_ORDER.map((s) => SPLIT_LABEL[s]),
    y: SPLIT_ORDER.map((s) => m.splits.find((row) => row.split === s)?.up_pct ?? null),
    marker: { color: CHART_PALETTE[idx] },
  }))
}

export default function LabelBalanceContent({ data }) {
  const barLayout = {
    ...BASE_LAYOUT,
    height: 300,
    barmode: 'group',
    bargap: 0.3,
    legend: { orientation: 'h', y: -0.2 },
    yaxis: { ...BASE_LAYOUT.yaxis, title: { text: 'Arah Naik (Up%)' }, range: [0, 100] },
    shapes: [
      {
        type: 'line',
        xref: 'paper',
        x0: 0,
        x1: 1,
        yref: 'y',
        y0: 50,
        y1: 50,
        line: { color: CHART_COLORS.slate, dash: 'dash', width: 1 },
      },
    ],
  }

  const rollingTrace = {
    type: 'scatter',
    mode: 'lines',
    name: `Up% bergerak (${data.rolling_window} hari)`,
    x: data.rolling.map((p) => p.date),
    y: data.rolling.map((p) => p.rolling_up_pct),
    line: { color: CHART_COLORS.navy, width: 1.3 },
    connectgaps: false,
  }

  const rollingLayout = {
    ...BASE_LAYOUT,
    height: 300,
    yaxis: { ...BASE_LAYOUT.yaxis, title: { text: 'Up% bergerak' } },
    shapes: [
      {
        type: 'line',
        xref: 'paper',
        x0: 0,
        x1: 1,
        yref: 'y',
        y0: 50,
        y1: 50,
        line: { color: CHART_COLORS.slate, dash: 'dash', width: 1 },
      },
    ],
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Perbandingan Arah Naik per Periode
        </p>
        <PlotlyChart data={barTraces(data.models)} layout={barLayout} />
      </div>
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Arah Naik Bergerak Sepanjang Waktu (garis putus = 50%)
        </p>
        <PlotlyChart data={[rollingTrace]} layout={rollingLayout} />
      </div>
    </div>
  )
}
