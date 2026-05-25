import { USE_MOCK } from '../constants'
import type { PredictionRequest, PredictionResult } from '../../types/prediction'
import { apiFetch } from './client'
import { ENDPOINTS } from './endpoints'
import { mockPrediction } from './mock/prediction.mock'

const delay = (ms: number) => new Promise(r => setTimeout(r, ms))

export async function getPrediction(req: PredictionRequest): Promise<PredictionResult> {
  if (USE_MOCK) {
    await delay(1200)
    return { ...mockPrediction, ticker: req.ticker }
  }
  return apiFetch<PredictionResult>(ENDPOINTS.PREDICT, {
    method: 'POST',
    body: JSON.stringify(req),
  })
}
