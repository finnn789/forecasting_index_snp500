import { useEffect, useState } from 'react'
import type { SentimentSummary } from '../types/sentiment'
import { getSentiment } from '../lib/api/sentiment.api'

export function useSentiment(ticker: string) {
  const [data, setData]       = useState<SentimentSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState<string | null>(null)

  useEffect(() => {
    if (!ticker) return
    setLoading(true)
    setError(null)

    getSentiment(ticker)
      .then(setData)
      .catch(e => setError(e instanceof Error ? e.message : 'Gagal mengambil data sentimen'))
      .finally(() => setLoading(false))
  }, [ticker])

  return { data, loading, error }
}
