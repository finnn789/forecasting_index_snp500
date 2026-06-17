import type { AsyncState } from '../types/async'
import type { StockHistory } from '../types/stock'
import { useAsync } from './core/useAsync'
import { getStockHistory } from '../lib/api/stock.api'

export function useStockData(ticker: string): AsyncState<StockHistory> & { refetch: () => void } {
  const useAsyncResult = useAsync(() => getStockHistory(ticker), [ticker], { enabled: !!ticker })

  return useAsyncResult
}
