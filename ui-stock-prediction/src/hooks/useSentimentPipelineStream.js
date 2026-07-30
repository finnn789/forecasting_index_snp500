import { useCallback, useEffect, useRef, useState } from 'react'
import { API_BASE } from '../utils/api'

const INITIAL_STATE = {
  status: 'idle', // idle | running | done | error
  step: null,
  pct: 0,
  msg: null,
  result: null,
  error: null,
}

/**
 * Hook untuk menjalankan sentiment pipeline (scoring FinBERT + agregasi
 * harian) via SSE (`POST /sentiment/pipeline/run`). Event flow satu level
 * (bukan bersarang seperti Random Search): loading_data -> filtering ->
 * loading_model -> model_ready -> inference -> aggregating -> saving ->
 * done/error.
 */
export function useSentimentPipelineStream() {
  const [state, setState] = useState(INITIAL_STATE)
  const abortRef = useRef(null)

  useEffect(() => {
    return () => abortRef.current?.abort()
  }, [])

  const reset = useCallback(() => {
    abortRef.current?.abort()
    setState(INITIAL_STATE)
  }, [])

  const run = useCallback(async () => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setState({ ...INITIAL_STATE, status: 'running' })

    try {
      const res = await fetch(`${API_BASE}/sentiment/pipeline/run`, {
        method: 'POST',
        signal: controller.signal,
      })

      if (!res.ok || !res.body) {
        throw new Error(`Pipeline gagal dimulai (${res.status})`)
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const chunks = buffer.split('\n\n')
        buffer = chunks.pop() ?? ''

        for (const chunk of chunks) {
          const line = chunk.trim()
          if (!line.startsWith('data:')) continue

          const jsonStr = line.slice(5).trim()
          if (!jsonStr) continue

          let event
          try {
            event = JSON.parse(jsonStr)
          } catch {
            continue
          }

          if (event.step === 'done') {
            setState((prev) => ({
              ...prev,
              status: 'done',
              step: 'done',
              pct: 100,
              msg: event.msg,
              result: event.result,
            }))
          } else if (event.step === 'error') {
            setState((prev) => ({ ...prev, status: 'error', error: event.msg }))
          } else {
            setState((prev) => ({ ...prev, step: event.step, pct: event.pct, msg: event.msg }))
          }
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') return
      setState((prev) => ({ ...prev, status: 'error', error: err.message }))
    }
  }, [])

  return { ...state, run, reset }
}
