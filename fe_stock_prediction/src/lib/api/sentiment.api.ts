import type { SentimentDistribution } from '../../types/sentiment'
import { apiFetch } from './client'
import { withMock } from './core/mock'
import { ENDPOINTS } from './endpoints'
import { mockSentiment } from './mock/sentiment.mock'

export const getSentiment = withMock(
  () =>apiFetch<SentimentDistribution>(`${ENDPOINTS.SENTIMENT}`),() => ({ ...mockSentiment }),500,
)
