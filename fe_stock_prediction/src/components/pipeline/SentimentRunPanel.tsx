import { useEffect, useRef } from 'react'
import { Play, Square, Loader2 } from 'lucide-react'
import { cn } from '../../lib/utils'
import { Button } from '../ui/button'
import { Progress } from '../ui/progress'
import { PipelineStatusBadge } from '../shared/StatusBadge'
import type { SentimentRunController } from '../../hooks/useSentimentPipeline'

interface Props {
  controller: SentimentRunController
}

export function SentimentRunPanel({ controller }: Props) {
  const { state, progress, logs, start, cancel } = controller
  const isRunning = state === 'running'
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  return (
    <div className="space-y-4">
      {/* Kontrol */}
      <div className="flex items-center justify-between gap-3">
        <PipelineStatusBadge state={state} />
        {isRunning ? (
          <Button variant="destructive" size="sm" onClick={cancel}>
            <Square className="size-4" /> Batalkan
          </Button>
        ) : (
          <Button size="sm" onClick={start}>
            {state === 'done' ? <><Play className="size-4" /> Jalankan Ulang</> : <><Play className="size-4" /> Jalankan Pipeline</>}
          </Button>
        )}
      </div>

      {/* Progress */}
      {(isRunning || state === 'done' || state === 'error') && (
        <Progress
          value={progress}
          variant={state === 'error' ? 'error' : state === 'done' ? 'done' : 'running'}
          showLabel
        />
      )}

      {/* Live log */}
      <div className="flex h-64 flex-col overflow-hidden rounded-[--radius-lg] border border-[--color-border] bg-[--color-surface]">
        <div className="flex items-center gap-1.5 border-b border-[--color-border] px-3 py-2 text-xs font-medium text-[--color-muted-foreground]">
          {isRunning && <Loader2 className="size-3 animate-spin" />}
          Log Real-time
        </div>
        <div className="flex-1 overflow-y-auto p-3 font-mono text-xs space-y-1">
          {logs.length === 0 ? (
            <p className="py-4 text-center text-[--color-muted-foreground]">
              {isRunning ? 'Menunggu event...' : 'Jalankan pipeline untuk melihat progres.'}
            </p>
          ) : (
            logs.map((log, i) => (
              <div key={i} className={cn('flex items-start gap-2', log.isError && 'text-[--color-pipeline-error]')}>
                <span className="shrink-0 tabular-nums text-[--color-muted-foreground]">
                  {new Date(log.at).toLocaleTimeString('id-ID')}
                </span>
                <span className="shrink-0 tabular-nums text-[--color-primary]/70">{log.pct}%</span>
                <span className="shrink-0 text-[--color-muted-foreground]">[{log.step}]</span>
                <span className="break-all">{log.msg}</span>
              </div>
            ))
          )}
          <div ref={bottomRef} />
        </div>
      </div>
    </div>
  )
}
