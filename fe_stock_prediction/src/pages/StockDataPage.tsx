import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Skeleton } from '../components/ui/skeleton'
import { PageContainer } from '../components/layout/PageContainer'
import { ErrorAlert } from '../components/shared/ErrorAlert'
import { EmptyState } from '../components/shared/EmptyState'
import { useStockData } from '../hooks/useStockData'
import { useStockTimeSeries } from '../hooks/useStockTimeSeries'
import { formatCurrency, formatVolume } from '../lib/format'
import { TICKERS } from '../lib/constants'
import { cn } from '../lib/utils'
import { TrendingUp } from 'lucide-react'

// Palet selaras token oklch di index.css
const C = {
  primary: '#6366f1',
  grid:    'rgba(255,255,255,0.06)',
  tick:    'rgba(255,255,255,0.45)',
  tooltip: { bg: '#1a1d2e', border: '#2d3058', label: '#e2e8f0' },
}

const dateFmt = (d: unknown) =>
  typeof d === 'string'
    ? new Date(d).toLocaleDateString('id-ID', { month: 'short', year: '2-digit' })
    : String(d)

const compact = (v: number) =>
  new Intl.NumberFormat('id-ID', { notation: 'compact', maximumFractionDigits: 1 }).format(v)

// Downsample agar render ringan saat ~1.5k titik
function downsample<T>(arr: T[], maxPoints = 600): T[] {
  if (arr.length <= maxPoints) return arr
  const step = Math.ceil(arr.length / maxPoints)
  return arr.filter((_, i) => i % step === 0)
}

function MetricCard({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="rounded-[--radius-lg] border border-[--color-border] bg-[--color-card] p-4">
      <p className="text-xs font-medium text-[--color-muted-foreground]">{label}</p>
      <p className={cn('mt-2 text-lg font-semibold', color)}>
        {value}
      </p>
    </div>
  )
}

export function StockDataPage() {
  const ticker = TICKERS[0].value
  const { data: stockData, loading, error } = useStockData(ticker)
  const { data: series, loading: seriesLoading, error: seriesError } = useStockTimeSeries()

  const chartData = useMemo(
    () => downsample(series?.data ?? []).map(p => ({ date: p.date, close: p.close })),
    [series],
  )

  const bars = stockData?.bars ?? []
  const hasEnoughData = bars.length >= 2
  const lastBar = bars[bars.length - 1]
  const prevBar = bars[bars.length - 2]

  const lastPrice = lastBar?.close ?? 0
  const prevPrice = prevBar?.close ?? 0
  const returnPercent = prevPrice > 0 ? ((lastPrice - prevPrice) / prevPrice) * 100 : 0
  const returnColor = returnPercent >= 0
    ? 'text-[--color-sentiment-pos]'
    : 'text-[--color-sentiment-neg]'

  const displayData = [...bars].reverse().slice(0, 10)

  return (
    <PageContainer
      title="Data Saham"
      description="Harga dan volume historis"
    >
      {error && <ErrorAlert message={error} />}

      {loading ? (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <Skeleton className="h-20" />
            <Skeleton className="h-20" />
            <Skeleton className="h-20" />
            <Skeleton className="h-20" />
          </div>
          <Skeleton className="h-80" />
        </div>
      ) : !stockData ? (
        <EmptyState
          icon={TrendingUp}
          title="Belum ada data"
          description="Data saham tidak tersedia untuk ticker ini."
        />
      ) : (
        <>
          {/* Summary Metrics */}
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <MetricCard
              label="Harga Terakhir"
              value={hasEnoughData ? formatCurrency(lastPrice) : '—'}
            />
            <MetricCard
              label="Volume"
              value={hasEnoughData ? formatVolume(lastBar.volume) : '—'}
            />
            <MetricCard
              label="Return 1D"
              value={hasEnoughData ? returnPercent.toFixed(2) + '%' : '—'}
              color={hasEnoughData ? returnColor : undefined}
            />
            <MetricCard
              label="High / Low"
              value={hasEnoughData ? `${formatCurrency(lastBar.high)} / ${formatCurrency(lastBar.low)}` : '—'}
            />
          </div>

          {/* Technical Indicators */}
          {hasEnoughData && lastBar && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Indikator Teknis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                  <MetricCard
                    label="HL Spread"
                    value={lastBar.hl_spread ? lastBar.hl_spread.toFixed(2) : '—'}
                  />
                  <MetricCard
                    label="OC Spread"
                    value={lastBar.oc_spread ? lastBar.oc_spread.toFixed(2) : '—'}
                  />
                  <MetricCard
                    label="MA 20"
                    value={lastBar.ma_20 ? formatCurrency(lastBar.ma_20) : '—'}
                  />
                  <MetricCard
                    label="MA 50"
                    value={lastBar.ma_50 ? formatCurrency(lastBar.ma_50) : '—'}
                  />
                  <MetricCard
                    label="MA 200"
                    value={lastBar.ma_200 ? formatCurrency(lastBar.ma_200) : '—'}
                  />
                  <MetricCard
                    label="Volatility 30D"
                    value={lastBar.volatility_30 ? (lastBar.volatility_30 * 100).toFixed(2) + '%' : '—'}
                  />
                </div>
              </CardContent>
            </Card>
          )}

          {/* Chart harga historis (time-series) */}
          <Card>
            <CardHeader>
              <CardTitle>
                Grafik Harga {series?.period ? `(${series.period})` : ''}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {seriesLoading ? (
                <Skeleton className="h-72 w-full" />
              ) : seriesError ? (
                <ErrorAlert message={seriesError} />
              ) : chartData.length === 0 ? (
                <EmptyState
                  icon={TrendingUp}
                  title="Tidak ada deret harga"
                  description="Data time-series tidak tersedia."
                />
              ) : (
                <ResponsiveContainer width="100%" height={288}>
                  <AreaChart data={chartData} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={C.primary} stopOpacity={0.3} />
                        <stop offset="95%" stopColor={C.primary} stopOpacity={0.02} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke={C.grid} vertical={false} />
                    <XAxis
                      dataKey="date"
                      tickFormatter={dateFmt}
                      tick={{ fill: C.tick, fontSize: 11 }}
                      tickLine={false}
                      axisLine={false}
                      minTickGap={48}
                    />
                    <YAxis
                      tickFormatter={compact}
                      tick={{ fill: C.tick, fontSize: 11 }}
                      tickLine={false}
                      axisLine={false}
                      width={52}
                      domain={['auto', 'auto']}
                    />
                    <Tooltip
                      contentStyle={{ backgroundColor: C.tooltip.bg, border: `1px solid ${C.tooltip.border}`, borderRadius: 8, fontSize: 12 }}
                      labelStyle={{ color: C.tooltip.label }}
                      labelFormatter={(d) => (typeof d === 'string' ? new Date(d).toLocaleDateString('id-ID') : String(d))}
                      formatter={(v) => [typeof v === 'number' ? v.toLocaleString('id-ID') : v, 'Close']}
                    />
                    <Area
                      type="monotone"
                      dataKey="close"
                      stroke={C.primary}
                      strokeWidth={2}
                      fill="url(#priceGrad)"
                      dot={false}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Histori Harga</CardTitle>
            </CardHeader>
            <CardContent>
              {displayData.length === 0 ? (
                <EmptyState
                  icon={TrendingUp}
                  title="Tidak ada data historis"
                  description="Data historis saham tidak tersedia."
                />
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-[--color-border]">
                        <th className="px-4 py-3 text-left font-semibold text-[--color-foreground]">
                          Tanggal
                        </th>
                        <th className="px-4 py-3 text-right font-semibold text-[--color-foreground]">
                          Open
                        </th>
                        <th className="px-4 py-3 text-right font-semibold text-[--color-foreground]">
                          High
                        </th>
                        <th className="px-4 py-3 text-right font-semibold text-[--color-foreground]">
                          Low
                        </th>
                        <th className="px-4 py-3 text-right font-semibold text-[--color-foreground]">
                          Close
                        </th>
                        <th className="px-4 py-3 text-right font-semibold text-[--color-foreground]">
                          Volume
                        </th>
                        <th className="px-4 py-3 text-right font-semibold text-[--color-foreground]">
                          Return
                        </th>
                        <th className="px-4 py-3 text-right font-semibold text-[--color-foreground]">
                          HL Spread
                        </th>
                        <th className="px-4 py-3 text-right font-semibold text-[--color-foreground]">
                          OC Spread
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[--color-border]">
                      {displayData.map((bar) => {
                        const closeIsUp = bar.close > bar.open
                        const closeColor = closeIsUp
                          ? 'text-[--color-sentiment-pos]'
                          : 'text-[--color-sentiment-neg]'
                        const returnColor = (bar.daily_return ?? 0) >= 0
                          ? 'text-[--color-sentiment-pos]'
                          : 'text-[--color-sentiment-neg]'

                        return (
                          <tr key={bar.date} className="hover:bg-[--color-surface-2]">
                            <td className="px-4 py-3 text-[--color-foreground]">
                              {bar.date}
                            </td>
                            <td className="px-4 py-3 text-right text-[--color-muted-foreground]">
                              {formatCurrency(bar.open)}
                            </td>
                            <td className="px-4 py-3 text-right text-[--color-muted-foreground]">
                              {formatCurrency(bar.high)}
                            </td>
                            <td className="px-4 py-3 text-right text-[--color-muted-foreground]">
                              {formatCurrency(bar.low)}
                            </td>
                            <td className={cn('px-4 py-3 text-right font-medium', closeColor)}>
                              {formatCurrency(bar.close)}
                            </td>
                            <td className="px-4 py-3 text-right text-[--color-muted-foreground]">
                              {formatVolume(bar.volume)}
                            </td>
                            <td className={cn('px-4 py-3 text-right text-xs', returnColor)}>
                              {bar.daily_return !== null && bar.daily_return !== undefined
                                ? (bar.daily_return * 100).toFixed(2) + '%'
                                : '—'}
                            </td>
                            <td className="px-4 py-3 text-right text-xs text-[--color-muted-foreground]">
                              {bar.hl_spread ? bar.hl_spread.toFixed(2) : '—'}
                            </td>
                            <td className="px-4 py-3 text-right text-xs text-[--color-muted-foreground]">
                              {bar.oc_spread ? bar.oc_spread.toFixed(2) : '—'}
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </PageContainer>
  )
}
