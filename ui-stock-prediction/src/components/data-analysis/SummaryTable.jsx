import { Table, TableBody, TableRow, TableCell } from '../ui/table'
import DataPreviewTable from './DataPreviewTable'

const SCALAR_LABELS = {
  total_rows: 'Total Rows',
  date_start: 'Date Start',
  date_end: 'Date End',
  duplicate_dates: 'Duplicate Dates',
  duplicate_rows: 'Duplicate Rows',
  duplicate_titles: 'Duplicate Titles',
  duplicate_title_date: 'Duplicate Title+Date',
}

export default function SummaryTable({ data, path }) {
  const scalarEntries = Object.entries(SCALAR_LABELS).filter(([key]) => key in data)
  const previewPath = path?.endsWith('raw-info') ? `${path.replace('raw-info', 'raw-preview')}?n=10` : null

  return (
    <div className="space-y-4">
      <Table>
        <TableBody>
          {scalarEntries.map(([key, label]) => (
            <TableRow key={key}>
              <TableCell className="w-48 font-medium text-slate-500">{label}</TableCell>
              <TableCell className="font-mono text-slate-900">{String(data[key])}</TableCell>
            </TableRow>
          ))}
          {Array.isArray(data.columns) && (
            <TableRow>
              <TableCell className="w-48 font-medium text-slate-500">Columns</TableCell>
              <TableCell className="font-mono text-slate-900">{data.columns.join(', ')}</TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>

      {data.missing_values && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Missing Values
          </p>
          <Table>
            <TableBody>
              {Object.entries(data.missing_values).map(([col, count]) => (
                <TableRow key={col}>
                  <TableCell className="w-48 text-slate-600">{col}</TableCell>
                  <TableCell
                    className={`font-mono ${count > 0 ? 'text-red-500' : 'text-slate-900'}`}
                  >
                    {count}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {previewPath && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Cuplikan 10 Baris Pertama
          </p>
          <DataPreviewTable path={previewPath} />
        </div>
      )}
    </div>
  )
}
