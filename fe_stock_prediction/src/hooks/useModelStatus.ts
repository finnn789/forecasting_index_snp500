import type { ModelInfo } from '../types/prediction'
import type { AsyncState } from '../types/async'
import { useAsync } from './core/useAsync'
import { getModelStatus } from '../lib/api/prediction.api'

/**
 * Auto-fetching hook for LSTM model status.
 *
 * Fetches on mount and exposes:
 *   data    — ModelInfo (null until first successful fetch)
 *   loading — true while request is in flight
 *   error   — error message if fetch failed, null otherwise
 *   status  — 'idle' | 'loading' | 'success' | 'error'
 *   refetch — re-trigger the fetch
 */
export function useModelStatus(): AsyncState<ModelInfo> & { refetch: () => void } {
  return useAsync(() => getModelStatus(), [])
}
