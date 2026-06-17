import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { PageContainer } from '../components/layout/PageContainer'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Skeleton } from '../components/ui/skeleton'
import { ErrorAlert } from '../components/shared/ErrorAlert'
import { useEdaDashboard } from '../hooks/useEdaDashboard'
import { fmt } from '../lib/format'
import type { SentimentDistributionItem } from '../types/eda'

// Approximate hex values matching index.css oklch tokens
const C = {
  primary:  '#6366f1',
  pos:      '#4ade80',
  neg:      '#f87171',
  neu:      '#94a3b8',
  grid:     'rgba(255,255,255,0.06)',
  tick:     'rgba(255,255,255,0.45)',
  tooltip:  { bg: '#1a1d2e', border: '#2d3058', label: '#e2e8f0' },
}

const tooltipStyle = {
  contentStyle: { backgroundColor: C.tooltip.bg, border: `1px solid ${C.tooltip.border}`, borderRadius: 8, fontSize: 12 },
  labelStyle:   { color: C.tooltip.label },
}

const axisProps = {
  tick:     { fill: C.tick, fontSize: 11 },
  tickLine: false as const,
  axisLine: false as const,
}

// Ensure chart data prop is always a real array
const toArr = <T,>(v: T[] | null | undefined): T[] =>
  Array.isArray(v) ? v : []

export function SentimentPage() {
  const { newsPerYear, newsPerDay, headlineLength, sentimentDist } = useEdaDashboard()
  

  return (
    <PageContainer
      title="Eksplorasi Data (EDA)"
      description="Analisis statistik dataset berita keuangan yang digunakan untuk pelatihan model."
    >
      <div className="grid gap-6 lg:grid-cols-2">

        {/* ── 1. Volume Berita per Tahun ─────────────────────────── */}
        <Card>
          <CardHeader>
            <CardTitle>Volume Berita per Tahun</CardTitle>
            <CardDescription>Tren pertumbuhan jumlah headline dari tahun ke tahun</CardDescription>
          </CardHeader>
          <CardContent>
            {newsPerYear.loading ? (
              <Skeleton className="h-60 w-full" />
            ) : newsPerYear.error ? (
              <ErrorAlert message={newsPerYear.error} />
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={toArr(newsPerYear.data)} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={C.grid} />
                  <XAxis dataKey="year" {...axisProps} />
                  <YAxis {...axisProps} width={42} />
                  <Tooltip {...tooltipStyle} itemStyle={{ color: C.primary }} />
                  <Bar dataKey="count" fill={C.primary} radius={[4, 4, 0, 0]} name="Jumlah Berita" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* ── 2. Aktivitas Harian ────────────────────────────────── */}
        <Card>
          <CardHeader>
            <CardTitle>Aktivitas Harian</CardTitle>
            <CardDescription>Statistik jumlah berita yang dipublikasikan per hari</CardDescription>
          </CardHeader>
          <CardContent>
            {newsPerDay.loading ? (
              <Skeleton className="h-60 w-full" />
            ) : newsPerDay.error ? (
              <ErrorAlert message={newsPerDay.error} />
            ) : newsPerDay.data ? (
              <div className="grid grid-cols-3 gap-3">
                {([
                  { label: 'Rata-rata / hari', value: fmt(newsPerDay.data.mean), sub: null },
                  {
                    label: 'Maksimum',
                    value: fmt(newsPerDay.data.max, 0),
                    sub: newsPerDay.data.max_date ?? null,
                  },
                  {
                    label: 'Minimum',
                    value: fmt(newsPerDay.data.min, 0),
                    sub: newsPerDay.data.min_date ?? null,
                  },
                ] as { label: string; value: string; sub: string | null }[]).map(({ label, value, sub }) => (
                  <div key={label} className="rounded-[--radius-md] bg-[--color-surface-2] p-3 text-center">
                    <p className="text-xs text-[--color-muted-foreground]">{label}</p>
                    <p className="mt-1 text-xl font-semibold tabular-nums">{value}</p>
                    {sub && <p className="mt-0.5 text-[10px] text-[--color-muted-foreground]">{sub}</p>}
                  </div>
                ))}
              </div>
            ) : null}
          </CardContent>
        </Card>

        {/* ── 3. Distribusi Panjang Headline ────────────────────── */}
        <Card>
          <CardHeader>
            <CardTitle>Distribusi Panjang Headline</CardTitle>
            <CardDescription>Sebaran jumlah karakter teks berita</CardDescription>
          </CardHeader>
          <CardContent>
            {headlineLength.loading ? (
              <Skeleton className="h-60 w-full" />
            ) : headlineLength.error ? (
              <ErrorAlert message={headlineLength.error} />
            ) : headlineLength.data ? (
              <div className="space-y-3">
                {([
                  { heading: 'Karakter', mean: headlineLength.data.char_mean, std: headlineLength.data.char_std, min: headlineLength.data.char_min, max: headlineLength.data.char_max },
                  { heading: 'Kata',     mean: headlineLength.data.word_mean, std: headlineLength.data.word_std, min: headlineLength.data.word_min, max: headlineLength.data.word_max },
                ] as { heading: string; mean: number; std: number; min: number; max: number }[]).map(({ heading, mean, std, min, max }) => (
                  <div key={heading} className="rounded-[--radius-md] bg-[--color-surface-2] p-3">
                    <p className="mb-2 text-xs font-medium text-[--color-muted-foreground]">{heading}</p>
                    <div className="grid grid-cols-4 gap-2 text-center">
                      {([['Mean', mean, 2], ['Std', std, 2], ['Min', min, 0], ['Max', max, 0]] as [string, number, number][]).map(([lbl, val, dec]) => (
                        <div key={lbl}>
                          <p className="text-[10px] text-[--color-muted-foreground]">{lbl}</p>
                          <p className="text-sm font-semibold tabular-nums">{fmt(val, dec)}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : null}
          </CardContent>
        </Card>

        {/* ── 4. Distribusi Sentimen ────────────────────────────── */}
        <Card>
          <CardHeader>
            <CardTitle>Distribusi Sentimen</CardTitle>
            <CardDescription>Proporsi label Positif / Negatif / Netral pada dataset</CardDescription>
          </CardHeader>
          <CardContent>
            {sentimentDist.loading ? (
              <Skeleton className="h-60 w-full" />
            ) : sentimentDist.error ? (
              <ErrorAlert message={sentimentDist.error} />
            ) : sentimentDist.data ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-[--radius-md] bg-[--color-surface-2] p-3 text-center">
                    <p className="text-xs text-[--color-muted-foreground]">Mean Score</p>
                    <p className="mt-1 text-xl font-semibold tabular-nums">
                      {sentimentDist.data.sentiment_score_mean != null && sentimentDist.data.sentiment_score_mean >= 0 ? '+' : ''}
                      {fmt(sentimentDist.data.sentiment_score_mean, 4)}
                    </p>
                  </div>
                  <div className="rounded-[--radius-md] bg-[--color-surface-2] p-3 text-center">
                    <p className="text-xs text-[--color-muted-foreground]">Std Score</p>
                    <p className="mt-1 text-xl font-semibold tabular-nums">
                      {fmt(sentimentDist.data.sentiment_score_std, 4)}
                    </p>
                  </div>
                </div>
                <ResponsiveContainer width="100%" height={180}>
                  <PieChart>
                    <Pie
                      data={toArr<SentimentDistributionItem>(sentimentDist.data.data).map((item) => ({
                        name: item.label.charAt(0).toUpperCase() + item.label.slice(1),
                        value: item.pct,
                        fill: item.label === 'positive' ? C.pos : item.label === 'negative' ? C.neg : C.neu,
                      }))}
                      cx="50%"
                      cy="50%"
                      innerRadius={52}
                      outerRadius={76}
                      paddingAngle={3}
                      dataKey="value"
                    />
                    <Tooltip
                      {...tooltipStyle}
                      formatter={(v) => v != null ? [`${Number(v).toFixed(1)}%`] : ['']}
                    />
                    <Legend
                      iconType="circle"
                      iconSize={8}
                      wrapperStyle={{ fontSize: 12, color: C.tick }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : null}
          </CardContent>
        </Card>

      </div>
    </PageContainer>
  )
}
