import type {
  DirectionPrediction,
  ModelInfo,
  BacktestResult,
} from '../../../types/prediction'

export const mockDirectionPrediction: DirectionPrediction = {
  ticker: 'GSPC',
  as_of_date: '2024-03-04',
  target_date: '2024-03-05',
  direction: 'up',
  probability_up: 0.529294,
  confidence: 0.529294,
  window: 20,
  features_used: ['Open', 'High', 'Low', 'Close', 'Volume', 'sentiment_mean'],
  model_version: '2026-06-11T11:42:06Z',
}

export const mockModelInfo: ModelInfo = {
  is_available: true,
  artifact_path: 'data/artifacts/lstm_weights',
  window: 20,
  features_used: ['Open', 'High', 'Low', 'Close', 'Volume', 'sentiment_mean'],
  n_features: 6,
  metrics: {
    val_acc: 0.5466666666666666,
    val_f1: 0.7068965517241379,
    val_auc: 0.5148652957117806,
    test_acc: 0.6086956521739131,
    test_f1: 0.7567567567567568,
    test_auc: 0.38095238095238093,
  },
  trained_at: '2026-06-11T11:44:11.567432+00:00',
}

// 23-point backtest mirroring real test split (2024-01-30 → 2024-03-04)
// Model always predicts "up" → tn=0, fn=0, tp=14, fp=9
const CLOSES = [
  4924.97, 4845.65, 4958.61, 4997.91, 5026.61,
  5088.8,  5069.53, 5005.57, 4958.61, 4967.23,
  4920.31, 4845.65, 4958.61, 5137.08, 5109.9,
  5088.8,  5057.64, 5026.61, 4978.87, 4942.81,
  4995.06, 5086.13, 5078.65,
]
const CORRECT = [
  false, true, true, true, true,
  false, false, true, false, true,
  false, true, true, true, false,
  false, true, true, false, true,
  true, true, false,
]

const startDate = new Date('2024-01-30')
const tradingDays = CLOSES.map((close, i) => {
  const d = new Date(startDate)
  d.setDate(startDate.getDate() + i)
  const iso = d.toISOString().split('T')[0]
  return {
    date: iso,
    close,
    actual_direction: (CORRECT[i] ? 'up' : 'down') as 'up' | 'down',
    predicted_direction: 'up' as const,
    probability_up: 0.529 + (i % 3) * 0.0003,
    correct: CORRECT[i],
  }
})

export const mockBacktest: BacktestResult = {
  ticker: 'GSPC',
  window: 20,
  split: 'test',
  n_samples: 23,
  metrics: {
    accuracy: 0.608696,
    precision: 0.608696,
    recall: 1.0,
    f1: 0.756757,
    auc: 0.380952,
  },
  confusion_matrix: { tp: 14, tn: 0, fp: 9, fn: 0 },
  points: tradingDays,
}
