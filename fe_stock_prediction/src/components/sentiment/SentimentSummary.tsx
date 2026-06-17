import { TrendingUp, TrendingDown, Minus, ArrowUpRight, ArrowDownRight } from 'lucide-react'
import { cn } from '../../lib/utils'
import type { SentimentDistribution as SentimentSummaryType } from '../../types/sentiment'
import { SentimentBadge } from '../shared/StatusBadge'

interface SentimentSummaryProps {
  summary: SentimentSummaryType
}

const trendConfig = {
  improving: {
    icon: <ArrowUpRight className="size-4" />,
    label: 'Membaik',
    color: 'text-[--color-sentiment-pos]',
  },
  declining: {
    icon: <ArrowDownRight className="size-4" />,
    label: 'Memburuk',
    color: 'text-[--color-sentiment-neg]',
  },
  stable: {
    icon: <Minus className="size-4" />,
    label: 'Stabil',
    color: 'text-[--color-muted-foreground]',
  },
}

export function SentimentSummary({ summary }: SentimentSummaryProps) {
  const trend = trendConfig[summary.trend]

  const lastDay   = summary.daily[summary.daily.length - 1]
  const totalNews = lastDay?.total ?? 0

  const pctPos = totalNews ? Math.round((lastDay.positive / totalNews) * 100) : 0
  const pctNeg = totalNews ? Math.round((lastDay.negative / totalNews) * 100) : 0
  const pctNeu = 100 - pctPos - pctNeg

  return (
    <div className="space-y-4">
      {/* Score besar */}
      <div className="flex items-end justify-between gap-3">
        <div>
          <p className="text-xs text-[--color-muted-foreground]">Rata-rata Skor Sentimen</p>
          <p
            className={cn(
              'text-4xl font-bold tabular-nums',
              summary.avgScore > 0.1  && 'text-[--color-sentiment-pos]',
              summary.avgScore < -0.1 && 'text-[--color-sentiment-neg]',
              Math.abs(summary.avgScore) <= 0.1 && 'text-[--color-muted-foreground]',
            )}
          >
            {summary.avgScore > 0 ? '+' : ''}{summary.avgScore.toFixed(2)}
          </p>
          <p className="mt-1 text-xs text-[--color-muted-foreground]">{summary.period}</p>
        </div>

        <div className="flex flex-col items-end gap-2">
          <SentimentBadge sentiment={summary.dominant} />
          <span className={cn('flex items-center gap-1 text-xs font-medium', trend.color)}>
            {trend.icon}{trend.label}
          </span>
        </div>
      </div>

      {/* Distribusi bar hari ini */}
      <div className="space-y-2">
        <p className="text-xs text-[--color-muted-foreground]">Distribusi hari ini ({totalNews} berita)</p>
        <div className="flex h-2 overflow-hidden rounded-full bg-[--color-surface-2]">
          <div className="bg-[--color-sentiment-pos] transition-[width] duration-700" style={{ width: `${pctPos}%` }} />
          <div className="bg-[--color-sentiment-neg] transition-[width] duration-700" style={{ width: `${pctNeg}%` }} />
          <div className="bg-[--color-sentiment-neu] flex-1" />
        </div>
        <div className="flex justify-between text-[10px] text-[--color-muted-foreground]">
          <span className="text-[--color-sentiment-pos]">Positif {pctPos}%</span>
          <span className="text-[--color-sentiment-neu]">Netral {pctNeu}%</span>
          <span className="text-[--color-sentiment-neg]">Negatif {pctNeg}%</span>
        </div>
      </div>

      {/* Stat grid */}
      <div className="grid grid-cols-3 gap-2">
        {[
          { icon: <TrendingUp className="size-3.5" />, label: 'Positif', value: lastDay?.positive ?? 0, color: 'text-[--color-sentiment-pos]' },
          { icon: <Minus      className="size-3.5" />, label: 'Netral',  value: lastDay?.neutral  ?? 0, color: 'text-[--color-muted-foreground]' },
          { icon: <TrendingDown className="size-3.5" />, label: 'Negatif', value: lastDay?.negative ?? 0, color: 'text-[--color-sentiment-neg]' },
        ].map(s => (
          <div key={s.label} className="rounded-[--radius-md] bg-[--color-surface-2] px-2 py-2 text-center">
            <p className={cn('flex items-center justify-center gap-1 text-xs', s.color)}>
              {s.icon}{s.label}
            </p>
            <p className="mt-0.5 text-base font-bold tabular-nums">{s.value}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
