import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Separator } from '../components/ui/separator'
import { Skeleton } from '../components/ui/skeleton'
import { PageContainer } from '../components/layout/PageContainer'
import { ErrorAlert } from '../components/shared/ErrorAlert'
import { EmptyState } from '../components/shared/EmptyState'
import { PredictionForm } from '../components/prediction/PredictionForm'
import { PredictionChart } from '../components/prediction/PredictionChart'
import { PredictionResultCard } from '../components/prediction/PredictionResultCard'
import { EnsembleBreakdown } from '../components/prediction/EnsembleBreakdown'
import { usePrediction } from '../hooks/usePrediction'
import { TrendingUp } from 'lucide-react'

export function PredictionPage() {
  const { result, loading, error, predict } = usePrediction()

  return (
    <PageContainer
      title="Prediksi Saham"
      description="Prediksi harga saham menggunakan ensemble FinBERT + LSTM."
    >
      {error && <ErrorAlert message={error} />}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left column — form + breakdown */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Parameter Prediksi</CardTitle>
            </CardHeader>
            <CardContent>
              <PredictionForm onSubmit={predict} loading={loading} />
            </CardContent>
          </Card>

          {result && (
            <Card>
              <CardHeader>
                <CardTitle>Bobot Model</CardTitle>
              </CardHeader>
              <CardContent>
                <EnsembleBreakdown ensemble={result.ensemble} />
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right column — chart + result */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Grafik Harga & Prediksi</CardTitle>
            </CardHeader>
            <CardContent>
              {loading && (
                <div className="space-y-2">
                  <Skeleton className="h-[280px] w-full" />
                  <div className="flex gap-3">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-4 w-24" />
                  </div>
                </div>
              )}
              {!loading && !result && (
                <EmptyState
                  icon={TrendingUp}
                  title="Belum ada prediksi"
                  description="Pilih ticker dan klik Prediksi Sekarang."
                />
              )}
              {!loading && result && <PredictionChart result={result} />}
            </CardContent>
          </Card>

          {(loading || result) && (
            <>
              <Separator />
              <Card>
                <CardHeader>
                  <CardTitle>Hasil Prediksi</CardTitle>
                </CardHeader>
                <CardContent>
                  {loading ? (
                    <div className="space-y-3">
                      <Skeleton className="h-10 w-48" />
                      <Skeleton className="h-px w-full" />
                      <div className="grid grid-cols-3 gap-3">
                        <Skeleton className="h-14" />
                        <Skeleton className="h-14" />
                        <Skeleton className="h-14" />
                      </div>
                    </div>
                  ) : result ? (
                    <PredictionResultCard result={result} />
                  ) : null}
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </div>
    </PageContainer>
  )
}
