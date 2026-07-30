export function fmtNum(value, digits = 4) {
  return typeof value === 'number' ? value.toFixed(digits) : '-'
}

export function fmtPct(value) {
  return typeof value === 'number' ? `${(value * 100).toFixed(2)}%` : '-'
}
