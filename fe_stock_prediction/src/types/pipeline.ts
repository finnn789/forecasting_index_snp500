export type PipelineState = 'idle' | 'running' | 'done' | 'error'

export interface StageResult {
  id: string
  label: string
  state: PipelineState
  startedAt?: string
  finishedAt?: string
  durationMs?: number
  errorMessage?: string
}

export interface PipelineStatus {
  runId: string
  state: PipelineState
  startedAt?: string
  finishedAt?: string
  stages: StageResult[]
  progress: number          // 0-100
}

export interface RunLog {
  timestamp: string
  level: 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG'
  stage: string
  message: string
}

export interface RunHistoryItem {
  runId: string
  startedAt: string
  finishedAt?: string
  state: PipelineState
  durationMs?: number
  errorMessage?: string
}
