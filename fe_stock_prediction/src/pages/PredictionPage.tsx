import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Skeleton } from '../components/ui/skeleton'
import { PageContainer } from '../components/layout/PageContainer'
import { ErrorAlert } from '../components/shared/ErrorAlert'
import { EmptyState } from '../components/shared/EmptyState'
import { PredictionForm } from '../components/prediction/PredictionForm'
import { PredictionResultCard } from '../components/prediction/PredictionResultCard'
import { ModelStatusCard } from '../components/prediction/ModelStatusCard'
import { BacktestPanel } from '../components/prediction/BacktestPanel'
import { usePrediction } from '../hooks/usePrediction'
import { useModelStatus } from '../hooks/useModelStatus'
import { useBacktest } from '../hooks/useBacktest'
import { TrendingUp } from 'lucide-react'

export function PredictionPage() {
  const { data: result, loading: predLoading, error: predError, predict } = usePrediction()
  const { data: modelInfo, loading: modelLoading, error: modelError } = useModelStatus()
  const { data: backtest, loading: backtestLoading, error: backtestError } = useBacktest()

  // Check if model is not trained (404 error)
  const isModelNotTrained = modelError?.includes('MODEL_NOT_TRAINED') || modelError?.includes('404') || modelError?.includes('belum dilatih')

  return (
    <PageContainer
      title="Prediksi Arah Saham"
      description="Klasifikasi arah harga (naik/turun) menggunakan FinBERT + LSTM."
    >
      {/* Disclaimer banner */}
      <ErrorAlert
        variant="info"
        message="Prediksi bersifat edukatif, bukan saran finansial. Akurasi model saat ini mendekati acak."
      />

      {predError && <ErrorAlert message={predError} className="mt-4" />}

      {isModelNotTrained && (
        <EmptyState
          icon={TrendingUp}
          title="Model belum dilatih"
          description="Model LSTM belum tersedia. Silakan jalankan pipeline pelatihan terlebih dahulu."
          className="mt-6"
        />
      )}

      {!isModelNotTrained && (
        <div className="grid gap-6 mt-6 lg:grid-cols-3">
          {/* Left column — form + model status */}
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Parameter Prediksi</CardTitle>
              </CardHeader>
              <CardContent>
                <PredictionForm onSubmit={predict} loading={predLoading} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Status Model</CardTitle>
              </CardHeader>
              <CardContent>
                {modelLoading ? (
                  <div className="space-y-3">
                    <Skeleton className="h-6 w-32" />
                    <Skeleton className="h-px w-full" />
                    <Skeleton className="h-12 w-full" />
                  </div>
                ) : modelError ? (
                  <p className="text-xs text-[--color-destructive]">{modelError}</p>
                ) : modelInfo ? (
                  <ModelStatusCard model={modelInfo} />
                ) : null}
              </CardContent>
            </Card>
          </div>

          {/* Right column — prediction + backtest */}
          <div className="lg:col-span-2 space-y-4">
            {/* Prediction result card */}
            <Card>
              <CardHeader>
                <CardTitle>Hasil Prediksi</CardTitle>
              </CardHeader>
              <CardContent>
                {predLoading ? (
                  <div className="space-y-3">
                    <Skeleton className="h-10 w-48" />
                    <Skeleton className="h-px w-full" />
                    <Skeleton className="h-20 w-full" />
                  </div>
                ) : !result ? (
                  <EmptyState
                    icon={TrendingUp}
                    title="Belum ada prediksi"
                    description="Klik tombol 'Prediksi Sekarang' untuk memulai."
                  />
                ) : (
                  <PredictionResultCard result={result} />
                )}
              </CardContent>
            </Card>

            {/* Backtest panel */}
            <Card>
              <CardHeader>
                <CardTitle>Evaluasi Backtest</CardTitle>
              </CardHeader>
              <CardContent>
                {backtestLoading ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-5 gap-2">
                      {[...Array(5)].map((_, i) => (
                        <Skeleton key={i} className="h-16" />
                      ))}
                    </div>
                    <Skeleton className="h-px w-full" />
                    <Skeleton className="h-40 w-full" />
                  </div>
                ) : backtestError ? (
                  <p className="text-xs text-[--color-destructive]">{backtestError}</p>
                ) : backtest ? (
                  <BacktestPanel backtest={backtest} />
                ) : null}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </PageContainer>
  )
}
