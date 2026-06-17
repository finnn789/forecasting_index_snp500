export interface ApiEnvelope<T> {
  success?: boolean
  data: T
  error?: { code?: string; message?: string; detail?: string } | null
  message?: string
}

export function isEnvelope(value: unknown): value is ApiEnvelope<unknown> {
  return (
    value !== null &&
    typeof value === 'object' &&
    'data' in (value as object)
  )
}
