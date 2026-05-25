export const TICKERS = [
  { value: 'BBCA.JK', label: 'BBCA — Bank Central Asia' },
  { value: 'BBRI.JK', label: 'BBRI — Bank Rakyat Indonesia' },
  { value: 'TLKM.JK', label: 'TLKM — Telkom Indonesia' },
  { value: 'ASII.JK', label: 'ASII — Astra International' },
  { value: 'BMRI.JK', label: 'BMRI — Bank Mandiri' },
  { value: 'GOTO.JK', label: 'GOTO — GoTo Group' },
  { value: 'UNVR.JK', label: 'UNVR — Unilever Indonesia' },
  { value: 'ICBP.JK', label: 'ICBP — Indofood CBP' },
] as const

export const PIPELINE_STAGES = [
  { id: 'fetch',     label: 'Fetch Data',         description: 'Unduh OHLCV & berita dari Yahoo Finance' },
  { id: 'clean',     label: 'Cleaning',            description: 'Normalisasi, handle missing values' },
  { id: 'sentiment', label: 'Analisis Sentimen',   description: 'FinBERT scoring per headline' },
  { id: 'feature',   label: 'Feature Engineering', description: 'Gabung sentimen + indikator teknikal' },
  { id: 'train',     label: 'Training LSTM',        description: 'Latih model LSTM dengan data baru' },
  { id: 'evaluate',  label: 'Evaluasi',             description: 'Hitung RMSE, MAE, MAPE' },
] as const

export type PipelineStageId = (typeof PIPELINE_STAGES)[number]['id']

export const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true' || import.meta.env.VITE_USE_MOCK === undefined
export const API_URL  = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
