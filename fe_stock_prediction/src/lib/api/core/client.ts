import { API_URL } from '../../constants'
import { ApiError, NetworkError, TimeoutError, ParseError } from './errors'
import { isEnvelope } from './envelope'

export type ApiFetchOptions = RequestInit & { timeoutMs?: number }

export async function apiFetch<T>(
  path: string,
  options?: ApiFetchOptions,
): Promise<T> {
  const { timeoutMs = 15000, ...fetchOptions } = options ?? {}
  const url = `${API_URL}${path}`

  const controller = new AbortController()
  let timedOut = false
  const timer = setTimeout(() => {
    timedOut = true
    controller.abort()
  }, timeoutMs)

  try {
    let res: Response
    try {
      res = await fetch(url, {
        ...fetchOptions,
        headers: { 'Content-Type': 'application/json', ...fetchOptions.headers },
        signal: controller.signal,
      })
    } catch (err) {
      const e = err as Error
      if (timedOut || e.name === 'AbortError') {
        throw new TimeoutError(`Request to ${path} timed out after ${timeoutMs}ms`)
      }
      throw new NetworkError(`Network error while fetching ${path}`, err)
    }

    if (!res.ok) {
      let message = res.statusText
      let code: string | undefined
      let body: unknown

      try {
        body = await res.json()
        const b = body as Record<string, unknown>
        const errObj = b['error'] as Record<string, unknown> | null | undefined
        message =
          (errObj?.['message'] as string | undefined) ??
          (errObj?.['detail'] as string | undefined) ??
          (b['detail'] as string | undefined) ??
          (b['message'] as string | undefined) ??
          res.statusText
        code = errObj?.['code'] as string | undefined
      } catch {
        try {
          message = await res.text()
        } catch {
          message = res.statusText
        }
      }

      throw new ApiError(res.status, message, code, body)
    }

    // Handle 204 No Content or empty body
    if (res.status === 204 || res.headers.get('content-length') === '0') {
      return undefined as T
    }

    let json: unknown
    try {
      json = await res.json()
    } catch (err) {
      throw new ParseError('Failed to parse response JSON', err)
    }

    if (isEnvelope(json)) {
      return json.data as T
    }
    return json as T
  } finally {
    clearTimeout(timer)
  }
}
