import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../ui/table'
import Icon from '../Icon'
import { cn } from '../../utils/cn'

function cell(value) {
  return (
    <span className={cn('font-mono', value >= 0 ? 'text-emerald-600' : 'text-red-600')}>
      {value >= 0 ? '+' : ''}
      {value.toFixed(3)}
    </span>
  )
}

export default function FeatureCorrelationContent({ data }) {
  return (
    <div className="space-y-4">
      <p className="text-xs text-slate-500">
        Baris yang ditandai berarti arah hubungan fitur dengan pergerakan harga BERBALIK antara
        periode latih dan periode uji — pola yang dipelajari model dari data latih tidak berlaku
        lagi (bahkan terbalik) saat diuji.
      </p>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Fitur</TableHead>
            <TableHead>Korelasi (Latih)</TableHead>
            <TableHead>Korelasi (Validasi)</TableHead>
            <TableHead>Korelasi (Uji)</TableHead>
            <TableHead>Arah Berbalik?</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.rows.map((row) => (
            <TableRow key={row.feature} className={cn(row.reversed_direction && 'bg-red-50')}>
              <TableCell className="font-medium text-slate-700">{row.feature}</TableCell>
              <TableCell>{cell(row.train_r)}</TableCell>
              <TableCell>{cell(row.val_r)}</TableCell>
              <TableCell>{cell(row.test_r)}</TableCell>
              <TableCell>
                {row.reversed_direction ? (
                  <span className="inline-flex items-center gap-1 text-xs font-medium text-red-600">
                    <Icon name="sync_alt" className="text-sm" />
                    Ya
                  </span>
                ) : (
                  <span className="text-xs text-slate-400">Tidak</span>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
