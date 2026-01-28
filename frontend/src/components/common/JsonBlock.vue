<template>
  <div class="block">
    <div class="block-header">
      <div class="title">{{ title }}</div>
      <button class="btn" @click="copy">复制</button>
      <button class="btn" @click="download">下载</button>
    </div>
    <pre class="pre">{{ pretty }}</pre>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, default: 'JSON' },
  value: { type: [Object, Array, String, Number, Boolean, null], default: null },
  filename: { type: String, default: 'data.json' }
})

const pretty = computed(() => {
  if (typeof props.value === 'string') return props.value
  try { return JSON.stringify(props.value, null, 2) } catch { return String(props.value) }
})

async function copy() {
  await navigator.clipboard.writeText(pretty.value)
}

function download() {
  const blob = new Blob([pretty.value], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = props.filename
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.block {
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--bg-card);
  box-shadow: var(--shadow-card);
}

.block-header {
  display: flex;
  gap: var(--spacing-2);
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-3) var(--spacing-4);
  background: var(--bg-input);
  border-bottom: 1px solid var(--border-light);
}

.title {
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
  color: var(--text-primary);
}

.btn {
  border: 1px solid var(--border-default);
  background: var(--bg-card);
  border-radius: var(--radius-md);
  padding: var(--spacing-2) var(--spacing-3);
  cursor: pointer;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  transition: all var(--duration-fast);
}

.btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.pre {
  margin: 0;
  padding: var(--spacing-4);
  overflow: auto;
  max-height: 420px;
  font-size: var(--font-size-xs);
  line-height: var(--line-height-relaxed);
  font-family: var(--font-mono);
  color: var(--text-secondary);
  background: var(--bg-card);
}
</style>
