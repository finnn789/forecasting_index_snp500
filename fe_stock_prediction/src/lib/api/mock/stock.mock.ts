import type { StockHistory, StockTimeSeries } from '../../../types/stock'

const rand = (min: number, max: number) => Math.random() * (max - min) + min

const isoDay = (offset: number): string => {
  const d = new Date()
  d.setDate(d.getDate() + offset)
  return d.toISOString().split('T')[0]
}

const BASE_PRICES: Record<string, number> = {
  'GSPC':    4800,
  'BBCA.JK': 9250,
  'BBRI.JK': 5400,
  'TLKM.JK': 3780,
  'ASII.JK': 6200,
  'BMRI.JK': 6875,
  'GOTO.JK': 68,
  'UNVR.JK': 2750,
  'ICBP.JK': 11800,
}

export function mockStockHistory(ticker: string): StockHistory {
  const basePrice = BASE_PRICES[ticker] ?? 5000

  const bars = Array.from({ length: 30 }, (_, i) => {
    const close = basePrice + rand(-200, 200)
    return {
      date:   isoDay(i - 30),
      open:   close - rand(0, 80),
      high:   close + rand(10, 120),
      low:    close - rand(10, 120),
      close,
      volume: Math.round(rand(40_000_000, 120_000_000)),
    }
  })

  return { ticker, bars }
}

// ~60 trading days ending 2024-03-04, GSPC range 4500–5100
const START_CLOSE = 4600
export const mockStockTimeSeries: StockTimeSeries = {
  ticker: 'GSPC',
  period: '2018-2024',
  data: Array.from({ length: 60 }, (_, i) => {
    const close = Math.max(
      4500,
      Math.min(5100, START_CLOSE + i * 8 + rand(-60, 60)),
    )
    const dateObj = new Date('2024-01-02')
    dateObj.setDate(dateObj.getDate() + i)
    return {
      date: dateObj.toISOString().split('T')[0],
      close,
      volume: Math.round(rand(3_000_000_000, 5_000_000_000)),
      is_crash_event: false,
    }
  }),
}
