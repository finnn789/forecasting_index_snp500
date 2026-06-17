export const TICKERS = [
  { value: 'GSPC', label: 'GSPC — S&P 500' },
] as const

export const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true' || import.meta.env.VITE_USE_MOCK === undefined
export const API_URL  = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
