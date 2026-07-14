import Icon from '../Icon'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../ui/table'

function ColumnsBadgeList({ columns, droppedSet }) {
  if (!columns?.length) return null

  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {columns.map((col) => {
        const isDropped = droppedSet?.has(col)
        return (
          <span
            key={col}
            className={
              isDropped
                ? 'rounded border border-red-200 bg-red-50 px-2 py-0.5 text-xs font-mono text-red-600 line-through'
                : 'rounded border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs font-mono text-slate-700'
            }
          >
            {col}
          </span>
        )
      })}
    </div>
  )
}

function SideCard({ title, titleClassName, dataset, droppedSet }) {
  const totalRows = dataset?.total_rows
  const columns = Array.isArray(dataset?.columns) ? dataset.columns : []
  const duplicateDates = dataset?.duplicate_dates

  return (
    <div className="rounded-lg border border-slate-200 p-4">
      <p className={`text-xs font-semibold uppercase tracking-wide ${titleClassName}`}>{title}</p>

      <p className="mt-2 font-mono text-2xl text-slate-900">
        {totalRows != null ? totalRows.toLocaleString() : '—'}
        <span className="ml-1 text-xs font-sans font-normal text-slate-500">baris</span>
      </p>

      <div className="mt-3">
        <p className="text-xs text-slate-500">{columns.length} kolom</p>
        <ColumnsBadgeList columns={columns} droppedSet={droppedSet} />
      </div>

      <div className="mt-3 flex items-center gap-2">
        <span className="text-xs text-slate-500">Duplicate Dates</span>
        <span
          className={
            duplicateDates > 0
              ? 'rounded bg-red-50 border border-red-200 px-2 py-0.5 text-xs font-mono text-red-600'
              : 'rounded bg-slate-50 border border-slate-200 px-2 py-0.5 text-xs font-mono text-slate-700'
          }
        >
          {duplicateDates ?? '—'}
        </span>
      </div>
    </div>
  )
}

export default function StockPreprocessingView({ data }) {
  const raw = data?.raw ?? {}
  const clean = data?.clean ?? {}
  const columnsDropped = Array.isArray(data?.columns_dropped) ? data.columns_dropped : []
  const invalidRowsDropped = data?.invalid_rows_dropped
  const droppedSet = new Set(columnsDropped)

  const missingKeys = Array.from(
    new Set([...Object.keys(raw?.missing_values ?? {}), ...Object.keys(clean?.missing_values ?? {})])
  )

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-center gap-3 sm:justify-between">
        <span className="rounded bg-slate-50 border border-slate-200 px-2 py-0.5 text-xs font-mono text-slate-700">
          {columnsDropped.length} kolom dibuang
        </span>
        <Icon name="arrow_forward" className="text-3xl text-slate-400" />
        {invalidRowsDropped > 0 ? (
          <span className="rounded bg-red-50 border border-red-200 px-2 py-0.5 text-xs font-mono text-red-600">
            {invalidRowsDropped.toLocaleString()} baris tidak valid dibuang
          </span>
        ) : (
          <span className="text-xs text-slate-500">Tidak ada baris tidak valid dibuang</span>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <SideCard title="Raw" titleClassName="text-slate-500" dataset={raw} droppedSet={droppedSet} />
        <SideCard title="Clean" titleClassName="text-emerald-600" dataset={clean} droppedSet={null} />
      </div>

      {missingKeys.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Missing Values</p>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Kolom</TableHead>
                <TableHead>Raw</TableHead>
                <TableHead>Clean</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {missingKeys.map((col) => {
                const rawCount = raw?.missing_values?.[col]
                const cleanCount = clean?.missing_values?.[col]
                const cleanIsDropped = !(col in (clean?.missing_values ?? {}))
                return (
                  <TableRow key={col}>
                    <TableCell className="text-slate-600">{col}</TableCell>
                    <TableCell className={`font-mono ${rawCount > 0 ? 'text-red-500' : 'text-slate-900'}`}>
                      {rawCount != null ? rawCount : '—'}
                    </TableCell>
                    <TableCell
                      className={`font-mono ${cleanCount > 0 ? 'text-red-500' : 'text-slate-900'}`}
                    >
                      {cleanIsDropped ? '—' : cleanCount != null ? cleanCount : '—'}
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </div>
      )}

      {data?.note && (
        <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          <Icon name="info" className="mt-0.5 shrink-0 text-lg" />
          <span>{data.note}</span>
        </div>
      )}
    </div>
  )
}
