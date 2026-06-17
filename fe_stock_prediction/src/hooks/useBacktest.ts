import type { BacktestResult } from '../types/prediction'
import type { AsyncState } from '../types/async'
import { useAsync } from './core/useAsync'
import { getBacktest } from '../lib/api/prediction.api'

/**
 * Auto-fetching hook for backtest results (test split).
 *
 * Fetches on mount and exposes:
 *   data    — BacktestResult (null until first successful fetch)
 *   loading — true while request is in flight
 *   error   — error message if fetch failed, null otherwise
 *   status  — 'idle' | 'loading' | 'success' | 'error'
 *   refetch — re-trigger the fetch
 */
export function useBacktest(): AsyncState<BacktestResult> & { refetch: () => void } {
  return useAsync(() => getBacktest('test'), [])
}
