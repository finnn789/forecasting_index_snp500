import { Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { PageContainer } from '../components/layout/PageContainer'
import { EmptyState } from '../components/shared/EmptyState'
import { ErrorAlert } from '../components/shared/ErrorAlert'
import { ScrollText, GitBranch } from 'lucide-react'

/**
 * Backend tidak menyediakan endpoint penyimpanan log sistem. Log hanya tersedia
 * secara real-time (SSE) saat Sentiment Pipeline dijalankan — lihat halaman Pipeline.
 */
export function LogsPage() {
  return (
    <PageContainer
      title="Log Sistem"
      description="Log eksekusi pipeline."
    >
      <ErrorAlert
        variant="info"
        message="Backend belum menyimpan riwayat log. Log progres ditampilkan secara real-time saat Sentiment Pipeline dijalankan."
      />

      <Card>
        <CardHeader>
          <CardTitle>Log Real-time</CardTitle>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={ScrollText}
            title="Tidak ada log tersimpan"
            description="Jalankan Sentiment Pipeline untuk melihat streaming log progres (loading → inference → aggregating → saving)."
          />
          <div className="mt-4 flex justify-center">
            <Button asChild variant="outline" size="sm">
              <Link to="/pipeline"><GitBranch className="size-4" /> Buka Sentiment Pipeline</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </PageContainer>
  )
}
