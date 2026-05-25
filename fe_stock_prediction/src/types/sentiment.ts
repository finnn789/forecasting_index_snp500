export type SentimentLabel = 'positive' | 'negative' | 'neutral'

export interface NewsItem {
  id: string
  title: string
  date: string
  source: string
  sentiment: SentimentLabel
  score: number    // -1 sampai 1
  ticker?: string
}

export interface DailySentiment {
  date: string
  avgScore: number
  positive: number
  negative: number
  neutral: number
  total: number
}

export interface SentimentSummary {
  ticker: string
  period: string
  avgScore: number
  dominant: SentimentLabel
  trend: 'improving' | 'declining' | 'stable'
  daily: DailySentiment[]
  recentNews: NewsItem[]
}
