import { Loader2, Sparkles } from 'lucide-react'
import { Button } from '../ui/button'
import { Label } from '../ui/label'
import type { PredictionRequest } from '../../types/prediction'

interface PredictionFormProps {
  onSubmit: (req: PredictionRequest) => void
  loading: boolean
}

export function PredictionForm({ onSubmit, loading }: PredictionFormProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({ ticker: 'GSPC' })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-1.5">
        <Label>Ticker</Label>
        <p className="text-sm font-medium">GSPC — S&P 500</p>
        <p className="text-xs text-[--color-muted-foreground]">
          Prediksi arah harga hari berikutnya.
        </p>
      </div>

      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? (
          <><Loader2 className="size-4 animate-spin" /> Memproses...</>
        ) : (
          <><Sparkles className="size-4" /> Prediksi Sekarang</>
        )}
      </Button>
    </form>
  )
}
