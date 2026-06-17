export interface OHLCVPoint {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  daily_return?: number | null
  hl_spread?: number
  oc_spread?: number
  ma_20?: number | null
  ma_50?: number | null
  ma_200?: number | null
  volatility_30?: number | null
}

export interface StockHistory {
  ticker: string
  bars: OHLCVPoint[]
}

export interface TimeSeriesPoint {
  date: string
  close: number
  volume: number
  is_crash_event: boolean
}

export interface StockTimeSeries {
  ticker: string
  period: string
  data: TimeSeriesPoint[]
}
