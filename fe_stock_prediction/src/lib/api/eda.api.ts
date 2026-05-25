import { apiFetch } from './client'
import { ENDPOINTS } from './endpoints'
import type {
  NewsPerYearItem,
  NewsPerDayData,
  HeadlineLengthData,
  SentimentDistribution,
} from '../../types/eda'

export const fetchNewsPerYear = () =>
  apiFetch<NewsPerYearItem[]>(ENDPOINTS.EDA_NEWS_PER_YEAR)


export const fetchNewsPerDay = () =>
  apiFetch<NewsPerDayData>(ENDPOINTS.EDA_NEWS_PER_DAY)

export const fetchHeadlineLength = () =>
  apiFetch<HeadlineLengthData>(ENDPOINTS.EDA_HEADLINE_LENGTH)

export const fetchSentimentDistribution = () =>
  apiFetch<SentimentDistribution>(ENDPOINTS.EDA_SENTIMENT_DISTRIBUTION)
