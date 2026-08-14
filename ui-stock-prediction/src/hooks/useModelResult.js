import { useCallback, useEffect, useState } from 'react'
import { fetchJson } from '../utils/api'

const IDLE = { data: null, loading: false, error: null }

/**
 * Hook untuk halaman Prediction: hasil training model yang sudah dipersist
 * di backend (bukan React state) untuk satu varian (Model A/Model B).
 *
 * - `resultPath` di-fetch otomatis on mount (pola useDataAnalysis.js).
 * - `backtest()` dipicu manual lewat tombol (bukan auto-fetch), mirip pola
 *   `startTraining` di useRandomSearchStream.js.
 */
export function useModelResult(resultPath) {
  const [result, setResult] = useState({ data: null, loading: true, error: null })
  const [backtestState, setBacktestState] = useState(IDLE)

  useEffect(() => {
    const controller = new AbortController()
    setResult({ data: null, loading: true, error: null })

    fetchJson(resultPath, { signal: controller.signal })
      .then((data) => setResult({ data, loading: false, error: null }))
      .catch((error) => {
        if (error.name === 'AbortError') return
        setResult({ data: null, loading: false, error: error.message })
      })

    return () => controller.abort()
  }, [resultPath])

  const backtest = useCallback(async (backtestPath) => {
    setBacktestState({ data: null, loading: true, error: null })
    try {
      const data = await fetchJson(backtestPath)
      setBacktestState({ data, loading: false, error: null })
    } catch (error) {
      setBacktestState({ data: null, loading: false, error: error.message })
    }
  }, [])

  return { result, backtest, backtestState }
}
