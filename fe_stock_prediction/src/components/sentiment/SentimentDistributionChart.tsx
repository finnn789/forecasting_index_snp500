import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Skeleton } from '../ui/skeleton'
import { formatNumber, fmt } from '../../lib/format'
import type { SentimentDistribution, SentimentLabel } from '../../types/sentiment'

interface SentimentDistributionChartProps {
  data: Pick<SentimentDistribution, 'data' | 'sentiment_score_mean' | 'sentiment_score_std' | 'plot_hint'>
  loading?: boolean
}

type ChartDataItem = {
  name: SentimentLabel
  count: number
  pct: number
}

export function SentimentDistributionChart({
  data,
  loading = false,
}: SentimentDistributionChartProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Distribusi Sentimen</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-64 w-full rounded-[--radius-md]" />
          <div className="grid grid-cols-3 gap-2">
            <Skeleton className="h-6 w-full rounded-[--radius-md]" />
            <Skeleton className="h-6 w-full rounded-[--radius-md]" />
            <Skeleton className="h-6 w-full rounded-[--radius-md]" />
          </div>
        </CardContent>
      </Card>
    )
  }

  const chartData: ChartDataItem[] = data.data.map((item) => ({
    name: item.label,
    count: item.count,
    pct: item.pct,
  }))

  const totalCount = data.data.reduce((sum, item) => sum + item.count, 0)

  const CustomTooltip = ({
    active,
    payload,
  }: {
    active?: boolean
    payload?: Array<{ value: number; name: string }>
  }) => {
    if (!active || !payload || payload.length === 0) {
      return null
    }

    const dataPoint = chartData.find((d) => d.name === payload[0].name)
    if (!dataPoint) {
      return null
    }

    return (
      <div className="rounded-[--radius-md] border border-[--color-border] bg-[--color-surface] p-3 text-xs">
        <p className="font-semibold capitalize text-[--color-foreground]">{dataPoint.name}</p>
        <p className="text-[--color-muted-foreground]">
          Count: {formatNumber(dataPoint.count)}
        </p>
        <p className="text-[--color-muted-foreground]">
          {fmt(dataPoint.pct, 2)}%
        </p>
      </div>
    )
  }

  const LegendFormatter = (value: string) => {
    const labelMap = {
      neutral: 'Netral',
      positive: 'Positif',
      negative: 'Negatif',
    } as const
    return labelMap[value as SentimentLabel] || value
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Distribusi Sentimen</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Chart Area */}
        <ResponsiveContainer width="100%" height={300}>
          <BarChart
            data={chartData}
            margin={{ top: 8, right: 16, left: 0, bottom: 0 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="oklch(28% 0.02 264)"
              vertical={false}
            />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 12, fill: 'oklch(58% 0.018 264)' }}
              axisLine={false}
              tickLine={false}
              tickFormatter={LegendFormatter}
            />
            <YAxis
              tick={{ fontSize: 10, fill: 'oklch(58% 0.018 264)' }}
              axisLine={false}
              tickLine={false}
              width={40}
              allowDecimals={false}
              tickFormatter={(v) => formatNumber(v)}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: 11, paddingTop: 12 }}
              formatter={LegendFormatter}
            />
            <Bar
              dataKey="count"
              fill="oklch(62% 0.2 250)"
              radius={[6, 6, 0, 0]}
              isAnimationActive={true}
            />
          </BarChart>
        </ResponsiveContainer>

        {/* Stats Footer */}
        <div className="border-t border-[--color-border] pt-4">
          <div className="grid grid-cols-3 gap-4 text-sm">
            {/* Mean */}
            <div className="flex flex-col gap-1">
              <p className="text-[--color-muted-foreground]">📊 Mean</p>
              <p className="font-semibold text-[--color-foreground]">
                {fmt(data.sentiment_score_mean, 4)}
              </p>
            </div>

            {/* Std Dev */}
            <div className="flex flex-col gap-1">
              <p className="text-[--color-muted-foreground]">📈 Std Dev</p>
              <p className="font-semibold text-[--color-foreground]">
                {fmt(data.sentiment_score_std, 4)}
              </p>
            </div>

            {/* Total Count */}
            <div className="flex flex-col gap-1">
              <p className="text-[--color-muted-foreground]">📋 Total</p>
              <p className="font-semibold text-[--color-foreground]">
                {formatNumber(totalCount)}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
