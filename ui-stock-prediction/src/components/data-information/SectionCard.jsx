import Card, { CardContent } from '../Card'
import Icon from '../Icon'
import ErrorBoundary from '../ErrorBoundary'
import { useDataAnalysis } from '../../hooks/useDataAnalysis'

/**
 * Wrapper 1 section = 1 temuan: fetch `path`, tangani loading/error, lalu
 * render `children(data)` (render-prop) di dalam ErrorBoundary.
 */
export default function SectionCard({ title, description, path, children }) {
  const { data, loading, error } = useDataAnalysis(path)

  return (
    <Card>
      <Card.Header className="block space-y-1 py-5">
        <Card.Title className="text-sm font-semibold normal-case text-slate-900">{title}</Card.Title>
        {description && <p className="text-xs leading-relaxed text-slate-500">{description}</p>}
      </Card.Header>
      <CardContent>
        {loading && (
          <div className="flex h-32 items-center justify-center gap-2 text-sm text-slate-400">
            <Icon name="progress_activity" className="animate-spin text-lg" />
            Memuat data...
          </div>
        )}
        {error && (
          <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
            <Icon name="error" className="text-lg" />
            {error}
          </div>
        )}
        {!loading && !error && data && <ErrorBoundary resetKey={path}>{children(data)}</ErrorBoundary>}
      </CardContent>
    </Card>
  )
}
