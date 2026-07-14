import { useEffect, useMemo, useRef, useState } from 'react'
import Card, { CardHeader, CardTitle, CardContent } from '../Card'
import Button from '../Button'
import Input from '../Input'
import Icon from '../Icon'
import PlotlyChart from '../charts/PlotlyChart'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../ui/table'
import { BASE_LAYOUT, CHART_COLORS } from '../../utils/chartTheme'
import { useTrainingStream } from '../../hooks/useTrainingStream'
import MetricsCards from './MetricsCards'
import ConfusionMatrixGrid from './ConfusionMatrixGrid'
import ClassCollapseBanner from './ClassCollapseBanner'

export const CONFIG_KEYS = ['seq_len', 'hidden_size', 'num_layers', 'dropout', 'lr', 'batch_size', 'epochs', 'early_stop']

const CONFIG_FIELDS = [
  { key: 'seq_len', label: 'Sequence Length', step: 1, min: 1 },
  { key: 'hidden_size', label: 'Hidden Size', step: 1, min: 1 },
  { key: 'num_layers', label: 'Jumlah Layer', step: 1, min: 1 },
  { key: 'dropout', label: 'Dropout', step: 0.01, min: 0, max: 1 },
  { key: 'lr', label: 'Learning Rate', step: 0.0001, min: 0 },
  { key: 'batch_size', label: 'Batch Size', step: 1, min: 1 },
  { key: 'epochs', label: 'Epochs', step: 1, min: 1 },
  { key: 'early_stop', label: 'Early Stop (patience)', step: 1, min: 0 },
]

export function fmtNum(value, digits = 4) {
  return typeof value === 'number' ? value.toFixed(digits) : '-'
}

export function fmtPct(value) {
  return typeof value === 'number' ? `${(value * 100).toFixed(2)}%` : '-'
}

/**
 * Panel training live (SSE) untuk satu varian model (mis. OHLCV+sentimen
 * atau OHLCV-only). Setiap instance punya `useTrainingStream(endpoint)`
 * sendiri — sengaja TIDAK di-unmount saat tab tidak aktif (lihat ModelTraining.jsx),
 * supaya training yang sedang berjalan tidak ter-abort ketika user pindah tab.
 */
export default function TrainingPanel({ endpoint, bestConfig }) {
  const [configOverrides, setConfigOverrides] = useState({})
  const stream = useTrainingStream(endpoint)
  const logEndRef = useRef(null)

  const effectiveConfig = useMemo(
    () => (bestConfig ? { ...bestConfig, ...configOverrides } : null),
    [bestConfig, configOverrides],
  )

  const isRunning = stream.status === 'running'
  const currentEpoch = stream.epochs.length > 0 ? stream.epochs[stream.epochs.length - 1].epoch : 0
  const totalEpochs = stream.start?.total_epochs

  function handleFieldChange(key, value) {
    setConfigOverrides((prev) => ({ ...prev, [key]: value }))
  }

  function handleStart() {
    if (!effectiveConfig || isRunning) return
    const payload = {}
    for (const key of CONFIG_KEYS) {
      const raw = effectiveConfig[key]
      payload[key] = typeof raw === 'string' ? Number(raw) : raw
    }
    stream.startTraining(payload)
  }

  const epochNums = useMemo(() => stream.epochs.map((e) => e.epoch), [stream.epochs])

  const lossChartData = useMemo(
    () => [
      {
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Train Loss',
        x: epochNums,
        y: stream.epochs.map((e) => e.train_loss),
        line: { color: CHART_COLORS.navy, width: 2 },
        marker: { size: 4 },
      },
      {
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Val Loss',
        x: epochNums,
        y: stream.epochs.map((e) => e.val_loss),
        line: { color: CHART_COLORS.emerald, width: 2 },
        marker: { size: 4 },
      },
    ],
    [epochNums, stream.epochs],
  )

  const f2ChartData = useMemo(
    () => [
      {
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Train F2',
        x: epochNums,
        y: stream.epochs.map((e) => e.train_f2),
        line: { color: CHART_COLORS.navy, width: 2 },
        marker: { size: 4 },
      },
      {
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Val F2',
        x: epochNums,
        y: stream.epochs.map((e) => e.val_f2),
        line: { color: CHART_COLORS.emerald, width: 2 },
        marker: { size: 4 },
      },
    ],
    [epochNums, stream.epochs],
  )

  // Layout baru per chart (bukan referensi BASE_LAYOUT yang sama) supaya
  // aman meski usePlotlyChart sudah deep-clone sebelum dipakai Plotly.
  const lossLayout = useMemo(
    () => ({
      ...BASE_LAYOUT,
      xaxis: { ...BASE_LAYOUT.xaxis, title: { text: 'Epoch' } },
      yaxis: { ...BASE_LAYOUT.yaxis, title: { text: 'Loss' } },
      legend: { orientation: 'h', y: -0.3 },
      margin: { l: 52, r: 16, t: 16, b: 48 },
    }),
    [],
  )

  const f2Layout = useMemo(
    () => ({
      ...BASE_LAYOUT,
      xaxis: { ...BASE_LAYOUT.xaxis, title: { text: 'Epoch' } },
      yaxis: { ...BASE_LAYOUT.yaxis, title: { text: 'F2 Score' } },
      legend: { orientation: 'h', y: -0.3 },
      margin: { l: 52, r: 16, t: 16, b: 48 },
    }),
    [],
  )

  const logRows = useMemo(() => {
    const rows = []
    if (stream.start) {
      const split = stream.start.split
      rows.push({
        id: 'start',
        note: `START — ${stream.start.total_epochs} epoch, device ${stream.start.device}, train ${split?.train_rows ?? '-'} baris / val ${split?.val_rows ?? '-'} / test ${split?.test_rows ?? '-'}`,
      })
    }
    stream.epochs.forEach((e) => {
      rows.push({
        id: `epoch-${e.epoch}`,
        epoch: `${e.epoch}/${e.total_epochs}`,
        train_loss: e.train_loss,
        val_loss: e.val_loss,
        train_f2: e.train_f2,
        val_f2: e.val_f2,
      })
    })
    if (stream.result) {
      rows.push({
        id: 'done',
        note: `DONE — best_val_f2=${fmtNum(stream.result.best_val_f2)} @ epoch ${stream.result.best_epoch}`,
      })
    }
    if (stream.status === 'error' && stream.error) {
      rows.push({ id: 'error', note: `ERROR — ${stream.error}` })
    }
    return rows
  }, [stream.start, stream.epochs, stream.result, stream.status, stream.error])

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ block: 'nearest' })
  }, [logRows.length])

  const diagnosis = stream.result?.diagnosis

  const metricEntries = stream.result
    ? [
        { label: 'Accuracy', value: fmtPct(stream.result.metrics.accuracy) },
        { label: 'Precision', value: fmtPct(stream.result.metrics.precision) },
        { label: 'Recall', value: fmtPct(stream.result.metrics.recall) },
        { label: 'F1', value: fmtPct(stream.result.metrics.f1) },
        { label: 'F2', value: fmtPct(stream.result.metrics.f2) },
      ]
    : []

  const cm = stream.result?.confusion_matrix

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Training Final (Live)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {CONFIG_FIELDS.map((field) => (
              <div key={field.key}>
                <label className="mb-1.5 block text-xs font-medium text-slate-600">{field.label}</label>
                <Input
                  type="number"
                  step={field.step}
                  min={field.min}
                  max={field.max}
                  disabled={isRunning || !effectiveConfig}
                  value={effectiveConfig?.[field.key] ?? ''}
                  onChange={(e) => handleFieldChange(field.key, e.target.value)}
                />
              </div>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <Button onClick={handleStart} disabled={!effectiveConfig || isRunning}>
              {isRunning ? (
                <Icon name="progress_activity" className="animate-spin text-base" />
              ) : (
                <Icon name="play_arrow" className="text-base" />
              )}
              Mulai Training
            </Button>

            {isRunning && (
              <div className="flex items-center gap-2 rounded border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-600">
                <Icon name="progress_activity" className="animate-spin text-base" />
                {stream.start ? `Epoch ${currentEpoch}/${totalEpochs}` : 'Memulai training...'}
              </div>
            )}
          </div>

          {stream.status === 'error' && stream.error && (
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
              <Icon name="error" className="text-lg" />
              {stream.error}
            </div>
          )}
        </CardContent>
      </Card>

      {stream.status !== 'idle' && (
        <>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Loss per Epoch</CardTitle>
              </CardHeader>
              <CardContent>
                <PlotlyChart data={lossChartData} layout={lossLayout} className="h-72" />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>F2 Score per Epoch</CardTitle>
              </CardHeader>
              <CardContent>
                <PlotlyChart data={f2ChartData} layout={f2Layout} className="h-72" />
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Run Log</CardTitle>
            </CardHeader>
            <CardContent className="max-h-80 overflow-y-auto p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Epoch</TableHead>
                    <TableHead>Train Loss</TableHead>
                    <TableHead>Val Loss</TableHead>
                    <TableHead>Train F2</TableHead>
                    <TableHead>Val F2</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {logRows.map((row) =>
                    row.note ? (
                      <TableRow key={row.id}>
                        <TableCell colSpan={5} className="font-mono text-slate-500">
                          {row.note}
                        </TableCell>
                      </TableRow>
                    ) : (
                      <TableRow key={row.id}>
                        <TableCell className="font-mono">{row.epoch}</TableCell>
                        <TableCell className="font-mono">{fmtNum(row.train_loss)}</TableCell>
                        <TableCell className="font-mono">{fmtNum(row.val_loss)}</TableCell>
                        <TableCell className="font-mono">{fmtNum(row.train_f2)}</TableCell>
                        <TableCell className="font-mono">{fmtNum(row.val_f2)}</TableCell>
                      </TableRow>
                    ),
                  )}
                </TableBody>
              </Table>
              <div ref={logEndRef} />
            </CardContent>
          </Card>
        </>
      )}

      {stream.result && (
        <>
          <MetricsCards entries={metricEntries} />

          <Card>
            <CardHeader>
              <CardTitle>Confusion Matrix</CardTitle>
            </CardHeader>
            <CardContent>
              <ConfusionMatrixGrid cm={cm} />
            </CardContent>
          </Card>

          <ClassCollapseBanner diagnosis={diagnosis} />

          <Card>
            <CardContent className="space-y-3 p-6">
              <div className="grid grid-cols-2 gap-4 text-xs sm:grid-cols-4">
                <div>
                  <p className="uppercase tracking-wide text-slate-400">Best Val F2</p>
                  <p className="font-mono text-slate-700">{fmtNum(stream.result.best_val_f2)}</p>
                </div>
                <div>
                  <p className="uppercase tracking-wide text-slate-400">Best Epoch</p>
                  <p className="font-mono text-slate-700">{stream.result.best_epoch}</p>
                </div>
                <div>
                  <p className="uppercase tracking-wide text-slate-400">Fit Status</p>
                  <p className="font-mono text-slate-700">{diagnosis?.fit_status ?? '-'}</p>
                </div>
              </div>
              <div className="space-y-1 text-xs">
                <p className="uppercase tracking-wide text-slate-400">Artifact Paths</p>
                <p className="break-all font-mono text-slate-600">model: {stream.result.artifact_paths?.model}</p>
                <p className="break-all font-mono text-slate-600">scaler: {stream.result.artifact_paths?.scaler}</p>
                <p className="break-all font-mono text-slate-600">
                  metadata: {stream.result.artifact_paths?.metadata}
                </p>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
