<template>
  <div class="content-generator-page">
    <!-- Header -->
    <header class="generator-header">
      <div class="header-left">
        <button class="back-btn" @click="goBack">← 返回大纲</button>
        <h1>✨ 内容生成器</h1>
      </div>
      <div class="header-right">
        <button 
          class="render-btn"
          @click="startRender"
          :disabled="!contentGenerator.allCompleted.value || isRendering"
          v-if="contentGenerator.allCompleted.value"
        >
          {{ isRendering ? '渲染中...' : '🎨 生成 PPT' }}
        </button>
        <button 
          class="generate-btn" 
          @click="startGeneration"
          :disabled="contentGenerator.isGenerating.value"
        >
          {{ contentGenerator.isGenerating.value ? '生成中...' : '🚀 开始生成' }}
        </button>
      </div>
    </header>

    <!-- Progress Bar -->
    <div class="progress-section">
      <div class="progress-info">
        <span class="progress-text">
          已完成 {{ contentGenerator.progress.value.completed }} / {{ contentGenerator.progress.value.total }} 页
        </span>
        <span class="progress-percent">{{ contentGenerator.progress.value.percent }}%</span>
      </div>
      <div class="progress-bar-container">
        <div 
          class="progress-bar-fill" 
          :style="{ width: contentGenerator.progress.value.percent + '%' }"
        ></div>
      </div>
    </div>

    <!-- Card Grid -->
    <div class="card-grid-container">
      <div class="card-grid">
        <ContentCard
          v-for="(slide, idx) in slides"
          :key="idx"
          :slide="slide"
          :index="idx"
          :status="contentGenerator.slideStatus[idx] || 'idle'"
          :content="contentGenerator.generatedContent[idx]"
          :error="contentGenerator.slideErrors[idx]"
          @regenerate="regenerateSlide(idx)"
          @update="(content) => handleUpdateContent(idx, content)"
        />
      </div>
    </div>

    <!-- Toast Container -->
    <div class="toast-container">
      <div 
        v-for="toast in contentGenerator.toasts.value" 
        :key="toast.id"
        class="toast"
        :class="toast.type"
      >
        {{ toast.message }}
        <button class="toast-close" @click="contentGenerator.removeToast(toast.id)">×</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkflow } from '../composables/useWorkflow'
import { useContentGenerator } from '../composables/useContentGenerator'
import ContentCard from '../components/content/ContentCard.vue'
import { api, getApiBase } from '../api'

const router = useRouter()
const workflow = useWorkflow()
const contentGenerator = useContentGenerator()

const isRendering = ref(false)

async function startRender() {
  if (!workflow.sessionId.value) return
  isRendering.value = true
  try {
    const res = await api.renderSlides(workflow.sessionId.value)
    if (res.ok && res.html_path) {
        // Convert absolute path to URL
        // Expected path: .../data/outputs/...
        const parts = res.html_path.split('/data/')
        if (parts.length > 1) {
            const relPath = parts[1] // outputs/session_id/index.html
            // Construct URL: API_BASE + /data/ + relPath
            const baseUrl = getApiBase().replace(/\/$/, '')
            const url = `${baseUrl}/data/${relPath}`
            window.open(url, '_blank')
            contentGenerator.addToast('渲染成功！已在新窗口打开', 'success')
        } else {
            console.warn('Path parse error:', res.html_path)
            contentGenerator.addToast('渲染成功，但无法解析路径', 'success') // still success but warn
        }
    } else {
        contentGenerator.addToast('渲染失败: ' + (res.error || 'Unknown'), 'error')
    }
  } catch (e) {
    contentGenerator.addToast('渲染请求出错: ' + e.message, 'error')
  } finally {
    isRendering.value = false
  }
}

// Get slides from workflow outline
const slides = computed(() => {
  return workflow.outline.value?.slides || []
})

// Initialize on mount
onMounted(() => {
  if (workflow.outline.value && workflow.sessionId.value) {
    contentGenerator.initForSlides(workflow.outline.value, workflow.sessionId.value)
  }
})

// Watch for outline changes
watch(() => workflow.outline.value, (newOutline) => {
  if (newOutline && workflow.sessionId.value) {
    contentGenerator.initForSlides(newOutline, workflow.sessionId.value)
  }
})

function goBack() {
  router.push('/outline-editor')
}

// ... existing code ...
async function startGeneration() {
  await contentGenerator.generateAllSlides(6) // concurrency limit = 6
}

async function regenerateSlide(index) {
  await contentGenerator.regenerateSlide(index)
}

function handleUpdateContent(index, content) {
  contentGenerator.updateContent(index, content)
}
</script>

<style scoped>
.content-generator-page {
  min-height: 100vh;
  background: #f8fafc;
}

.generator-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
}

.back-btn {
  padding: 8px 12px;
  background: none;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}

.back-btn:hover {
  background: #f3f4f6;
}

.generate-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.3);
}

.generate-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
}

.generate-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.render-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3);
  margin-right: 12px;
}
.render-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
}
.render-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  background: #9ca3af;
  box-shadow: none;
}

.progress-section {
  padding: 16px 24px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.progress-text {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.progress-percent {
  font-size: 14px;
  font-weight: 600;
  color: #6366f1;
}

.progress-bar-container {
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.card-grid-container {
  padding: 24px;
  overflow-y: auto;
  max-height: calc(100vh - 180px);
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

/* Toast Notifications */
.toast-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 1000;
}

.toast {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  font-size: 14px;
  animation: slideIn 0.3s ease;
  min-width: 250px;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.toast.success {
  border-left: 4px solid #10b981;
}

.toast.error {
  border-left: 4px solid #ef4444;
}

.toast-close {
  background: none;
  border: none;
  font-size: 18px;
  color: #9ca3af;
  cursor: pointer;
  padding: 0 0 0 12px;
}

.toast-close:hover {
  color: #374151;
}
</style>
