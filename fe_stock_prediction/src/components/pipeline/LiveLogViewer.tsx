import { useEffect, useRef } from 'react'
import { Wifi, WifiOff } from 'lucide-react'
import { cn } from '../../lib/utils'
import { useSSE } from '../../hooks/useSSE'
import type { RunLog } from '../../types/pipeline'

const levelStyle: Record<RunLog['level'], string> = {
  INFO:    'text-[--color-foreground]',
  WARNING: 'text-[--color-pipeline-running]',
  ERROR:   'text-[--color-pipeline-error]',
  DEBUG:   'text-[--color-muted-foreground]',
}

const levelBadge: Record<RunLog['level'], string> = {
  INFO:    'bg-[--color-surface-2] text-[--color-muted-foreground]',
  WARNING: 'bg-[--color-pipeline-running]/15 text-[--color-pipeline-running]',
  ERROR:   'bg-[--color-pipeline-error]/15 text-[--color-pipeline-error]',
  DEBUG:   'bg-[--color-surface-2] text-[--color-muted-foreground]',
}

interface LiveLogViewerProps {
  active: boolean
}

export function LiveLogViewer({ active }: LiveLogViewerProps) {
  const { logs, connected } = useSSE(active)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  return (
    <div className="flex flex-col h-72 rounded-[--radius-lg] border border-[--color-border] bg-[--color-surface] overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between border-b border-[--color-border] px-3 py-2">
        <span className="text-xs font-medium text-[--color-muted-foreground]">Live Log</span>
        <div className="flex items-center gap-1.5">
          {connected ? (
            <><Wifi className="size-3 text-[--color-pipeline-done]" /><span className="text-xs text-[--color-pipeline-done]">Terhubung</span></>
          ) : (
            <><WifiOff className="size-3 text-[--color-muted-foreground]" /><span className="text-xs text-[--color-muted-foreground]">Tidak aktif</span></>
          )}
        </div>
      </div>

      {/* Log entries */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1 font-mono text-xs">
        {logs.length === 0 ? (
          <p className="text-[--color-muted-foreground] py-4 text-center">
            {active ? 'Menunggu log...' : 'Jalankan pipeline untuk melihat log.'}
          </p>
        ) : (
          logs.map((log, i) => (
            <div key={i} className={cn('flex items-start gap-2', levelStyle[log.level])}>
              <span className="text-[--color-muted-foreground] shrink-0 tabular-nums">
                {new Date(log.timestamp).toLocaleTimeString('id-ID')}
              </span>
              <span className={cn('shrink-0 rounded px-1 py-0.5 text-[10px] font-semibold uppercase', levelBadge[log.level])}>
                {log.level}
              </span>
              <span className="text-[--color-primary]/70 shrink-0">[{log.stage}]</span>
              <span className="break-all">{log.message}</span>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
