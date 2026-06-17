// Domain: Sentiment Pipeline (FinBERT) — satu-satunya pipeline yang ada di backend.
// Endpoint: GET /api/v1/sentiment/pipeline/status, GET /api/v1/sentiment/model/status,
//           POST /api/v1/sentiment/pipeline/run (SSE stream).

/** Dipakai oleh PipelineStatusBadge untuk pewarnaan status ringkas. */
export type PipelineState = 'idle' | 'running' | 'done' | 'error'

/** GET /api/v1/sentiment/pipeline/status */
export interface SentimentPipelineStatus {
  clean_file_exists: boolean
  daily_file_exists: boolean
  total_headlines: number | null
  total_days: number | null
  date_range: { start: string | null; end: string | null }
}

/** GET /api/v1/sentiment/model/status (FinBERT) */
export interface FinbertModelStatus {
  is_available: boolean
  model_path: string
  source: string
  snapshot_path: string | null
  required_files: Record<string, boolean>
  model_size_mb: number | null
}

/** Urutan step pada SSE: loading_data → filtering → loading_model → model_ready →
 *  inference → aggregating → saving → done | error. */
export type PipelineStep =
  | 'loading_data'
  | 'filtering'
  | 'loading_model'
  | 'model_ready'
  | 'inference'
  | 'aggregating'
  | 'saving'
  | 'done'
  | 'error'

/** Satu event SSE dari POST /api/v1/sentiment/pipeline/run. */
export interface PipelineProgressEvent {
  step: PipelineStep | string
  pct: number
  msg: string
  result?: unknown
}

/** Baris log yang dirender di UI (event + timestamp sisi klien). */
export interface PipelineLogLine {
  step: string
  pct: number
  msg: string
  at: string
  isError?: boolean
}
