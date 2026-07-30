import { useCallback, useEffect, useRef, useState } from 'react'
import { API_BASE } from '../utils/api'

const INITIAL_STATE = {
  status: 'idle', // idle | running | done | error
  start: null, // payload event "start"
  config: null, // config yang sedang/sudah dilatih
  epochs: [], // 1 entri per event "epoch" (training flat, 1 model — aman disimpan semua)
  result: null, // payload event "done"
  error: null,
}

/**
 * Hook untuk menjalankan Training Manual skripsi-scoped (1 konfigurasi fixed,
 * BUKAN Random Search) via SSE. Stream FLAT — start -> epoch xN -> done/error
 * (beda dari useRandomSearchStream yang bersarang 3 level) karena hanya 1
 * model yang dilatih, bukan N kandidat per iterasi.
 */
export function useManualTrainStream(endpoint) {
  const [state, setState] = useState(INITIAL_STATE)
  const abortRef = useRef(null)

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

    setState({ ...INITIAL_STATE, status: 'running' })

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
      setState((prev) => ({ ...prev, start: event, config: event.config }))
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
