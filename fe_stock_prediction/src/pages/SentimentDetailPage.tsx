import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Skeleton } from '../components/ui/skeleton'
import { PageContainer } from '../components/layout/PageContainer'
import { ErrorAlert } from '../components/shared/ErrorAlert'
import { EmptyState } from '../components/shared/EmptyState'
// import { SentimentSummary } from '../components/sentiment/SentimentSummary'
// import { SentimentChart } from '../components/sentiment/SentimentChart'
import { SentimentDistributionChart } from '../components/sentiment/SentimentDistributionChart'
// import { NewsHeadlineList } from '../components/sentiment/NewsHeadlineList'
import { useSentiment } from '../hooks/useSentiment'
import { TICKERS } from '../lib/constants'
import { Newspaper } from 'lucide-react'

export function SentimentDetailPage() {
  const ticker = TICKERS[0].value
  const { data: sentiment, loading, error } = useSentiment(ticker)
  console.log('Sentiment data:', sentiment)
  return (
    <PageContainer
      title="Analisis Sentimen"
      description="Tren sentimen berita dan media"
    >
      {error && <ErrorAlert message={error} />}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-1">
          {loading && (
            <div className="space-y-4">
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-32 w-full" />
            </div>
          )}
          {/* {sentiment && <SentimentSummary summary={sentiment} />} */}
          {!loading && !sentiment && !error && (
            <EmptyState
              icon={Newspaper}
              title="Belum ada data"
              description="Sentimen tidak tersedia untuk ticker ini."
            />
          )}
        </div>

        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Tren Harian</CardTitle>
            </CardHeader>
            <CardContent>
              {loading && <Skeleton className="h-64 w-full" />}
              {/* {sentiment && <SentimentChart data={sentiment.daily} />} */}
              {!loading && !sentiment && !error && (
                <EmptyState
                  icon={Newspaper}
                  title="Belum ada data"
                  description="Tren sentimen tidak tersedia untuk ticker ini."
                />
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Distribusi Sentimen */}
      {sentiment && (
        <SentimentDistributionChart
          data={{
            data: sentiment.data,
            sentiment_score_mean: sentiment.sentiment_score_mean,
            sentiment_score_std: sentiment.sentiment_score_std,
            plot_hint: sentiment.plot_hint,
          }}
          loading={loading}
        />
      )}

      <Card>
        <CardHeader>
          <CardTitle>Berita Terkini</CardTitle>
        </CardHeader>
        <CardContent>
          {loading && (
            <div className="space-y-2">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          )}
          {/* {sentiment && <NewsHeadlineList items={sentiment.recentNews} />} */}
          {!loading && !sentiment && !error && (
            <EmptyState
              icon={Newspaper}
              title="Belum ada berita"
              description="Tidak ada berita terkini untuk ticker ini."
            />
          )}
        </CardContent>
      </Card>
    </PageContainer>
  )
}
