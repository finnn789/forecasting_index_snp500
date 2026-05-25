import { Brain, BarChart2, ShieldCheck } from 'lucide-react'
import { cn } from '../../lib/utils'
import type { EnsembleWeight } from '../../types/prediction'

interface EnsembleBreakdownProps {
  ensemble: EnsembleWeight
}

export function EnsembleBreakdown({ ensemble }: EnsembleBreakdownProps) {
  const lstmPct      = Math.round(ensemble.lstmWeight * 100)
  const sentimentPct = Math.round(ensemble.sentimentWeight * 100)
  const confidencePct = Math.round(ensemble.confidence * 100)

  return (
    <div className="space-y-4">
      <p className="text-xs font-medium text-[--color-muted-foreground] uppercase tracking-wide">
        Bobot Ensemble
      </p>

      {/* Weight bars */}
      <div className="space-y-3">
        <WeightRow
          icon={<BarChart2 className="size-4" />}
          label="LSTM (OHLCV)"
          pct={lstmPct}
          color="bg-[--color-primary]"
        />
        <WeightRow
          icon={<Brain className="size-4" />}
          label="FinBERT (Sentimen)"
          pct={sentimentPct}
          color="bg-[--color-sentiment-neu]"
        />
      </div>

      {/* Confidence */}
      <div className="flex items-center gap-2 rounded-[--radius-md] border border-[--color-border] bg-[--color-surface-2] px-3 py-2">
        <ShieldCheck
          className={cn(
            'size-4 shrink-0',
            confidencePct >= 70 ? 'text-[--color-pipeline-done]' :
            confidencePct >= 45 ? 'text-[--color-pipeline-running]' :
            'text-[--color-pipeline-error]',
          )}
        />
        <div className="flex-1">
          <p className="text-xs text-[--color-muted-foreground]">Confidence Model</p>
          <p className="text-sm font-semibold">{confidencePct}%</p>
        </div>
        <div className="h-8 w-px bg-[--color-border]" />
        <p className={cn(
          'text-xs font-medium',
          confidencePct >= 70 ? 'text-[--color-pipeline-done]' :
          confidencePct >= 45 ? 'text-[--color-pipeline-running]' :
          'text-[--color-pipeline-error]',
        )}>
          {confidencePct >= 70 ? 'Tinggi' : confidencePct >= 45 ? 'Sedang' : 'Rendah'}
        </p>
      </div>
    </div>
  )
}

function WeightRow({
  icon, label, pct, color,
}: { icon: React.ReactNode; label: string; pct: number; color: string }) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="flex items-center gap-1.5 text-[--color-foreground]">
          <span className="text-[--color-muted-foreground]">{icon}</span>
          {label}
        </span>
        <span className="tabular-nums font-medium">{pct}%</span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-[--color-surface-2] overflow-hidden">
        <div
          className={cn('h-full rounded-full transition-[width] duration-700', color)}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
