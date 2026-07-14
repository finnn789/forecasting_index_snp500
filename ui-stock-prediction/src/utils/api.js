export const API_BASE = 'http://localhost:8000/api/v1'

async function request(path, { method = 'GET', signal } = {}) {
  const res = await fetch(`${API_BASE}${path}`, { method, signal })
  const body = await res.json().catch(() => null)

  if (!res.ok || !body?.success) {
    const message = body?.error?.message ?? `Request failed (${res.status})`
    throw new Error(message)
  }

  return body.data
}

export function fetchJson(path, { signal } = {}) {
  return request(path, { method: 'GET', signal })
}

export function postJson(path, { signal } = {}) {
  return request(path, { method: 'POST', signal })
}
