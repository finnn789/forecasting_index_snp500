import PlotlyChart from '../charts/PlotlyChart'
import StatCard from '../charts/StatCard'
import { BASE_LAYOUT, CHART_COLORS } from '../../utils/chartTheme'

export default function EdaSummaryView({ data }) {
  const annualTrace = {
    type: 'bar',
    x: data.annual_returns.map((r) => String(r.year)),
    y: data.annual_returns.map((r) => r.return_pct),
    marker: {
      color: data.annual_returns.map((r) => (r.return_pct >= 0 ? CHART_COLORS.emerald : CHART_COLORS.crimson)),
    },
  }

  const annualLayout = {
    ...BASE_LAYOUT,
    height: 320,
    bargap: 0.3,
    yaxis: { ...BASE_LAYOUT.yaxis, title: { text: 'Return Tahunan (%)' } },
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Total Trading Days" value={data.total_trading_days.toLocaleString()} />
        <StatCard label="Start Price" value={data.start_price.toFixed(2)} />
        <StatCard label="End Price" value={data.end_price.toFixed(2)} />
        <StatCard label="Cumulative Return" value={`${data.cumulative_return_pct.toFixed(2)}%`} delta={data.cumulative_return_pct} />
        <StatCard label="Max Drawdown" value={`${data.max_drawdown_pct.toFixed(2)}%`} delta={data.max_drawdown_pct} />
        <StatCard label="Mean Daily Return" value={`${data.mean_daily_return_pct.toFixed(4)}%`} delta={data.mean_daily_return_pct} />
        <StatCard label="Annualized Volatility" value={`${data.annualized_volatility_pct.toFixed(2)}%`} />
        <StatCard label="Skewness / Kurtosis" value={`${data.skewness.toFixed(2)} / ${data.kurtosis.toFixed(2)}`} />
        <StatCard
          label="Bullish Days"
          value={`${data.bullish_days.toLocaleString()} (${data.bullish_pct.toFixed(1)}%)`}
        />
        <StatCard
          label="Bearish Days"
          value={`${data.bearish_days.toLocaleString()} (${data.bearish_pct.toFixed(1)}%)`}
        />
      </div>

      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Return per Tahun
        </p>
        <PlotlyChart data={[annualTrace]} layout={annualLayout} />
      </div>
    </div>
  )
}
