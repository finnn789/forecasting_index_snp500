import { Play, Square, RefreshCw } from 'lucide-react'
import { useState } from 'react'
import { Button } from '../ui/button'
import { Progress } from '../ui/progress'
import { PipelineStatusBadge } from '../shared/StatusBadge'
import { Skeleton } from '../ui/skeleton'
import { runPipeline, stopPipeline } from '../../lib/api/pipeline.api'
import type { PipelineStatus } from '../../types/pipeline'

interface PipelineControlPanelProps {
  status: PipelineStatus | null
  loading: boolean
  onRefresh: () => void
}

export function PipelineControlPanel({ status, loading, onRefresh }: PipelineControlPanelProps) {
  const [actionLoading, setActionLoading] = useState(false)

  const handleRun = async () => {
    setActionLoading(true)
    try {
      await runPipeline()
      onRefresh()
    } finally {
      setActionLoading(false)
    }
  }

  const handleStop = async () => {
    setActionLoading(true)
    try {
      await stopPipeline()
      onRefresh()
    } finally {
      setActionLoading(false)
    }
  }

  const isRunning = status?.state === 'running'

  return (
    <div className="space-y-4">
      {/* Status row */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          {loading ? (
            <Skeleton className="h-6 w-24" />
          ) : status ? (
            <>
              <PipelineStatusBadge state={status.state} />
              <span className="text-xs text-[--color-muted-foreground] font-mono">
                {status.runId}
              </span>
            </>
          ) : (
            <span className="text-sm text-[--color-muted-foreground]">Belum ada run aktif</span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={onRefresh}
            disabled={loading || actionLoading}
            aria-label="Refresh status"
          >
            <RefreshCw className={loading ? 'size-4 animate-spin' : 'size-4'} />
          </Button>

          {isRunning ? (
            <Button
              variant="destructive"
              size="sm"
              onClick={handleStop}
              disabled={actionLoading}
            >
              <Square className="size-4" />
              Stop
            </Button>
          ) : (
            <Button
              size="sm"
              onClick={handleRun}
              disabled={actionLoading || loading}
            >
              <Play className="size-4" />
              Jalankan Pipeline
            </Button>
          )}
        </div>
      </div>

      {/* Progress bar */}
      {status && (
        <div className="space-y-1.5">
          <Progress
            value={status.progress}
            variant={
              status.state === 'error'   ? 'error'   :
              status.state === 'done'    ? 'done'    :
              status.state === 'running' ? 'running' : 'default'
            }
            showLabel
          />
          {status.startedAt && (
            <p className="text-xs text-[--color-muted-foreground]">
              Dimulai {new Date(status.startedAt).toLocaleString('id-ID')}
              {status.finishedAt && (
                <> · Selesai {new Date(status.finishedAt).toLocaleString('id-ID')}</>
              )}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
