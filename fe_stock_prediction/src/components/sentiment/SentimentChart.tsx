import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import type { ValueType, NameType } from 'recharts/types/component/DefaultTooltipContent'
import type { DailySentiment } from '../../types/sentiment'

interface SentimentChartProps {
  data: DailySentiment[]
}

const fmt = (d: unknown) =>
  typeof d === 'string'
    ? new Date(d).toLocaleDateString('id-ID', { day: '2-digit', month: 'short' })
    : String(d)

export function SentimentChart({ data }: SentimentChartProps) {
  /* Tampilkan 30 titik terakhir agar chart tidak terlalu padat */
  const visible = data.slice(-30)

  return (
    <ResponsiveContainer width="100%" height={240}>
      <ComposedChart data={visible} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
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
          interval={4}
        />

        {/* Sumbu kiri: jumlah berita (bar) */}
        <YAxis
          yAxisId="count"
          orientation="left"
          tick={{ fontSize: 10, fill: 'oklch(58% 0.018 264)' }}
          axisLine={false}
          tickLine={false}
          width={28}
          allowDecimals={false}
        />

        {/* Sumbu kanan: skor sentimen rata-rata (-1 s/d 1) */}
        <YAxis
          yAxisId="score"
          orientation="right"
          domain={[-1, 1]}
          tick={{ fontSize: 10, fill: 'oklch(58% 0.018 264)' }}
          axisLine={false}
          tickLine={false}
          width={32}
          tickFormatter={v => v.toFixed(1)}
        />

        <ReferenceLine yAxisId="score" y={0} stroke="oklch(40% 0.02 264)" strokeDasharray="3 3" />

        <Tooltip
          contentStyle={{
            background: 'oklch(17% 0.018 264)',
            border: '1px solid oklch(28% 0.02 264)',
            borderRadius: '0.5rem',
            fontSize: 12,
          }}
          labelStyle={{ color: 'oklch(95% 0.01 264)', fontWeight: 600 }}
          labelFormatter={fmt}
          formatter={(value: ValueType | undefined, name: NameType | undefined) => {
            const labels = {
              positive: 'Positif',
              negative: 'Negatif',
              neutral:  'Netral',
              avgScore: 'Skor Rata-rata',
            } as const
            const labelKey = name as keyof typeof labels | undefined
            return [
              typeof value === 'number' && name === 'avgScore' ? value.toFixed(3) : value,
              labelKey && labelKey in labels ? labels[labelKey] : name,
            ]
          }}
        />

        <Legend
          wrapperStyle={{ fontSize: 11, paddingTop: 8 }}
          formatter={(v) => {
            const labels = { positive: 'Positif', negative: 'Negatif', neutral: 'Netral', avgScore: 'Skor Rata-rata' } as const
            const key = v as keyof typeof labels | string
            return (key in labels ? labels[key as keyof typeof labels] : v) ?? v
          }}
        />

        {/* Stacked bars — jumlah berita per kategori */}
        <Bar yAxisId="count" dataKey="positive" stackId="a" fill="oklch(72% 0.18 145)" radius={[0,0,0,0]} barSize={8} />
        <Bar yAxisId="count" dataKey="neutral"  stackId="a" fill="oklch(58% 0.05 250)" barSize={8} />
        <Bar yAxisId="count" dataKey="negative" stackId="a" fill="oklch(62% 0.22 27)"  radius={[2,2,0,0]} barSize={8} />

        {/* Garis skor rata-rata harian */}
        <Line
          yAxisId="score"
          type="monotone"
          dataKey="avgScore"
          stroke="oklch(78% 0.18 85)"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4 }}
        />
      </ComposedChart>
    </ResponsiveContainer>
  )
}
