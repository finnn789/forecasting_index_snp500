import { TrendingUp, GitBranch, Newspaper, Activity } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Skeleton } from '../components/ui/skeleton'
import { PipelineStatusBadge } from '../components/shared/StatusBadge'
import { PageContainer } from '../components/layout/PageContainer'
import { usePipelineStatus } from '../hooks/usePipelineStatus'

export function DashboardPage() {
  const { status, loading } = usePipelineStatus(5000)

  return (
    <PageContainer title="Dashboard" description="Ringkasan sistem prediksi saham">
      {/* Stat cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          icon={<GitBranch className="size-5" />}
          label="Status Pipeline"
          value={
            loading ? <Skeleton className="h-5 w-20" /> :
            status ? <PipelineStatusBadge state={status.state} /> : '—'
          }
        />
        <StatCard
          icon={<Activity className="size-5" />}
          label="Progress"
          value={loading ? <Skeleton className="h-5 w-12" /> : status ? `${status.progress}%` : '—'}
        />
        <StatCard
          icon={<TrendingUp className="size-5" />}
          label="Prediksi Terakhir"
          value="BBCA +1.89%"
        />
        <StatCard
          icon={<Newspaper className="size-5" />}
          label="Sentimen Hari Ini"
          value="Positif 0.18"
        />
      </div>

      {/* Quick actions */}
      <Card>
        <CardHeader>
          <CardTitle>Akses Cepat</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Button asChild variant="outline" size="sm">
            <Link to="/pipeline"><GitBranch className="size-4" /> Monitor Pipeline</Link>
          </Button>
          <Button asChild variant="outline" size="sm">
            <Link to="/prediction"><TrendingUp className="size-4" /> Jalankan Prediksi</Link>
          </Button>
          <Button asChild variant="outline" size="sm">
            <Link to="/sentiment"><Newspaper className="size-4" /> Lihat Sentimen</Link>
          </Button>
        </CardContent>
      </Card>
    </PageContainer>
  )
}

function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: React.ReactNode }) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 pt-5">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-[--radius-lg] bg-[--color-primary]/10 text-[--color-primary]">
          {icon}
        </div>
        <div className="min-w-0">
          <p className="text-xs text-[--color-muted-foreground]">{label}</p>
          <div className="mt-0.5 text-sm font-semibold">{value}</div>
        </div>
      </CardContent>
    </Card>
  )
}
