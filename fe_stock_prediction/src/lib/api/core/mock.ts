import { USE_MOCK } from '../../constants'

export const delay = (ms: number) => new Promise<void>(r => setTimeout(r, ms))

export function withMock<Args extends unknown[], T>(
  realFn: (...args: Args) => Promise<T>,
  mockFn: (...args: Args) => T | Promise<T>,
  delayMs = 300,
): (...args: Args) => Promise<T> {
  return async (...args: Args): Promise<T> => {
    if (USE_MOCK) {
      await delay(delayMs)
      return await mockFn(...args)
    }
    return realFn(...args)
  }
}
