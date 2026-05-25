import { useEffect, useRef, useState } from 'react'
import type { RunLog } from '../types/pipeline'
import { API_URL, USE_MOCK } from '../lib/constants'
import { ENDPOINTS } from '../lib/api/endpoints'
import { mockLogs } from '../lib/api/mock/pipeline.mock'

export function useSSE(active: boolean) {
  const [logs, setLogs]       = useState<RunLog[]>([])
  const [connected, setConnected] = useState(false)
  const esRef = useRef<EventSource | null>(null)

  useEffect(() => {
    if (!active) { setLogs([]); setConnected(false); return }

    if (USE_MOCK) {
      setLogs(mockLogs)
      setConnected(true)
      return
    }

    const es = new EventSource(`${API_URL}${ENDPOINTS.PIPELINE_LOGS}`)
    esRef.current = es

    es.onopen = () => setConnected(true)
    es.onmessage = (e) => {
      try {
        const log: RunLog = JSON.parse(e.data)
        setLogs(prev => [...prev, log])
      } catch { /* ignore malformed */ }
    }
    es.onerror = () => { setConnected(false); es.close() }

    return () => { es.close(); esRef.current = null }
  }, [active])

  return { logs, connected }
}
