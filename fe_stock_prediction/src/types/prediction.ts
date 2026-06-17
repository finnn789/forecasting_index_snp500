export interface PredictionRequest {
  ticker?: string   // default "GSPC"
}

export interface DirectionPrediction {
  ticker: string
  as_of_date: string          // tanggal data terakhir, ISO
  target_date: string         // tanggal yang diprediksi
  direction: 'up' | 'down'
  probability_up: number      // 0..1
  confidence: number          // 0..1 = max(p, 1-p)
  window: number              // 20
  features_used: string[]     // ["Open","High","Low","Close","Volume","sentiment_mean"]
  model_version: string | null
}

export interface ModelInfo {
  is_available: boolean
  artifact_path: string
  window: number | null
  features_used: string[]
  n_features: number | null
  metrics: {
    val_acc: number; val_f1: number; val_auc: number
    test_acc: number; test_f1: number; test_auc: number
  } | null
  trained_at: string | null
}

export interface BacktestPoint {
  date: string
  close: number
  actual_direction: 'up' | 'down'
  predicted_direction: 'up' | 'down'
  probability_up: number
  correct: boolean
}

export interface ConfusionMatrix { tp: number; tn: number; fp: number; fn: number }

export interface BacktestResult {
  ticker: string
  window: number
  split: string
  n_samples: number
  metrics: Record<string, number>   // accuracy, precision, recall, f1, auc
  confusion_matrix: ConfusionMatrix
  points: BacktestPoint[]
}
