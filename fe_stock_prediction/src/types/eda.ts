export interface NewsPerYearItem {
  year: number
  count: number
}

export interface NewsPerDayData {
  mean: number
  max: number
  min: number
  max_date: string
  min_date: string
  data: { date: string; count: number }[]
}

export interface HeadlineLengthData {
  char_mean: number
  char_std: number
  char_min: number
  char_max: number
  word_mean: number
  word_std: number
  word_min: number
  word_max: number
}

export interface SentimentDistributionItem {
  label: 'positive' | 'negative' | 'neutral'
  count: number
  pct: number
}

export interface SentimentDistribution {
  data: SentimentDistributionItem[]
  sentiment_score_mean: number
  sentiment_score_std: number
  plot_hint: string
}
