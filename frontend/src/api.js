const DEFAULT_BASE = 'http://localhost:8000'

let currentBase = localStorage.getItem('api_base') || (import.meta.env.VITE_API_BASE || DEFAULT_BASE)

export function getApiBase() {
  return currentBase
}

export function setApiBase(v) {
  currentBase = (v || '').trim() || DEFAULT_BASE
  localStorage.setItem('api_base', currentBase)
}

async function http(path, { method = 'GET', body } = {}) {
  const base = getApiBase()
  const url = base.replace(/\/$/, '') + path
  const headers = { 'Content-Type': 'application/json' }
  const res = await fetch(url, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    const txt = await res.text()
    throw new Error(`HTTP ${res.status}: ${txt}`)
  }
  const ct = res.headers.get('content-type') || ''
  if (ct.includes('application/json')) return await res.json()
  return await res.text()
}

export const api = {
  health() { return http('/api/health') },
  createSession() { return http('/api/session', { method: 'POST' }) },
  // NOTE: backend expects field name `user_text`.
  // Added stop_at parameter for module testing
  runWorkflow(session_id, userText, answers = {}, auto_fill_defaults = false, stop_at = null) {
    return http('/api/workflow/run', {
      method: 'POST',
      body: { session_id, user_text: userText, answers, auto_fill_defaults, stop_at }
    })
  },
  getSession(session_id) { return http(`/api/session/${session_id}`) },
  logsUrl(session_id) { 
    const base = getApiBase().replace(/\/$/, '')
    return `${base}/api/logs/${session_id}`
  }
}
