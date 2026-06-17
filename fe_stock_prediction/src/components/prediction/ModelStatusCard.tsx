import { CheckCircle2, XCircle } from 'lucide-react'
import { formatDate } from '../../lib/utils'
import { fmt } from '../../lib/format'
import type { ModelInfo } from '../../types/prediction'
import { Badge } from '../ui/badge'
import { Separator } from '../ui/separator'

interface ModelStatusCardProps {
  model: ModelInfo
}

export function ModelStatusCard({ model }: ModelStatusCardProps) {
  const isAvailable = model.is_available
  const metrics = model.metrics

  return (
    <div className="space-y-4">
      {/* Status badge */}
      <div className="flex items-center gap-2">
        {isAvailable ? (
          <>
            <CheckCircle2 className="size-5 text-[--color-sentiment-pos]" />
            <p className="font-medium text-[--color-sentiment-pos]">Model Tersedia</p>
          </>
        ) : (
          <>
            <XCircle className="size-5 text-[--color-sentiment-neg]" />
            <p className="font-medium text-[--color-sentiment-neg]">Model Tidak Tersedia</p>
          </>
        )}
      </div>

      <Separator />

      {/* Metadata */}
      <div className="space-y-2">
        {model.trained_at && (
          <div className="flex justify-between text-sm">
            <span className="text-[--color-muted-foreground]">Dilatih pada</span>
            <span className="font-medium">{formatDate(model.trained_at)}</span>
          </div>
        )}
        {model.window != null && (
          <div className="flex justify-between text-sm">
            <span className="text-[--color-muted-foreground]">Window</span>
            <span className="font-medium">{model.window} hari</span>
          </div>
        )}
        {model.n_features != null && (
          <div className="flex justify-between text-sm">
            <span className="text-[--color-muted-foreground]">Jumlah Fitur</span>
            <span className="font-medium">{model.n_features}</span>
          </div>
        )}
      </div>

      {/* Metrics table */}
      {metrics ? (
        <>
          <Separator />
          <div className="space-y-2">
            <p className="text-xs font-medium text-[--color-muted-foreground]">Metrik Model</p>
            <div className="grid grid-cols-2 gap-2">
              {/* Validation */}
              <div className="rounded-[--radius-md] bg-[--color-surface-2] p-2">
                <p className="text-[10px] text-[--color-muted-foreground] font-medium">Validasi</p>
                <div className="mt-1 space-y-0.5 text-[11px]">
                  <div className="flex justify-between">
                    <span>Acc</span>
                    <span className="font-mono font-semibold">{fmt(metrics.val_acc, 3)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>F1</span>
                    <span className="font-mono font-semibold">{fmt(metrics.val_f1, 3)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>AUC</span>
                    <span className="font-mono font-semibold">{fmt(metrics.val_auc, 3)}</span>
                  </div>
                </div>
              </div>

              {/* Test */}
              <div className="rounded-[--radius-md] bg-[--color-surface-2] p-2">
                <p className="text-[10px] text-[--color-muted-foreground] font-medium">Test</p>
                <div className="mt-1 space-y-0.5 text-[11px]">
                  <div className="flex justify-between">
                    <span>Acc</span>
                    <span className="font-mono font-semibold">{fmt(metrics.test_acc, 3)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>F1</span>
                    <span className="font-mono font-semibold">{fmt(metrics.test_f1, 3)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>AUC</span>
                    <span className="font-mono font-semibold">{fmt(metrics.test_auc, 3)}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      ) : null}

      {/* Features */}
      {model.features_used.length > 0 && (
        <>
          <Separator />
          <div className="space-y-1.5">
            <p className="text-xs font-medium text-[--color-muted-foreground]">Fitur</p>
            <div className="flex flex-wrap gap-1">
              {model.features_used.map(f => (
                <Badge key={f} variant="primary" className="text-xs">
                  {f}
                </Badge>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
