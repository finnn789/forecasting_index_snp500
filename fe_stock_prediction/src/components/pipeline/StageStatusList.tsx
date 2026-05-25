import { StageCard } from './StageCard'
import { Skeleton } from '../ui/skeleton'
import type { StageResult } from '../../types/pipeline'

interface StageStatusListProps {
  stages?: StageResult[]
  loading?: boolean
}

export function StageStatusList({ stages, loading }: StageStatusListProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 6 }, (_, i) => (
          <Skeleton key={i} className="h-14 w-full" />
        ))}
      </div>
    )
  }

  if (!stages?.length) return null

  return (
    <div>
      {stages.map((stage, i) => (
        <StageCard key={stage.id} stage={stage} isLast={i === stages.length - 1} />
      ))}
    </div>
  )
}
