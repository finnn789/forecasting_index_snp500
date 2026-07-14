import PageContainer from '../layout/PageContainer'
import Card, { CardHeader, CardTitle, CardContent } from '../components/Card'
import Button from '../components/Button'
import Icon from '../components/Icon'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../components/ui/table'
import { cn } from '../utils/cn'

const STAGES = [
  { name: 'Scrape OHLCV', status: 'done', icon: 'download' },
  { name: 'FinBERT Sentiment Scoring', status: 'done', icon: 'psychology' },
  { name: 'Feature Processing', status: 'running', icon: 'settings' },
  { name: 'LSTM Training / Inference', status: 'pending', icon: 'model_training' },
]

const STATUS_STYLES = {
  done: { label: 'Done', className: 'bg-emerald-50 text-emerald-600' },
  running: { label: 'Running', className: 'bg-amber-50 text-amber-600' },
  pending: { label: 'Pending', className: 'bg-slate-100 text-slate-500' },
}

const RUN_LOGS = [
  { time: '09:14:02', stage: 'Feature Processing', message: 'Computing weighted sentiment features...' },
  { time: '09:12:47', stage: 'FinBERT Sentiment Scoring', message: 'Scored 312 headlines, completed' },
  { time: '09:10:15', stage: 'Scrape OHLCV', message: 'Fetched 5 days of OHLCV data' },
]

export default function Pipeline() {
  return (
    <PageContainer
      title="Data Pipeline"
      description="Status pipeline pemrosesan data: scraping, sentiment scoring, hingga training model."
      action={
        <Button>
          <Icon name="play_arrow" className="text-base" />
          Run Pipeline
        </Button>
      }
    >
      <div className="grid grid-cols-4 gap-4">
        {STAGES.map((stage) => (
          <Card key={stage.name}>
            <CardContent className="space-y-3 p-5">
              <div className="flex items-center justify-between">
                <div className="flex size-9 items-center justify-center rounded bg-slate-100">
                  <Icon name={stage.icon} className="text-lg text-slate-600" />
                </div>
                <span
                  className={cn(
                    'rounded-full px-2 py-0.5 text-xs font-medium',
                    STATUS_STYLES[stage.status].className,
                  )}
                >
                  {STATUS_STYLES[stage.status].label}
                </span>
              </div>
              <p className="text-sm font-medium text-slate-900">{stage.name}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Run Log</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Time</TableHead>
                <TableHead>Stage</TableHead>
                <TableHead>Message</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {RUN_LOGS.map((row) => (
                <TableRow key={row.time}>
                  <TableCell className="font-mono text-slate-500">{row.time}</TableCell>
                  <TableCell className="font-medium text-slate-900">{row.stage}</TableCell>
                  <TableCell className="text-slate-600">{row.message}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </PageContainer>
  )
}
