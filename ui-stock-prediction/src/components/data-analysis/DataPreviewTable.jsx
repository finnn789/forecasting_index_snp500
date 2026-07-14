import { useDataAnalysis } from '../../hooks/useDataAnalysis'
import Icon from '../Icon'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../ui/table'

function formatCell(value) {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'number') {
    return Number.isInteger(value) ? value.toLocaleString() : value.toFixed(2)
  }
  return String(value)
}

export default function DataPreviewTable({ path }) {
  const { data, loading, error } = useDataAnalysis(path)

  if (loading) {
    return (
      <div className="flex h-24 items-center justify-center gap-2 text-sm text-slate-400">
        <Icon name="progress_activity" className="animate-spin text-lg" />
        Memuat cuplikan data...
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
        <Icon name="error" className="text-lg" />
        {error}
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-slate-200">
      <Table>
        <TableHeader>
          <TableRow>
            {data.columns.map((col) => (
              <TableHead key={col} className="whitespace-nowrap">
                {col}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.rows.map((row, i) => (
            <TableRow key={i}>
              {data.columns.map((col) => (
                <TableCell key={col} className="whitespace-nowrap font-mono">
                  {formatCell(row[col])}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
