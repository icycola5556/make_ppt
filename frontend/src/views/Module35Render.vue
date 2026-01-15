<template>
  <div class="module-35-container">
    <h2 class="module-title">3.5 智能排版与动态渲染</h2>
    
    <div class="control-panel">
      <button @click="testRender" class="btn-primary" :disabled="loading">
        {{ loading ? '渲染中...' : '测试渲染' }}
      </button>
      
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
        <div v-for="slot in renderResult.image_slots.slice(0, 6)" :key="slot.slot_id" class="slot-card">
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
      <p v-if="renderResult.image_slots.length > 6" class="more-slots">
        还有 {{ renderResult.image_slots.length - 6 }} 个插槽...
      </p>
    </div>

    <!-- HTML 预览 -->
    <div v-if="htmlPath" class="html-preview">
      <h3>📄 HTML 输出</h3>
      <div class="preview-actions">
        <a :href="`http://127.0.0.1:8000/data/outputs/${htmlPath.split('/').pop()}`" 
           target="_blank" 
           class="btn-secondary">
          在新窗口打开
        </a>
        <button @click="copyPath" class="btn-secondary">复制路径</button>
      </div>
      <div class="path-display">
        <code>{{ htmlPath }}</code>
      </div>
    </div>

    <!-- 错误信息 -->
    <div v-if="error" class="error-panel">
      <h3>❌ 错误</h3>
      <pre>{{ error }}</pre>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import api from '../api'

export default {
  name: 'Module35Render',
  setup() {
    const loading = ref(false)
    const renderResult = ref(null)
    const htmlPath = ref(null)
    const error = ref(null)

    const testRender = async () => {
      loading.value = true
      error.value = null
      renderResult.value = null
      htmlPath.value = null

      try {
        // 创建测试 session
        const sessionRes = await api.post('/api/session')
        const sessionId = sessionRes.data.session_id

        // 运行完整工作流到 3.4
        const workflowRes = await api.post('/api/workflow/run', {
          session_id: sessionId,
          user_text: '液压系统工作原理',
          answers: {
            professional_category: '机械制造',
            teaching_scenario: 'practice',
            slide_count: 7,
          },
          auto_fill_defaults: true,
          stop_at: '3.4',
        })

        if (workflowRes.data.status === 'ok' && workflowRes.data.deck_content) {
          // 调用 3.5 渲染 API (需要在后端添加)
          const renderRes = await api.post('/api/workflow/render', {
            session_id: sessionId,
          })

          renderResult.value = renderRes.data
          htmlPath.value = renderRes.data.html_path
        } else {
          error.value = '工作流未完成到 3.4 阶段'
        }
      } catch (err) {
        error.value = err.response?.data?.detail || err.message
      } finally {
        loading.value = false
      }
    }

    const copyPath = () => {
      navigator.clipboard.writeText(htmlPath.value)
      alert('路径已复制到剪贴板')
    }

    return {
      loading,
      renderResult,
      htmlPath,
      error,
      testRender,
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
  gap: 2rem;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.btn-primary, .btn-secondary {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
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
  background: white;
  color: #3498db;
  border: 2px solid #3498db;
  text-decoration: none;
  display: inline-block;
}

.btn-secondary:hover {
  background: #3498db;
  color: white;
}

.stats {
  display: flex;
  gap: 1.5rem;
}

.stat-item {
  font-size: 0.95rem;
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
</style>
