import { useEffect, useState } from 'react'
import { formatDate, formatDuration } from '../../lib/utils'
import { PipelineStatusBadge } from '../shared/StatusBadge'
import { Skeleton } from '../ui/skeleton'
import { EmptyState } from '../shared/EmptyState'
import { ScrollText } from 'lucide-react'
import { getPipelineHistory } from '../../lib/api/pipeline.api'
import type { RunHistoryItem } from '../../types/pipeline'

export function RunHistoryTable() {
  const [history, setHistory] = useState<RunHistoryItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getPipelineHistory()
      .then(setHistory)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 3 }, (_, i) => <Skeleton key={i} className="h-12 w-full" />)}
      </div>
    )
  }

  if (!history.length) {
    return (
      <EmptyState
        icon={ScrollText}
        title="Belum ada riwayat run"
        description="Riwayat akan muncul setelah pipeline dijalankan."
      />
    )
  }

  return (
    <div className="overflow-x-auto rounded-[--radius-lg] border border-[--color-border]">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[--color-border] bg-[--color-surface-2] text-left">
            <th className="px-4 py-3 text-xs font-medium text-[--color-muted-foreground]">Run ID</th>
            <th className="px-4 py-3 text-xs font-medium text-[--color-muted-foreground]">Waktu Mulai</th>
            <th className="px-4 py-3 text-xs font-medium text-[--color-muted-foreground]">Durasi</th>
            <th className="px-4 py-3 text-xs font-medium text-[--color-muted-foreground]">Status</th>
            <th className="px-4 py-3 text-xs font-medium text-[--color-muted-foreground]">Keterangan</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[--color-border]">
          {history.map(run => (
            <tr key={run.runId} className="bg-[--color-card] hover:bg-[--color-surface-2] transition-colors">
              <td className="px-4 py-3 font-mono text-xs text-[--color-muted-foreground]">
                {run.runId}
              </td>
              <td className="px-4 py-3 text-xs">{formatDate(run.startedAt)}</td>
              <td className="px-4 py-3 text-xs tabular-nums text-[--color-muted-foreground]">
                {run.durationMs !== undefined ? formatDuration(run.durationMs) : '—'}
              </td>
              <td className="px-4 py-3">
                <PipelineStatusBadge state={run.state} />
              </td>
              <td className="px-4 py-3 text-xs text-[--color-muted-foreground] max-w-xs truncate">
                {run.errorMessage ?? '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
