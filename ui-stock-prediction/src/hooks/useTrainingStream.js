import { useCallback, useEffect, useRef, useState } from 'react'
import { API_BASE } from '../utils/api'

const INITIAL_STATE = {
  status: 'idle', // idle | running | done | error
  start: null, // payload event "start"
  epochs: [], // list payload event "epoch"
  result: null, // payload event "done"
  error: null,
}

/**
 * Hook untuk menjalankan training LSTM (Notebook 05) via SSE.
 * EventSource tidak bisa POST body, jadi stream dikonsumsi lewat fetch +
 * ReadableStream reader. Tiap event SSE berbentuk baris "data: {json}\n\n" —
 * dibaca per chunk, di-buffer, lalu di-split pada "\n\n".
 */
export function useTrainingStream(endpoint = '/train/notebook05') {
  const [state, setState] = useState(INITIAL_STATE)
  const abortRef = useRef(null)

  // Pastikan koneksi ditutup kalau komponen unmount saat masih running.
  useEffect(() => {
    return () => abortRef.current?.abort()
  }, [])

  const reset = useCallback(() => {
    abortRef.current?.abort()
    setState(INITIAL_STATE)
  }, [])

  const startTraining = useCallback(async (config) => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setState({ status: 'running', start: null, epochs: [], result: null, error: null })

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config ?? {}),
        signal: controller.signal,
      })

      if (!res.ok || !res.body) {
        throw new Error(`Training gagal dimulai (${res.status})`)
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

  return { ...state, startTraining, reset, abort }
}

function applyEvent(event, setState) {
  switch (event.type) {
    case 'start':
      setState((prev) => ({ ...prev, start: event }))
      break
    case 'epoch':
      setState((prev) => ({ ...prev, epochs: [...prev.epochs, event] }))
      break
    case 'done':
      setState((prev) => ({ ...prev, status: 'done', result: event }))
      break
    case 'error':
      setState((prev) => ({ ...prev, status: 'error', error: event.message }))
      break
    default:
      break
  }
}
