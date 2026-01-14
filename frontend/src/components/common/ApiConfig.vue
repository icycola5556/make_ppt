<template>
  <div class="api-config">
    <div class="row">
      <div class="label">后端 API</div>
      <input class="input" v-model="localApiBase" placeholder="http://localhost:8000" />
      <button class="primary" @click="doCheck" :disabled="busy">连通性检测</button>
    </div>
    <div class="muted">提示：默认后端端口 8000；前端 dev 端口 5173。</div>
    <div v-if="health" class="ok">✅ 后端正常，LLM启用：{{ health.llm_enabled }}</div>
    <div v-if="err" class="err">❌ {{ err }}</div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useWorkflow } from '../../composables/useWorkflow'

const { apiBase, busy, err, health, checkHealth, setApiBase } = useWorkflow()

const localApiBase = ref(apiBase.value)

watch(localApiBase, (v) => {
  setApiBase(v)
  apiBase.value = v
})

async function doCheck() {
  await checkHealth()
}
</script>

<style scoped>
.api-config { padding: 14px; border: 1px solid #e5e7eb; border-radius: 14px; background: #fff; margin-bottom: 12px; }
.row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.label { font-weight: 600; }
.input { flex: 1; min-width: 240px; border: 1px solid #d1d5db; border-radius: 10px; padding: 8px 10px; }
.primary { background: #111827; color: #fff; border: 1px solid #111827; border-radius: 10px; padding: 9px 12px; cursor: pointer; }
.primary:disabled { opacity: 0.5; cursor: not-allowed; }
.muted { color: #6b7280; font-size: 13px; margin-top: 6px; }
.ok { margin-top: 8px; color: #065f46; font-weight: 600; }
.err { margin-top: 8px; color: #b91c1c; font-weight: 600; }
</style>
