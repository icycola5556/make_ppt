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
  padding: 24px;
  max-width: 480px;
  margin: 0 auto;
}

.workflow-progress.fullscreen {
  position: fixed;
  inset: 0;
  max-width: none;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(4px);
  z-index: 50;
}

/* 加载动画 */
.spinner-container {
  position: relative;
  width: 48px;
  height: 48px;
  margin-bottom: 16px;
}

.spinner-outer {
  position: absolute;
  inset: 0;
  border: 4px solid #e5e7eb;
  border-radius: 50%;
}

.spinner-inner {
  position: absolute;
  inset: 0;
  border: 4px solid #2563eb;
  border-radius: 50%;
  border-top-color: transparent;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 主消息 */
.main-message {
  font-size: 18px;
  color: #374151;
  margin-bottom: 16px;
  text-align: center;
}

/* 进度条 */
.progress-section {
  width: 100%;
  margin-bottom: 16px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 8px;
}

.step-label {
  font-weight: 500;
}

.percent {
  font-weight: 600;
  color: #2563eb;
}

.progress-bar {
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(to right, #3b82f6, #2563eb);
  transition: width 0.3s ease;
  border-radius: 4px;
}

/* 消息日志 */
.message-log {
  width: 100%;
  max-height: 160px;
  overflow-y: auto;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px;
  font-size: 12px;
  margin-bottom: 16px;
}

.log-item {
  padding: 4px 0;
  color: #6b7280;
  display: flex;
  gap: 8px;
}

.log-item.latest {
  color: #1d4ed8;
  font-weight: 500;
}

.indicator {
  color: #93c5fd;
}

/* 后台按钮 */
.bg-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  font-size: 14px;
  color: #6b7280;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.bg-btn:hover {
  color: #2563eb;
  border-color: #2563eb;
  background: #eff6ff;
}
</style>
