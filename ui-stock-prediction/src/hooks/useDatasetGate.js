import { useDataAnalysis } from './useDataAnalysis'

/**
 * Gate training: cek artifact dataset (dibangun tombol "Bangun Dataset Latih"
 * di halaman Workflow) tersedia & sinkron sebelum tombol Run diaktifkan —
 * mencerminkan guard yang sama di training_service.py::_require_dataset_bundle().
 */
export function useDatasetGate(variant, splitMode) {
  const status = useDataAnalysis(`/data-analysis/combined/dataset-status?variant=${variant}&split_mode=${splitMode}`)
  const ready = Boolean(status.data?.exists && status.data?.is_fresh)
  return { ...status, ready }
}
