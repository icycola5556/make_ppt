<template>
  <div class="app">
    <!-- 顶部导航栏 -->
    <header class="glass-bg border-b border-light sticky top-0 z-50 backdrop-blur-md">
      <div class="header-content">
        <div class="header-title">
          <h1 class="text-gradient hover-lift">PPT 智能生成工作流</h1>
          <p class="header-desc">从需求到成品，五步完成专业 PPT</p>
        </div>
        <div class="header-actions">
           <router-link to="/design-demo" class="btn btn-ghost btn-sm" title="查看设计系统演示">
             🎨 设计演示
           </router-link>
           <button
            class="btn btn-ghost btn-sm accessibility-toggle"
            @click="toggleAccessibilityMode"
            :title="isAccessibilityMode ? '切换到标准模式' : '切换到大字号模式'"
          >
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3"></circle>
              <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"></path>
            </svg>
            <span>{{ isAccessibilityMode ? '标准' : '大字号' }}</span>
          </button>
        </div>
      </div>
    </header>

    <!-- 步骤导航 -->
    <StepProgress
      :steps="steps"
      :current-step="currentStep"
      max-step="3.5"
      @navigate="navigateTo"
    />

    <!-- 模块内容 -->
    <main class="app-content">
      <router-view v-slot="{ Component }">
        <keep-alive>
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import StepProgress from './components/common/StepProgress.vue'

const router = useRouter()
const route = useRoute()

// 无障碍模式
const isAccessibilityMode = ref(false)

const toggleAccessibilityMode = () => {
  isAccessibilityMode.value = !isAccessibilityMode.value
  document.documentElement.classList.toggle('accessibility-mode', isAccessibilityMode.value)
  localStorage.setItem('accessibility-mode', isAccessibilityMode.value)
}

// 初始化时检查本地存储
onMounted(() => {
  const saved = localStorage.getItem('accessibility-mode')
  if (saved === 'true') {
    isAccessibilityMode.value = true
    document.documentElement.classList.add('accessibility-mode')
  }
})

// 步骤配置 - 使用新的模块装饰色
// 注意：3.2 风格设计已移除，功能已合并到 3.1 意图识别
const steps = [
  { id: '3.1', label: '意图理解', color: '#6366F1', colorLight: '#E0E7FF' },
  { id: '3.3', label: '大纲生成', color: '#8B5CF6', colorLight: '#EDE9FE' },
  { id: '3.4', label: '内容生成', color: '#F97316', colorLight: '#FFEDD5' },
  { id: '3.5', label: '智能排版', color: '#EC4899', colorLight: '#FCE7F3' },
]

const currentStep = computed(() => {
  const path = route.path
  if (path === '/' || path === '/3.1') return '3.1'
  if (path.includes('3.3') || path.includes('outline-editor')) return '3.3'
  if (path.includes('3.4') || path.includes('content-generator')) return '3.4'
  if (path.includes('3.5')) return '3.5'
  return '3.1'
})

const navigateTo = (stepId) => {
  router.push(`/${stepId}`)
}
</script>

<style>
/* 导入设计令牌和组件样式 */
@import './styles/tokens.css';
@import './styles/components.css';
</style>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 顶部导航栏 */
/* 顶部导航栏 - Glass Style */
.glass-bg {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.3);
  position: sticky;
  top: 0;
  z-index: var(--z-fixed);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.header-content {
  max-width: var(--container-xl);
  margin: 0 auto;
  padding: var(--spacing-4) var(--spacing-6);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-title h1 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  margin: 0;
}

.header-desc {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  margin: var(--spacing-1) 0 0 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.accessibility-toggle {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.accessibility-toggle .icon {
  width: 18px;
  height: 18px;
}

/* 主内容区 */
.app-content {
  flex: 1;
  padding: var(--spacing-6);
  max-width: var(--container-lg);
  margin: 0 auto;
  width: 100%;
}

/* 3.5 渲染模块使用全宽布局 */
:deep(.layout-workbench) {
  max-width: none;
  padding: 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .header-content {
    padding: var(--spacing-3) var(--spacing-4);
  }

  .header-title h1 {
    font-size: var(--font-size-lg);
  }

  .header-desc {
    display: none;
  }

  .app-content {
    padding: var(--spacing-4);
  }

  .accessibility-toggle span {
    display: none;
  }
}
</style>
