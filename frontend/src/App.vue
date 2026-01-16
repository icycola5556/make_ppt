<template>
  <div class="app">
    <header class="header">
      <div class="h1">PPT大纲工作流（模块 3.1 → 3.4）</div>
      <div class="sub">
        模块化测试页面，可独立测试各模块功能。
      </div>
    </header>

    <!-- 模块Tab导航 -->
    <nav class="tabs">
      <button 
        v-for="tab in tabs" 
        :key="tab.id"
        :class="['tab', { active: currentTab === tab.id }]"
        :style="{ '--tab-color': tab.color }"
        @click="navigateTo(tab.id)"
      >
        <span class="tab-badge">{{ tab.badge }}</span>
        {{ tab.label }}
      </button>
    </nav>

    <!-- 模块内容 -->
    <main class="content">
      <router-view v-slot="{ Component }">
        <keep-alive>
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const tabs = [
  { id: '3.1', badge: '3.1', label: '意图理解', color: '#2563eb' },
  { id: '3.2', badge: '3.2', label: '风格设计', color: '#059669' },
  { id: '3.3', badge: '3.3', label: '大纲生成', color: '#7c3aed' },
  { id: '3.4', badge: '3.4', label: '内容生成', color: '#dc2626' },
  { id: '3.5', badge: '3.5', label: '智能排版', color: '#ea580c' },
  // { id: 'full', badge: '✓', label: '完整流程', color: '#111827' },
]

const currentTab = computed(() => {
  // Extract module number from path, e.g. /3.1 -> 3.1
  const path = route.path
  if (path === '/' || path === '/3.1') return '3.1'
  if (path.includes('3.2')) return '3.2'
  if (path.includes('3.3')) return '3.3'
  if (path.includes('3.4')) return '3.4'
  if (path.includes('3.5')) return '3.5'
  return '3.1'
})

const navigateTo = (tabId) => {
  if (tabId === 'full') {
    // router.push('/full')
    alert('完整流程暂未迁移')
  } else {
    router.push(`/${tabId}`)
  }
}
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: ui-sans-serif, system-ui, -apple-system, sans-serif; background: #f9fafb; color: #111827; }
</style>

<style scoped>
.app { min-height: 100vh; }
.header { padding: 20px 24px 12px; background: #fff; border-bottom: 1px solid #e5e7eb; }
.h1 { font-size: 22px; font-weight: 800; }
.sub { margin-top: 4px; color: #6b7280; font-size: 14px; }

.tabs { display: flex; gap: 4px; padding: 12px 24px; background: #fff; border-bottom: 1px solid #e5e7eb; overflow-x: auto; }
.tab { display: flex; align-items: center; gap: 8px; padding: 10px 16px; border: 2px solid transparent; border-radius: 10px; background: #f9fafb; cursor: pointer; font-weight: 500; font-size: 14px; transition: all 0.2s; }
.tab:hover { background: #f3f4f6; }
.tab.active { border-color: var(--tab-color); background: white; }
.tab-badge { background: var(--tab-color); color: white; padding: 2px 8px; border-radius: 6px; font-size: 12px; font-weight: 700; }

.content { padding: 20px; }
.placeholder { text-align: center; padding: 60px; color: #6b7280; font-size: 16px; }
</style>
