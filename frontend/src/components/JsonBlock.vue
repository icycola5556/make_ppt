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
.block { border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden; background: #fff; }
.block-header { display:flex; gap:8px; align-items:center; justify-content:space-between; padding: 10px 12px; background:#f9fafb; border-bottom:1px solid #e5e7eb; }
.title { font-weight: 600; }
.btn { border: 1px solid #d1d5db; background:#fff; border-radius: 8px; padding: 6px 10px; cursor:pointer; }
.btn:hover { background:#f3f4f6; }
.pre { margin: 0; padding: 12px; overflow:auto; max-height: 420px; font-size: 12px; line-height: 1.5; }
</style>
