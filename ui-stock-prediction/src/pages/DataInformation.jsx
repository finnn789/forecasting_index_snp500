import { useState } from 'react'
import PageContainer from '../layout/PageContainer'
import SectionCard from '../components/data-information/SectionCard'
import RegimeOverviewContent from '../components/data-information/RegimeOverviewContent'
import LabelBalanceContent from '../components/data-information/LabelBalanceContent'
import ScalingRangeContent from '../components/data-information/ScalingRangeContent'
import FeatureCorrelationContent from '../components/data-information/FeatureCorrelationContent'
import SentimentLagContent from '../components/data-information/SentimentLagContent'
import BaselineComparisonContent from '../components/data-information/BaselineComparisonContent'
import DistributionDriftContent from '../components/data-information/DistributionDriftContent'
import { cn } from '../utils/cn'

const MODEL_OPTIONS = [
  { value: 'joined', label: 'Model B — FinBERT-LSTM' },
  { value: 'ohlcv', label: 'Model A — OHLCV' },
]

const HORIZON_OPTIONS = [
  { value: 1, label: '1 Hari' },
  { value: 5, label: '5 Hari' },
]

function ToggleGroup({ value, onChange, options }) {
  return (
    <div className="inline-flex rounded-lg border border-slate-200 bg-slate-50 p-1">
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          onClick={() => onChange(opt.value)}
          className={cn(
            'rounded-md px-3 py-1.5 text-xs font-medium transition-colors',
            value === opt.value ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700',
          )}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}

export default function DataInformation() {
  const [model, setModel] = useState('joined')
  const [horizon, setHorizon] = useState(1)

  const modelHorizonQuery = `model=${model}&horizon=${horizon}`

  return (
    <PageContainer
      title="Data Information"
      description="Kenapa model prediksi arah harga sering meleset? Temuan di bawah ini dihitung langsung dari data terbaru saat halaman dibuka — bukan tangkapan layar statis."
    >
      <div className="flex flex-wrap items-center gap-6 rounded-lg border border-slate-200 bg-white p-4">
        <div>
          <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">Model</p>
          <ToggleGroup value={model} onChange={setModel} options={MODEL_OPTIONS} />
        </div>
        <div>
          <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Horizon Prediksi
          </p>
          <ToggleGroup value={horizon} onChange={setHorizon} options={HORIZON_OPTIONS} />
        </div>
        <p className="max-w-xs text-xs text-slate-400 sm:ml-auto">
          Pilihan ini berlaku untuk section yang bergantung pada model &amp; horizon di bawah.
        </p>
      </div>

      <SectionCard
        title="1. Pergeseran Pola Pasar Antar Periode"
        description="Periode data latih, validasi, dan uji kebetulan jatuh di kondisi pasar dengan arah yang berbeda."
        path={`/data-information/regime-overview?${modelHorizonQuery}`}
      >
        {(data) => <RegimeOverviewContent data={data} />}
      </SectionCard>

      <SectionCard
        title="2. Distribusi Arah Naik/Turun per Periode"
        description="Perbandingan proporsi arah naik antar periode untuk kedua model, dan pergerakannya sepanjang waktu."
        path={`/data-information/label-balance?horizon=${horizon}`}
      >
        {(data) => <LabelBalanceContent data={data} />}
      </SectionCard>

      <SectionCard
        title="3. Nilai di Luar Jangkauan Data Latihan"
        description="Karena harga terus mencetak rekor baru, sebagian data validasi/uji berada di luar jangkauan hasil normalisasi data latih."
        path={`/data-information/scaling-range?${modelHorizonQuery}`}
      >
        {(data) => <ScalingRangeContent data={data} />}
      </SectionCard>

      <SectionCard
        title="4. Arah Hubungan Fitur yang Berbalik"
        description="Korelasi tiap fitur dengan arah pergerakan harga, dibandingkan antara periode latih dan periode uji."
        path={`/data-information/feature-label-correlation?${modelHorizonQuery}`}
      >
        {(data) => <FeatureCorrelationContent data={data} />}
      </SectionCard>

      <SectionCard
        title="5. Sentimen Berita: Reaktif atau Memimpin Harga?"
        description="Korelasi skor sentimen berita dengan perubahan harga pada hari yang sama, dibandingkan beberapa hari ke depan."
        path="/data-information/sentiment-lag-correlation"
      >
        {(data) => <SentimentLagContent data={data} />}
      </SectionCard>

      <SectionCard
        title="6. Model vs Baseline Sederhana"
        description="Membandingkan akurasi kedua model dengan dua cara tebakan sederhana, di semua periode dan horizon."
        path="/data-information/baseline-comparison"
      >
        {(data) => <BaselineComparisonContent data={data} />}
      </SectionCard>

      <SectionCard
        title="7. Uji Perbedaan Distribusi Data (opsional)"
        description="Bukti statistik formal bahwa sebaran nilai fitur di data latih dan data uji berbeda secara signifikan."
        path={`/data-information/distribution-drift?${modelHorizonQuery}`}
      >
        {(data) => <DistributionDriftContent data={data} />}
      </SectionCard>
    </PageContainer>
  )
}
