import type { PipelineStatus, RunHistoryItem, RunLog } from '../../../types/pipeline'
import { PIPELINE_STAGES } from '../../constants'

export const mockPipelineStatus: PipelineStatus = {
  runId: 'run-mock-001',
  state: 'running',
  startedAt: new Date(Date.now() - 45_000).toISOString(),
  stages: PIPELINE_STAGES.map((s, i) => ({
    id: s.id,
    label: s.label,
    state: i < 2 ? 'done' : i === 2 ? 'running' : 'idle',
    startedAt:  i <= 2 ? new Date(Date.now() - (5 - i) * 15_000).toISOString() : undefined,
    finishedAt: i < 2  ? new Date(Date.now() - (4 - i) * 15_000).toISOString() : undefined,
    durationMs: i < 2  ? (i + 1) * 12_000 : undefined,
  })),
  progress: 35,
}

export const mockRunHistory: RunHistoryItem[] = [
  {
    runId: 'run-mock-000',
    startedAt: new Date(Date.now() - 3_600_000).toISOString(),
    finishedAt: new Date(Date.now() - 3_480_000).toISOString(),
    state: 'done',
    durationMs: 120_000,
  },
  {
    runId: 'run-mock-099',
    startedAt: new Date(Date.now() - 86_400_000).toISOString(),
    finishedAt: new Date(Date.now() - 86_350_000).toISOString(),
    state: 'error',
    durationMs: 50_000,
    errorMessage: 'FinBERT OOM pada batch ke-42',
  },
]

export const mockLogs: RunLog[] = [
  { timestamp: new Date().toISOString(), level: 'INFO',    stage: 'fetch',     message: 'Memulai unduh data OHLCV BBCA.JK...' },
  { timestamp: new Date().toISOString(), level: 'INFO',    stage: 'fetch',     message: '2450 baris berhasil diunduh.' },
  { timestamp: new Date().toISOString(), level: 'INFO',    stage: 'clean',     message: 'Handling 12 missing values via forward-fill.' },
  { timestamp: new Date().toISOString(), level: 'INFO',    stage: 'sentiment', message: 'Memproses 318 headlines dengan FinBERT...' },
  { timestamp: new Date().toISOString(), level: 'WARNING', stage: 'sentiment', message: 'Batch 3/8 lambat, GPU utilization 94%.' },
]
