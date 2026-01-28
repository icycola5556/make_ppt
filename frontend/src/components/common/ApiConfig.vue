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
.api-config {
  padding: var(--spacing-4);
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(8px);
  margin-bottom: var(--spacing-4);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.api-config:hover {
  background: rgba(255, 255, 255, 0.8);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.row { display: flex; gap: var(--spacing-3); align-items: center; flex-wrap: wrap; }

.label { 
  font-weight: var(--font-weight-semibold); 
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 4px;
}

.label::before {
  content: '';
  display: inline-block;
  width: 6px;
  height: 6px;
  background: var(--color-success);
  border-radius: 50%;
}

.input { 
  flex: 1; 
  min-width: 240px; 
  border: 1px solid var(--border-light); 
  border-radius: var(--radius-md); 
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.8);
  transition: all 0.2s;
  font-size: var(--font-size-sm);
}

.input:focus {
  outline: none;
  border-color: var(--color-brand);
  background: #fff;
  box-shadow: 0 0 0 2px var(--color-brand-light);
}

.primary { 
  background: var(--color-brand); 
  color: var(--text-inverse); 
  border: none;
  border-radius: var(--radius-md); 
  padding: 8px 16px; 
  cursor: pointer;
  font-weight: 600;
  font-size: var(--font-size-sm);
  transition: all 0.2s;
}

.primary:hover:not(:disabled) { 
  background: var(--color-brand-hover);
  transform: translateY(-1px); 
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
}

.primary:disabled { opacity: 0.6; cursor: not-allowed; }

.muted { 
  color: var(--text-secondary); 
  font-size: var(--font-size-xs); 
  margin-top: var(--spacing-2); 
  margin-left: 12px;
}

.ok { 
  margin-top: var(--spacing-2); 
  color: var(--color-success); 
  font-weight: 600; 
  font-size: var(--font-size-sm);
  display: flex;
  align-items: center;
  gap: 6px;
}

.err { 
  margin-top: var(--spacing-2); 
  color: var(--color-error); 
  font-weight: 600; 
  font-size: var(--font-size-sm);
}
</style>
