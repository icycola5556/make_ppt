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
    <div v-if="renderResult?.layouts_used" class="layouts-stats highlight-panel">
      <h3>📊 布局使用统计</h3>
      <div class="layout-grid">
        <div v-for="(count, layout) in renderResult.layouts_used" :key="layout" class="layout-card">
          <span class="layout-name">{{ layout }}</span>
          <span class="layout-count">{{ count }} 页</span>
        </div>
      </div>
    </div>

    <!-- 图片插槽列表 -->
    <div v-if="renderResult?.image_slots?.length" class="image-slots-panel highlight-panel">
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
    <div v-if="htmlPath" class="html-preview-panel">
      <h3>📄 渲染结果预览 (HTML Output)</h3>
      <div class="preview-actions">
        <a :href="getHtmlUrl(htmlPath)" 
           target="_blank" 
           class="btn-secondary">
          🔗 在新窗口打开
        </a>
        <button @click="copyPath" class="btn-secondary">📋 复制路径</button>
        <a :href="downloadUrl" target="_blank" class="btn-primary" style="background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); border:none; box-shadow: 0 4px 6px -1px rgba(217, 119, 6, 0.3);">
          📥 下载项目包 (ZIP)
        </a>
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
import { ref, onMounted, computed } from 'vue'
import { api } from '../api'
import { useWorkflow } from '../composables/useWorkflow'

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

    // 使用useWorkflow获取缓存
    const { getCachedSessionId, hasCachedSession, hasCache } = useWorkflow()

    // 从URL参数、props或缓存获取sessionId
    const getSessionId = () => {
      const urlParams = new URLSearchParams(window.location.search)
      // 优先级：URL参数 > props > 缓存
      return urlParams.get('session_id') || props.initialSessionId || getCachedSessionId()
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
        error.value = `❌ API Key 未配置\n\n请在环境变量中设置：\n• DASHSCOPE_API_KEY=your-dashscope-api-key\n• DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1`
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

          // ✅【关键修复】立即更新浏览器 URL，防止刷新后丢失新 Session ID
          window.history.replaceState({}, '', `?session_id=${renderRes.session_id}`)

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
      const urlParams = new URLSearchParams(window.location.search)
      // 优先从URL获取，然后从props，最后从缓存
      let sid = urlParams.get('session_id') || props.initialSessionId
      const shouldAutoRun = urlParams.get('auto_run') === 'true'

      // 如果URL和props都没有sessionId，尝试从缓存获取
      if (!sid && hasCachedSession()) {
        sid = getCachedSessionId()
        console.log('[Module35] 从缓存恢复sessionId:', sid)
        // 更新URL以便刷新后保持状态
        if (sid) {
          const newUrl = window.location.protocol + "//" + window.location.host + window.location.pathname + `?session_id=${sid}`;
          window.history.replaceState({path: newUrl}, '', newUrl);
        }
      }

      if (sid) {
        sessionId.value = sid

        // ✅ 新增：如果检测到自动运行标记，且没有正在加载，则自动触发
        if (shouldAutoRun && !loading.value) {
          console.log('Auto-running workflow based on URL param...')
          // 清除 URL 中的 auto_run 参数，防止刷新页面重复触发
          const newUrl = window.location.protocol + "//" + window.location.host + window.location.pathname + `?session_id=${sid}`;
          window.history.replaceState({path: newUrl}, '', newUrl);

          // 触发正常渲染流程
          runFullWorkflow()
        }
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

    const downloadUrl = computed(() => {
      if (!sessionId.value) return '#'
      return api.getDownloadUrl(sessionId.value)
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
      downloadUrl
    }
  },
}
</script>

<style scoped>
/* 模块35容器 - 工作台布局 */
.module-35-container {
  --color-module: var(--color-35);
  --color-module-light: var(--color-35-light);
  padding: var(--spacing-6);
  max-width: 1200px;
  margin: 0 auto;
  animation: slide-up 0.5s ease-out;
}

.module-title {
  font-family: var(--font-serif);
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-black);
  color: var(--color-brand);
  margin-bottom: var(--spacing-8);
  letter-spacing: -0.02em;
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.module-title::before {
  content: '3.5';
  font-size: var(--font-size-sm);
  background: linear-gradient(135deg, var(--color-module) 0%, #F472B6 100%);
  color: #fff;
  padding: 4px 10px;
  border-radius: var(--radius-full);
  font-weight: 800;
  vertical-align: middle;
  box-shadow: 0 2px 4px rgba(236, 72, 153, 0.3);
}

/* 控制面板 - 玻璃态 */
.control-panel {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
  margin-bottom: var(--spacing-8);
  padding: var(--spacing-6);
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border-radius: var(--radius-xl);
  flex-wrap: wrap;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 10px 30px -10px rgba(0,0,0,0.05);
}

/* 按钮组优化 */
.btn-primary, .btn-secondary, .btn-success {
  padding: var(--spacing-4) var(--spacing-6);
  border: none;
  border-radius: var(--radius-lg);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--duration-fast);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-width: 140px;
}

.btn-primary {
  background: linear-gradient(135deg, var(--color-brand) 0%, var(--color-brand-hover) 100%);
  color: var(--text-inverse);
  box-shadow: 0 4px 6px -1px rgba(13, 148, 136, 0.3);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(13, 148, 136, 0.4);
}

.btn-primary:disabled {
  background: var(--text-muted);
  cursor: not-allowed;
  box-shadow: none;
}

.btn-secondary {
  background: #fff;
  color: var(--text-primary);
  border: 1px solid var(--border-light);
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}

.btn-secondary:hover:not(:disabled) {
  border-color: var(--color-brand);
  background: var(--color-brand-light);
  transform: translateY(-2px);
  color: var(--color-brand);
}

.btn-secondary:disabled {
  background: var(--bg-input);
  color: var(--text-muted);
  cursor: not-allowed;
}

.btn-success {
  background: linear-gradient(135deg, #10B981 0%, #059669 100%);
  color: var(--text-inverse);
  box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.3);
}

.btn-success:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.4);
}

.btn-hint {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-normal);
  opacity: 0.85;
  margin-top: 4px;
}

.subject-select {
  padding: var(--spacing-3) var(--spacing-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-base);
  background: #fff;
  color: var(--text-primary);
  cursor: pointer;
  transition: all var(--duration-fast);
  min-width: 120px;
}

.subject-select:focus {
  outline: none;
  border-color: var(--color-brand);
  box-shadow: 0 0 0 3px var(--color-brand-light);
}

.stats {
  display: flex;
  gap: var(--spacing-6);
  margin-left: auto;
  padding: var(--spacing-3) var(--spacing-5);
  background: rgba(255,255,255,0.5);
  border-radius: var(--radius-full);
}

.stat-item {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}
.stat-item strong { color: var(--text-primary); }

.progress-status {
  width: 100%;
  margin-top: var(--spacing-4);
  padding-top: var(--spacing-4);
  border-top: 1px solid rgba(0,0,0,0.05);
}

.progress-bar-container {
  width: 100%;
  height: 6px;
  background: var(--bg-input);
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-bottom: var(--spacing-2);
}

.progress-bar-fill {
  height: 100%;
  background: var(--color-success);
  transition: width 0.3s ease;
  border-radius: var(--radius-full);
}

.progress-text {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  font-weight: 600;
  display: flex;
  justify-content: space-between;
}

.failed-text { color: var(--color-error); }
.success-text { color: var(--color-success); }

/* 面板通用样式 */
.highlight-panel {
  background: #fff;
  border-radius: var(--radius-xl);
  padding: var(--spacing-8);
  margin-bottom: var(--spacing-8);
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
  border: 1px solid var(--border-light);
}

.highlight-panel h3 {
  margin: 0 0 var(--spacing-6) 0;
  color: var(--text-primary);
  font-weight: var(--font-weight-bold);
  font-size: var(--font-size-xl);
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.layout-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: var(--spacing-4);
}

.layout-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-4);
  background: var(--bg-input);
  border-radius: var(--radius-lg);
  border: 1px solid transparent;
  transition: all 0.2s;
}

.layout-card:hover { border-color: var(--color-brand); background: var(--color-brand-light); }

.layout-name {
  font-family: var(--font-mono);
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  font-weight: 600;
}

.layout-count {
  font-weight: var(--font-weight-bold);
  color: var(--color-brand);
  background: #fff;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: var(--font-size-xs);
}

/* 图片插槽 */
.slots-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--spacing-5);
  margin-bottom: var(--spacing-4);
}

.slot-card {
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  padding: var(--spacing-5);
  background: #fff;
  transition: all 0.3s;
}

.slot-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--color-module);
}

.slot-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--spacing-3);
  padding-bottom: var(--spacing-3);
  border-bottom: 1px solid var(--border-light);
}

.slot-header strong {
  font-family: var(--font-mono);
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  background: var(--bg-input);
  padding: 2px 6px;
  border-radius: 4px;
}

.slot-page {
  font-size: var(--font-size-xs);
  color: var(--color-brand);
  font-weight: 600;
}

.slot-theme {
  font-weight: var(--font-weight-bold);
  margin: 0 0 var(--spacing-3) 0;
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-snug);
}

.slot-meta {
  display: flex;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-3);
}

.slot-style, .slot-ratio {
  font-size: 10px;
  text-transform: uppercase;
  padding: 2px 6px;
  background: var(--bg-input);
  border-radius: 4px;
  color: var(--text-secondary);
  font-weight: 600;
}

.slot-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.keyword-tag {
  font-size: 10px;
  padding: 2px 6px;
  background: var(--color-brand-light);
  color: var(--color-brand);
  border-radius: 4px;
}

.more-slots {
  text-align: center;
  color: var(--text-muted);
  font-size: var(--font-size-sm);
  margin-top: var(--spacing-4);
}

/* HTML 预览面板 */
.html-preview-panel {
  background: #fff;
  border-radius: var(--radius-xl);
  padding: var(--spacing-6);
  box-shadow: var(--shadow-xl);
  border: 1px solid var(--border-light);
}

.preview-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-4);
  padding-bottom: var(--spacing-4);
  border-bottom: 1px solid var(--border-light);
}

.path-display {
  background: var(--bg-input);
  padding: var(--spacing-3) var(--spacing-4);
  border-radius: var(--radius-md);
  border: 1px dashed var(--border-default);
  margin-top: var(--spacing-4);
}

.path-display code {
  font-family: var(--font-mono);
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

/* 错误面板 */
.error-panel {
  background: #FEF2F2;
  border: 1px solid #FCA5A5;
  border-radius: var(--radius-lg);
  padding: var(--spacing-6);
  margin-bottom: var(--spacing-6);
}

.error-panel h3 { margin-top: 0; color: #DC2626; display: flex; align-items: center; gap: 8px; }
.error-panel pre { color: #B91C1C; background: rgba(255,255,255,0.5); padding: var(--spacing-4); border-radius: var(--radius-md); }

/* WARNINGS */
.warnings-panel {
  background: #FFFBEB;
  border: 1px solid #FCD34D;
  border-radius: var(--radius-lg);
  padding: var(--spacing-6);
  margin-bottom: var(--spacing-6);
}

.warnings-panel h3 { margin-top: 0; color: #D97706; }
.warnings-panel li { color: #B45309; }

/* iframe 预览 */
.iframe-container {
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: #f8fafc;
  position: relative;
  width: 100%;
  padding-top: 56.25%; /* 16:9 Aspect Ratio */
  box-shadow: inset 0 0 20px rgba(0,0,0,0.05);
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
