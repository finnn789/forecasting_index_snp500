import PageContainer from '../layout/PageContainer'
import Card, { CardHeader, CardTitle, CardContent } from '../components/Card'
import Button from '../components/Button'
import Input from '../components/Input'

export default function Settings() {
  return (
    <PageContainer title="Settings" description="Konfigurasi umum aplikasi dan model prediksi.">
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Data Source</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="mb-1.5 block text-xs font-medium text-slate-600">Default Ticker</label>
              <Input defaultValue="^GSPC" />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-slate-600">News API Endpoint</label>
              <Input defaultValue="https://api.example.com/news" />
            </div>
            <Button size="sm">Save Changes</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Model</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="mb-1.5 block text-xs font-medium text-slate-600">FinBERT Checkpoint</label>
              <Input defaultValue="finbert-sentiment-v2" />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-slate-600">LSTM Lookback Window (days)</label>
              <Input type="number" defaultValue={30} />
            </div>
            <Button size="sm">Save Changes</Button>
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  )
}
