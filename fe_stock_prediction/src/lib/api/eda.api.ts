import type {
  NewsPerYearItem,
  NewsPerDayData,
  HeadlineLengthData,
  SentimentDistribution,
} from '../../types/eda'
import { apiFetch } from './client'
import { withMock } from './core/mock'
import { ENDPOINTS } from './endpoints'
import {
  mockNewsPerYear,
  mockNewsPerDay,
  mockHeadlineLength,
  mockSentimentDistribution,
} from './mock/eda.mock'

// Respons nyata membungkus array di `{ data: [...], total, plot_hint }`.
// Unwrap ke array; tetap robust bila backend mengirim array langsung.
export const fetchNewsPerYear = withMock(
  async () => {
    const res = await apiFetch<{ data: NewsPerYearItem[] } | NewsPerYearItem[]>(
      ENDPOINTS.EDA_NEWS_PER_YEAR,
    )
    return Array.isArray(res) ? res : (res?.data ?? [])
  },
  () => mockNewsPerYear,
  400,
)

export const fetchNewsPerDay = withMock(
  () => apiFetch<NewsPerDayData>(ENDPOINTS.EDA_NEWS_PER_DAY),
  () => mockNewsPerDay,
  400,
)

export const fetchHeadlineLength = withMock(
  () => apiFetch<HeadlineLengthData>(ENDPOINTS.EDA_HEADLINE_LENGTH),
  () => mockHeadlineLength,
  400,
)

export const fetchSentimentDistribution = withMock(
  () => apiFetch<SentimentDistribution>(ENDPOINTS.EDA_SENTIMENT_DISTRIBUTION),
  () => mockSentimentDistribution,
  400,
)
