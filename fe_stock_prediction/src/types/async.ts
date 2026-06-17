export type AsyncStatus = 'idle' | 'loading' | 'success' | 'error'

export interface AsyncState<T> {
  data: T | null
  error: string | null
  loading: boolean
  status: AsyncStatus
}
