import type {
  SentimentPipelineStatus,
  FinbertModelStatus,
  PipelineProgressEvent,
} from '../../../types/pipeline'

export const mockPipelineStatus: SentimentPipelineStatus = {
  clean_file_exists: true,
  daily_file_exists: true,
  total_headlines: 19127,
  total_days: 3507,
  date_range: { start: '2008-01-02', end: '2024-03-04' },
}

export const mockFinbertStatus: FinbertModelStatus = {
  is_available: true,
  model_path: 'models/finbert/models--ProsusAI--finbert',
  source: 'local_snapshot',
  snapshot_path:
    'models/finbert/models--ProsusAI--finbert/snapshots/4556d13015211d73dccd3fdd39d39232506f3e43',
  required_files: {
    'config.json': true,
    'pytorch_model.bin': true,
    'tokenizer_config.json': true,
    'vocab.txt': true,
  },
  model_size_mb: 1253.48,
}

// Urutan event yang meniru stream SSE backend.
const MOCK_STEPS: PipelineProgressEvent[] = [
  { step: 'loading_data',  pct: 10,  msg: 'Memuat 19.127 headline...' },
  { step: 'filtering',     pct: 20,  msg: 'Memfilter rentang tanggal...' },
  { step: 'loading_model', pct: 35,  msg: 'Memuat model FinBERT (1.25 GB)...' },
  { step: 'model_ready',   pct: 45,  msg: 'Model siap. Memulai inferensi.' },
  { step: 'inference',     pct: 60,  msg: 'Inferensi batch 1/8...' },
  { step: 'inference',     pct: 78,  msg: 'Inferensi batch 5/8...' },
  { step: 'aggregating',   pct: 88,  msg: 'Mengagregasi sentimen harian...' },
  { step: 'saving',        pct: 95,  msg: 'Menyimpan headlines_daily_sentiment.csv...' },
  { step: 'done',          pct: 100, msg: 'Pipeline selesai.', result: { total_headlines: 19127, total_days: 3507 } },
]

/** Simulasi stream progress saat VITE_USE_MOCK=true. */
export async function simulatePipelineRun(
  onEvent: (e: PipelineProgressEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  for (const ev of MOCK_STEPS) {
    if (signal?.aborted) return
    await new Promise<void>(r => setTimeout(r, 600))
    if (signal?.aborted) return
    onEvent(ev)
  }
}
