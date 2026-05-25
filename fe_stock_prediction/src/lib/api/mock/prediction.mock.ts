import type { PredictionResult } from '../../../types/prediction'

const today = new Date()
const days = (n: number) => {
  const d = new Date(today)
  d.setDate(d.getDate() + n)
  return d.toISOString().split('T')[0]
}

const basePrice = 9250
const rand = (min: number, max: number) => Math.random() * (max - min) + min

export const mockPrediction: PredictionResult = {
  ticker: 'BBCA.JK',
  predictionDate: days(1),
  predictedClose: 9425,
  change: 1.89,
  direction: 'up',
  ensemble: {
    lstmWeight: 0.68,
    sentimentWeight: 0.32,
    confidence: 0.74,
  },
  history: Array.from({ length: 30 }, (_, i) => {
    const close = basePrice + rand(-200, 200)
    return {
      date: days(i - 30),
      open:   close - rand(0, 80),
      high:   close + rand(10, 120),
      low:    close - rand(10, 120),
      close,
      volume: Math.round(rand(40_000_000, 120_000_000)),
    }
  }),
  forecast: Array.from({ length: 7 }, (_, i) => ({
    date: days(i + 1),
    predicted: 9250 + (i + 1) * 25 + rand(-30, 30),
    upper: 9250 + (i + 1) * 25 + 80,
    lower: 9250 + (i + 1) * 25 - 80,
  })),
  metrics: { rmse: 142.3, mae: 98.7, mape: 1.54 },
}
