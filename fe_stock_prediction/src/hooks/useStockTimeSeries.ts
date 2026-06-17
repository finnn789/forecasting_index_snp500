import type { AsyncState } from '../types/async'
import type { StockTimeSeries } from '../types/stock'
import { useAsync } from './core/useAsync'
import { getStockTimeSeries } from '../lib/api/stock.api'

/**
 * Auto-fetch deret waktu harga (Close & Volume) GSPC 2018–2024.
 * Dipakai untuk chart harga historis di StockDataPage.
 */
export function useStockTimeSeries(): AsyncState<StockTimeSeries> & { refetch: () => void } {
  return useAsync(() => getStockTimeSeries(), [])
}
