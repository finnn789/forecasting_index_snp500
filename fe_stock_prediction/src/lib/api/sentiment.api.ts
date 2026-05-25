import { USE_MOCK } from '../constants'
import type { SentimentSummary } from '../../types/sentiment'
import { apiFetch } from './client'
import { ENDPOINTS } from './endpoints'
import { mockSentiment } from './mock/sentiment.mock'

const delay = (ms: number) => new Promise(r => setTimeout(r, ms))

export async function getSentiment(ticker: string): Promise<SentimentSummary> {
  if (USE_MOCK) {
    await delay(500)
    return { ...mockSentiment, ticker }
  }
  return apiFetch<SentimentSummary>(`${ENDPOINTS.SENTIMENT}?ticker=${ticker}`)
}
