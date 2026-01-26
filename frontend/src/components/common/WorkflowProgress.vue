<template>
  <div class="workflow-progress" :class="{ fullscreen }">
    <!-- 加载动画 -->
    <div class="spinner-container">
      <div class="spinner-outer"></div>
      <div class="spinner-inner"></div>
    </div>
    
    <!-- 主消息 -->
    <p class="main-message">{{ mainMessage }}</p>
    
    <!-- 进度条 -->
    <div v-if="hasProgress" class="progress-section">
      <div class="progress-header">
        <span class="step-label">{{ currentStep }}</span>
        <span class="percent">{{ percent }}%</span>
      </div>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: percent + '%' }"></div>
      </div>
    </div>
    
    <!-- 滚动消息日志 -->
    <div v-if="messages.length > 0" class="message-log" ref="logContainer">
      <div 
        v-for="(msg, idx) in displayMessages" 
        :key="idx"
        class="log-item"
        :class="{ latest: idx === displayMessages.length - 1 }"
      >
        <span class="indicator">›</span>
        <span class="text">{{ msg.text || msg }}</span>
      </div>
    </div>
    
    <!-- 后台执行按钮 -->
    <button v-if="showBackgroundButton" @click="$emit('background')" class="bg-btn">
      ← 在后台执行
    </button>
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick } from 'vue'

const props = defineProps({
  fullscreen: { type: Boolean, default: false },
  mainMessage: { type: String, default: '处理中...' },
  currentStep: { type: String, default: '' },
  progress: { 
    type: Object, 
    default: null 
    // { total: number, completed: number, percent?: number }
  },
  messages: { 
    type: Array, 
    default: () => [] 
  },
  showBackgroundButton: { type: Boolean, default: false }
})

defineEmits(['background'])

const logContainer = ref(null)

const hasProgress = computed(() => {
  return props.progress && (props.progress.total > 0 || props.progress.percent !== undefined)
})

const percent = computed(() => {
  if (!props.progress) return 0
  if (props.progress.percent !== undefined) return props.progress.percent
  if (props.progress.total > 0) {
    return Math.round((props.progress.completed / props.progress.total) * 100)
  }
  return 0
})

// 只显示最近 20 条消息
const displayMessages = computed(() => {
  const msgs = props.messages
  if (msgs.length <= 20) return msgs
  return msgs.slice(-20)
})

// 自动滚动到最新消息
watch(() => props.messages.length, async () => {
  await nextTick()
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
})
</script>

<style scoped>
.workflow-progress {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-6);
  max-width: 480px;
  margin: 0 auto;
}

.workflow-progress.fullscreen {
  position: fixed;
  inset: 0;
  max-width: none;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(4px);
  z-index: var(--z-modal);
}

/* 加载动画 */
.spinner-container {
  position: relative;
  width: 48px;
  height: 48px;
  margin-bottom: var(--spacing-4);
}

.spinner-outer {
  position: absolute;
  inset: 0;
  border: 4px solid var(--border-light);
  border-radius: var(--radius-full);
}

.spinner-inner {
  position: absolute;
  inset: 0;
  border: 4px solid var(--color-brand);
  border-radius: var(--radius-full);
  border-top-color: transparent;
  animation: spin var(--duration-loading) linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 主消息 */
.main-message {
  font-size: var(--font-size-lg);
  color: var(--text-primary);
  margin-bottom: var(--spacing-4);
  text-align: center;
}

/* 进度条 */
.progress-section {
  width: 100%;
  margin-bottom: var(--spacing-4);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-2);
}

.step-label {
  font-weight: var(--font-weight-medium);
}

.percent {
  font-weight: var(--font-weight-semibold);
  color: var(--color-brand);
}

.progress-bar {
  height: 8px;
  background: var(--border-light);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(to right, var(--color-brand), var(--color-brand-hover));
  transition: width 0.3s ease;
  border-radius: var(--radius-full);
}

/* 消息日志 */
.message-log {
  width: 100%;
  max-height: 160px;
  overflow-y: auto;
  background: var(--bg-input);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: var(--spacing-3);
  font-size: var(--font-size-xs);
  margin-bottom: var(--spacing-4);
}

.log-item {
  padding: var(--spacing-1) 0;
  color: var(--text-secondary);
  display: flex;
  gap: var(--spacing-2);
}

.log-item.latest {
  color: var(--color-brand);
  font-weight: var(--font-weight-medium);
}

.indicator {
  color: var(--color-brand-light);
}

/* 后台按钮 */
.bg-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-4);
  font-size: var(--font-size-base);
  color: var(--text-secondary);
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-fast);
}

.bg-btn:hover {
  color: var(--color-brand);
  border-color: var(--color-brand);
  background: var(--color-brand-light);
}
</style>
