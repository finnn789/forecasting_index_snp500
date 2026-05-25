import { useState } from 'react'
import { Loader2, Sparkles } from 'lucide-react'
import { Button } from '../ui/button'
import { Label } from '../ui/label'
import { Input } from '../ui/input'
import { TickerSelector } from './TickerSelector'
import type { PredictionRequest } from '../../types/prediction'

interface PredictionFormProps {
  onSubmit: (req: PredictionRequest) => void
  loading: boolean
}

export function PredictionForm({ onSubmit, loading }: PredictionFormProps) {
  const [ticker, setTicker] = useState('BBCA.JK')
  const [date, setDate]     = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({ ticker, date: date || undefined })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <TickerSelector value={ticker} onChange={setTicker} />

      <div className="space-y-1.5">
        <Label htmlFor="pred-date">Tanggal Prediksi</Label>
        <Input
          id="pred-date"
          type="date"
          value={date}
          onChange={e => setDate(e.target.value)}
          min={new Date().toISOString().split('T')[0]}
          placeholder="Hari berikutnya (default)"
          className="[color-scheme:dark]"
        />
        <p className="text-xs text-[--color-muted-foreground]">
          Kosongkan untuk prediksi hari kerja berikutnya.
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
