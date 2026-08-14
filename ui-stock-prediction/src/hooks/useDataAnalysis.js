import { useCallback, useEffect, useState } from 'react'
import { fetchJson } from '../utils/api'

export function useDataAnalysis(path) {
  const [state, setState] = useState({ data: null, loading: true, error: null })
  const [reloadIndex, setReloadIndex] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    setState({ data: null, loading: true, error: null })

    fetchJson(path, { signal: controller.signal })
      .then((data) => setState({ data, loading: false, error: null }))
      .catch((error) => {
        if (error.name === 'AbortError') return
        setState({ data: null, loading: false, error: error.message })
      })

    return () => controller.abort()
  }, [path, reloadIndex])

  const refetch = useCallback(() => setReloadIndex((i) => i + 1), [])

  return { ...state, refetch }
}
