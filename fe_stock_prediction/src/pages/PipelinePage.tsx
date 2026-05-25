import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Separator } from '../components/ui/separator'
import { PageContainer } from '../components/layout/PageContainer'
import { ErrorAlert } from '../components/shared/ErrorAlert'
import { PipelineControlPanel } from '../components/pipeline/PipelineControlPanel'
import { StageStatusList } from '../components/pipeline/StageStatusList'
import { LiveLogViewer } from '../components/pipeline/LiveLogViewer'
import { RunHistoryTable } from '../components/pipeline/RunHistoryTable'
import { usePipelineStatus } from '../hooks/usePipelineStatus'

export function PipelinePage() {
  const { status, loading, error, refetch } = usePipelineStatus(3000)

  const isRunning = status?.state === 'running'

  return (
    <PageContainer
      title="Data Pipeline"
      description="Monitor, jalankan, dan hentikan pipeline pemrosesan data."
    >
      {error && <ErrorAlert message={error} />}

      {/* Control + Stage status */}
      <div className="grid gap-6 lg:grid-cols-5">
        {/* Left: Control panel */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Kontrol Pipeline</CardTitle>
            </CardHeader>
            <CardContent>
              <PipelineControlPanel
                status={status}
                loading={loading}
                onRefresh={refetch}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Riwayat Run</CardTitle>
            </CardHeader>
            <CardContent>
              <RunHistoryTable />
            </CardContent>
          </Card>
        </div>

        {/* Right: Stage list + live log */}
        <div className="lg:col-span-3 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Tahapan Pipeline</CardTitle>
            </CardHeader>
            <CardContent>
              <StageStatusList stages={status?.stages} loading={loading} />
            </CardContent>
          </Card>

          <Separator />

          <Card>
            <CardHeader>
              <CardTitle>Log Real-time</CardTitle>
            </CardHeader>
            <CardContent>
              <LiveLogViewer active={isRunning} />
            </CardContent>
          </Card>
        </div>
      </div>
    </PageContainer>
  )
}
