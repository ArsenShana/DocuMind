const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  health: () => request('/health'),
  upload: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return fetch(`${BASE}/documents/upload`, { method: 'POST', body: fd }).then(r => r.json())
  },
  analyze: (id) => request(`/documents/analyze/${id}`, { method: 'POST' }),
  classify: (id) => request(`/documents/classify/${id}`, { method: 'POST' }),
  extract: (id) => request(`/documents/extract/${id}`, { method: 'POST' }),
  validate: (ids) => request('/documents/validate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(ids),
  }),
  listDocuments: () => request('/documents/'),
  getDocument: (id) => request(`/documents/${id}`),
}
