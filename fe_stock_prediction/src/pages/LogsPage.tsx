import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Skeleton } from '../components/ui/skeleton'
import { Badge } from '../components/ui/badge'
import { PageContainer } from '../components/layout/PageContainer'
import { EmptyState } from '../components/shared/EmptyState'
import { ErrorAlert } from '../components/shared/ErrorAlert'
import { ScrollText } from 'lucide-react'
import { getPipelineLogs } from '../lib/api/pipeline.api'
import type { RunLog } from '../types/pipeline'
import { cn } from '../lib/utils'

const levelVariant: Record<RunLog['level'], 'default' | 'running' | 'error' | 'idle'> = {
  INFO:    'idle',
  WARNING: 'running',
  ERROR:   'error',
  DEBUG:   'idle',
}

const levelColor: Record<RunLog['level'], string> = {
  INFO:    'text-[--color-foreground]',
  WARNING: 'text-[--color-pipeline-running]',
  ERROR:   'text-[--color-pipeline-error]',
  DEBUG:   'text-[--color-muted-foreground]',
}

export function LogsPage() {
  const [logs, setLogs]       = useState<RunLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState<string | null>(null)
  const [filter, setFilter]   = useState<RunLog['level'] | 'ALL'>('ALL')

  useEffect(() => {
    getPipelineLogs()
      .then(setLogs)
      .catch(e => setError(e instanceof Error ? e.message : 'Gagal mengambil log'))
      .finally(() => setLoading(false))
  }, [])

  const levels: Array<RunLog['level'] | 'ALL'> = ['ALL', 'INFO', 'WARNING', 'ERROR', 'DEBUG']

  const visible = filter === 'ALL' ? logs : logs.filter(l => l.level === filter)

  return (
    <PageContainer
      title="Log Sistem"
      description="Riwayat log dari semua tahap pipeline."
    >
      {error && <ErrorAlert message={error} />}

      <Card>
        <CardHeader className="flex-row items-center justify-between gap-4 space-y-0">
          <CardTitle>Log Pipeline</CardTitle>
          {/* Level filter */}
          <div className="flex flex-wrap gap-1.5">
            {levels.map(lv => (
              <button
                key={lv}
                onClick={() => setFilter(lv)}
                className={cn(
                  'rounded-[--radius-md] px-2.5 py-1 text-xs font-medium transition-colors',
                  filter === lv
                    ? 'bg-[--color-primary] text-[--color-primary-foreground]'
                    : 'bg-[--color-surface-2] text-[--color-muted-foreground] hover:text-[--color-foreground]',
                )}
              >
                {lv}
              </button>
            ))}
          </div>
        </CardHeader>

        <CardContent>
          {loading ? (
            <div className="space-y-2">
              {Array.from({ length: 8 }, (_, i) => (
                <Skeleton key={i} className="h-9 w-full" />
              ))}
            </div>
          ) : !visible.length ? (
            <EmptyState
              icon={ScrollText}
              title="Tidak ada log"
              description={filter !== 'ALL' ? `Tidak ada log level ${filter}.` : 'Belum ada log tersedia.'}
            />
          ) : (
            <div className="overflow-x-auto rounded-[--radius-lg] border border-[--color-border]">
              <table className="w-full font-mono text-xs">
                <thead>
                  <tr className="border-b border-[--color-border] bg-[--color-surface-2] text-left">
                    <th className="px-4 py-2.5 font-medium text-[--color-muted-foreground] w-28">Waktu</th>
                    <th className="px-4 py-2.5 font-medium text-[--color-muted-foreground] w-24">Level</th>
                    <th className="px-4 py-2.5 font-medium text-[--color-muted-foreground] w-28">Tahap</th>
                    <th className="px-4 py-2.5 font-medium text-[--color-muted-foreground]">Pesan</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[--color-border]">
                  {visible.map((log, i) => (
                    <tr
                      key={i}
                      className="bg-[--color-card] hover:bg-[--color-surface-2] transition-colors"
                    >
                      <td className="px-4 py-2.5 text-[--color-muted-foreground] tabular-nums">
                        {new Date(log.timestamp).toLocaleTimeString('id-ID')}
                      </td>
                      <td className="px-4 py-2.5">
                        <Badge variant={levelVariant[log.level]}>{log.level}</Badge>
                      </td>
                      <td className="px-4 py-2.5 text-[--color-primary]/80">
                        [{log.stage}]
                      </td>
                      <td className={cn('px-4 py-2.5 break-all', levelColor[log.level])}>
                        {log.message}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {!loading && visible.length > 0 && (
            <p className="mt-3 text-xs text-[--color-muted-foreground]">
              Menampilkan {visible.length} dari {logs.length} entri log.
            </p>
          )}
        </CardContent>
      </Card>
    </PageContainer>
  )
}
