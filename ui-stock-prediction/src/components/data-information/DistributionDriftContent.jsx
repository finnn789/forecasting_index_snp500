import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../ui/table'
import Icon from '../Icon'
import { cn } from '../../utils/cn'

export default function DistributionDriftContent({ data }) {
  return (
    <div className="space-y-4">
      <p className="text-xs text-slate-500">
        Uji statistik perbedaan distribusi (KS-test) membandingkan bentuk sebaran nilai suatu
        fitur antara periode latih dan periode uji. Ditandai signifikan berarti perbedaannya
        bukan kebetulan — data uji memang berasal dari kondisi pasar yang berbeda dari data latih.
      </p>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Fitur</TableHead>
            <TableHead>KS-statistic</TableHead>
            <TableHead>p-value</TableHead>
            <TableHead>Signifikan?</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.rows.map((row) => (
            <TableRow key={row.feature} className={cn(row.significant && 'bg-red-50')}>
              <TableCell className="font-medium text-slate-700">{row.feature}</TableCell>
              <TableCell className="font-mono">{row.ks_statistic.toFixed(3)}</TableCell>
              <TableCell className="font-mono">{row.p_value.toFixed(4)}</TableCell>
              <TableCell>
                {row.significant ? (
                  <span className="inline-flex items-center gap-1 text-xs font-medium text-red-600">
                    <Icon name="warning" className="text-sm" />
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
