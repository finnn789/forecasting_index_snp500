import { useState } from 'react'
import PageContainer from '../layout/PageContainer'
import PredictionPanel, {
  NOTEBOOK07_METRIC_KEYS,
  NOTEBOOK07_HEADER_STATS,
} from '../components/prediction/PredictionPanel'
import { cn } from '../utils/cn'

const VARIANTS = [
  {
    key: 'sentiment',
    label: 'OHLCV + Sentimen',
    resultPath: '/train/notebook05/result',
    predictPath: '/train/notebook05/predict',
    backtestPath: '/train/notebook05/backtest?split=test',
  },
  {
    key: 'ohlcv',
    label: 'OHLCV Saja',
    resultPath: '/train/notebook05/ohlcv/result',
    predictPath: '/train/notebook05/ohlcv/predict',
    backtestPath: '/train/notebook05/ohlcv/backtest?split=test',
  },
  {
    key: 'skripsi-baseline',
    label: 'Skripsi: LSTM-OHLCV',
    resultPath: '/train/skripsi/ohlcv/result',
    predictPath: '/train/skripsi/ohlcv/predict',
    backtestPath: '/train/skripsi/ohlcv/backtest?split=test',
    metricKeys: NOTEBOOK07_METRIC_KEYS,
    backtestMetricKeys: NOTEBOOK07_METRIC_KEYS,
    headerStats: NOTEBOOK07_HEADER_STATS,
  },
  {
    key: 'skripsi-finbert',
    label: 'Skripsi: FinBERT-LSTM',
    resultPath: '/train/skripsi/finbert-lstm/result',
    predictPath: '/train/skripsi/finbert-lstm/predict',
    backtestPath: '/train/skripsi/finbert-lstm/backtest?split=test',
    metricKeys: NOTEBOOK07_METRIC_KEYS,
    backtestMetricKeys: NOTEBOOK07_METRIC_KEYS,
    headerStats: NOTEBOOK07_HEADER_STATS,
  },
]

export default function Predictions() {
  const [activeVariant, setActiveVariant] = useState(VARIANTS[0].key)

  return (
    <PageContainer
      title="Predictions"
      description="Hasil training tersimpan di backend — lihat metrik, jalankan prediksi hari berikutnya, dan backtest untuk tiap varian model (Training Live Notebook 05 & Random Search Skripsi)."
    >
      <div className="flex gap-2 border-b border-slate-200">
        {VARIANTS.map((variant) => (
          <button
            key={variant.key}
            type="button"
            onClick={() => setActiveVariant(variant.key)}
            className={cn(
              'border-b-2 px-4 py-2 text-sm font-medium transition-colors',
              activeVariant === variant.key
                ? 'border-slate-900 text-slate-900'
                : 'border-transparent text-slate-400 hover:text-slate-600',
            )}
          >
            {variant.label}
          </button>
        ))}
      </div>

      {/*
        Semua panel dirender SEKALIGUS dan tetap mounted permanen — tab yang
        tidak aktif hanya disembunyikan lewat className, BUKAN conditional
        render, supaya hasil fetch/prediksi/backtest salah satu tab tidak
        hilang saat pindah tab (pola sama seperti ModelTraining.jsx).
      */}
      {VARIANTS.map((variant) => (
        <div key={variant.key} className={cn(activeVariant !== variant.key && 'hidden')}>
          <PredictionPanel
            resultPath={variant.resultPath}
            predictPath={variant.predictPath}
            backtestPath={variant.backtestPath}
            metricKeys={variant.metricKeys}
            backtestMetricKeys={variant.backtestMetricKeys}
            headerStats={variant.headerStats}
          />
        </div>
      ))}
    </PageContainer>
  )
}
