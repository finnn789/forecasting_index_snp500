import Icon from '../Icon'
import DataPreviewTable from './DataPreviewTable'

function formatValue(value) {
  if (typeof value === 'number') {
    return Number.isInteger(value) ? value.toLocaleString() : value.toFixed(2)
  }
  if (Array.isArray(value)) return value.join(', ')
  return String(value)
}

function RowsBadge({ rowsIn, rowsOut }) {
  if (rowsIn == null && rowsOut == null) return null

  if (rowsIn != null && rowsOut != null) {
    const diff = rowsOut - rowsIn
    return (
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded bg-slate-50 border border-slate-200 px-2 py-0.5 text-xs font-mono text-slate-700">
          {rowsIn.toLocaleString()} → {rowsOut.toLocaleString()}
        </span>
        {diff < 0 && (
          <span className="rounded bg-red-50 border border-red-200 px-2 py-0.5 text-xs font-mono text-red-600">
            {diff.toLocaleString()} baris
          </span>
        )}
      </div>
    )
  }

  return (
    <span className="rounded bg-slate-50 border border-slate-200 px-2 py-0.5 text-xs font-mono text-slate-700">
      {rowsOut.toLocaleString()} baris
    </span>
  )
}

function SplitDetail({ detail }) {
  const splits = [
    { key: 'train', label: 'TRAIN' },
    { key: 'val', label: 'VAL' },
    { key: 'test', label: 'TEST' },
  ]

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      {splits.map(({ key, label }) => {
        const split = detail?.[key]
        return (
          <div key={key} className="rounded-lg border border-slate-200 p-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
            <p className="mt-1 font-mono text-lg text-slate-900">
              {split?.rows != null ? split.rows.toLocaleString() : '—'}
            </p>
            <p className="text-xs text-slate-500">{split?.range ?? '—'}</p>
          </div>
        )
      })}
    </div>
  )
}

function ScalerDetail({ detail, featureCols }) {
  const cols = featureCols?.length ? featureCols : Object.keys(detail?.train_min ?? {})

  if (!cols.length) return null

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50">
            <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              Fitur
            </th>
            <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              Train Min
            </th>
            <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              Train Max
            </th>
          </tr>
        </thead>
        <tbody>
          {cols.map((col) => {
            const min = detail?.train_min?.[col]
            const max = detail?.train_max?.[col]
            return (
              <tr key={col} className="border-b border-slate-100 last:border-0">
                <td className="px-3 py-2 text-slate-600">{col}</td>
                <td className="px-3 py-2 font-mono text-slate-900">
                  {min != null ? formatValue(min) : '—'}
                </td>
                <td className="px-3 py-2 font-mono text-slate-900">
                  {max != null ? formatValue(max) : '—'}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function GenericDetail({ detail }) {
  if (!detail || typeof detail !== 'object') return null
  const entries = Object.entries(detail).filter(([, value]) => value !== null && typeof value !== 'object')

  if (!entries.length) return null

  return (
    <div className="flex flex-wrap gap-2">
      {entries.map(([key, value]) => (
        <span
          key={key}
          className="rounded bg-slate-50 border border-slate-200 px-2 py-0.5 text-xs text-slate-600"
        >
          {key}: <span className="font-mono text-slate-900">{formatValue(value)}</span>
        </span>
      ))}
    </div>
  )
}

function StepDetail({ step, featureCols }) {
  if (step.order === 5) return <SplitDetail detail={step.detail} />
  if (step.order === 7) return <ScalerDetail detail={step.detail} featureCols={featureCols} />
  return <GenericDetail detail={step.detail} />
}

function MiniTable({ rows, title }) {
  if (!rows?.length) return null
  const cols = Object.keys(rows[0])

  return (
    <div>
      {title && <p className="mb-1 text-xs font-medium text-slate-500">{title}</p>}
      <div className="overflow-x-auto rounded-lg border border-slate-200">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50">
              {cols.map((col) => (
                <th
                  key={col}
                  className="whitespace-nowrap px-2 py-1 text-left font-semibold uppercase tracking-wide text-slate-500"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i} className="border-b border-slate-100 last:border-0">
                {cols.map((col) => (
                  <td key={col} className="whitespace-nowrap px-2 py-1 font-mono text-slate-900">
                    {formatValue(row[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function SamplePreview({ step }) {
  if (!step.sample_before?.length && !step.sample_after?.length) return null

  return (
    <div className="space-y-2">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Contoh Baris Nyata</p>
      <div className="grid grid-cols-1 gap-3 xl:grid-cols-2">
        <MiniTable rows={step.sample_before} title="Sebelum" />
        <MiniTable rows={step.sample_after} title={step.sample_before?.length ? 'Sesudah' : undefined} />
      </div>
    </div>
  )
}

export default function PipelineStepsView({ data }) {
  const steps = Array.isArray(data?.steps) ? data.steps : []
  const featureCols = Array.isArray(data?.feature_cols) ? data.feature_cols : []

  return (
    <div className="space-y-6">
      <div>
        {steps.map((step, i) => (
          <div key={step.order ?? i} className="flex gap-4">
            <div className="flex flex-col items-center">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-900 font-mono text-xs text-white">
                {step.order}
              </div>
              {i < steps.length - 1 && <div className="mt-1 mb-1 w-px flex-1 border-l border-slate-200" />}
            </div>
            <div className={`flex-1 ${i < steps.length - 1 ? 'pb-6' : ''}`}>
              <p className="font-medium text-slate-900">{step.name}</p>
              {step.description && <p className="text-sm text-slate-500">{step.description}</p>}
              <div className="mt-2 space-y-3">
                <RowsBadge rowsIn={step.rows_in} rowsOut={step.rows_out} />
                <StepDetail step={step} featureCols={featureCols} />
                <SamplePreview step={step} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {data?.note && (
        <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          <Icon name="info" className="mt-0.5 text-lg" />
          <span>{data.note}</span>
        </div>
      )}

      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Hasil Akhir — Cuplikan Data Siap Training (Setelah MinMax Scaling)
        </p>
        <DataPreviewTable
          path={`/data-analysis/combined/scaled-preview?n=10&split=train&variant=${data?.variant ?? 'finbert'}&split_mode=${data?.split_mode ?? 'random_search'}`}
        />
      </div>
    </div>
  )
}
