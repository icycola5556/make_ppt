<template>
  <div class="module-35-container">
    <h2 class="module-title">3.5 智能排版与动态渲染</h2>
    
    <div class="control-panel">
      <!-- 正常流程：从session读取3.1-3.4数据 -->
      <button @click="runFullWorkflow" class="btn-primary" :disabled="loading">
        {{ loading ? '运行中...' : '正常流程渲染' }}
        <span class="btn-hint">使用session中3.1-3.4数据</span>
      </button>
      
      <!-- Mock数据渲染：完整Mock数据 -->
      <button @click="renderWithMockFull" class="btn-secondary" :disabled="loading">
        {{ loading ? '渲染中...' : 'Mock完整数据渲染' }}
        <span class="btn-hint">使用预设Mock数据（机械/化学）</span>
      </button>
      
      <!-- 独立生图按钮 -->
      <button @click="generateImages" class="btn-success" :disabled="generatingImages || !sessionId">
        {{ generatingImages ? '生图中...' : '生成教学配图' }}
      </button>
      
      <!-- 学科选择（用于Mock数据） -->
      <select v-model="mockSubject" class="subject-select">
        <option value="mechanical">机械制造</option>
        <option value="chemistry">化学</option>
      </select>
      
      <div v-if="renderResult" class="stats">
        <span class="stat-item">
          <strong>总页数:</strong> {{ renderResult.total_pages }}
        </span>
        <span class="stat-item">
          <strong>图片插槽:</strong> {{ renderResult.image_slots?.length || 0 }}
        </span>
        <span class="stat-item" v-if="renderResult.warnings?.length">
          <strong>警告:</strong> {{ renderResult.warnings.length }}
        </span>
      </div>
      
      <!-- 生图进度 -->
      <div v-if="imageProgress" class="progress-status" :class="{'progress-complete': imageProgress.done === imageProgress.total && imageProgress.total > 0}">
        <div class="progress-bar-container">
          <div class="progress-bar-fill" :style="{width: (imageProgress.done / imageProgress.total * 100) + '%'}"></div>
        </div>
        <span class="progress-text">
          {{ imageProgress.done }} / {{ imageProgress.total }} 
          <span v-if="imageProgress.failed > 0" class="failed-text">(失败: {{ imageProgress.failed }})</span>
        </span>
      </div>
    </div>

    <!-- 错误信息 -->
    <div v-if="error" class="error-panel">
      <h3>❌ 错误</h3>
      <pre>{{ error }}</pre>
    </div>

    <!-- 警告信息 -->
    <div v-if="renderResult?.warnings?.length" class="warnings-panel">
      <h3>⚠️ 警告信息</h3>
      <ul>
        <li v-for="(warning, index) in renderResult.warnings" :key="index">
          {{ warning }}
        </li>
      </ul>
    </div>

    <!-- 布局统计 -->
    <div v-if="renderResult?.layouts_used" class="layouts-stats">
      <h3>📊 布局使用统计</h3>
      <div class="layout-grid">
        <div v-for="(count, layout) in renderResult.layouts_used" :key="layout" class="layout-card">
          <span class="layout-name">{{ layout }}</span>
          <span class="layout-count">{{ count }} 页</span>
        </div>
      </div>
    </div>

    <!-- 图片插槽列表 -->
    <div v-if="renderResult?.image_slots?.length" class="image-slots-panel">
      <h3>🖼️ 图片插槽 ({{ renderResult.image_slots.length }} 个)</h3>
      <div class="slots-grid">
        <div v-for="slot in renderResult.image_slots.slice(0, 12)" :key="slot.slot_id" class="slot-card">
          <div class="slot-header">
            <strong>{{ slot.slot_id }}</strong>
            <span class="slot-page">页面 {{ slot.page_index }}</span>
          </div>
          <div class="slot-content">
            <p class="slot-theme">{{ slot.theme }}</p>
            <div class="slot-meta">
              <span class="slot-style">{{ slot.visual_style }}</span>
              <span class="slot-ratio">{{ slot.aspect_ratio }}</span>
            </div>
            <div class="slot-keywords">
              <span v-for="kw in slot.keywords.slice(0, 3)" :key="kw" class="keyword-tag">
                {{ kw }}
              </span>
            </div>
          </div>
        </div>
      </div>
      <p v-if="renderResult.image_slots.length > 12" class="more-slots">
        还有 {{ renderResult.image_slots.length - 12 }} 个插槽...
      </p>
    </div>

    <!-- HTML 预览 -->
    <div v-if="htmlPath" class="html-preview">
      <h3>📄 渲染结果预览 (HTML Output)</h3>
      <div class="preview-actions">
        <a :href="getHtmlUrl(htmlPath)" 
           target="_blank" 
           class="btn-secondary">
          在新窗口打开
        </a>
        <button @click="copyPath" class="btn-secondary">复制路径</button>
      </div>
      
      <!-- 嵌入预览窗口 -->
      <div class="iframe-container">
        <iframe 
          :src="getHtmlUrl(htmlPath)"
          class="slide-preview-frame"
          title="Slide Preview">
        </iframe>
      </div>
      
      <div class="path-display">
        <code>{{ htmlPath }}</code>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { api } from '../api'

export default {
  name: 'Module35Render',
  props: {
    initialSessionId: {
      type: String,
      default: null
    }
  },
  setup(props) {
    const loading = ref(false)
    const generatingImages = ref(false)
    const error = ref(null)
    const renderResult = ref(null)
    const htmlPath = ref(null)
    const sessionId = ref(null)
    const imageProgress = ref(null)
    const mockSubject = ref('mechanical')
    let pollTimer = null

    // 从URL参数或props获取sessionId
    const getSessionId = () => {
      const urlParams = new URLSearchParams(window.location.search)
      return urlParams.get('session_id') || props.initialSessionId
    }

    const startPolling = (sid) => {
      if (pollTimer) clearInterval(pollTimer)
      
      pollTimer = setInterval(async () => {
        try {
          const res = await api.getRenderStatus(sid)
          if (res.ok && res.images) {
            const images = res.images
            const total = res.total || Object.keys(images).length
            const done = res.done || Object.values(images).filter(i => i.status === 'done').length
            const failed = res.failed || Object.values(images).filter(i => i.status === 'failed').length
            const generating = Object.values(images).filter(i => i.status === 'generating').length
            
            imageProgress.value = { total, done, failed, generating }
            
            // 通知 iframe
            notifyIframe(sid, {
                ok: true,
                images: images,
                total: total,
                done: done,
                failed: failed
            })

            if (done + failed === total && total > 0) {
              clearInterval(pollTimer)
              generatingImages.value = false
            }
          }
        } catch (e) {
          console.error("Poll error", e)
        }
      }, 3000)
    }

    const notifyIframe = (sid, payload) => {
      const iframe = document.querySelector('.slide-preview-frame');
      if (iframe && iframe.contentWindow) {
        iframe.contentWindow.postMessage({
          type: 'IMAGE_STATUS_UPDATE',
          sessionId: sid,
          payload: payload
        }, '*');
      }
    }

    // 方法1：正常流程渲染（从session读取3.1-3.4数据，如果session为空则使用Mock数据）
    const runFullWorkflow = async () => {
      loading.value = true
      error.value = null
      renderResult.value = null
      htmlPath.value = null
      imageProgress.value = null
      if (pollTimer) clearInterval(pollTimer)

      try {
        // 1. 获取或创建session
        let sid = sessionId.value || getSessionId()
        if (!sid) {
          // 如果没有session，创建一个新的
          const sessionRes = await api.createSession()
          sid = sessionRes.session_id
          sessionId.value = sid
          window.history.replaceState({}, '', `?session_id=${sid}`)
        }

        // 2. 尝试从session读取数据
        const sessionData = await api.getSession(sid)
        
        // 3. 检查session中是否有deck_content
        if (sessionData && sessionData.deck_content) {
          // 有deck_content，使用正常流程
          const renderRes = await api.renderSlides(sid)

          if (renderRes.ok) {
            renderResult.value = renderRes
            htmlPath.value = renderRes.html_path
            
            // 开始生成图片
            await generateImages()
          } else {
            error.value = renderRes.error || '渲染失败'
          }
        } else {
          // 没有deck_content，提示用户或使用Mock数据
          console.log('Session中没有deck_content数据，将使用Mock数据进行演示')
          
          // 自动切换到Mock数据渲染
          error.value = null
          await renderWithMockFull()
        }
      } catch (err) {
        // 如果获取session失败，也使用Mock数据
        console.error('获取session失败:', err)
        // 自动切换到Mock数据渲染
        error.value = null
        await renderWithMockFull()
      } finally {
        loading.value = false
      }
    }

    // 错误处理辅助函数
    const handleError = (errorMsg) => {
      if (errorMsg.includes('DASHSCOPE_API_KEY') || errorMsg.includes('API key') || errorMsg.includes('API配置')) {
        error.value = `❌ API Key 未配置\n\n请在环境变量中设置：\n• DASHSCOPE_API_KEY=sk-a46b0b320c0f47b2a0a41a70031ea32b\n• DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1`
      } else if (errorMsg.includes('image.png') || errorMsg.includes('Cannot read')) {
        error.value = `❌ 图片生成失败\n\n原因：API 配置问题\n\n请检查：\n1. DASHSCOPE_API_KEY 是否正确设置\n2. DASHSCOPE_BASE_URL 是否正确设置\n3. 网络连接是否正常`
      } else {
        error.value = errorMsg
      }
    }

    // 方法2：Mock完整数据渲染（使用预设的Mock数据进行测试）
    const renderWithMockFull = async () => {
      loading.value = true
      error.value = null
      renderResult.value = null
      htmlPath.value = null
      imageProgress.value = null
      if (pollTimer) clearInterval(pollTimer)

      try {
        // 使用新的API端点，传入subject参数
        const renderRes = await api.renderWithMockData(mockSubject.value)

        if (renderRes.ok) {
          renderResult.value = renderRes
          htmlPath.value = renderRes.html_path
          sessionId.value = renderRes.session_id

          // 开始生成图片
          await generateImages()
        } else {
          handleError(renderRes.error || 'Mock渲染失败')
        }
      } catch (err) {
        handleError(err.response?.data?.error || err.message)
      } finally {
        loading.value = false
      }
    }

    // 将绝对路径转换为URL路径
    // 后端已挂载 /data 静态目录，只需提取相对路径
    const getHtmlUrl = (absolutePath) => {
      if (!absolutePath) return ''
      
      // 提取 data/ 之后的相对路径
      const dataMatch = absolutePath.match(/data\/(.+)/)
      if (dataMatch) {
        return '/data/' + dataMatch[1]
      }
      
      // 如果路径不匹配，尝试提取 outputs 后的部分
      const outputsMatch = absolutePath.match(/outputs\/(.+)/)
      if (outputsMatch) {
        return '/data/outputs/' + outputsMatch[1]
      }
      
      // 回退：直接使用文件名（可能会404）
      return '/data/outputs/' + absolutePath.split('/').pop()
    }

    // 生成图片
    const generateImages = async () => {
      if (!sessionId.value) {
        error.value = '没有会话ID，无法生成图片'
        return
      }
      
      generatingImages.value = true
      imageProgress.value = { total: 0, done: 0, failed: 0 }
      
      try {
        const res = await api.triggerImageGeneration(sessionId.value)

        if (res.ok) {
          startPolling(sessionId.value)
        } else {
          handleError(res.error || '生成图片失败')
          generatingImages.value = false
        }
      } catch (err) {
        handleError(err.response?.data?.error || err.message)
        generatingImages.value = false
      }
    }

    const copyPath = () => {
      navigator.clipboard.writeText(htmlPath.value)
      alert('路径已复制到剪贴板')
    }

    onMounted(() => {
      const sid = getSessionId()
      if (sid) {
        sessionId.value = sid
      }

      // 监听来自 iframe 的消息
      window.addEventListener('message', (event) => {
        if (event.data && event.data.type === 'GENERATION_STARTED') {
          console.log('[Module35] Generation started from iframe');
          generatingImages.value = true;
          startPolling(event.data.sessionId);
        }
      });
    })

    return {
      loading,
      generatingImages,
      error,
      renderResult,
      htmlPath,
      sessionId,
      imageProgress,
      mockSubject,
      getHtmlUrl,
      runFullWorkflow,
      renderWithMockFull,
      generateImages,
      copyPath,
    }
  },
}
</script>

<style scoped>
.module-35-container {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.module-title {
  font-size: 2rem;
  font-weight: 600;
  margin-bottom: 2rem;
  color: #2c3e50;
}

.control-panel {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: #f8f9fa;
  border-radius: 8px;
  flex-wrap: wrap;
}

.btn-primary, .btn-secondary, .btn-success {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2980b9;
}

.btn-primary:disabled {
  background: #95a5a6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #9b59b6;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #8e44ad;
}

.btn-secondary:disabled {
  background: #95a5a6;
  cursor: not-allowed;
}

.btn-success {
  background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
  color: white;
}

.btn-success:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(39, 174, 96, 0.4);
}

.btn-success:disabled {
  background: #95a5a6;
  cursor: not-allowed;
}

.btn-hint {
  font-size: 0.75rem;
  font-weight: normal;
  opacity: 0.8;
  margin-top: 2px;
}

.subject-select {
  padding: 0.75rem 1rem;
  border: 2px solid #3498db;
  border-radius: 6px;
  font-size: 0.95rem;
  background: white;
  color: #2c3e50;
  cursor: pointer;
}

.subject-select:focus {
  outline: none;
  border-color: #2980b9;
}

.stats {
  display: flex;
  gap: 1.5rem;
  margin-left: auto;
}

.stat-item {
  font-size: 0.95rem;
}

.progress-status {
  width: 100%;
  padding: 1rem;
  background: white;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
}

.progress-status.progress-complete {
  background: #e8f5e9;
  border-color: #27ae60;
}

.progress-bar-container {
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.9rem;
  color: #333;
}

.failed-text {
  color: #e74c3c;
}

.success-text {
  color: #2e7d32;
}

.warnings-panel {
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.warnings-panel h3 {
  margin-top: 0;
  color: #856404;
}

.warnings-panel ul {
  margin: 0;
  padding-left: 1.5rem;
}

.warnings-panel li {
  color: #856404;
  margin-bottom: 0.5rem;
}

.layouts-stats, .image-slots-panel {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.layouts-stats h3, .image-slots-panel h3 {
  margin-top: 0;
  color: #2c3e50;
}

.layout-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.layout-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 6px;
}

.layout-name {
  font-family: monospace;
  font-size: 0.9rem;
  color: #495057;
}

.layout-count {
  font-weight: 600;
  color: #3498db;
}

.slots-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.slot-card {
  border: 1px solid #dee2e6;
  border-radius: 6px;
  padding: 1rem;
  background: #f8f9fa;
}

.slot-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #dee2e6;
}

.slot-header strong {
  font-family: monospace;
  font-size: 0.85rem;
  color: #495057;
}

.slot-page {
  font-size: 0.85rem;
  color: #6c757d;
}

.slot-theme {
  font-weight: 500;
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
}

.slot-meta {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.slot-style, .slot-ratio {
  font-size: 0.8rem;
  padding: 0.25rem 0.5rem;
  background: white;
  border-radius: 4px;
  color: #495057;
}

.slot-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.keyword-tag {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  background: #e3f2fd;
  color: #1976d2;
  border-radius: 4px;
}

.more-slots {
  text-align: center;
  color: #6c757d;
  font-style: italic;
}

.html-preview {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.html-preview h3 {
  margin-top: 0;
  color: #2c3e50;
}

.preview-actions {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.path-display {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 6px;
  border: 1px solid #dee2e6;
}

.path-display code {
  font-family: monospace;
  font-size: 0.9rem;
  color: #495057;
  word-break: break-all;
}

.error-panel {
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 8px;
  padding: 1.5rem;
}

.error-panel h3 {
  margin-top: 0;
  color: #721c24;
}

.error-panel pre {
  margin: 0;
  color: #721c24;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.iframe-container {
  margin-bottom: 1rem;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  overflow: hidden;
  background: #f1f3f5;
  position: relative;
  width: 100%;
  padding-top: 56.25%;
}

.slide-preview-frame {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: none;
}
</style>
