import { useState, useEffect } from 'react'
import {
  fetchNewsPerYear,
  fetchNewsPerDay,
  fetchHeadlineLength,
  fetchSentimentDistribution,
} from '../lib/api/eda.api'
import type {
  NewsPerYearItem,
  NewsPerDayData,
  HeadlineLengthData,
  SentimentDistribution,
} from '../types/eda'

type AsyncState<T> = { response: T | null; loading: boolean; error: string | null }

function pending<T>(): AsyncState<T> {
  return { response: null, loading: true, error: null }
}

function resolved<T>(data: T): AsyncState<T> {
  return { response: data, loading: false, error: null }
}

function rejected<T>(err: unknown): AsyncState<T> {
  const msg = err instanceof Error ? err.message : String(err)
  return { response: null, loading: false, error: msg }
}

export function useEdaDashboard() {
  const [newsPerYear, setNewsPerYear] = useState<AsyncState<NewsPerYearItem[]>>(pending)
  const [newsPerDay, setNewsPerDay] = useState<AsyncState<NewsPerDayData>>(pending)
  const [headlineLength, setHeadlineLength] = useState<AsyncState<HeadlineLengthData>>(pending)
  const [sentimentDist, setSentimentDist] = useState<AsyncState<SentimentDistribution>>(pending)

  useEffect(() => {
    Promise.allSettled([
      fetchNewsPerYear(),
      fetchNewsPerDay(),
      fetchHeadlineLength(),
      fetchSentimentDistribution(),
    ]).then(([y, d, h, s]) => {
      setNewsPerYear(y.status === 'fulfilled' ? resolved(y.value) : rejected(y.reason))
      setNewsPerDay(d.status === 'fulfilled' ? resolved(d.value) : rejected(d.reason))
      setHeadlineLength(h.status === 'fulfilled' ? resolved(h.value) : rejected(h.reason))
      setSentimentDist(s.status === 'fulfilled' ? resolved(s.value) : rejected(s.reason))
    })
  }, [])

  return { newsPerYear, newsPerDay, headlineLength, sentimentDist }
}
