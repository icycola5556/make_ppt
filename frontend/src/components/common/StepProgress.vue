<template>
  <nav class="step-progress" role="navigation" aria-label="流程步骤">
    <!-- 步骤项 -->
    <div class="step-list">
      <div
        v-for="(step, index) in steps"
        :key="step.id"
        class="step-item"
        :class="{
          'step-completed': index < currentStepIndex,
          'step-active': index === currentStepIndex,
          'step-pending': index > currentStepIndex
        }"
        @click="handleStepClick(step, index)"
        role="button"
        :tabindex="index <= currentStepIndex ? 0 : -1"
        :aria-current="index === currentStepIndex ? 'step' : undefined"
        @keydown.enter="handleStepClick(step, index)"
        @keydown.space.prevent="handleStepClick(step, index)"
      >
        <!-- 连接线 -->
        <div v-if="index > 0" class="step-connector">
          <div
            class="step-connector-fill"
            :class="{ 'filled': index <= currentStepIndex }"
          ></div>
        </div>

        <!-- 步骤指示器 -->
        <div
          class="step-indicator"
          :style="{ '--step-color': step.color, '--step-color-light': step.colorLight }"
        >
          <svg v-if="index < currentStepIndex" class="check-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
          <span v-else class="step-number">{{ index + 1 }}</span>
        </div>

        <!-- 步骤标签 -->
        <div class="step-label">{{ step.label }}</div>
      </div>
    </div>

    <!-- 底部进度条（移动端显示） -->
    <div class="progress-bar-mobile" aria-hidden="true">
      <div
        class="progress-fill"
        :style="{ width: progressWidth }"
      ></div>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  steps: {
    type: Array,
    required: true,
    // 每个 step 应包含: { id, label, color, colorLight }
  },
  currentStep: {
    type: String,
    required: true
  },
  maxStep: {
    type: String,
    default: ''
  },
  allowNavigation: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['navigate'])

const currentStepIndex = computed(() => {
  return props.steps.findIndex(step => step.id === props.currentStep)
})

const maxStepIndex = computed(() => {
  if (!props.maxStep) return 4 // 默认为最后一个步骤 (index 4)，即默认解锁所有，或者可以设为 currentStepIndex
  return props.steps.findIndex(step => step.id === props.maxStep)
})

const progressWidth = computed(() => {
  const index = currentStepIndex.value
  if (index <= 0) return '0%'
  return `${(index / (props.steps.length - 1)) * 100}%`
})

const handleStepClick = (step, index) => {
  // 允许导航到 maxStep 之前的所有步骤
  // 默认为解锁所有，方便调试 (maxStepIndex >= index)
  if (props.allowNavigation) {
    if (props.maxStep) {
        if (index <= maxStepIndex.value) {
            emit('navigate', step.id)
        }
    } else {
        // 如果没有传入 maxStep，则允许任意跳转 (针对用户 "解锁冻结模块" 的需求)
        emit('navigate', step.id)
    }
  }
}
</script>

<style scoped>
.step-progress {
  background: var(--bg-card);
  padding: var(--spacing-4) var(--spacing-6);
  border-bottom: 1px solid var(--border-light);
}

.step-list {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
}

.step-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  cursor: pointer;
  padding: var(--spacing-2) var(--spacing-3);
  border-radius: var(--radius-lg);
  transition: background var(--duration-fast);
  position: relative;
}

.step-item:hover:not(.step-pending) {
  background: var(--bg-hover);
}

.step-item.step-pending {
  /* cursor: not-allowed; */
  opacity: 0.8;
}

/* 连接线 */
.step-connector {
  position: absolute;
  right: 100%;
  top: 50%;
  width: 40px;
  height: 3px;
  background: var(--border-light);
  margin-right: var(--spacing-3);
}

.step-connector-fill {
  height: 100%;
  width: 0;
  background: var(--color-brand);
  transition: width var(--duration-normal) var(--easing-default);
}

.step-connector-fill.filled {
  width: 100%;
}

/* 步骤指示器 */
.step-indicator {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  transition: all var(--duration-fast);
  flex-shrink: 0;
}

/* 待处理状态 */
.step-pending .step-indicator {
  background: var(--bg-input);
  color: var(--text-muted);
  border: 2px solid var(--border-light);
}

/* 当前状态 */
.step-active .step-indicator {
  background: var(--step-color-light, var(--color-brand-light));
  color: var(--step-color, var(--color-brand));
  border: 2px solid var(--step-color, var(--color-brand));
  box-shadow: 0 0 0 4px var(--step-color-light, var(--color-brand-light));
}

/* 已完成状态 */
.step-completed .step-indicator {
  background: var(--color-success);
  color: white;
  border: 2px solid var(--color-success);
}

.check-icon {
  width: 18px;
  height: 18px;
}

.step-number {
  line-height: 1;
}

/* 步骤标签 */
.step-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-muted);
  white-space: nowrap;
  transition: color var(--duration-fast);
}

.step-active .step-label {
  color: var(--text-primary);
  font-weight: var(--font-weight-semibold);
}

.step-completed .step-label {
  color: var(--text-secondary);
}

/* 移动端进度条 */
.progress-bar-mobile {
  display: none;
  height: 3px;
  background: var(--border-light);
  border-radius: var(--radius-full);
  margin-top: var(--spacing-4);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-brand);
  border-radius: var(--radius-full);
  transition: width var(--duration-normal) var(--easing-default);
}

/* 响应式：平板及以下隐藏标签，显示进度条 */
@media (max-width: 768px) {
  .step-progress {
    padding: var(--spacing-3) var(--spacing-4);
  }

  .step-label {
    display: none;
  }

  .step-connector {
    width: 24px;
  }

  .step-item {
    padding: var(--spacing-2);
  }

  .progress-bar-mobile {
    display: block;
  }
}

/* 响应式：小屏幕进一步缩小 */
@media (max-width: 480px) {
  .step-indicator {
    width: 32px;
    height: 32px;
  }

  .step-connector {
    width: 16px;
  }
}
</style>
