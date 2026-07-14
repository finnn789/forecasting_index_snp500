import { useDataAnalysis } from '../../hooks/useDataAnalysis'
import Icon from '../Icon'
import ErrorBoundary from '../ErrorBoundary'
import SummaryTable from './SummaryTable'
import StatsTable from './StatsTable'
import TimeSeriesChart from './TimeSeriesChart'
import PriceVolumeChart from './PriceVolumeChart'
import CorrelationHeatmap from './CorrelationHeatmap'
import DistributionView from './DistributionView'
import SeasonalityChart from './SeasonalityChart'
import EdaSummaryView from './EdaSummaryView'
import PipelineStepsView from './PipelineStepsView'
import StockPreprocessingView from './StockPreprocessingView'
import RawJsonView from './RawJsonView'

function pickRenderer(data) {
  if (!data || typeof data !== 'object') return RawJsonView
  if (Array.isArray(data.points)) {
    const first = data.points[0] ?? {}
    if ('close' in first && 'volume' in first) return PriceVolumeChart
    return TimeSeriesChart
  }
  if (Array.isArray(data.matrix)) return CorrelationHeatmap
  if (data.label_counts && data.score_histogram) return DistributionView
  if (Array.isArray(data.monthly) && Array.isArray(data.weekday)) return SeasonalityChart
  if (Array.isArray(data.annual_returns) && 'cumulative_return_pct' in data) return EdaSummaryView
  if (data.raw && data.clean && Array.isArray(data.columns_dropped)) return StockPreprocessingView
  if (Array.isArray(data.steps)) return PipelineStepsView
  if (data.columns && !Array.isArray(data.columns) && typeof data.columns === 'object') {
    return StatsTable
  }
  if (Array.isArray(data.columns) && 'total_rows' in data) return SummaryTable
  return RawJsonView
}

export default function AnalysisPanel({ path }) {
  const { data, loading, error } = useDataAnalysis(path)

  if (loading) {
    return (
      <div className="flex h-40 items-center justify-center gap-2 text-sm text-slate-400">
        <Icon name="progress_activity" className="animate-spin text-lg" />
        Memuat data...
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
        <Icon name="error" className="text-lg" />
        {error}
      </div>
    )
  }

  const Renderer = pickRenderer(data)
  return (
    <ErrorBoundary resetKey={path}>
      <Renderer data={data} path={path} />
    </ErrorBoundary>
  )
}
