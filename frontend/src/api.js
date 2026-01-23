const DEFAULT_BASE = ''

// 强制清理可能残留的旧配置，确保使用代理
localStorage.removeItem('api_base')
let currentBase = import.meta.env.VITE_API_BASE || DEFAULT_BASE

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
  // Added style_name parameter for test mode 3.1->3.3
  runWorkflow(session_id, userText, answers = {}, auto_fill_defaults = false, stop_at = null, style_name = null) {
    return http('/api/workflow/run', {
      method: 'POST',
      body: { session_id, user_text: userText, answers, auto_fill_defaults, stop_at, style_name }
    })
  },
  renderMock() {
    return http('/api/workflow/render/mock', { method: 'POST' })
  },
  getSession(session_id) { return http(`/api/session/${session_id}`) },
  getSlideTypes() { return http('/api/slide-types') },
  logsUrl(session_id) {
    const base = getApiBase().replace(/\/$/, '')
    return `${base}/api/logs/${session_id}`
  },
  getRenderStatus(session_id) {
    return http(`/api/workflow/render/status/${session_id}`)
  },

  // ======= Phase 1: Outline Editor =======
  updateOutline(session_id, slides) {
    return http('/api/workflow/outline/update', {
      method: 'POST',
      body: { session_id, slides }
    })
  },

  // ======= Phase 2: Async Content Generation =======
  generateSlideContent(session_id, slide_index, context = null) {
    return http('/api/workflow/slide/generate', {
      method: 'POST',
      body: { session_id, slide_index, context }
    })
  },

  // ======= Phase 6: Parallel Outline & Render =======
  generateOutlineStructure(session_id, style_name = null) {
    return http('/api/workflow/outline/structure', {
      method: 'POST',
      body: { session_id, style_name }
    })
  },

  expandSlide(session_id, slide_index) {
    return http('/api/workflow/outline/expand', {
      method: 'POST',
      body: { session_id, slide_index }
    })
  },

  postProcessOutline(session_id) {
    return http('/api/workflow/outline/post-process', {
      method: 'POST',
      body: { session_id }
    })
  },

  renderSlides(session_id) {
    return http('/api/workflow/render', {
      method: 'POST',
      body: { session_id }
    })
  },

  // 3.4 -> 3.5 数据同步
  updateSlidesBatch(session_id, slides) {
    return http('/api/workflow/slides/update_batch', {
      method: 'POST',
      body: { session_id, slides }
    })
  },

  // 3.4 -> 3.5 过渡：强制保存内容
  updateDeck(session_id, deck_content) {
    return http('/api/workflow/deck/update', {
      method: 'POST',
      body: { session_id, deck_content }
    })
  },

  // 3.4 -> 3.5 核心修复：发送内容列表，由后端组装
  assembleDeck(session_id, contents) {
    return http('/api/workflow/deck/assemble', {
      method: 'POST',
      body: { session_id, contents }
    })
  },

  // ======= 3.5 图片生成 =======
  triggerImageGeneration(session_id) {
    return http(`/api/workflow/render/generate/${session_id}`, { method: 'POST' })
  },

  // ======= 3.5 Mock 数据渲染 =======
  renderWithMockData(subject = 'mechanical') {
    return http('/api/workflow/render/mock', {
      method: 'POST',
      body: { use_mock: true, subject }
    })
  },

  getDownloadUrl(session_id) {
    const base = getApiBase().replace(/\/$/, '')
    return `${base}/api/workflow/download/${session_id}`
  },
}

