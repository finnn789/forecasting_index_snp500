import { useCallback, useEffect, useState } from 'react'
import { fetchJson, postJson } from '../utils/api'

const IDLE = { data: null, loading: false, error: null }

/**
 * Hook untuk halaman Prediction: hasil training model yang sudah dipersist
 * di backend (bukan React state) untuk satu varian (Model A/Model B).
 *
 * - `resultPath` di-fetch otomatis on mount (pola useDataAnalysis.js).
 * - `predict()`/`backtest()` dipicu manual lewat tombol (bukan auto-fetch),
 *   mirip pola `startTraining` di useRandomSearchStream.js.
 */
export function useModelResult(resultPath) {
  const [result, setResult] = useState({ data: null, loading: true, error: null })
  const [predictState, setPredictState] = useState(IDLE)
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

  const predict = useCallback(async (predictPath) => {
    setPredictState({ data: null, loading: true, error: null })
    try {
      const data = await postJson(predictPath)
      setPredictState({ data, loading: false, error: null })
    } catch (error) {
      setPredictState({ data: null, loading: false, error: error.message })
    }
  }, [])

  const backtest = useCallback(async (backtestPath) => {
    setBacktestState({ data: null, loading: true, error: null })
    try {
      const data = await fetchJson(backtestPath)
      setBacktestState({ data, loading: false, error: null })
    } catch (error) {
      setBacktestState({ data: null, loading: false, error: error.message })
    }
  }, [])

  return { result, predict, predictState, backtest, backtestState }
}
