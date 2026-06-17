import type {
  NewsPerYearItem,
  NewsPerDayData,
  HeadlineLengthData,
  SentimentDistribution,
} from '../../../types/eda'

export const mockNewsPerYear: NewsPerYearItem[] = [
  { year: 2019, count: 2341 },
  { year: 2020, count: 3187 },
  { year: 2021, count: 4052 },
  { year: 2022, count: 5219 },
  { year: 2023, count: 6481 },
  { year: 2024, count: 4873 },
]

const today = new Date()
const isoDay = (offset: number): string => {
  const d = new Date(today)
  d.setDate(d.getDate() + offset)
  return d.toISOString().split('T')[0]
}

const perDayData = Array.from({ length: 30 }, (_, i) => ({
  date: isoDay(i - 30),
  count: Math.round(60 + Math.random() * 80),
}))

const counts = perDayData.map(d => d.count)
const maxCount = Math.max(...counts)
const minCount = Math.min(...counts)
const maxIdx = counts.indexOf(maxCount)
const minIdx = counts.indexOf(minCount)

export const mockNewsPerDay: NewsPerDayData = {
  mean: parseFloat((counts.reduce((a, b) => a + b, 0) / counts.length).toFixed(1)),
  max: maxCount,
  min: minCount,
  max_date: perDayData[maxIdx].date,
  min_date: perDayData[minIdx].date,
  data: perDayData,
}

export const mockHeadlineLength: HeadlineLengthData = {
  char_mean: 87.4,
  char_std: 22.1,
  char_min: 18,
  char_max: 214,
  word_mean: 13.8,
  word_std: 3.7,
  word_min: 3,
  word_max: 38,
}

export const mockSentimentDistribution: SentimentDistribution = {
  data: [
    { label: 'positive', count: 14382, pct: 55.3 },
    { label: 'neutral',  count: 7210,  pct: 27.7 },
    { label: 'negative', count: 4408,  pct: 17.0 },
  ],
  sentiment_score_mean: 0.1847,
  sentiment_score_std: 0.3912,
  plot_hint: 'pie',
}
