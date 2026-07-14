import { Component } from 'react'
import Icon from './Icon'

class ErrorBoundary extends Component {
  state = { error: null }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    console.error('ErrorBoundary caught an error:', error, info)
  }

  componentDidUpdate(prevProps) {
    if (this.state.error && prevProps.resetKey !== this.props.resetKey) {
      this.setState({ error: null })
    }
  }

  render() {
    const { error } = this.state

    if (error) {
      return (
        <div className="flex flex-col items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-10 text-center">
          <Icon name="error" className="text-2xl text-red-500" />
          <p className="text-sm font-medium text-red-600">Terjadi kesalahan saat menampilkan konten ini.</p>
          <p className="max-w-md font-mono text-xs text-red-500">{error.message ?? 'Unknown error'}</p>
          <button
            type="button"
            onClick={() => this.setState({ error: null })}
            className="mt-1 rounded bg-red-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-red-700"
          >
            Coba lagi
          </button>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
