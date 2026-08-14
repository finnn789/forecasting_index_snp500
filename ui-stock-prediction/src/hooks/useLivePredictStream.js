import { useCallback, useEffect, useRef, useState } from 'react'
import { API_BASE } from '../utils/api'

const INITIAL_STATE = {
  status: 'idle', // idle | running | done | error
  stage: null, // tipe event terakhir yang diterima (dipakai step indicator)
  events: [], // seluruh event mentah, urut (dipakai step indicator & debug)
  result: null, // payload event "done"
  error: null,
}

/**
 * Hook untuk menjalankan pipeline "Prediksi Live" (fetch OHLCV+berita ->
 * preprocessing -> inference) via SSE. Stream FLAT (start -> fetching_ohlcv ->
 * fetching_ohlcv_done -> fetching_news -> fetching_news_done -> preprocessing ->
 * preprocessing_done -> inferring -> done/error) — pola sama useManualTrainStream,
 * cuma nama event beda (bukan epoch loop, tapi tahapan pipeline data live).
 */
export function useLivePredictStream(endpoint) {
  const [state, setState] = useState(INITIAL_STATE)
  const abortRef = useRef(null)

  useEffect(() => {
    return () => abortRef.current?.abort()
  }, [])

  const reset = useCallback(() => {
    abortRef.current?.abort()
    setState(INITIAL_STATE)
  }, [])

  const start = useCallback(async () => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setState({ ...INITIAL_STATE, status: 'running' })

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        signal: controller.signal,
      })

      if (!res.ok || !res.body) {
        throw new Error(`Prediksi gagal dimulai (${res.status})`)
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

          applyEvent(event, setState)
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') return
      setState((prev) => ({ ...prev, status: 'error', error: err.message }))
    }
  }, [endpoint])

  const abort = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  return { ...state, start, reset, abort }
}

function applyEvent(event, setState) {
  setState((prev) => ({
    ...prev,
    stage: event.type,
    events: [...prev.events, event],
    ...(event.type === 'done' ? { status: 'done', result: event } : {}),
    ...(event.type === 'error' ? { status: 'error', error: event.message } : {}),
  }))
}
