export interface NewsPerYearItem {
  year: number
  count: number
}

export interface NewsPerDayData {
  mean: number
  max: number
  min: number
  data: { date: string; count: number }[]
}

export interface HeadlineLengthData {
  avg_chars: number
  avg_words: number
  char_bins: { label: string; count: number }[]
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
