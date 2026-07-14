import PlotlyChart from './PlotlyChart'
import { BASE_LAYOUT, CHART_PALETTE, CHART_FONTS } from '../../utils/chartTheme'
import { cn } from '../../utils/cn'

export default function PieChart({
  labels,
  values,
  colors = CHART_PALETTE,
  hole = 0.6,
  height = 280,
  className,
}) {
  const trace = {
    type: 'pie',
    labels,
    values,
    hole,
    marker: { colors, line: { color: '#ffffff', width: 2 } },
    textfont: { family: CHART_FONTS.sans, size: 12 },
    textinfo: 'label+percent',
    hoverinfo: 'label+value+percent',
  }

  const layout = {
    ...BASE_LAYOUT,
    height,
    margin: { l: 16, r: 16, t: 16, b: 16 },
    showlegend: true,
    legend: { orientation: 'h', font: { family: CHART_FONTS.sans, size: 11 }, y: -0.1 },
  }

  return <PlotlyChart data={[trace]} layout={layout} className={cn(className)} />
}
