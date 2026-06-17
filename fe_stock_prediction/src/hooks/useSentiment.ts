import type { AsyncState } from '../types/async'
import type { SentimentDistribution } from '../types/sentiment'
import { useAsync } from './core/useAsync'
import { getSentiment } from '../lib/api/sentiment.api'

export function useSentiment(ticker: string): AsyncState<SentimentDistribution> & { refetch: () => void } {
  return useAsync(
    () => getSentiment(),
    [ticker],
    { enabled: !!ticker },
  )
}
