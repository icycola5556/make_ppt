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

// 注意：3.2 风格设计已移除，功能已合并到 3.1 意图识别
const steps = [
  { id: '3.1', name: '意图理解' },
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
  background: linear-gradient(135deg, var(--color-brand-light), var(--bg-input));
  border: 1px solid var(--color-brand-light);
  border-radius: var(--radius-lg);
  padding: var(--spacing-3);
  margin-bottom: var(--spacing-4);
}

.cache-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-3);
  padding-bottom: var(--spacing-2);
  border-bottom: 1px dashed var(--color-brand-light);
}

.cache-icon { font-size: var(--font-size-lg); }
.cache-title {
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
  color: var(--color-brand);
  flex: 1;
}

.clear-btn {
  font-size: var(--font-size-xs);
  padding: var(--spacing-1) var(--spacing-2);
  border: 1px solid var(--color-error-light);
  background: var(--color-error-light);
  color: var(--color-error);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-fast);
}

.clear-btn:hover {
  background: #FEE2E2;
}

.cache-items {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
}

.cache-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-3);
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-fast);
  min-width: 180px;
  flex: 1;
}

.cache-item:hover {
  border-color: var(--color-brand);
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1);
}

.cache-item.cached {
  background: var(--color-success-light);
  border-color: var(--color-success);
}

.cache-item.active {
  border-color: var(--color-brand);
  box-shadow: 0 0 0 2px var(--focus-ring-color);
}

.step-badge {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-full);
  background: var(--border-light);
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  flex-shrink: 0;
}

.step-badge.cached {
  background: var(--color-success);
  color: var(--text-inverse);
}

.step-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.step-name {
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-xs);
  color: var(--text-primary);
}

.step-status {
  font-size: var(--font-size-xs);
  color: var(--color-success);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.step-status.empty {
  color: var(--text-muted);
}

.use-btn {
  padding: var(--spacing-1) var(--spacing-3);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  background: var(--color-brand);
  color: var(--text-inverse);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  white-space: nowrap;
  transition: all var(--duration-fast);
}

.use-btn:hover {
  background: var(--color-brand-hover);
}

.cache-hint {
  margin-top: var(--spacing-3);
  padding-top: var(--spacing-2);
  border-top: 1px dashed var(--color-brand-light);
  font-size: var(--font-size-xs);
  color: var(--color-brand);
}
</style>
