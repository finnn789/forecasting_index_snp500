import { useCallback, useRef, useState } from 'react'
import type {
  SentimentPipelineStatus,
  FinbertModelStatus,
  PipelineProgressEvent,
  PipelineLogLine,
  PipelineState,
} from '../types/pipeline'
import type { AsyncState } from '../types/async'
import { useAsync } from './core/useAsync'
import {
  getSentimentPipelineStatus,
  getFinbertModelStatus,
  runSentimentPipeline,
} from '../lib/api/pipeline.api'
import { toErrorMessage } from '../lib/api/core/errors'

/** Status pipeline sentimen (auto-fetch on mount). */
export function useSentimentPipelineStatus(): AsyncState<SentimentPipelineStatus> & { refetch: () => void } {
  return useAsync(() => getSentimentPipelineStatus(), [])
}

/** Status model FinBERT (auto-fetch on mount). */
export function useFinbertStatus(): AsyncState<FinbertModelStatus> & { refetch: () => void } {
  return useAsync(() => getFinbertModelStatus(), [])
}

export interface SentimentRunController {
  state: PipelineState
  progress: number
  logs: PipelineLogLine[]
  error: string | null
  start: () => void
  cancel: () => void
}

/**
 * Kontrol eksekusi sentiment pipeline via SSE.
 * `start()` memulai stream; tiap event memperbarui progress + log.
 */
export function useSentimentRun(onDone?: () => void): SentimentRunController {
  const [state, setState] = useState<PipelineState>('idle')
  const [progress, setProgress] = useState(0)
  const [logs, setLogs] = useState<PipelineLogLine[]>([])
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const start = useCallback(() => {
    if (abortRef.current) abortRef.current.abort()
    const ac = new AbortController()
    abortRef.current = ac

    setState('running')
    setProgress(0)
    setError(null)
    setLogs([])

    const onEvent = (e: PipelineProgressEvent) => {
      const isError = e.step === 'error'
      setProgress(prev => (typeof e.pct === 'number' ? e.pct : prev))
      setLogs(prev => [
        ...prev,
        { step: e.step, pct: e.pct, msg: e.msg, at: new Date().toISOString(), isError },
      ])
      if (e.step === 'done') {
        setState('done')
        onDone?.()
      } else if (isError) {
        setState('error')
        setError(e.msg)
      }
    }

    runSentimentPipeline(onEvent, { signal: ac.signal })
      .then(() => {
        // Jika stream selesai tanpa event 'done' eksplisit, tandai selesai.
        setState(prev => (prev === 'running' ? 'done' : prev))
      })
      .catch(err => {
        if (ac.signal.aborted) return
        setState('error')
        setError(toErrorMessage(err))
      })
  }, [onDone])

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    setState(prev => (prev === 'running' ? 'idle' : prev))
  }, [])

  return { state, progress, logs, error, start, cancel }
}
