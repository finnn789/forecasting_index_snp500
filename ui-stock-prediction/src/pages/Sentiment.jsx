import PageContainer from '../layout/PageContainer'
import Card, { CardHeader, CardTitle, CardContent } from '../components/Card'
import StatCard from '../components/charts/StatCard'
import PieChart from '../components/charts/PieChart'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../components/ui/table'
import { CHART_COLORS } from '../utils/chartTheme'
import { cn } from '../utils/cn'

const SENTIMENT_DISTRIBUTION = {
  labels: ['Positive', 'Neutral', 'Negative'],
  values: [54, 31, 15],
  colors: [CHART_COLORS.emerald, CHART_COLORS.slate, CHART_COLORS.crimson],
}

const HEADLINES = [
  { time: '09:12', headline: 'Fed signals rate stability into Q3, markets rally', label: 'Positive' },
  { time: '08:47', headline: 'Tech earnings beat estimates, S&P futures climb', label: 'Positive' },
  { time: '07:55', headline: 'Oil prices flat amid mixed inventory data', label: 'Neutral' },
  { time: '07:20', headline: 'Manufacturing PMI misses forecast, growth concerns rise', label: 'Negative' },
]

const LABEL_STYLES = {
  Positive: 'bg-emerald-50 text-emerald-600',
  Neutral: 'bg-slate-100 text-slate-600',
  Negative: 'bg-red-50 text-red-600',
}

export default function Sentiment() {
  return (
    <PageContainer
      title="Sentiment Analysis"
      description="Analisis sentimen berita pasar dari model FinBERT."
    >
      <div className="grid grid-cols-3 gap-4">
        <StatCard label="Positive Sentiment" value="54%" delta={4.2} sparkline={[42, 45, 48, 50, 52, 54]} />
        <StatCard label="Negative Sentiment" value="15%" delta={-2.1} sparkline={[21, 19, 18, 17, 16, 15]} />
        <StatCard label="Articles Analyzed (24h)" value="312" sparkline={[210, 240, 260, 280, 300, 312]} />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Sentiment Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <PieChart
              labels={SENTIMENT_DISTRIBUTION.labels}
              values={SENTIMENT_DISTRIBUTION.values}
              colors={SENTIMENT_DISTRIBUTION.colors}
            />
          </CardContent>
        </Card>

        <Card className="col-span-2">
          <CardHeader>
            <CardTitle>Latest Headlines</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Time</TableHead>
                  <TableHead>Headline</TableHead>
                  <TableHead>Sentiment</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {HEADLINES.map((row) => (
                  <TableRow key={row.time}>
                    <TableCell className="font-mono text-slate-500">{row.time}</TableCell>
                    <TableCell className="text-slate-900">{row.headline}</TableCell>
                    <TableCell>
                      <span
                        className={cn(
                          'inline-flex rounded-full px-2 py-0.5 text-xs font-medium',
                          LABEL_STYLES[row.label],
                        )}
                      >
                        {row.label}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  )
}
