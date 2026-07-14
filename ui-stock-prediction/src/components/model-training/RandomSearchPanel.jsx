import { useEffect, useMemo, useRef, useState } from 'react'
import Card, { CardHeader, CardTitle, CardContent } from '../Card'
import Button from '../Button'
import Input from '../Input'
import Icon from '../Icon'
import PlotlyChart from '../charts/PlotlyChart'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../ui/table'
import { BASE_LAYOUT, CHART_COLORS } from '../../utils/chartTheme'
import { useRandomSearchStream } from '../../hooks/useRandomSearchStream'
import { fmtNum, fmtPct } from './TrainingPanel'

const HISTORY_COLUMNS = [
  { key: 'hidden_size', label: 'Hidden' },
  { key: 'num_layers', label: 'Layers' },
  { key: 'optimizer', label: 'Optimizer' },
  { key: 'activation', label: 'Aktivasi' },
  { key: 'lr', label: 'LR' },
  { key: 'epochs', label: 'Epochs' },
  { key: 'batch_size', label: 'Batch' },
]

/**
 * Panel Random Search (live SSE, nested per-iterasi + per-epoch) untuk satu
 * varian model skripsi-scoped (Model A: LSTM-OHLCV baseline, atau Model B:
 * FinBERT-LSTM). Beda dari TrainingPanel.jsx (notebook 05, 1 model final):
 * di sini N_ITER model independen dilatih berurutan — chart live cuma
 * menampilkan iterasi yang SEDANG berjalan, histori iterasi selesai
 * ditampilkan sbg tabel ringkasan di bawahnya.
 *
 * Search space & window TIDAK bisa dikonfigurasi dari UI (tetap sesuai
 * Batasan Masalah BAB I skripsi) — hanya jumlah iterasi yang bisa di-override.
 */
export default function RandomSearchPanel({ endpoint, onDone }) {
  const [nIter, setNIter] = useState(20)
  const stream = useRandomSearchStream(endpoint)
  const logEndRef = useRef(null)

  const isRunning = stream.status === 'running'

  useEffect(() => {
    if (stream.status === 'done' && stream.result && onDone) {
      onDone(stream.result)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stream.status, stream.result])

  function handleStart() {
    if (isRunning) return
    stream.startTraining({ n_iter: Number(nIter) })
  }

  const currentEpochNums = useMemo(() => stream.currentEpochs.map((e) => e.epoch), [stream.currentEpochs])
  const currentTotalEpochs = stream.currentEpochs.length > 0
    ? stream.currentEpochs[stream.currentEpochs.length - 1].total_epochs
    : stream.currentConfig?.epochs

  const lossChartData = useMemo(
    () => [
      {
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Train Loss',
        x: currentEpochNums,
        y: stream.currentEpochs.map((e) => e.train_loss),
        line: { color: CHART_COLORS.navy, width: 2 },
        marker: { size: 4 },
      },
      {
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Val Loss',
        x: currentEpochNums,
        y: stream.currentEpochs.map((e) => e.val_loss),
        line: { color: CHART_COLORS.emerald, width: 2 },
        marker: { size: 4 },
      },
    ],
    [currentEpochNums, stream.currentEpochs],
  )

  const qualityChartData = useMemo(
    () => [
      {
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Val Accuracy',
        x: currentEpochNums,
        y: stream.currentEpochs.map((e) => e.val_acc),
        line: { color: CHART_COLORS.navy, width: 2 },
        marker: { size: 4 },
      },
      {
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Val F1',
        x: currentEpochNums,
        y: stream.currentEpochs.map((e) => e.val_f1),
        line: { color: CHART_COLORS.emerald, width: 2 },
        marker: { size: 4 },
      },
    ],
    [currentEpochNums, stream.currentEpochs],
  )

  const lossLayout = useMemo(
    () => ({
      ...BASE_LAYOUT,
      xaxis: { ...BASE_LAYOUT.xaxis, title: { text: 'Epoch (iterasi saat ini)' } },
      yaxis: { ...BASE_LAYOUT.yaxis, title: { text: 'Loss' } },
      legend: { orientation: 'h', y: -0.3 },
      margin: { l: 52, r: 16, t: 16, b: 48 },
    }),
    [],
  )

  const qualityLayout = useMemo(
    () => ({
      ...BASE_LAYOUT,
      xaxis: { ...BASE_LAYOUT.xaxis, title: { text: 'Epoch (iterasi saat ini)' } },
      yaxis: { ...BASE_LAYOUT.yaxis, title: { text: 'Skor' }, range: [0, 1] },
      legend: { orientation: 'h', y: -0.3 },
      margin: { l: 52, r: 16, t: 16, b: 48 },
    }),
    [],
  )

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ block: 'nearest' })
  }, [stream.iterationHistory.length])

  const bestSoFarF1 = stream.iterationHistory.reduce(
    (max, row) => Math.max(max, row.val_f1 ?? -1),
    -1,
  )

  const cm = stream.result?.confusion_matrix
  const metricEntries = stream.result
    ? [
        { label: 'Accuracy', value: stream.result.metrics.accuracy },
        { label: 'Precision', value: stream.result.metrics.precision },
        { label: 'Recall', value: stream.result.metrics.recall },
        { label: 'F1', value: stream.result.metrics.f1 },
      ]
    : []

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Random Search (Live) — 20 Iterasi Default</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-end gap-3">
            <div>
              <label className="mb-1.5 block text-xs font-medium text-slate-600">Jumlah Iterasi</label>
              <Input
                type="number"
                min={1}
                step={1}
                disabled={isRunning}
                value={nIter}
                onChange={(e) => setNIter(e.target.value)}
                className="w-28"
              />
            </div>
            <Button onClick={handleStart} disabled={isRunning}>
              {isRunning ? (
                <Icon name="progress_activity" className="animate-spin text-base" />
              ) : (
                <Icon name="play_arrow" className="text-base" />
              )}
              Mulai Random Search
            </Button>
          </div>

          {stream.status !== 'idle' && (
            <div className="space-y-2 rounded border border-slate-200 bg-slate-50 px-4 py-3 text-xs font-medium text-slate-600">
              <div className="flex items-center justify-between">
                <span>
                  Random Search: Iterasi{' '}
                  <span className="font-mono font-semibold text-slate-900">
                    {stream.currentIteration || 0} / {stream.totalIterations ?? '-'}
                  </span>
                </span>
                {isRunning && <Icon name="progress_activity" className="animate-spin text-base" />}
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
                <div
                  className="h-full rounded-full bg-slate-900 transition-all"
                  style={{
                    width: `${((stream.currentIteration || 0) / (stream.totalIterations || 1)) * 100}%`,
                  }}
                />
              </div>

              {isRunning && (
                <>
                  <div className="flex items-center justify-between pt-1">
                    <span>
                      Iterasi saat ini — Epoch{' '}
                      <span className="font-mono font-semibold text-slate-900">
                        {currentEpochNums.length > 0 ? currentEpochNums[currentEpochNums.length - 1] : 0} /{' '}
                        {currentTotalEpochs ?? '-'}
                      </span>
                    </span>
                  </div>
                  <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
                    <div
                      className="h-full rounded-full bg-emerald-500 transition-all"
                      style={{
                        width: `${
                          ((currentEpochNums.length > 0 ? currentEpochNums[currentEpochNums.length - 1] : 0) /
                            (currentTotalEpochs || 1)) *
                          100
                        }%`,
                      }}
                    />
                  </div>
                </>
              )}
            </div>
          )}

          {stream.status === 'error' && stream.error && (
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
              <Icon name="error" className="text-lg" />
              {stream.error}
            </div>
          )}
        </CardContent>
      </Card>

      {stream.status !== 'idle' && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Loss per Epoch (Iterasi ke-{stream.currentIteration || '-'})</CardTitle>
            </CardHeader>
            <CardContent>
              <PlotlyChart data={lossChartData} layout={lossLayout} className="h-64" />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Val Accuracy & F1 per Epoch (Iterasi ke-{stream.currentIteration || '-'})</CardTitle>
            </CardHeader>
            <CardContent>
              <PlotlyChart data={qualityChartData} layout={qualityLayout} className="h-64" />
            </CardContent>
          </Card>
        </div>
      )}

      {stream.iterationHistory.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Riwayat Iterasi</CardTitle>
          </CardHeader>
          <CardContent className="max-h-80 overflow-y-auto p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>#</TableHead>
                  {HISTORY_COLUMNS.map((col) => (
                    <TableHead key={col.key}>{col.label}</TableHead>
                  ))}
                  <TableHead>Val F1</TableHead>
                  <TableHead>Val Acc</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {stream.iterationHistory.map((row) => {
                  const isBest = row.val_f1 === bestSoFarF1
                  return (
                    <TableRow key={row.iteration}>
                      <TableCell className="font-mono">{row.iteration}</TableCell>
                      {HISTORY_COLUMNS.map((col) => (
                        <TableCell key={col.key} className="font-mono">
                          {col.key === 'lr' ? fmtNum(row.config[col.key], 5) : row.config[col.key]}
                        </TableCell>
                      ))}
                      <TableCell className="font-mono font-semibold text-slate-900">
                        <div className="flex items-center gap-2">
                          {fmtNum(row.val_f1)}
                          {isBest && (
                            <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-600">
                              Best
                            </span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="font-mono">{fmtNum(row.val_acc)}</TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
            <div ref={logEndRef} />
          </CardContent>
        </Card>
      )}

      {stream.result && (
        <>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {metricEntries.map((m) => (
              <Card key={m.label}>
                <CardContent className="p-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{m.label}</p>
                  <p className="mt-1 font-mono text-xl font-semibold text-slate-900">{fmtPct(m.value)}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Confusion Matrix (Test Set)</CardTitle>
            </CardHeader>
            <CardContent>
              {cm && (
                <div className="inline-grid grid-cols-3 gap-px overflow-hidden rounded border border-slate-200 bg-slate-200 text-sm">
                  <div className="bg-slate-50 p-3" />
                  <div className="bg-slate-50 p-3 text-center font-semibold text-slate-600">Pred Down</div>
                  <div className="bg-slate-50 p-3 text-center font-semibold text-slate-600">Pred Up</div>

                  <div className="bg-slate-50 p-3 font-semibold text-slate-600">Actual Down</div>
                  <div className="bg-white p-3 text-center font-mono">{cm.tn}</div>
                  <div className="bg-white p-3 text-center font-mono">{cm.fp}</div>

                  <div className="bg-slate-50 p-3 font-semibold text-slate-600">Actual Up</div>
                  <div className="bg-white p-3 text-center font-mono">{cm.fn}</div>
                  <div className="bg-white p-3 text-center font-mono">{cm.tp}</div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardContent className="space-y-3 p-6">
              <div className="grid grid-cols-2 gap-4 text-xs sm:grid-cols-4">
                <div>
                  <p className="uppercase tracking-wide text-slate-400">Best Val F1</p>
                  <p className="font-mono text-slate-700">{fmtNum(stream.result.best_val_f1)}</p>
                </div>
                <div>
                  <p className="uppercase tracking-wide text-slate-400">Best Val Acc</p>
                  <p className="font-mono text-slate-700">{fmtNum(stream.result.best_val_acc)}</p>
                </div>
              </div>
              <div className="space-y-1 text-xs">
                <p className="uppercase tracking-wide text-slate-400">Best Config</p>
                <p className="break-all font-mono text-slate-600">
                  {Object.entries(stream.result.best_config ?? {})
                    .map(([k, v]) => `${k}=${v}`)
                    .join(', ')}
                </p>
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
