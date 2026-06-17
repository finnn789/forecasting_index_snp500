import { useCallback, useEffect, useState } from 'react'
import type { AsyncState } from '../../types/async'
import { toErrorMessage } from '../../lib/api/core/errors'

export function useAsync<T>(
  fn: () => Promise<T>, 
  deps: unknown[], 
  opts?: { enabled?: boolean },
): AsyncState<T> & { refetch: () => void } {
  const enabled = opts?.enabled ?? true

  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    error: null,
    loading: enabled,
    status: enabled ? 'loading' : 'idle',
  })

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const run = useCallback(() => {
    let alive = true
    setState(s => ({ ...s, loading: true, status: 'loading', error: null }))
    fn()
      .then(data => {
        if (alive) setState({ data, error: null, loading: false, status: 'success' })
      })
      .catch(e => {
        if (alive) setState({ data: null, error: toErrorMessage(e), loading: false, status: 'error' })
      })
    return () => { alive = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => {
    if (!enabled) return
    return run()
  }, [run, enabled])

  return { ...state, refetch: () => { run() } }
}
