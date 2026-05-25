import { Badge } from '../ui/badge'
import type { PipelineState } from '../../types/pipeline'
import type { SentimentLabel } from '../../types/sentiment'

const pipelineMap: Record<PipelineState, { variant: 'running' | 'done' | 'error' | 'idle'; label: string }> = {
  running: { variant: 'running', label: 'Berjalan' },
  done:    { variant: 'done',    label: 'Selesai'  },
  error:   { variant: 'error',   label: 'Error'    },
  idle:    { variant: 'idle',    label: 'Idle'     },
}

const sentimentMap: Record<SentimentLabel, { variant: 'positive' | 'negative' | 'neutral'; label: string }> = {
  positive: { variant: 'positive', label: 'Positif' },
  negative: { variant: 'negative', label: 'Negatif' },
  neutral:  { variant: 'neutral',  label: 'Netral'  },
}

export function PipelineStatusBadge({ state }: { state: PipelineState }) {
  const { variant, label } = pipelineMap[state]
  return <Badge variant={variant} dot>{label}</Badge>
}

export function SentimentBadge({ sentiment }: { sentiment: SentimentLabel }) {
  const { variant, label } = sentimentMap[sentiment]
  return <Badge variant={variant}>{label}</Badge>
}
