export { formatDate } from './utils'

/**
 * Safe number formatter. Returns '—' for null / undefined / non-finite values.
 */
export function fmt(n: number | null | undefined, decimals = 1): string {
  return n != null && isFinite(n) ? n.toFixed(decimals) : '—'
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

export function formatVolume(value: number): string {
  const millions = value / 1_000_000
  if (millions >= 1000) {
    return (millions / 1000).toFixed(1) + 'B'
  }
  return millions.toFixed(1) + 'M'
}

export function formatPercent(value: number, decimals = 2): string {
  return value.toFixed(decimals) + '%'
}

export function formatNumber(value: number, decimals = 0): string {
  return new Intl.NumberFormat('id-ID', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}
