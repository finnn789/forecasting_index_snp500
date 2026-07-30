import PlotlyChart from '../charts/PlotlyChart'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../ui/table'
import { BASE_LAYOUT, CHART_COLORS } from '../../utils/chartTheme'
import { cn } from '../../utils/cn'
import { SPLIT_LABEL } from './shared'

const SPLIT_COLOR = { train: CHART_COLORS.emerald, val: CHART_COLORS.amber, test: CHART_COLORS.crimson }

function splitTrace(points, split) {
  const subset = points.filter((p) => p.split === split)
  return {
    type: 'scatter',
    mode: 'lines',
    name: SPLIT_LABEL[split],
    x: subset.map((p) => p.date),
    y: subset.map((p) => p.close_scaled),
    line: { color: SPLIT_COLOR[split], width: 1.4 },
  }
}

export default function ScalingRangeContent({ data }) {
  const traces = ['train', 'val', 'test'].map((s) => splitTrace(data.close_series, s))

  const layout = {
    ...BASE_LAYOUT,
    height: 320,
    legend: { orientation: 'h', y: -0.2 },
    yaxis: { ...BASE_LAYOUT.yaxis, title: { text: 'Harga penutupan ternormalisasi' } },
    shapes: [0, 1].map((y) => ({
      type: 'line',
      xref: 'paper',
      x0: 0,
      x1: 1,
      yref: 'y',
      y0: y,
      y1: y,
      line: { color: CHART_COLORS.slate, dash: 'dash', width: 1 },
    })),
  }

  return (
    <div className="space-y-4">
      <p className="text-xs text-slate-500">
        Garis putus-putus menandai batas jangkauan data latihan (0 dan 1) — bagian garis yang
        keluar dari kedua batas ini berarti nilainya belum pernah dilihat model saat pelatihan.
      </p>
      <PlotlyChart data={traces} layout={layout} />

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Fitur</TableHead>
            <TableHead>Rentang Data Latih</TableHead>
            <TableHead>% Validasi di Luar Jangkauan</TableHead>
            <TableHead>% Uji di Luar Jangkauan</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.features.map((f) => (
            <TableRow key={f.feature}>
              <TableCell className="font-medium text-slate-700">{f.feature}</TableCell>
              <TableCell className="font-mono text-xs">
                {f.train_min.toLocaleString()} &ndash; {f.train_max.toLocaleString()}
              </TableCell>
              <TableCell
                className={cn('font-mono', f.val_pct_out_of_range > 0 ? 'text-red-600' : 'text-slate-500')}
              >
                {f.val_pct_out_of_range.toFixed(1)}%
              </TableCell>
              <TableCell
                className={cn('font-mono', f.test_pct_out_of_range > 0 ? 'text-red-600' : 'text-slate-500')}
              >
                {f.test_pct_out_of_range.toFixed(1)}%
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
