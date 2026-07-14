import PageContainer from '../layout/PageContainer'
import Card, { CardHeader, CardTitle, CardContent } from '../components/Card'
import Button from '../components/Button'
import StatCard from '../components/charts/StatCard'
import PriceCandlestickChart from '../components/charts/PriceCandlestickChart'
import PieChart from '../components/charts/PieChart'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../components/ui/table'
import { cn } from '../utils/cn'

const OHLC = [
  { date: '2026-07-01', open: 5480, high: 5510, low: 5460, close: 5495 },
  { date: '2026-07-02', open: 5495, high: 5530, low: 5480, close: 5520 },
  { date: '2026-07-03', open: 5520, high: 5525, low: 5470, close: 5482 },
  { date: '2026-07-04', open: 5482, high: 5540, low: 5475, close: 5535 },
  { date: '2026-07-05', open: 5535, high: 5560, low: 5520, close: 5550 },
]

const PREDICTED = [
  { date: '2026-07-05', close: 5550 },
  { date: '2026-07-06', close: 5572 },
  { date: '2026-07-07', close: 5590 },
]

const SECTOR_ALLOCATION = {
  labels: ['Technology', 'Healthcare', 'Financials', 'Energy', 'Other'],
  values: [38, 18, 16, 12, 16],
}

const WATCHLIST = [
  { ticker: 'AAPL', price: 231.45, change: 1.24 },
  { ticker: 'MSFT', price: 468.12, change: -0.38 },
  { ticker: 'NVDA', price: 142.87, change: 2.91 },
]

export default function Dashboard() {
  return (
    <PageContainer
      title="Overview"
      description="Ringkasan indeks S&P 500 dan hasil prediksi model terbaru."
      action={<Button>Generate Report</Button>}
    >
      <div className="grid grid-cols-3 gap-4">
        <StatCard
          label="S&P 500 Index"
          value="5,550.20"
          delta={1.24}
          sparkline={[5420, 5450, 5480, 5460, 5495, 5520, 5550]}
        />
        <StatCard
          label="Predicted Close"
          value="5,590.00"
          delta={0.72}
          sparkline={[5495, 5510, 5535, 5550, 5572, 5590]}
        />
        <StatCard
          label="Volatility Index"
          value="14.32"
          delta={-3.15}
          sparkline={[16.1, 15.7, 15.2, 14.9, 14.6, 14.32]}
        />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Card className="col-span-2">
          <CardHeader>
            <CardTitle>Price & Prediction</CardTitle>
          </CardHeader>
          <CardContent>
            <PriceCandlestickChart data={OHLC} predicted={PREDICTED} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Sector Allocation</CardTitle>
          </CardHeader>
          <CardContent>
            <PieChart labels={SECTOR_ALLOCATION.labels} values={SECTOR_ALLOCATION.values} />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Watchlist</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Ticker</TableHead>
                <TableHead>Price</TableHead>
                <TableHead>Change</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {WATCHLIST.map((row) => (
                <TableRow key={row.ticker}>
                  <TableCell className="font-medium text-slate-900">{row.ticker}</TableCell>
                  <TableCell className="font-mono">{row.price.toFixed(2)}</TableCell>
                  <TableCell
                    className={cn('font-mono', row.change >= 0 ? 'text-emerald-500' : 'text-red-500')}
                  >
                    {row.change >= 0 ? '+' : ''}
                    {row.change.toFixed(2)}%
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </PageContainer>
  )
}
