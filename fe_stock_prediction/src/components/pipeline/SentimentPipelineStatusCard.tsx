import { CheckCircle2, XCircle, FileText, CalendarRange } from 'lucide-react'
import { cn } from '../../lib/utils'
import { Skeleton } from '../ui/skeleton'
import { formatNumber } from '../../lib/format'
import type { SentimentPipelineStatus } from '../../types/pipeline'

interface Props {
  status: SentimentPipelineStatus | null
  loading: boolean
}

function FileBadge({ ok, label }: { ok: boolean; label: string }) {
  return (
    <div className="flex items-center gap-2 rounded-[--radius-md] bg-[--color-surface-2] px-3 py-2">
      {ok ? (
        <CheckCircle2 className="size-4 text-[--color-pipeline-done]" />
      ) : (
        <XCircle className="size-4 text-[--color-pipeline-error]" />
      )}
      <div className="min-w-0">
        <p className="truncate text-xs font-medium">{label}</p>
        <p className={cn('text-[10px]', ok ? 'text-[--color-pipeline-done]' : 'text-[--color-pipeline-error]')}>
          {ok ? 'Tersedia' : 'Belum ada'}
        </p>
      </div>
    </div>
  )
}

export function SentimentPipelineStatusCard({ status, loading }: Props) {
  if (loading) return <Skeleton className="h-40 w-full" />
  if (!status) return null

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <FileBadge ok={status.clean_file_exists} label="headlines_clean.csv" />
        <FileBadge ok={status.daily_file_exists} label="daily_sentiment.csv" />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-[--radius-md] border border-[--color-border] px-3 py-2.5">
          <p className="flex items-center gap-1.5 text-xs text-[--color-muted-foreground]">
            <FileText className="size-3.5" /> Total Headline
          </p>
          <p className="mt-1 text-lg font-semibold tabular-nums">
            {status.total_headlines != null ? formatNumber(status.total_headlines) : '—'}
          </p>
        </div>
        <div className="rounded-[--radius-md] border border-[--color-border] px-3 py-2.5">
          <p className="flex items-center gap-1.5 text-xs text-[--color-muted-foreground]">
            <CalendarRange className="size-3.5" /> Total Hari
          </p>
          <p className="mt-1 text-lg font-semibold tabular-nums">
            {status.total_days != null ? formatNumber(status.total_days) : '—'}
          </p>
        </div>
      </div>

      {(status.date_range.start || status.date_range.end) && (
        <p className="text-xs text-[--color-muted-foreground]">
          Rentang data: <span className="text-[--color-foreground]">{status.date_range.start ?? '—'}</span>
          {' → '}
          <span className="text-[--color-foreground]">{status.date_range.end ?? '—'}</span>
        </p>
      )}
    </div>
  )
}
