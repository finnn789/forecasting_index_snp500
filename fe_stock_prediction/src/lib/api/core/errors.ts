export class ApiError extends Error {
  public readonly status: number
  public readonly code: string | undefined
  public readonly body: unknown

  constructor(status: number, message: string, code?: string, body?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.body = body
  }
}

export class NetworkError extends Error {
  constructor(message = 'Network error', cause?: unknown) {
    super(message)
    this.name = 'NetworkError'
    if (cause !== undefined) {
      this.cause = cause
    }
  }
}

export class TimeoutError extends Error {
  constructor(message = 'Request timed out') {
    super(message)
    this.name = 'TimeoutError'
  }
}

export class ParseError extends Error {
  constructor(message = 'Failed to parse response', cause?: unknown) {
    super(message)
    this.name = 'ParseError'
    if (cause !== undefined) {
      this.cause = cause
    }
  }
}

export function isApiError(value: unknown): value is ApiError {
  return value instanceof ApiError
}

export function isNetworkError(value: unknown): value is NetworkError {
  return value instanceof NetworkError
}

export function isTimeoutError(value: unknown): value is TimeoutError {
  return value instanceof TimeoutError
}

export function isParseError(value: unknown): value is ParseError {
  return value instanceof ParseError
}

export function toErrorMessage(e: unknown): string {
  if (isTimeoutError(e)) return 'Permintaan melebihi batas waktu. Coba lagi.'
  if (isNetworkError(e)) return 'Gagal terhubung ke server.'
  if (isApiError(e))     return e.message || `Error ${e.status}`
  return e instanceof Error ? e.message : 'Terjadi kesalahan tak terduga.'
}
