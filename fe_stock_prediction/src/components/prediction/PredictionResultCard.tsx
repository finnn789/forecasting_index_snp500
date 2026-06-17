import { TrendingUp, TrendingDown } from 'lucide-react'
import { cn, formatDate } from '../../lib/utils'
import type { DirectionPrediction } from '../../types/prediction'
import { Separator } from '../ui/separator'
import { Badge } from '../ui/badge'

interface PredictionResultCardProps {
  result: DirectionPrediction
}

export function PredictionResultCard({ result }: PredictionResultCardProps) {
  const isUp = result.direction === 'up'
  const isDown = result.direction === 'down'
  const isWeakSignal = result.confidence < 0.55

  // Probability gauge: 0-100%
  const probPercent = (result.probability_up * 100).toFixed(1)
  const confPercent = (result.confidence * 100).toFixed(1)

  return (
    <div className="space-y-4">
      {/* Main direction badge + gauge */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs text-[--color-muted-foreground] mb-2">{result.ticker}</p>
          <div className="flex items-center gap-2">
            <div
              className={cn(
                'flex items-center gap-1.5 rounded-[--radius-lg] px-3 py-2 text-sm font-semibold',
                isUp && !isWeakSignal && 'bg-[--color-sentiment-pos]/15 text-[--color-sentiment-pos]',
                isDown && !isWeakSignal && 'bg-[--color-sentiment-neg]/15 text-[--color-sentiment-neg]',
                isWeakSignal && 'bg-[--color-surface-2] text-[--color-muted-foreground]',
              )}
            >
              {isUp && <TrendingUp className="size-4" />}
              {isDown && <TrendingDown className="size-4" />}
              {isUp ? 'Naik' : 'Turun'}
            </div>
            {isWeakSignal && <Badge variant="error" className="text-xs">Sinyal Lemah</Badge>}
          </div>
          <p className="text-xs text-[--color-muted-foreground] mt-2">
            Dari {formatDate(result.as_of_date)} → {formatDate(result.target_date)}
          </p>
        </div>
      </div>

      <Separator />

      {/* Probability gauge */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <p className="text-xs font-medium text-[--color-muted-foreground]">Probabilitas Naik</p>
          <p className="text-sm font-semibold tabular-nums">{probPercent}%</p>
        </div>
        <div className="relative h-2 overflow-hidden rounded-full bg-[--color-surface-2]">
          <div
            className="absolute inset-y-0 left-0 bg-gradient-to-r from-[--color-sentiment-neg] to-[--color-sentiment-pos]"
            style={{ width: `${result.probability_up * 100}%` }}
          />
        </div>
        <div className="flex justify-between text-[10px] text-[--color-muted-foreground]">
          <span>0%</span>
          <span>50% (random)</span>
          <span>100%</span>
        </div>
      </div>

      <Separator />

      {/* Confidence & features */}
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-[--radius-md] bg-[--color-surface-2] px-3 py-2 text-center">
          <p className="text-xs text-[--color-muted-foreground]">Keyakinan</p>
          <p className="mt-1 text-sm font-semibold tabular-nums">{confPercent}%</p>
        </div>
        <div className="rounded-[--radius-md] bg-[--color-surface-2] px-3 py-2 text-center">
          <p className="text-xs text-[--color-muted-foreground]">Window</p>
          <p className="mt-1 text-sm font-semibold tabular-nums">{result.window} hari</p>
        </div>
      </div>

      {/* Features used */}
      <div className="space-y-1.5">
        <p className="text-xs font-medium text-[--color-muted-foreground]">Fitur yang Digunakan</p>
        <div className="flex flex-wrap gap-1">
          {result.features_used.map(f => (
            <Badge key={f} variant="primary" className="text-xs">
              {f}
            </Badge>
          ))}
        </div>
      </div>
    </div>
  )
}
