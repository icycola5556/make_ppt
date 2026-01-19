<template>
  <div class="outline-editor-page">
    <!-- Header -->
    <header class="editor-header">
      <div class="header-left">
        <button class="back-btn" @click="goBack">← 返回</button>
        <h1>📋 大纲编辑器</h1>
      </div>
      <div class="header-right">
        <span v-if="outlineEditor.isDirty.value" class="unsaved-badge">未保存</span>
        <button 
          class="save-btn" 
          @click="handleSave" 
          :disabled="outlineEditor.saving.value"
        >
          {{ outlineEditor.saving.value ? '保存中...' : '💾 保存' }}
        </button>
        <button 
          class="next-btn" 
          @click="goToContentGenerator"
          :disabled="outlineEditor.slideCount.value === 0"
        >
          下一步 →
        </button>
      </div>
    </header>

    <!-- Toolbar -->
    <div class="toolbar">
      <button class="tool-btn primary" @click="addNewSlide">
        ➕ 添加页面
      </button>
      <div class="slide-count">
        共 {{ outlineEditor.slideCount.value }} 页
      </div>
    </div>

    <!-- Error Message -->
    <div v-if="outlineEditor.saveError.value" class="error-banner">
      ❌ {{ outlineEditor.saveError.value }}
    </div>

    <!-- Main Content -->
    <div class="editor-layout">
      <!-- Left: Card List -->
      <div class="card-list-container">
        <div v-if="outlineEditor.slides.value.length === 0" class="empty-state">
          <div class="empty-icon">📝</div>
          <h3>还没有幻灯片</h3>
          <p>点击"添加页面"创建第一页，或从模块3.3生成大纲</p>
        </div>
        
        <div v-else class="card-list">
          <OutlineCard
            v-for="(slide, idx) in outlineEditor.slides.value"
            :key="slide.index || idx"
            :slide="slide"
            :index="idx"
            :is-selected="outlineEditor.selectedIndex.value === idx"
            @select="outlineEditor.selectSlide(idx)"
            @update="(data) => handleUpdateSlide(idx, data)"
            @delete="handleDeleteSlide(idx)"
          />
        </div>
      </div>

      <!-- Right: Preview Panel -->
      <div class="preview-panel">
        <h3>预览</h3>
        <div v-if="outlineEditor.selectedSlide.value" class="preview-content">
          <div class="preview-header">
            <span class="preview-page">第 {{ outlineEditor.selectedIndex.value + 1 }} 页</span>
            <span class="preview-type">{{ outlineEditor.selectedSlide.value.slide_type }}</span>
          </div>
          <h4 class="preview-title">{{ outlineEditor.selectedSlide.value.title }}</h4>
          <ul v-if="outlineEditor.selectedSlide.value.bullets && outlineEditor.selectedSlide.value.bullets.length" class="preview-bullets">
            <li v-for="(b, i) in outlineEditor.selectedSlide.value.bullets" :key="i">{{ b }}</li>
          </ul>
          <div v-else class="preview-empty">暂无要点内容</div>
        </div>
        <div v-else class="preview-placeholder">
          <div class="placeholder-icon">👆</div>
          <p>点击左侧卡片查看详情</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useWorkflow } from '../composables/useWorkflow'
import { useOutlineEditor } from '../composables/useOutlineEditor'
import OutlineCard from '../components/outline/OutlineCard.vue'

const router = useRouter()
const route = useRoute()
const workflow = useWorkflow()
const outlineEditor = useOutlineEditor()

// Initialize from workflow state on mount
onMounted(() => {
  if (workflow.outline.value && workflow.sessionId.value) {
    outlineEditor.initFromOutline(workflow.outline.value, workflow.sessionId.value)
  }
})

// Watch for outline changes from workflow
watch(() => workflow.outline.value, (newOutline) => {
  if (newOutline && workflow.sessionId.value) {
    outlineEditor.initFromOutline(newOutline, workflow.sessionId.value)
  }
})

function goBack() {
  router.push('/3.3')
}

function handleUpdateSlide(index, data) {
  outlineEditor.updateSlide(index, data)
}

function handleDeleteSlide(index) {
  outlineEditor.deleteSlide(index)
}

function addNewSlide() {
  outlineEditor.addSlide()
}

async function handleSave() {
  await outlineEditor.saveOutline()
}

async function goToContentGenerator() {
  // Save first if dirty
  if (outlineEditor.isDirty.value) {
    const saved = await outlineEditor.saveOutline()
    if (!saved) return
  }
  
  router.push('/content-generator')
}
</script>

<style scoped>
.outline-editor-page {
  min-height: 100vh;
  background: #f8fafc;
}

.editor-header {
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

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.unsaved-badge {
  padding: 4px 8px;
  background: #fef3c7;
  color: #d97706;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.save-btn, .next-btn {
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.save-btn {
  background: white;
  border: 1px solid #d1d5db;
  color: #374151;
}

.save-btn:hover:not(:disabled) {
  background: #f3f4f6;
}

.next-btn {
  background: #6366f1;
  border: none;
  color: white;
}

.next-btn:hover:not(:disabled) {
  background: #4f46e5;
}

.next-btn:disabled, .save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
}

.tool-btn {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.tool-btn.primary {
  background: #10b981;
  border: none;
  color: white;
}

.tool-btn.primary:hover {
  background: #059669;
}

.slide-count {
  font-size: 14px;
  color: #6b7280;
}

.error-banner {
  padding: 12px 24px;
  background: #fef2f2;
  border-bottom: 1px solid #fecaca;
  color: #dc2626;
  font-size: 14px;
}

.editor-layout {
  display: flex;
  height: calc(100vh - 140px);
}

.card-list-container {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #6b7280;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-state h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #374151;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}

.card-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 700px;
  margin: 0 auto;
}

.preview-panel {
  width: 350px;
  background: white;
  border-left: 1px solid #e5e7eb;
  padding: 24px;
  overflow-y: auto;
}

.preview-panel h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #374151;
}

.preview-content {
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.preview-header {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.preview-page {
  padding: 4px 8px;
  background: #6366f1;
  color: white;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.preview-type {
  padding: 4px 8px;
  background: #e0e7ff;
  color: #4f46e5;
  border-radius: 4px;
  font-size: 12px;
}

.preview-title {
  margin: 0 0 12px 0;
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.preview-bullets {
  margin: 0;
  padding-left: 20px;
  color: #475569;
  font-size: 14px;
  line-height: 1.6;
}

.preview-bullets li {
  margin-bottom: 6px;
}

.preview-empty {
  color: #9ca3af;
  font-size: 13px;
  font-style: italic;
}

.preview-placeholder {
  text-align: center;
  padding: 40px 20px;
  color: #9ca3af;
}

.placeholder-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.preview-placeholder p {
  margin: 0;
  font-size: 14px;
}
</style>
