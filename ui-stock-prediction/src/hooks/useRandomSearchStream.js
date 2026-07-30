import { useCallback, useEffect, useRef, useState } from 'react'
import { API_BASE } from '../utils/api'

const INITIAL_STATE = {
  status: 'idle', // idle | running | done | error
  start: null, // payload event "start"
  totalIterations: null,
  currentIteration: 0,
  currentConfig: null,
  currentEpochs: [], // di-reset tiap "iteration_start" baru — hanya iterasi yang SEDANG jalan
  iterationHistory: [], // 1 baris per "iteration_end", terus bertambah (tidak di-reset)
  result: null, // payload event "done"
  error: null,
}

/**
 * Hook untuk menjalankan Random Search skripsi-scoped (notebook 07) via SSE.
 * Stream ini BERSARANG 3 level — start -> [iteration_start -> epoch xN ->
 * iteration_end] x n_iter -> done/error — karena Random Search melatih N
 * model independen (1 model = 1 konfigurasi), bukan 1 model final.
 *
 * `currentEpochs` HANYA menyimpan epoch dari iterasi yang sedang berjalan (di-reset
 * tiap iteration_start) supaya chart tetap ringan & bermakna — histori 20 iterasi
 * disimpan sbg ringkasan 1 baris per iterasi di `iterationHistory`, bukan detail
 * per-epoch-nya (bisa sampai ~1000+ event epoch total kalau disimpan semua).
 */
export function useRandomSearchStream(endpoint) {
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
      setState((prev) => ({ ...prev, start: event, totalIterations: event.total_iterations }))
      break
    case 'iteration_start':
      setState((prev) => ({
        ...prev,
        currentIteration: event.iteration,
        currentConfig: event.config,
        currentEpochs: [], // reset — chart live hanya utk iterasi ini
      }))
      break
    case 'epoch':
      setState((prev) => ({ ...prev, currentEpochs: [...prev.currentEpochs, event] }))
      break
    case 'iteration_end':
      setState((prev) => ({ ...prev, iterationHistory: [...prev.iterationHistory, event] }))
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
