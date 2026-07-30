import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../ui/table'
import { cn } from '../../utils/cn'
import { SPLIT_LABEL } from './shared'

function pct(value) {
  return value == null ? '—' : `${(value * 100).toFixed(1)}%`
}

export default function BaselineComparisonContent({ data }) {
  return (
    <div className="space-y-4">
      <p className="text-xs text-slate-500">
        Baseline Selalu-Mayoritas = akurasi jika sistem selalu menebak arah yang lebih sering
        muncul. Baseline Ikuti-Arah-Kemarin = akurasi jika sistem selalu menebak arah hari ini
        sama dengan arah hari sebelumnya. Metrik model sungguhan hanya tersedia untuk periode uji.
        Kalau model tidak mengungguli kedua baseline ini, model belum menemukan pola yang berguna.
      </p>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Model</TableHead>
            <TableHead>Horizon</TableHead>
            <TableHead>Periode</TableHead>
            <TableHead>n</TableHead>
            <TableHead>Baseline Mayoritas</TableHead>
            <TableHead>Baseline Ikuti-Kemarin</TableHead>
            <TableHead>Akurasi Model</TableHead>
            <TableHead>Precision</TableHead>
            <TableHead>Recall</TableHead>
            <TableHead>F1</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.rows.map((row, idx) => (
            <TableRow
              key={`${row.model}-${row.horizon}-${row.split}`}
              className={cn(idx > 0 && data.rows[idx - 1].model !== row.model && 'border-t-2 border-t-slate-300')}
            >
              <TableCell className="font-medium text-slate-700">{row.model_label}</TableCell>
              <TableCell className="font-mono">{row.horizon} hari</TableCell>
              <TableCell>{SPLIT_LABEL[row.split]}</TableCell>
              <TableCell className="font-mono">{row.n}</TableCell>
              <TableCell className="font-mono">{pct(row.majority_baseline_acc)}</TableCell>
              <TableCell className="font-mono">{pct(row.persistence_baseline_acc)}</TableCell>
              <TableCell className="font-mono font-medium">{pct(row.model_accuracy)}</TableCell>
              <TableCell className="font-mono">{pct(row.model_precision)}</TableCell>
              <TableCell className="font-mono">{pct(row.model_recall)}</TableCell>
              <TableCell className="font-mono">{pct(row.model_f1)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
