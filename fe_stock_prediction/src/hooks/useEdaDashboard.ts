import { useEffect, useState } from 'react'
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
import type { AsyncState, AsyncStatus } from '../types/async'
import { toErrorMessage } from '../lib/api/core/errors'

function pending<T>(): AsyncState<T> {
  return { data: null, loading: true, error: null, status: 'loading' }
}

function resolved<T>(value: T): AsyncState<T> {
  return { data: value, loading: false, error: null, status: 'success' }
}

function rejected<T>(reason: unknown): AsyncState<T> {
  return { data: null, loading: false, error: toErrorMessage(reason), status: 'error' as AsyncStatus }
}

export function useEdaDashboard() {
  const [newsPerYear,   setNewsPerYear]   = useState<AsyncState<NewsPerYearItem[]>>(pending)
  const [newsPerDay,    setNewsPerDay]    = useState<AsyncState<NewsPerDayData>>(pending)
  const [headlineLength, setHeadlineLength] = useState<AsyncState<HeadlineLengthData>>(pending)
  const [sentimentDist, setSentimentDist] = useState<AsyncState<SentimentDistribution>>(pending)

  useEffect(() => {
    let alive = true
    Promise.allSettled([
      fetchNewsPerYear(),
      fetchNewsPerDay(),
      fetchHeadlineLength(),
      fetchSentimentDistribution(),
    ]).then(([y, d, h, s]) => {
      if (!alive) return
      setNewsPerYear(y.status === 'fulfilled' ? resolved(y.value) : rejected(y.reason))
      setNewsPerDay(d.status === 'fulfilled' ? resolved(d.value) : rejected(d.reason))
      setHeadlineLength(h.status === 'fulfilled' ? resolved(h.value) : rejected(h.reason))
      setSentimentDist(s.status === 'fulfilled' ? resolved(s.value) : rejected(s.reason))
    })
    return () => { alive = false }
  }, [])

  return { newsPerYear, newsPerDay, headlineLength, sentimentDist }
}
