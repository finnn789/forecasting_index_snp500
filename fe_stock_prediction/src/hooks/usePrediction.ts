import type { PredictionRequest, DirectionPrediction } from '../types/prediction'
import type { AsyncState } from '../types/async'
import { useAsyncAction } from './core/useAsyncAction'
import { predictDirection } from '../lib/api/prediction.api'

/**
 * Imperative hook for triggering a direction prediction.
 *
 * Returns AsyncState<DirectionPrediction> fields:
 *   data    — the prediction result (null until first successful predict call)
 *   loading — true while a prediction request is in flight
 *   error   — error message from last failed attempt, null otherwise
 *   status  — 'idle' | 'loading' | 'success' | 'error'
 *   predict — call predict(req) to trigger a new prediction
 */
export function usePrediction(): AsyncState<DirectionPrediction> & { predict: (req: PredictionRequest) => Promise<void> } {
  const { trigger, ...state } = useAsyncAction(
    (req: PredictionRequest) => predictDirection(req),
  )
  return { ...state, predict: trigger }
}
