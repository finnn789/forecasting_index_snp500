import { CheckCircle2, XCircle, Loader2, Circle, ChevronDown, ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { cn } from '../../lib/utils'
import { formatDuration } from '../../lib/utils'
import { PipelineStatusBadge } from '../shared/StatusBadge'
import type { StageResult } from '../../types/pipeline'
import { PIPELINE_STAGES } from '../../lib/constants'

const stageDesc = Object.fromEntries(PIPELINE_STAGES.map(s => [s.id, s.description]))

const stateIcon: Record<string, React.ReactNode> = {
  idle:    <Circle    className="size-4 text-[--color-pipeline-idle]" />,
  running: <Loader2   className="size-4 text-[--color-pipeline-running] animate-spin" />,
  done:    <CheckCircle2 className="size-4 text-[--color-pipeline-done]" />,
  error:   <XCircle   className="size-4 text-[--color-pipeline-error]" />,
}

const stateLine: Record<string, string> = {
  idle:    'border-[--color-pipeline-idle]/30',
  running: 'border-[--color-pipeline-running]',
  done:    'border-[--color-pipeline-done]',
  error:   'border-[--color-pipeline-error]',
}

interface StageCardProps {
  stage: StageResult
  isLast?: boolean
}

export function StageCard({ stage, isLast = false }: StageCardProps) {
  const [expanded, setExpanded] = useState(stage.state === 'error')

  return (
    <div className="relative flex gap-4">
      {/* Connector line */}
      {!isLast && (
        <div className="absolute left-4.25 top-8 bottom-0 w-px bg-[--color-border]" />
      )}

      {/* Icon column */}
      <div className="relative z-10 flex size-9 shrink-0 items-center justify-center rounded-full bg-[--color-surface-2] border border-[--color-border]">
        {stateIcon[stage.state]}
      </div>

      {/* Content */}
      <div
        className={cn(
          'mb-4 flex-1 rounded-[--radius-lg] border bg-[--color-card] px-4 py-3',
          'transition-colors',
          stateLine[stage.state],
        )}
      >
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-sm font-medium truncate">{stage.label}</span>
            <PipelineStatusBadge state={stage.state} />
          </div>
          <div className="flex items-center gap-3 shrink-0">
            {stage.durationMs !== undefined && (
              <span className="text-xs tabular-nums text-[--color-muted-foreground]">
                {formatDuration(stage.durationMs)}
              </span>
            )}
            {(stage.errorMessage || stageDesc[stage.id]) && (
              <button
                onClick={() => setExpanded(v => !v)}
                className="text-[--color-muted-foreground] hover:text-[--color-foreground] transition-colors"
                aria-label={expanded ? 'Tutup detail' : 'Buka detail'}
              >
                {expanded
                  ? <ChevronDown className="size-4" />
                  : <ChevronRight className="size-4" />}
              </button>
            )}
          </div>
        </div>

        {expanded && (
          <div className="mt-2 space-y-1">
            {stageDesc[stage.id] && (
              <p className="text-xs text-[--color-muted-foreground]">{stageDesc[stage.id]}</p>
            )}
            {stage.errorMessage && (
              <p className="rounded-[--radius-sm] bg-[--color-destructive]/10 px-2 py-1 text-xs text-[--color-destructive] font-mono">
                {stage.errorMessage}
              </p>
            )}
            {stage.startedAt && (
              <p className="text-xs text-[--color-muted-foreground]">
                Mulai: {new Date(stage.startedAt).toLocaleTimeString('id-ID')}
                {stage.finishedAt && (
                  <> · Selesai: {new Date(stage.finishedAt).toLocaleTimeString('id-ID')}</>
                )}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
