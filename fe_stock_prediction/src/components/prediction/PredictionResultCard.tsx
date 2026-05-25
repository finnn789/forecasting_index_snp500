import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { cn } from '../../lib/utils'
import type { PredictionResult } from '../../types/prediction'
import { Separator } from '../ui/separator'

interface PredictionResultCardProps {
  result: PredictionResult
}

export function PredictionResultCard({ result }: PredictionResultCardProps) {
  const isUp   = result.direction === 'up'
  const isDown = result.direction === 'down'

  return (
    <div className="space-y-4">
      {/* Main prediction */}
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-xs text-[--color-muted-foreground]">{result.ticker}</p>
          <p className="text-3xl font-bold tabular-nums">
            {result.predictedClose.toLocaleString('id-ID')}
          </p>
          <p className="text-xs text-[--color-muted-foreground] mt-0.5">
            Prediksi untuk {result.predictionDate}
          </p>
        </div>
        <div
          className={cn(
            'flex items-center gap-1.5 rounded-[--radius-lg] px-3 py-2 text-sm font-semibold',
            isUp   && 'bg-[--color-pipeline-done]/15 text-[--color-pipeline-done]',
            isDown && 'bg-[--color-pipeline-error]/15 text-[--color-pipeline-error]',
            !isUp && !isDown && 'bg-[--color-surface-2] text-[--color-muted-foreground]',
          )}
        >
          {isUp   && <TrendingUp  className="size-4" />}
          {isDown && <TrendingDown className="size-4" />}
          {!isUp && !isDown && <Minus className="size-4" />}
          {isUp ? '+' : ''}{result.change.toFixed(2)}%
        </div>
      </div>

      <Separator />

      {/* Metrics */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'RMSE', value: result.metrics.rmse.toFixed(1) },
          { label: 'MAE',  value: result.metrics.mae.toFixed(1)  },
          { label: 'MAPE', value: `${result.metrics.mape.toFixed(2)}%` },
        ].map(m => (
          <div key={m.label} className="rounded-[--radius-md] bg-[--color-surface-2] px-3 py-2 text-center">
            <p className="text-xs text-[--color-muted-foreground]">{m.label}</p>
            <p className="mt-0.5 text-sm font-semibold tabular-nums">{m.value}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
