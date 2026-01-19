<template>
  <div class="content-card" :class="statusClass">
    <!-- Header -->
    <div class="card-header">
      <span class="page-num">{{ index + 1 }}</span>
      <span class="slide-type-tag">{{ slideTypeLabel }}</span>
      <span class="slide-title">{{ slide.title }}</span>
    </div>
    
    <!-- Loading State (Skeleton) -->
    <div v-if="status === 'loading'" class="skeleton-content">
      <div class="skeleton-line long"></div>
      <div class="skeleton-line medium"></div>
      <div class="skeleton-line short"></div>
      <div class="loading-spinner">⏳</div>
    </div>
    
    <!-- Error State -->
    <div v-else-if="status === 'error'" class="error-content">
      <div class="error-icon">❌</div>
      <div class="error-message">{{ error || '生成失败' }}</div>
      <button class="btn-retry" @click="$emit('regenerate')">重新生成</button>
    </div>
    
    <!-- Idle State (Not Generated) -->
    <div v-else-if="status === 'idle'" class="idle-content">
      <div class="idle-icon">📝</div>
      <div class="idle-text">等待生成内容...</div>
    </div>
    
    <!-- Generated Content -->
    <div v-else-if="status === 'done'" class="generated-content">
      <!-- View Mode -->
      <template v-if="!isEditing">
        <!-- Script -->
        <div class="content-section">
          <h5 class="section-label">🎤 演讲脚本</h5>
          <div class="script-text">{{ content.script || '无' }}</div>
        </div>
        
        <!-- Bullets -->
        <div class="content-section">
          <h5 class="section-label">📋 详细要点</h5>
          <ul v-if="content.bullets && content.bullets.length" class="bullet-list">
            <li v-for="(bullet, i) in content.bullets" :key="i">{{ bullet }}</li>
          </ul>
          <div v-else class="no-content">暂无要点</div>
        </div>
        
        <!-- Visual Suggestions -->
        <div class="content-section">
          <h5 class="section-label">🎨 视觉建议</h5>
          <ul v-if="content.visual_suggestions && content.visual_suggestions.length" class="suggestion-list">
            <li v-for="(sug, i) in content.visual_suggestions" :key="i">{{ sug }}</li>
          </ul>
          <div v-else class="no-content">暂无建议</div>
        </div>
      </template>
      
      <!-- Edit Mode -->
      <template v-else>
        <div class="edit-form" @click.stop>
          <div class="form-group">
            <label>演讲脚本</label>
            <textarea v-model="editScript" rows="3"></textarea>
          </div>
          <div class="form-group">
            <label>详细要点（每行一个）</label>
            <textarea v-model="editBullets" rows="4"></textarea>
          </div>
          <div class="form-group">
            <label>视觉建议（每行一个）</label>
            <textarea v-model="editSuggestions" rows="3"></textarea>
          </div>
          <div class="edit-actions">
            <button class="btn-cancel" @click="cancelEdit">取消</button>
            <button class="btn-save" @click="saveEdit">保存</button>
          </div>
        </div>
      </template>
      
      <!-- Action Bar -->
      <div v-if="!isEditing" class="action-bar">
        <button class="action-btn" @click="startEdit" title="编辑">✏️ 编辑</button>
        <button class="action-btn regenerate" @click="$emit('regenerate')" title="重新生成">🔄 重新生成</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  slide: { type: Object, required: true },
  index: { type: Number, required: true },
  status: { type: String, default: 'idle' }, // 'idle' | 'loading' | 'done' | 'error'
  content: { type: Object, default: null },
  error: { type: String, default: null }
})

const emit = defineEmits(['regenerate', 'update'])

// Edit state
const isEditing = ref(false)
const editScript = ref('')
const editBullets = ref('')
const editSuggestions = ref('')

// Slide type label
const slideTypeMap = {
  title: '封面', objectives: '目标', concept: '概念', content: '内容',
  steps: '步骤', comparison: '对比', tools: '工具', summary: '总结', exercise: '练习'
}

const slideTypeLabel = computed(() => slideTypeMap[props.slide.slide_type] || props.slide.slide_type)

const statusClass = computed(() => ({
  'is-loading': props.status === 'loading',
  'is-error': props.status === 'error',
  'is-done': props.status === 'done',
  'is-idle': props.status === 'idle'
}))

function startEdit() {
  if (!props.content) return
  editScript.value = props.content.script || ''
  editBullets.value = (props.content.bullets || []).join('\n')
  editSuggestions.value = (props.content.visual_suggestions || []).join('\n')
  isEditing.value = true
}

function cancelEdit() {
  isEditing.value = false
}

function saveEdit() {
  const updated = {
    script: editScript.value.trim(),
    bullets: editBullets.value.split('\n').map(b => b.trim()).filter(b => b),
    visual_suggestions: editSuggestions.value.split('\n').map(s => s.trim()).filter(s => s)
  }
  emit('update', updated)
  isEditing.value = false
}
</script>

<style scoped>
.content-card {
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px;
  transition: all 0.2s;
}

.content-card.is-loading {
  border-color: #fbbf24;
  background: #fffbeb;
}

.content-card.is-error {
  border-color: #ef4444;
  background: #fef2f2;
}

.content-card.is-done {
  border-color: #10b981;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.page-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: #6366f1;
  color: white;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
}

.slide-type-tag {
  padding: 2px 8px;
  background: #e0e7ff;
  color: #4f46e5;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.slide-title {
  font-weight: 600;
  color: #1e293b;
  font-size: 14px;
}

/* Skeleton Loading */
.skeleton-content {
  position: relative;
  padding: 16px 0;
}

.skeleton-line {
  height: 12px;
  background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
  margin-bottom: 8px;
}

.skeleton-line.long { width: 100%; }
.skeleton-line.medium { width: 75%; }
.skeleton-line.short { width: 50%; }

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.loading-spinner {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 24px;
  animation: bounce 1s infinite;
}

@keyframes bounce {
  0%, 100% { transform: translate(-50%, -50%) scale(1); }
  50% { transform: translate(-50%, -50%) scale(1.2); }
}

/* Error State */
.error-content {
  text-align: center;
  padding: 20px;
}

.error-icon { font-size: 32px; margin-bottom: 8px; }
.error-message { color: #dc2626; font-size: 13px; margin-bottom: 12px; }

.btn-retry {
  padding: 8px 16px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
}

.btn-retry:hover { background: #dc2626; }

/* Idle State */
.idle-content {
  text-align: center;
  padding: 24px;
  color: #9ca3af;
}

.idle-icon { font-size: 32px; margin-bottom: 8px; }
.idle-text { font-size: 13px; }

/* Generated Content */
.generated-content .content-section {
  margin-bottom: 16px;
}

.section-label {
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  margin: 0 0 8px 0;
}

.script-text {
  background: #f8fafc;
  padding: 12px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
  color: #334155;
}

.bullet-list, .suggestion-list {
  margin: 0;
  padding-left: 20px;
  font-size: 14px;
  line-height: 1.6;
  color: #475569;
}

.bullet-list li, .suggestion-list li {
  margin-bottom: 4px;
}

.no-content {
  color: #9ca3af;
  font-size: 13px;
  font-style: italic;
}

/* Edit Form */
.edit-form { display: flex; flex-direction: column; gap: 12px; }

.form-group label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 4px;
}

.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  resize: vertical;
}

.form-group textarea:focus {
  outline: none;
  border-color: #6366f1;
}

.edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.btn-cancel, .btn-save {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
}

.btn-cancel {
  background: white;
  border: 1px solid #d1d5db;
  color: #6b7280;
}

.btn-save {
  background: #6366f1;
  border: none;
  color: white;
}

/* Action Bar */
.action-bar {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #e5e7eb;
}

.action-btn {
  padding: 6px 12px;
  background: #f1f5f9;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.action-btn:hover { background: #e2e8f0; }
.action-btn.regenerate { color: #6366f1; }
</style>
