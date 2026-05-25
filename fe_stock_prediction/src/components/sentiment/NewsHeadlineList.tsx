import { ExternalLink } from 'lucide-react'
import { cn } from '../../lib/utils'
import { formatDate } from '../../lib/utils'
import { SentimentBadge } from '../shared/StatusBadge'
import type { NewsItem } from '../../types/sentiment'

interface NewsHeadlineListProps {
  items: NewsItem[]
}

const scoreBar = (score: number) => {
  const pct  = Math.round(((score + 1) / 2) * 100)
  const color =
    score >  0.1 ? 'bg-[--color-sentiment-pos]' :
    score < -0.1 ? 'bg-[--color-sentiment-neg]' :
                   'bg-[--color-sentiment-neu]'
  return { pct, color }
}

export function NewsHeadlineList({ items }: NewsHeadlineListProps) {
  if (!items.length) return (
    <p className="py-6 text-center text-sm text-[--color-muted-foreground]">
      Tidak ada berita tersedia.
    </p>
  )

  return (
    <ul className="divide-y divide-[--color-border]">
      {items.map(item => {
        const { pct, color } = scoreBar(item.score)
        return (
          <li key={item.id} className="group flex gap-3 py-3">
            {/* Score bar di kiri */}
            <div className="flex w-1 shrink-0 flex-col overflow-hidden rounded-full bg-[--color-surface-2]">
              <div
                className={cn('w-full rounded-full transition-[height] duration-500', color)}
                style={{ height: `${pct}%` }}
              />
            </div>

            <div className="min-w-0 flex-1 space-y-1">
              {/* Judul */}
              <p className="text-sm leading-snug text-[--color-foreground] line-clamp-2">
                {item.title}
              </p>

              {/* Meta row */}
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs text-[--color-muted-foreground]">
                  {item.source}
                </span>
                <span className="text-[--color-border]">·</span>
                <span className="text-xs text-[--color-muted-foreground]">
                  {formatDate(item.date)}
                </span>
                <SentimentBadge sentiment={item.sentiment} />
                <span className="ml-auto text-xs tabular-nums text-[--color-muted-foreground]">
                  {item.score > 0 ? '+' : ''}{item.score.toFixed(2)}
                </span>
              </div>
            </div>

            <ExternalLink className="size-3.5 shrink-0 self-start text-[--color-muted-foreground] opacity-0 group-hover:opacity-100 transition-opacity mt-0.5" />
          </li>
        )
      })}
    </ul>
  )
}
