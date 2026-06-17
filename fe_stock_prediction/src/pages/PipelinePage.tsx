import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { PageContainer } from '../components/layout/PageContainer'
import { ErrorAlert } from '../components/shared/ErrorAlert'
import { SentimentPipelineStatusCard } from '../components/pipeline/SentimentPipelineStatusCard'
import { FinbertModelCard } from '../components/pipeline/FinbertModelCard'
import { SentimentRunPanel } from '../components/pipeline/SentimentRunPanel'
import {
  useSentimentPipelineStatus,
  useFinbertStatus,
  useSentimentRun,
} from '../hooks/useSentimentPipeline'

export function PipelinePage() {
  const status = useSentimentPipelineStatus()
  const finbert = useFinbertStatus()
  // Setelah run selesai, refresh status file & jumlah headline.
  const run = useSentimentRun(() => status.refetch())

  return (
    <PageContainer
      title="Sentiment Pipeline"
      description="Status & eksekusi pipeline analisis sentimen FinBERT atas headline keuangan."
    >
      <div className="grid gap-6 lg:grid-cols-5">
        {/* Kiri: status pipeline + model */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Status Pipeline</CardTitle>
              <CardDescription>Ketersediaan data sentimen terproses</CardDescription>
            </CardHeader>
            <CardContent>
              {status.error ? (
                <ErrorAlert message={status.error} />
              ) : (
                <SentimentPipelineStatusCard status={status.data} loading={status.loading} />
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Model FinBERT</CardTitle>
              <CardDescription>Ketersediaan model inferensi sentimen</CardDescription>
            </CardHeader>
            <CardContent>
              {finbert.error ? (
                <ErrorAlert message={finbert.error} />
              ) : (
                <FinbertModelCard status={finbert.data} loading={finbert.loading} />
              )}
            </CardContent>
          </Card>
        </div>

        {/* Kanan: eksekusi + log real-time */}
        <div className="lg:col-span-3">
          <Card>
            <CardHeader>
              <CardTitle>Jalankan Pipeline</CardTitle>
              <CardDescription>
                Streaming progres FinBERT (loading → inference → aggregating → saving)
              </CardDescription>
            </CardHeader>
            <CardContent>
              {run.error && <ErrorAlert message={run.error} className="mb-4" />}
              <SentimentRunPanel controller={run} />
            </CardContent>
          </Card>
        </div>
      </div>
    </PageContainer>
  )
}
