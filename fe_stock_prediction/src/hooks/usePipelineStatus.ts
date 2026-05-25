import { useEffect, useRef, useState } from 'react'
import type { PipelineStatus } from '../types/pipeline'
import { getPipelineStatus } from '../lib/api/pipeline.api'

export function usePipelineStatus(pollIntervalMs = 3000) {
  const [status, setStatus]   = useState<PipelineStatus | null>(null)
  const [error, setError]     = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchStatus = async () => { 
    try {
      const data = await getPipelineStatus()
      setStatus(data)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Gagal mengambil status pipeline')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
    intervalRef.current = setInterval(fetchStatus, pollIntervalMs)
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [pollIntervalMs])

  return { status, error, loading, refetch: fetchStatus }
}
