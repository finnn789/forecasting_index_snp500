import type { StockHistory, OHLCVPoint, StockTimeSeries } from '../../types/stock'
import { apiFetch } from './client'
import { withMock } from './core/mock'
import { ENDPOINTS } from './endpoints'
import { mockStockHistory, mockStockTimeSeries } from './mock/stock.mock'

async function normalizeStockHistory(ticker: string): Promise<StockHistory> {
  const data = await apiFetch<StockHistory | OHLCVPoint[]>(`${ENDPOINTS.STOCK_HISTORY}?ticker=${ticker}`)

  // If data is already StockHistory format, return as-is
  if (!Array.isArray(data)) {
    return data as StockHistory
  }

  // If data is direct array, wrap it in StockHistory format
  return {
    ticker,
    bars: data as OHLCVPoint[],
  }
}

export const getStockHistory = withMock(normalizeStockHistory, mockStockHistory, 400)

export const getStockTimeSeries = withMock(
  () => apiFetch<StockTimeSeries>(ENDPOINTS.STOCK_TIMESERIES),
  () => ({ ...mockStockTimeSeries }),
  600,
)
