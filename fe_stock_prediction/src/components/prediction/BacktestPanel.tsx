import {
  ComposedChart,
  Line,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { fmt } from '../../lib/format'
import type { BacktestResult } from '../../types/prediction'
import { Separator } from '../ui/separator'

interface BacktestPanelProps {
  backtest: BacktestResult
}

// Approximate hex values matching index.css oklch tokens
const C = {
  grid:    'rgba(255,255,255,0.06)',
  tick:    'rgba(255,255,255,0.45)',
  pos:     '#4ade80',    // sentiment-pos / pipeline-done
  neg:     '#f87171',    // sentiment-neg / pipeline-error
  neutral: '#94a3b8',    // muted
  tooltip: { bg: '#1a1d2e', border: '#2d3058', label: '#e2e8f0' },
}

const tooltipStyle = {
  contentStyle: { backgroundColor: C.tooltip.bg, border: `1px solid ${C.tooltip.border}`, borderRadius: 8, fontSize: 12 },
  labelStyle:   { color: C.tooltip.label },
}

const axisProps = {
  tick:     { fill: C.tick, fontSize: 11 },
  tickLine: false as const,
  axisLine: false as const,
}

export function BacktestPanel({ backtest }: BacktestPanelProps) {
  const metrics = backtest.metrics
  const cm = backtest.confusion_matrix
  const points = backtest.points || []

  // Custom dot: hijau jika correct, merah jika salah
  const CustomDot = (props: any) => {
    const { cx, cy, payload } = props
    if (payload && typeof cx === 'number' && typeof cy === 'number') {
      const color = payload.correct ? C.pos : C.neg
      return (
        <circle cx={cx} cy={cy} r={3.5} fill={color} opacity={0.8} />
      )
    }
    return null
  }

  return (
    <div className="space-y-6">
      {/* Metric cards */}
      <div className="grid grid-cols-5 gap-2">
        {[
          { label: 'Akurasi', key: 'accuracy', decimals: 3 },
          { label: 'Presisi', key: 'precision', decimals: 3 },
          { label: 'Recall', key: 'recall', decimals: 3 },
          { label: 'F1', key: 'f1', decimals: 3 },
          { label: 'AUC', key: 'auc', decimals: 3 },
        ].map(m => (
          <div key={m.key} className="rounded-[--radius-md] bg-[--color-surface-2] p-2 text-center">
            <p className="text-[10px] text-[--color-muted-foreground]">{m.label}</p>
            <p className="mt-0.5 text-sm font-semibold tabular-nums">
              {fmt(metrics[m.key], m.decimals)}
            </p>
          </div>
        ))}
      </div>

      <Separator />

      {/* Confusion Matrix */}
      <div className="space-y-2">
        <p className="text-xs font-medium text-[--color-muted-foreground]">Confusion Matrix (Test Split)</p>
        <div className="grid grid-cols-2 gap-2">
          {/* TP */}
          <div className="rounded-[--radius-md] bg-[--color-sentiment-pos]/10 border border-[--color-sentiment-pos]/30 p-3">
            <p className="text-[10px] text-[--color-muted-foreground]">True Positive</p>
            <p className="mt-1 text-lg font-bold text-[--color-sentiment-pos] tabular-nums">{cm.tp}</p>
          </div>

          {/* FP */}
          <div className="rounded-[--radius-md] bg-[--color-sentiment-neg]/10 border border-[--color-sentiment-neg]/30 p-3">
            <p className="text-[10px] text-[--color-muted-foreground]">False Positive</p>
            <p className="mt-1 text-lg font-bold text-[--color-sentiment-neg] tabular-nums">{cm.fp}</p>
          </div>

          {/* FN */}
          <div className="rounded-[--radius-md] bg-[--color-sentiment-neg]/10 border border-[--color-sentiment-neg]/30 p-3">
            <p className="text-[10px] text-[--color-muted-foreground]">False Negative</p>
            <p className="mt-1 text-lg font-bold text-[--color-sentiment-neg] tabular-nums">{cm.fn}</p>
          </div>

          {/* TN */}
          <div className="rounded-[--radius-md] bg-[--color-sentiment-pos]/10 border border-[--color-sentiment-pos]/30 p-3">
            <p className="text-[10px] text-[--color-muted-foreground]">True Negative</p>
            <p className="mt-1 text-lg font-bold text-[--color-sentiment-pos] tabular-nums">{cm.tn}</p>
          </div>
        </div>
        <p className="text-[10px] text-[--color-muted-foreground] italic mt-2">
          ⚠️ Model cenderung selalu memprediksi "naik" — TN sangat kecil.
        </p>
      </div>

      <Separator />

      {/* Backtest chart */}
      <div className="space-y-2">
        <p className="text-xs font-medium text-[--color-muted-foreground]">Harga vs Prediksi (Test Split)</p>
        {points.length > 0 ? (
          <ResponsiveContainer width="100%" height={240}>
            <ComposedChart data={points} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.grid} />
              <XAxis dataKey="date" {...axisProps} />
              <YAxis {...axisProps} />
              <Tooltip {...tooltipStyle} />
              <Line
                type="monotone"
                dataKey="close"
                stroke={C.neutral}
                strokeWidth={2}
                dot={false}
                name="Harga Aktual"
              />
              <Scatter
                name="Prediksi (hijau=benar, merah=salah)"
                dataKey="close"
                fill={C.pos}
                shape={<CustomDot />}
              />
            </ComposedChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-40 flex items-center justify-center text-[--color-muted-foreground] text-sm">
            Tidak ada data backtest
          </div>
        )}
      </div>
    </div>
  )
}
