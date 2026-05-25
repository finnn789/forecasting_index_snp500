export interface OHLCVPoint {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface PredictionPoint {
  date: string
  predicted: number
  actual?: number
  upper?: number
  lower?: number
}

export interface EnsembleWeight {
  lstmWeight: number      // 0-1
  sentimentWeight: number // 0-1
  confidence: number      // 0-1
}

export interface PredictionResult {
  ticker: string
  predictionDate: string
  predictedClose: number
  change: number          // persen dari close terakhir
  direction: 'up' | 'down' | 'flat'
  ensemble: EnsembleWeight
  history: OHLCVPoint[]
  forecast: PredictionPoint[]
  metrics: {
    rmse: number
    mae: number
    mape: number
  }
}

export interface PredictionRequest {
  ticker: string
  date?: string
}
