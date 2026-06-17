import type {
  PredictionRequest,
  DirectionPrediction,
  ModelInfo,
  BacktestResult,
} from '../../types/prediction'
import { apiFetch } from './client'
import { withMock } from './core/mock'
import { ENDPOINTS } from './endpoints'
import {
  mockDirectionPrediction,
  mockModelInfo,
  mockBacktest,
} from './mock/prediction.mock'

export const predictDirection = withMock(
  (req: PredictionRequest) =>
    apiFetch<DirectionPrediction>(ENDPOINTS.PREDICT, {
      method: 'POST',
      body: JSON.stringify(req),
    }),
  (_req: PredictionRequest) => ({ ...mockDirectionPrediction }),
  1200,
)

export const getModelStatus = withMock(
  () => apiFetch<ModelInfo>(ENDPOINTS.PREDICT_STATUS),
  () => ({ ...mockModelInfo }),
  400,
)

export const getBacktest = withMock(
  (split = 'test') =>
    apiFetch<BacktestResult>(`${ENDPOINTS.PREDICT_BACKTEST}?split=${split}`),
  (_split = 'test') => ({ ...mockBacktest }),
  800,
)
