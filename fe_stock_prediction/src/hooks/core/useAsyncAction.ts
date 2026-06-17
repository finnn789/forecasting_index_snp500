import { useCallback, useRef, useState } from 'react'
import type { AsyncState } from '../../types/async'
import { toErrorMessage } from '../../lib/api/core/errors'

/**
 * Variant of useAsync for imperative actions (e.g. form submit).
 * Does NOT auto-run. Call `trigger(...args)` to execute the async fn.
 * Stale/unmounted updates are ignored via an `alive` flag per invocation.
 */
export function useAsyncAction<Args extends unknown[], T>(
  fn: (...args: Args) => Promise<T>,
): AsyncState<T> & { trigger: (...args: Args) => Promise<void> } {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    error: null,
    loading: false,
    status: 'idle',
  })

  const mountedRef = useRef(true)
  // Track each invocation so only the latest settles state
  const runIdRef = useRef(0)

  // Keep fn stable across renders — callers may pass an inline fn
  const fnRef = useRef(fn)
  fnRef.current = fn

  const trigger = useCallback(async (...args: Args): Promise<void> => {
    const runId = ++runIdRef.current
    setState({ data: null, error: null, loading: true, status: 'loading' })
    try {
      const data = await fnRef.current(...args)
      if (mountedRef.current && runId === runIdRef.current) {
        setState({ data, error: null, loading: false, status: 'success' })
      }
    } catch (e) {
      if (mountedRef.current && runId === runIdRef.current) {
        setState({ data: null, error: toErrorMessage(e), loading: false, status: 'error' })
      }
    }
  }, [])

  return { ...state, trigger }
}
