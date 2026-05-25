import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { useMemo } from 'react'
import type { PredictionResult } from '../../types/prediction'

interface PredictionChartProps {
  result: PredictionResult
}

interface ChartPoint {
  date: string
  close?: number
  predicted?: number
  upper?: number
  lower?: number
  isForecast: boolean
}

const fmt = (d: string) =>
  new Date(d).toLocaleDateString('id-ID', { day: '2-digit', month: 'short' })

const currFmt = (v: number) =>
  new Intl.NumberFormat('id-ID', { notation: 'compact', maximumFractionDigits: 1 }).format(v)

export function PredictionChart({ result }: PredictionChartProps) {
  const data: ChartPoint[] = useMemo(() => {
    const history = result.history.map(h => ({
      date: h.date,
      close: h.close,
      predicted: undefined,
      upper: undefined,
      lower: undefined,
      isForecast: false,
    }))

    // Last historical point anchors the forecast line
    const last = result.history[result.history.length - 1]
    const forecast = result.forecast.map((f, i) => ({
      date: f.date,
      close: i === 0 ? last?.close : undefined,
      predicted: f.predicted,
      upper: f.upper,
      lower: f.lower,
      isForecast: true,
    }))

    return [...history, ...forecast]
  }, [result])

  const splitDate = result.forecast[0]?.date

  return (
    <ResponsiveContainer width="100%" height={280}>
      <ComposedChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="confidenceGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#6366f1" stopOpacity={0.25} />
            <stop offset="95%" stopColor="#6366f1" stopOpacity={0.02} />
          </linearGradient>
        </defs>

        <CartesianGrid
          strokeDasharray="3 3"
          stroke="oklch(28% 0.02 264)"
          vertical={false}
        />

        <XAxis
          dataKey="date"
          tickFormatter={fmt}
          tick={{ fontSize: 10, fill: 'oklch(58% 0.018 264)' }}
          axisLine={false}
          tickLine={false}
          interval="preserveStartEnd"
        />

        <YAxis
          tickFormatter={currFmt}
          tick={{ fontSize: 10, fill: 'oklch(58% 0.018 264)' }}
          axisLine={false}
          tickLine={false}
          width={52}
          domain={['auto', 'auto']}
        />

        <Tooltip
          contentStyle={{
            background: 'oklch(17% 0.018 264)',
            border: '1px solid oklch(28% 0.02 264)',
            borderRadius: '0.5rem',
            fontSize: 12,
          }}
          labelStyle={{ color: 'oklch(95% 0.01 264)', fontWeight: 600 }}
          labelFormatter={fmt}
          formatter={(value: number, name: string) => [
            value?.toLocaleString('id-ID'),
            name === 'close'     ? 'Close Aktual'  :
            name === 'predicted' ? 'Prediksi'      :
            name === 'upper'     ? 'Batas Atas'    : 'Batas Bawah',
          ]}
        />

        <Legend
          wrapperStyle={{ fontSize: 11, paddingTop: 8 }}
          formatter={(value) =>
            value === 'close' ? 'Close Aktual' : value === 'predicted' ? 'Prediksi' : 'Confidence Band'
          }
        />

        {/* Divider antara histori dan forecast */}
        {splitDate && (
          <ReferenceLine
            x={splitDate}
            stroke="oklch(58% 0.018 264)"
            strokeDasharray="4 4"
            label={{
              value: 'Prediksi →',
              position: 'insideTopRight',
              fontSize: 10,
              fill: 'oklch(58% 0.018 264)',
            }}
          />
        )}

        {/* Confidence band (area antara upper-lower) */}
        <Area
          type="monotone"
          dataKey="upper"
          stroke="none"
          fill="url(#confidenceGrad)"
          legendType="none"
          dot={false}
          activeDot={false}
          connectNulls
        />
        <Area
          type="monotone"
          dataKey="lower"
          stroke="none"
          fill="oklch(12% 0.015 264)"
          legendType="square"
          name="lower"
          dot={false}
          activeDot={false}
          connectNulls
        />

        {/* Historical close */}
        <Line
          type="monotone"
          dataKey="close"
          stroke="oklch(62% 0.2 250)"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, fill: 'oklch(62% 0.2 250)' }}
          connectNulls
        />

        {/* Forecast line */}
        <Line
          type="monotone"
          dataKey="predicted"
          stroke="oklch(72% 0.18 145)"
          strokeWidth={2}
          strokeDasharray="5 3"
          dot={(props) => {
            const { cx, cy, index } = props
            if (index !== data.length - 1) return <g key={index} />
            return (
              <circle key={index} cx={cx} cy={cy} r={5}
                fill="oklch(72% 0.18 145)" stroke="oklch(12% 0.015 264)" strokeWidth={2} />
            )
          }}
          activeDot={{ r: 4, fill: 'oklch(72% 0.18 145)' }}
          connectNulls
        />
      </ComposedChart>
    </ResponsiveContainer>
  )
}
