import type {
  SentimentPipelineStatus,
  FinbertModelStatus,
  PipelineProgressEvent,
} from '../../types/pipeline'
import { API_URL, USE_MOCK } from '../constants'
import { apiFetch } from './client'
import { withMock } from './core/mock'
import { ENDPOINTS } from './endpoints'
import { mockPipelineStatus, mockFinbertStatus, simulatePipelineRun } from './mock/pipeline.mock'

// GET status pipeline sentimen (file processed, jumlah headline, rentang tanggal)
export const getSentimentPipelineStatus = withMock(
  () => apiFetch<SentimentPipelineStatus>(ENDPOINTS.PIPELINE_STATUS),
  () => mockPipelineStatus,
  300,
)

// GET status model FinBERT (ketersediaan + file + ukuran)
export const getFinbertModelStatus = withMock(
  () => apiFetch<FinbertModelStatus>(ENDPOINTS.SENTIMENT_MODEL),
  () => mockFinbertStatus,
  300,
)

export interface RunPipelineOptions {
  signal?: AbortSignal
  startDate?: string
  endDate?: string
  batchSize?: number
}

/**
 * Jalankan sentiment pipeline via POST SSE stream.
 * Tiap event progress (`{ step, pct, msg, result? }`) dikirim ke `onEvent`.
 *
 * Catatan: endpoint adalah POST `text/event-stream`, sehingga `EventSource`
 * (GET-only) TIDAK bisa dipakai — kita stream manual via fetch + ReadableStream.
 */
export async function runSentimentPipeline(
  onEvent: (e: PipelineProgressEvent) => void,
  opts: RunPipelineOptions = {},
): Promise<void> {
  if (USE_MOCK) {
    return simulatePipelineRun(onEvent, opts.signal)
  }

  const params = new URLSearchParams()
  if (opts.startDate) params.set('start_date', opts.startDate)
  if (opts.endDate) params.set('end_date', opts.endDate)
  if (opts.batchSize != null) params.set('batch_size', String(opts.batchSize))
  const qs = params.toString()
  const url = `${API_URL}${ENDPOINTS.PIPELINE_RUN}${qs ? `?${qs}` : ''}`

  const res = await fetch(url, {
    method: 'POST',
    headers: { Accept: 'text/event-stream' },
    signal: opts.signal,
  })

  if (!res.ok || !res.body) {
    throw new Error(`Pipeline run gagal (HTTP ${res.status})`)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      // SSE: event dipisah baris kosong; payload pada baris berawalan "data:"
      let idx: number
      while ((idx = buffer.indexOf('\n')) >= 0) {
        const line = buffer.slice(0, idx).trim()
        buffer = buffer.slice(idx + 1)
        if (!line.startsWith('data:')) continue
        const json = line.slice(5).trim()
        if (!json) continue
        try {
          onEvent(JSON.parse(json) as PipelineProgressEvent)
        } catch {
          /* abaikan baris malformed */
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}
