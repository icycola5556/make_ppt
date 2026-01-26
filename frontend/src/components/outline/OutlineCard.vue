<template>
  <div class="outline-card" :class="{ editing: isEditing, selected: isSelected }" @click="handleClick">
    <!-- Drag Handle -->
    <div class="drag-handle" v-if="!isEditing">
      <span>⋮⋮</span>
    </div>
    
    <!-- Card Content -->
    <div class="card-content">
      <!-- Header: Page number and slide type -->
      <div class="card-header">
        <span class="page-num">{{ index + 1 }}</span>
        <span class="slide-type-tag" :style="{ background: slideTypeColor }">
          {{ slideTypeLabel }}
        </span>
      </div>
      
      <!-- View Mode -->
      <div v-if="!isEditing" class="view-mode">
        <h4 class="slide-title">{{ slide.title }}</h4>
        <ul v-if="slide.bullets && slide.bullets.length" class="bullet-list">
          <li v-for="(bullet, i) in slide.bullets" :key="i">{{ bullet }}</li>
        </ul>
        <div v-else class="no-bullets">暂无要点内容</div>
      </div>
      
      <!-- Edit Mode -->
      <div v-else class="edit-mode" @click.stop>
        <input 
          v-model="editTitle" 
          class="edit-input title-input"
          placeholder="幻灯片标题"
        />
        <textarea 
          v-model="editBullets" 
          class="edit-textarea"
          placeholder="要点内容（每行一个）"
          rows="5"
        ></textarea>
        <div class="edit-actions">
          <button class="btn-cancel" @click="cancelEdit">取消</button>
          <button class="btn-save" @click="saveEdit">保存</button>
        </div>
      </div>
    </div>
    
    <!-- Action Buttons -->
    <div v-if="!isEditing" class="card-actions">
      <button class="action-btn" @click.stop="startEdit" title="编辑">✏️</button>
      <button class="action-btn danger" @click.stop="confirmDelete" title="删除">🗑️</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  slide: { type: Object, required: true },
  index: { type: Number, required: true },
  isSelected: { type: Boolean, default: false }
})

const emit = defineEmits(['update', 'delete', 'select'])

// Edit mode state
const isEditing = ref(false)
const editTitle = ref('')
const editBullets = ref('')

// Slide type styling - 完整的中文映射和颜色
const slideTypeMap = {
  title: { label: '封面', color: '#3b82f6' },
  cover: { label: '封面', color: '#3b82f6' },
  intro: { label: '导入', color: '#14b8a6' },
  objectives: { label: '目标', color: '#10b981' },
  concept: { label: '概念', color: '#8b5cf6' },
  content: { label: '内容', color: '#6366f1' },
  principle: { label: '原理', color: '#7c3aed' },
  steps: { label: '步骤', color: '#f59e0b' },
  practice: { label: '实践', color: '#f97316' },
  process: { label: '流程', color: '#eab308' },
  comparison: { label: '对比', color: '#ef4444' },
  case: { label: '案例', color: '#dc2626' },
  case_compare: { label: '案例对比', color: '#b91c1c' },
  tools: { label: '工具', color: '#06b6d4' },
  data: { label: '数据', color: '#0891b2' },
  chart: { label: '图表', color: '#0284c7' },
  summary: { label: '总结', color: '#84cc16' },
  bridge: { label: '过渡', color: '#a3a3a3' },
  transition: { label: '过渡', color: '#a3a3a3' },
  agenda: { label: '议程', color: '#64748b' },
  qa: { label: '问答', color: '#a855f7' },
  discussion: { label: '讨论', color: '#c026d3' },
  exercise: { label: '练习', color: '#ec4899' },
  exercises: { label: '练习', color: '#ec4899' },
  warning: { label: '注意', color: '#ea580c' },
  reference: { label: '参考', color: '#78716c' },
  appendix: { label: '附录', color: '#737373' },
  structure: { label: '结构', color: '#4f46e5' },
  map: { label: '地图', color: '#059669' }
}

// 使用 fallback 避免显示英文
const slideTypeLabel = computed(() => {
  return slideTypeMap[props.slide.slide_type]?.label || '页面'
})

const slideTypeColor = computed(() => {
  return slideTypeMap[props.slide.slide_type]?.color || '#6b7280'
})

// Initialize edit values when entering edit mode
function startEdit() {
  editTitle.value = props.slide.title || ''
  editBullets.value = (props.slide.bullets || []).join('\n')
  isEditing.value = true
}

function cancelEdit() {
  isEditing.value = false
  editTitle.value = ''
  editBullets.value = ''
}

function saveEdit() {
  const bullets = editBullets.value
    .split('\n')
    .map(b => b.trim())
    .filter(b => b.length > 0)
  
  emit('update', {
    title: editTitle.value.trim(),
    bullets
  })
  
  isEditing.value = false
}

function confirmDelete() {
  if (confirm(`确定要删除第 ${props.index + 1} 页吗？`)) {
    emit('delete')
  }
}

// Click handler for selection
function handleClick() {
  if (!isEditing.value) {
    emit('select')
  }
}
</script>

<style scoped>
.outline-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  transition: all 0.2s ease;
  cursor: pointer;
}

.outline-card:hover {
  border-color: #c7d2fe;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.1);
}

.outline-card.selected {
  border-color: #6366f1;
  background: #f5f3ff;
}

.outline-card.editing {
  border-color: #6366f1;
  cursor: default;
}

.drag-handle {
  cursor: grab;
  color: #9ca3af;
  padding: 4px;
  user-select: none;
  font-size: 14px;
  letter-spacing: -2px;
}

.drag-handle:hover {
  color: #6b7280;
}

.card-content {
  flex: 1;
  min-width: 0;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
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
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  color: white;
}

.view-mode .slide-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 8px 0;
}

.bullet-list {
  margin: 0;
  padding-left: 20px;
  color: #475569;
  font-size: 14px;
  line-height: 1.6;
}

.bullet-list li {
  margin-bottom: 4px;
}

.no-bullets {
  color: #9ca3af;
  font-size: 13px;
  font-style: italic;
}

.edit-mode {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.edit-input, .edit-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.edit-input:focus, .edit-textarea:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.title-input {
  font-weight: 600;
}

.edit-textarea {
  resize: vertical;
  min-height: 100px;
  font-family: inherit;
  line-height: 1.6;
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
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  background: white;
  border: 1px solid #d1d5db;
  color: #6b7280;
}

.btn-cancel:hover {
  background: #f3f4f6;
}

.btn-save {
  background: #6366f1;
  border: none;
  color: white;
}

.btn-save:hover {
  background: #4f46e5;
}

.card-actions {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.action-btn {
  padding: 6px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.action-btn:hover {
  opacity: 1;
}

.action-btn.danger:hover {
  opacity: 1;
}
</style>
