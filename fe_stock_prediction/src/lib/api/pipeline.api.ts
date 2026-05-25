import { USE_MOCK } from '../constants'
import type { PipelineStatus, RunHistoryItem, RunLog } from '../../types/pipeline'
import { apiFetch } from './client'
import { ENDPOINTS } from './endpoints'
import { mockPipelineStatus, mockRunHistory, mockLogs } from './mock/pipeline.mock'

const delay = (ms: number) => new Promise(r => setTimeout(r, ms))

export async function getPipelineStatus(): Promise<PipelineStatus> {
  if (USE_MOCK) { await delay(300); return mockPipelineStatus }
  return apiFetch<PipelineStatus>(ENDPOINTS.PIPELINE_STATUS)
}

export async function runPipeline(): Promise<{ runId: string }> {
  if (USE_MOCK) { await delay(500); return { runId: 'run-mock-new' } }
  return apiFetch<{ runId: string }>(ENDPOINTS.PIPELINE_RUN, { method: 'POST' })
}

export async function stopPipeline(): Promise<void> {
  if (USE_MOCK) { await delay(300); return }
  await apiFetch<void>(ENDPOINTS.PIPELINE_STOP, { method: 'POST' })
}

export async function getPipelineHistory(): Promise<RunHistoryItem[]> {
  if (USE_MOCK) { await delay(400); return mockRunHistory }
  return apiFetch<RunHistoryItem[]>(ENDPOINTS.PIPELINE_HISTORY)
}

export async function getPipelineLogs(): Promise<RunLog[]> {
  if (USE_MOCK) { await delay(200); return mockLogs }
  return apiFetch<RunLog[]>(ENDPOINTS.PIPELINE_LOGS)
}
