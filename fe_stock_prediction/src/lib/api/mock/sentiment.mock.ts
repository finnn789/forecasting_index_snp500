import type { SentimentDistribution } from '../../../types/sentiment'

const days = (n: number) => {
  const d = new Date()
  d.setDate(d.getDate() + n)
  return d.toISOString().split('T')[0]
}

export const mockSentiment: SentimentDistribution = {
  ticker: 'GSPC',
  period: '2018-2024',
  avgScore: 0.18,
  dominant: 'positive',
  trend: 'improving',
  daily: Array.from({ length: 30 }, (_, i) => ({
    date: days(i - 30),
    avgScore: Math.random() * 0.8 - 0.2,
    positive: Math.round(Math.random() * 8 + 2),
    negative: Math.round(Math.random() * 4),
    neutral:  Math.round(Math.random() * 5 + 1),
    total: 0,
  })).map(d => ({ ...d, total: d.positive + d.negative + d.neutral })),
  recentNews: [
    { id: '1', title: 'S&P 500 Records Strong Q1 2024 Gains',        date: days(-1), source: 'Bloomberg',     sentiment: 'positive', score: 0.82 },
    { id: '2', title: 'Fed Holds Rates, Markets Rally on Tech',       date: days(-2), source: 'Reuters',       sentiment: 'positive', score: 0.61 },
    { id: '3', title: 'Inflation Data Sparks Volatility on Wall St',  date: days(-2), source: 'CNBC',          sentiment: 'negative', score: -0.44 },
    { id: '4', title: 'AI Sector Drives S&P 500 to Record Highs',    date: days(-3), source: 'WSJ',           sentiment: 'positive', score: 0.55 },
    { id: '5', title: 'Analysts Revise S&P 500 Year-End Targets Up', date: days(-4), source: 'MarketWatch',   sentiment: 'neutral',  score: 0.12 },
  ],
  data: [
    { label: 'neutral',  count: 10956, pct: 57.28 },
    { label: 'negative', count: 4777,  pct: 24.98 },
    { label: 'positive', count: 3394,  pct: 17.74 },
  ],
  sentiment_score_mean: 0.8192,
  sentiment_score_std: 0.1395,
  plot_hint: 'bar chart — x: label, y: count',
}
