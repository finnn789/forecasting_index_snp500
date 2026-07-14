import PlotlyChart from '../charts/PlotlyChart'
import { BASE_LAYOUT, CHART_FONTS } from '../../utils/chartTheme'

export default function CorrelationHeatmap({ data, height = 380 }) {
  const trace = {
    type: 'heatmap',
    x: data.columns,
    y: data.columns,
    z: data.matrix,
    zmin: -1,
    zmax: 1,
    colorscale: [
      [0, '#ef4444'],
      [0.5, '#f8fafc'],
      [1, '#10b981'],
    ],
    hoverongaps: false,
    texttemplate: '%{z:.2f}',
    textfont: { family: CHART_FONTS.mono, size: 10 },
  }

  const layout = {
    ...BASE_LAYOUT,
    height,
    margin: { l: 80, r: 16, t: 16, b: 60 },
  }

  return <PlotlyChart data={[trace]} layout={layout} />
}
