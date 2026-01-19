<template>
  <div class="cache-status">
    <div class="cache-header">
      <span class="cache-icon">💾</span>
      <span class="cache-title">步骤缓存状态</span>
      <button class="clear-btn" @click="handleClearAll" title="清空所有缓存">🗑️ 清空</button>
    </div>
    
    <div class="cache-items">
      <div 
        v-for="step in steps" 
        :key="step.id"
        class="cache-item"
        :class="{ cached: hasCache(step.id), active: activeStep === step.id }"
        @click="handleLoadCache(step.id)"
      >
        <span class="step-badge" :class="{ cached: hasCache(step.id) }">{{ step.id }}</span>
        <div class="step-info">
          <span class="step-name">{{ step.name }}</span>
          <span class="step-status" v-if="hasCache(step.id)">
            ✅ {{ getCacheInfo(step.id) }}
          </span>
          <span class="step-status empty" v-else>无缓存</span>
        </div>
        <button 
          v-if="hasCache(step.id)" 
          class="use-btn"
          @click.stop="$emit('use-cache', step.id)"
          title="使用此缓存继续后续步骤"
        >
          使用 →
        </button>
      </div>
    </div>
    
    <div v-if="hasAnyCached" class="cache-hint">
      💡 点击"使用"可跳过该步骤，直接使用缓存结果
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useWorkflow } from '../../composables/useWorkflow'

const props = defineProps({
  activeStep: { type: String, default: '' }
})

defineEmits(['use-cache', 'clear-cache'])

const { stepCache, hasCache, getCacheSummary, clearCacheFrom } = useWorkflow()

const steps = [
  { id: '3.1', name: '意图理解' },
  { id: '3.2', name: '风格设计' },
  { id: '3.3', name: '大纲生成' },
  { id: '3.4', name: '内容生成' },
]

const hasAnyCached = computed(() => {
  return steps.some(s => hasCache(s.id))
})

function getCacheInfo(stepId) {
  const summary = getCacheSummary()
  const info = summary[stepId]
  if (!info) return ''
  
  switch (stepId) {
    case '3.1':
      return `${info.subject || '未知课程'} (${info.kpCount}个知识点, ${info.slideCount}页)`
    case '3.2':
      return info.styleName || '已配置'
    case '3.3':
      return `${info.title || '大纲'} (${info.slideCount}页)`
    case '3.4':
      return '已生成'
    default:
      return '已缓存'
  }
}

function handleLoadCache(stepId) {
  // 点击缓存项时的行为，可以预览缓存内容
  console.log('[CacheStatus] 点击缓存项:', stepId, stepCache[stepId])
}

function handleClearAll() {
  if (confirm('确定清空所有步骤缓存吗？')) {
    clearCacheFrom('3.1')
  }
}
</script>

<style scoped>
.cache-status {
  background: linear-gradient(135deg, #f0f9ff, #f8fafc);
  border: 1px solid #bae6fd;
  border-radius: 12px;
  padding: 12px;
  margin-bottom: 16px;
}

.cache-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px dashed #bae6fd;
}

.cache-icon { font-size: 16px; }
.cache-title { font-weight: 600; font-size: 13px; color: #0369a1; flex: 1; }

.clear-btn {
  font-size: 11px;
  padding: 4px 8px;
  border: 1px solid #fecaca;
  background: #fef2f2;
  color: #dc2626;
  border-radius: 6px;
  cursor: pointer;
}
.clear-btn:hover { background: #fee2e2; }

.cache-items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.cache-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 180px;
  flex: 1;
}

.cache-item:hover {
  border-color: #0ea5e9;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.1);
}

.cache-item.cached {
  background: #f0fdf4;
  border-color: #86efac;
}

.cache-item.active {
  border-color: #7c3aed;
  box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.2);
}

.step-badge {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #e2e8f0;
  color: #64748b;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  flex-shrink: 0;
}

.step-badge.cached {
  background: #22c55e;
  color: white;
}

.step-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.step-name {
  font-weight: 600;
  font-size: 12px;
  color: #334155;
}

.step-status {
  font-size: 11px;
  color: #16a34a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.step-status.empty {
  color: #94a3b8;
}

.use-btn {
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 600;
  background: #0ea5e9;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  white-space: nowrap;
}

.use-btn:hover {
  background: #0284c7;
}

.cache-hint {
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px dashed #bae6fd;
  font-size: 11px;
  color: #0369a1;
}
</style>
