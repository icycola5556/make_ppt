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
        @click="currentTab = tab.id"
      >
        <span class="tab-badge">{{ tab.badge }}</span>
        {{ tab.label }}
      </button>
    </nav>

    <!-- 模块内容 -->
    <main class="content">
      <Module31Intent v-if="currentTab === '3.1'" />
      <Module32Style v-else-if="currentTab === '3.2'" />
      <Module33Outline v-else-if="currentTab === '3.3'" />
      <Module34Content v-else-if="currentTab === '3.4'" />
      <FullWorkflow v-else-if="currentTab === 'full'" />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Module31Intent from './views/Module31Intent.vue'
import Module32Style from './views/Module32Style.vue'
import Module33Outline from './views/Module33Outline.vue'
import Module34Content from './views/Module34Content.vue'

// Tab暂时用占位
const FullWorkflow = { template: '<div class="placeholder">完整流程页面（保留原App.vue逻辑）</div>' }

const tabs = [
  { id: '3.1', badge: '3.1', label: '意图理解', color: '#2563eb' },
  { id: '3.2', badge: '3.2', label: '风格设计', color: '#059669' },
  { id: '3.3', badge: '3.3', label: '大纲生成', color: '#7c3aed' },
  { id: '3.4', badge: '3.4', label: '内容生成', color: '#dc2626' },
  { id: 'full', badge: '✓', label: '完整流程', color: '#111827' },
]

const currentTab = ref('3.1')
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
