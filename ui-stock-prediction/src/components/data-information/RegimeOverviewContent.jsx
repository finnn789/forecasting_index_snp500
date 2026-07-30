import PlotlyChart from '../charts/PlotlyChart'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../ui/table'
import { BASE_LAYOUT, CHART_COLORS } from '../../utils/chartTheme'
import { cn } from '../../utils/cn'
import { SPLIT_LABEL } from './shared'

const SPLIT_COLOR = { train: CHART_COLORS.emerald, val: CHART_COLORS.amber, test: CHART_COLORS.crimson }

export default function RegimeOverviewContent({ data }) {
  const trace = {
    type: 'scatter',
    mode: 'lines',
    x: data.points.map((p) => p.date),
    y: data.points.map((p) => p.close),
    line: { color: CHART_COLORS.navy, width: 1.2 },
    hoverinfo: 'x+y',
    name: 'Harga penutupan',
  }

  const shapes = data.splits.map((s) => ({
    type: 'rect',
    xref: 'x',
    yref: 'paper',
    x0: s.date_start,
    x1: s.date_end,
    y0: 0,
    y1: 1,
    fillcolor: SPLIT_COLOR[s.split],
    opacity: 0.12,
    line: { width: 0 },
  }))

  const layout = {
    ...BASE_LAYOUT,
    height: 340,
    shapes,
    yaxis: { ...BASE_LAYOUT.yaxis, title: { text: 'Harga penutupan' } },
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-4 text-xs text-slate-500">
        {data.splits.map((s) => (
          <span key={s.split} className="flex items-center gap-1.5">
            <span className="size-2.5 rounded-full" style={{ backgroundColor: SPLIT_COLOR[s.split] }} />
            Periode {SPLIT_LABEL[s.split]}
          </span>
        ))}
      </div>

      <PlotlyChart data={[trace]} layout={layout} />

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Periode</TableHead>
            <TableHead>Rentang Tanggal</TableHead>
            <TableHead>Perubahan Harga</TableHead>
            <TableHead>Arah Naik (Up%)</TableHead>
            <TableHead>Jumlah Hari</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.splits.map((s) => (
            <TableRow key={s.split}>
              <TableCell className="font-medium text-slate-700">{SPLIT_LABEL[s.split]}</TableCell>
              <TableCell className="font-mono text-xs">
                {s.date_start} &ndash; {s.date_end}
              </TableCell>
              <TableCell
                className={cn('font-mono', s.change_pct >= 0 ? 'text-emerald-600' : 'text-red-600')}
              >
                {s.change_pct >= 0 ? '+' : ''}
                {s.change_pct.toFixed(2)}%
              </TableCell>
              <TableCell className="font-mono">{s.up_pct.toFixed(1)}%</TableCell>
              <TableCell className="font-mono">{s.n_rows}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
