import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import Card, { CardHeader, CardTitle, CardContent } from '../Card'
import Button from '../Button'
import Input from '../Input'
import Icon from '../Icon'
import PlotlyChart from '../charts/PlotlyChart'
import { BASE_LAYOUT, CHART_COLORS } from '../../utils/chartTheme'
import { useManualTrainStream } from '../../hooks/useManualTrainStream'
import { useDatasetGate } from '../../hooks/useDatasetGate'
import { cn } from '../../utils/cn'
import { fmtNum, fmtPct } from './format'

const DEFAULT_FORM = {
  hidden_size: 64,
  num_layers: 1,
  dropout: 0.3,
  optimizer: 'adam',
  activation: 'relu',
  lr: 0.001,
  epochs: 30,
  batch_size: 32,
}

const SELECT_CLASS = cn(
  'h-10 w-full rounded border border-slate-300 bg-white px-3 text-sm text-slate-900',
  'transition-colors',
  'focus:border-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900/10',
  'disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-400',
)

/**
 * Panel Training Manual (1 konfigurasi hyperparameter fixed, input bebas —
 * BUKAN Random Search) untuk satu varian model skripsi-scoped. Dipakai untuk
 * training manual biasa MAUPUN "Retrain dengan Best Config" (form di-prefill
 * lewat prop `prefill` saat user klik tombol terkait di RandomSearchPanel).
 *
 * Training ini MENIMPA artefak resmi varian (sama nama file dgn Random
 * Search) — sengaja, supaya halaman Prediction otomatis ikut ter-update.
 */
export default function ManualTrainingPanel({ endpoint, variant, prefill, onDone }) {
  const [form, setForm] = useState(DEFAULT_FORM)
  const [appliedToken, setAppliedToken] = useState(prefill?.token)
  const stream = useManualTrainStream(endpoint)
  const gate = useDatasetGate(variant, 'manual')

  const isRunning = stream.status === 'running'
  const canStart = !isRunning && !gate.loading && gate.ready

  // "Adjust state during render" (bukan useEffect) supaya form ter-prefill
  // tiap prefill.token berubah (mis. user klik "Retrain dengan Best Config"
  // berkali-kali dgn config yang sama persis) tanpa render tambahan.
  if (prefill?.token !== appliedToken) {
    setAppliedToken(prefill?.token)
    if (prefill?.config) {
      setForm(prefill.config)
    }
  }

  useEffect(() => {
    if (stream.status === 'done' && stream.result && onDone) {
      onDone(stream.result)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stream.status, stream.result])

  function updateField(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  function handleStart() {
    if (!canStart) return
    stream.startTraining({
      hidden_size: Number(form.hidden_size),
      num_layers: Number(form.num_layers),
      dropout: Number(form.dropout),
      optimizer: form.optimizer,
      activation: form.activation,
      lr: Number(form.lr),
      epochs: Number(form.epochs),
      batch_size: Number(form.batch_size),
    })
  }

  const epochNums = useMemo(() => stream.epochs.map((e) => e.epoch), [stream.epochs])
  const currentEpoch = epochNums.length > 0 ? epochNums[epochNums.length - 1] : 0
  const totalEpochs = stream.epochs.length > 0
    ? stream.epochs[stream.epochs.length - 1].total_epochs
    : Number(form.epochs)

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
        name: 'Test Loss',
        x: epochNums,
        y: stream.epochs.map((e) => e.test_loss),
        line: { color: CHART_COLORS.emerald, width: 2 },
        marker: { size: 4 },
      },
    ],
    [epochNums, stream.epochs],
  )

  const qualityChartData = useMemo(
    () => [
      {
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Test Accuracy',
        x: epochNums,
        y: stream.epochs.map((e) => e.test_acc),
        line: { color: CHART_COLORS.navy, width: 2 },
        marker: { size: 4 },
      },
      {
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Test F1',
        x: epochNums,
        y: stream.epochs.map((e) => e.test_f1),
        line: { color: CHART_COLORS.emerald, width: 2 },
        marker: { size: 4 },
      },
    ],
    [epochNums, stream.epochs],
  )

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

  const qualityLayout = useMemo(
    () => ({
      ...BASE_LAYOUT,
      xaxis: { ...BASE_LAYOUT.xaxis, title: { text: 'Epoch' } },
      yaxis: { ...BASE_LAYOUT.yaxis, title: { text: 'Skor' }, range: [0, 1] },
      legend: { orientation: 'h', y: -0.3 },
      margin: { l: 52, r: 16, t: 16, b: 48 },
    }),
    [],
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
          <CardTitle>Training Manual — Konfigurasi Kustom</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <Field label="Hidden Size">
              <Input
                type="number"
                min={1}
                step={1}
                disabled={isRunning}
                value={form.hidden_size}
                onChange={(e) => updateField('hidden_size', e.target.value)}
              />
            </Field>
            <Field label="Jumlah Layer">
              <Input
                type="number"
                min={1}
                step={1}
                disabled={isRunning}
                value={form.num_layers}
                onChange={(e) => updateField('num_layers', e.target.value)}
              />
            </Field>
            <Field label="Dropout">
              <Input
                type="number"
                min={0}
                max={0.99}
                step={0.01}
                disabled={isRunning}
                value={form.dropout}
                onChange={(e) => updateField('dropout', e.target.value)}
              />
            </Field>
            <Field label="Learning Rate">
              <Input
                type="number"
                min={0}
                step={0.0001}
                disabled={isRunning}
                value={form.lr}
                onChange={(e) => updateField('lr', e.target.value)}
              />
            </Field>
            <Field label="Epochs">
              <Input
                type="number"
                min={1}
                step={1}
                disabled={isRunning}
                value={form.epochs}
                onChange={(e) => updateField('epochs', e.target.value)}
              />
            </Field>
            <Field label="Batch Size">
              <Input
                type="number"
                min={1}
                step={1}
                disabled={isRunning}
                value={form.batch_size}
                onChange={(e) => updateField('batch_size', e.target.value)}
              />
            </Field>
            <Field label="Optimizer">
              <select
                className={SELECT_CLASS}
                disabled={isRunning}
                value={form.optimizer}
                onChange={(e) => updateField('optimizer', e.target.value)}
              >
                <option value="adam">adam</option>
                <option value="rmsprop">rmsprop</option>
                <option value="sgd">sgd</option>
              </select>
            </Field>
            <Field label="Aktivasi">
              <select
                className={SELECT_CLASS}
                disabled={isRunning}
                value={form.activation}
                onChange={(e) => updateField('activation', e.target.value)}
              >
                <option value="relu">relu</option>
                <option value="tanh">tanh</option>
                <option value="sigmoid">sigmoid</option>
              </select>
            </Field>
          </div>

          <Button onClick={handleStart} disabled={!canStart}>
            {isRunning ? (
              <Icon name="progress_activity" className="animate-spin text-base" />
            ) : (
              <Icon name="play_arrow" className="text-base" />
            )}
            Mulai Training Manual
          </Button>

          {!gate.loading && !gate.ready && (
            <div className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
              <Icon name="info" className="text-lg" />
              <span>
                Dataset latih (split 80/20) belum dibangun atau basi.{' '}
                <Link to="/workflow" className="font-medium underline">
                  Bangun di halaman Workflow →
                </Link>
              </span>
            </div>
          )}

          {stream.status !== 'idle' && (
            <div className="space-y-2 rounded border border-slate-200 bg-slate-50 px-4 py-3 text-xs font-medium text-slate-600">
              <div className="flex items-center justify-between">
                <span>
                  Epoch{' '}
                  <span className="font-mono font-semibold text-slate-900">
                    {currentEpoch} / {totalEpochs ?? '-'}
                  </span>
                </span>
                {isRunning && <Icon name="progress_activity" className="animate-spin text-base" />}
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
                <div
                  className="h-full rounded-full bg-emerald-500 transition-all"
                  style={{ width: `${(currentEpoch / (totalEpochs || 1)) * 100}%` }}
                />
              </div>
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
              <CardTitle>Loss per Epoch</CardTitle>
            </CardHeader>
            <CardContent>
              <PlotlyChart data={lossChartData} layout={lossLayout} className="h-64" />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Test Accuracy & F1 per Epoch</CardTitle>
            </CardHeader>
            <CardContent>
              <PlotlyChart data={qualityChartData} layout={qualityLayout} className="h-64" />
            </CardContent>
          </Card>
        </div>
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
                  <p className="uppercase tracking-wide text-slate-400">Final Test F1</p>
                  <p className="font-mono text-slate-700">{fmtNum(stream.result.final_test_f1)}</p>
                </div>
                <div>
                  <p className="uppercase tracking-wide text-slate-400">Final Test Acc</p>
                  <p className="font-mono text-slate-700">{fmtNum(stream.result.final_test_acc)}</p>
                </div>
              </div>
              <div className="space-y-1 text-xs">
                <p className="uppercase tracking-wide text-slate-400">Konfigurasi Dipakai</p>
                <p className="break-all font-mono text-slate-600">
                  {Object.entries(stream.result.config ?? {})
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

function Field({ label, children }) {
  return (
    <div>
      <label className="mb-1.5 block text-xs font-medium text-slate-600">{label}</label>
      {children}
    </div>
  )
}
