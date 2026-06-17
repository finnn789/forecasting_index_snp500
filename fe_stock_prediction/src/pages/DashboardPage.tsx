import { TrendingUp, GitBranch, Newspaper, Activity } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Skeleton } from '../components/ui/skeleton'
import { Badge } from '../components/ui/badge'
import { PageContainer } from '../components/layout/PageContainer'
import { useSentimentPipelineStatus } from '../hooks/useSentimentPipeline'
import { formatNumber } from '../lib/format'

export function DashboardPage() {
  const { data: status, loading } = useSentimentPipelineStatus()

  const dataReady = !!status?.clean_file_exists && !!status?.daily_file_exists

  return (
    <PageContainer title="Dashboard" description="Ringkasan sistem prediksi saham">
      {/* Stat cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          icon={<GitBranch className="size-5" />}
          label="Data Sentimen"
          value={
            loading ? <Skeleton className="h-5 w-20" /> :
            status ? <Badge variant={dataReady ? 'done' : 'idle'} dot>{dataReady ? 'Siap' : 'Belum lengkap'}</Badge> : '—'
          }
        />
        <StatCard
          icon={<Activity className="size-5" />}
          label="Total Headline"
          value={loading ? <Skeleton className="h-5 w-12" /> : status?.total_headlines != null ? formatNumber(status.total_headlines) : '—'}
        />
        <StatCard
          icon={<TrendingUp className="size-5" />}
          label="Ticker Model"
          value="GSPC (S&P 500)"
        />
        <StatCard
          icon={<Newspaper className="size-5" />}
          label="Rentang Data"
          value={loading ? <Skeleton className="h-5 w-24" /> : status?.date_range?.end ?? '—'}
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
