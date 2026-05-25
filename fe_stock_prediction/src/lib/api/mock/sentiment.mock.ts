import type { SentimentSummary } from '../../../types/sentiment'

const days = (n: number) => {
  const d = new Date()
  d.setDate(d.getDate() + n)
  return d.toISOString().split('T')[0]
}

export const mockSentiment: SentimentSummary = {
  ticker: 'BBCA.JK',
  period: '30 hari terakhir',
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
    { id: '1', title: 'BBCA Catat Laba Bersih Rp12,8 T di Q1 2024', date: days(-1), source: 'Bisnis.com',    sentiment: 'positive', score: 0.82 },
    { id: '2', title: 'BI Tahan Suku Bunga, Perbankan Diuntungkan',   date: days(-2), source: 'Kontan',       sentiment: 'positive', score: 0.61 },
    { id: '3', title: 'Volatilitas Rupiah Tekan Saham Perbankan',     date: days(-2), source: 'CNBC Indonesia', sentiment: 'negative', score: -0.44 },
    { id: '4', title: 'BBCA Ekspansi Digital Banking ke Segmen UMKM', date: days(-3), source: 'Detik Finance', sentiment: 'positive', score: 0.55 },
    { id: '5', title: 'Analis: Target Harga BBCA Direvisi ke 10.500', date: days(-4), source: 'Bloomberg',    sentiment: 'neutral',  score: 0.12 },
  ],
}
