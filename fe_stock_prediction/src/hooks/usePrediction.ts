import { useState } from 'react'
import type { PredictionRequest, PredictionResult } from '../types/prediction'
import { getPrediction } from '../lib/api/prediction.api'

export function usePrediction() {
  const [result, setResult]   = useState<PredictionResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState<string | null>(null)

  const predict = async (req: PredictionRequest) => {
    setLoading(true)
    setError(null)
    try {
      const data = await getPrediction(req)
      setResult(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Prediksi gagal')
    } finally {
      setLoading(false)
    }
  }

  return { result, loading, error, predict }
}
