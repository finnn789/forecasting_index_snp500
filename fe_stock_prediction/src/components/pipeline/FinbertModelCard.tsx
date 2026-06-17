import { CheckCircle2, XCircle, Cpu } from 'lucide-react'
import { cn } from '../../lib/utils'
import { Badge } from '../ui/badge'
import { Skeleton } from '../ui/skeleton'
import type { FinbertModelStatus } from '../../types/pipeline'

interface Props {
  status: FinbertModelStatus | null
  loading: boolean
}

export function FinbertModelCard({ status, loading }: Props) {
  if (loading) return <Skeleton className="h-40 w-full" />
  if (!status) return null

  const files = Object.entries(status.required_files)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Cpu className="size-4 text-[--color-primary]" />
          <span className="text-sm font-medium">FinBERT</span>
        </div>
        <Badge variant={status.is_available ? 'done' : 'error'} dot>
          {status.is_available ? 'Tersedia' : 'Tidak tersedia'}
        </Badge>
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs">
        <div>
          <p className="text-[--color-muted-foreground]">Sumber</p>
          <p className="font-medium">{status.source}</p>
        </div>
        <div>
          <p className="text-[--color-muted-foreground]">Ukuran Model</p>
          <p className="font-medium tabular-nums">
            {status.model_size_mb != null ? `${status.model_size_mb.toFixed(0)} MB` : '—'}
          </p>
        </div>
      </div>

      <div className="space-y-1.5">
        <p className="text-xs text-[--color-muted-foreground]">File yang diperlukan</p>
        <div className="grid grid-cols-2 gap-1.5">
          {files.map(([name, ok]) => (
            <div key={name} className="flex items-center gap-1.5 text-xs">
              {ok ? (
                <CheckCircle2 className="size-3.5 shrink-0 text-[--color-pipeline-done]" />
              ) : (
                <XCircle className="size-3.5 shrink-0 text-[--color-pipeline-error]" />
              )}
              <span className={cn('truncate font-mono', !ok && 'text-[--color-pipeline-error]')}>{name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
