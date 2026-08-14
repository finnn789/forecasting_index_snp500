import Card, { CardHeader, CardTitle, CardContent } from '../Card'
import Icon from '../Icon'
import { cn } from '../../utils/cn'
import { useDataAnalysis } from '../../hooks/useDataAnalysis'

const NEWS_PATH = '/live/news/latest?n=10'

const SENTIMENT_STYLES = {
  positive: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  negative: 'bg-red-50 text-red-700 border-red-200',
  neutral: 'bg-slate-100 text-slate-600 border-slate-200',
}

function SentimentBadge({ label }) {
  return (
    <span
      className={cn(
        'shrink-0 rounded-full border px-2 py-0.5 text-xs font-medium capitalize',
        SENTIMENT_STYLES[label] ?? SENTIMENT_STYLES.neutral,
      )}
    >
      {label}
    </span>
  )
}

export default function LatestNewsCard({ refreshKey = 0 }) {
  const news = useDataAnalysis(refreshKey ? `${NEWS_PATH}&_r=${refreshKey}` : NEWS_PATH)
  const headlines = news.data?.headlines ?? []
  const dailySentiment = news.data?.daily_sentiment ?? []
  const accumulatedDays = news.data?.accumulated_days

  return (
    <Card>
      <CardHeader>
        <CardTitle>Berita Terkini (S&P 500)</CardTitle>
        {typeof accumulatedDays === 'number' && (
          <span className="text-xs text-slate-400">
            {accumulatedDays} hari sentimen terakumulasi
          </span>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        {news.loading && (
          <div className="flex h-16 items-center gap-2 text-sm text-slate-400">
            <Icon name="progress_activity" className="animate-spin text-lg" />
            Mengambil berita terbaru...
          </div>
        )}

        {news.error && (
          <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
            <Icon name="error" className="text-lg" />
            {news.error}
          </div>
        )}

        {dailySentiment.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {dailySentiment.map((d) => (
              <div
                key={d.date}
                className="flex items-center gap-2 rounded border border-slate-200 px-3 py-1.5 text-xs"
              >
                <span className="font-mono text-slate-500">{d.date}</span>
                <span className="text-slate-400">·</span>
                <span className="text-slate-500">{d.headline_count} berita</span>
                <SentimentBadge label={d.sentiment_label} />
              </div>
            ))}
          </div>
        )}

        {headlines.length > 0 && (
          <ul className="divide-y divide-slate-100">
            {headlines.map((h, i) => (
              <li key={`${h.date}-${i}`} className="flex items-start justify-between gap-3 py-2.5">
                <div className="min-w-0">
                  <p className="truncate text-sm text-slate-800">{h.title}</p>
                  <p className="mt-0.5 font-mono text-xs text-slate-400">{h.date}</p>
                </div>
                <SentimentBadge label={h.sentiment_label} />
              </li>
            ))}
          </ul>
        )}

        {!news.loading && !news.error && headlines.length === 0 && (
          <p className="text-sm text-slate-400">Tidak ada berita ditemukan.</p>
        )}
      </CardContent>
    </Card>
  )
}
