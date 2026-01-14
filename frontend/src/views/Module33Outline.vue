<template>
  <div class="module-page">
    <div class="module-header">
      <span class="badge">3.3</span>
      <h2>大纲生成模块</h2>
    </div>
    <p class="desc">基于教学需求和风格配置生成PPT结构化大纲</p>

    <ApiConfig />

    <!-- 输入区 -->
    <section class="card">
      <div class="h3">输入需求</div>
      <textarea class="textarea" v-model="rawText" placeholder="例如：给我一个机械专业「液压传动原理」的理论课课件，10页左右"></textarea>
      
      <!-- 模式选择 -->
      <div class="mode-select">
        <label class="mode-option">
          <input type="radio" v-model="skipStyle" :value="false" />
          <span>完整流程 (3.1→3.2→3.3)</span>
        </label>
        <label class="mode-option">
          <input type="radio" v-model="skipStyle" :value="true" />
          <span>跳过3.2 (3.1→3.3)</span>
        </label>
      </div>

      <!-- style_name输入（跳过3.2时） -->
      <div v-if="skipStyle" class="style-name-input">
        <label>Style Name:</label>
        <input class="input" v-model="styleName" placeholder="理论课 / 实训课 / 复习课" />
        <div class="hint">支持：theory_clean, practice_steps, review_mindmap</div>
      </div>
      
      <div class="row">
        <button class="primary" @click="runOutline" :disabled="busy || !rawText.trim()">
          运行大纲生成
        </button>
        <button class="btn" @click="reset" :disabled="busy">重置</button>
      </div>
      <div v-if="err" class="err">❌ {{ err }}</div>
    </section>

    <!-- 意图理解结果 -->
    <section v-if="teachingRequest" class="card">
      <div class="h3">3.1 意图理解结果</div>
      <JsonBlock title="teaching_request.json" :value="teachingRequest" collapsed />
    </section>

    <!-- 风格配置结果（非跳过模式） -->
    <section v-if="styleConfig && !skipStyle" class="card">
      <div class="h3">3.2 风格配置结果</div>
      <JsonBlock title="style_config.json" :value="styleConfig" collapsed />
    </section>

    <!-- 大纲结果 -->
    <section v-if="outline" class="card highlight">
      <div class="h3">3.3 PPT大纲结果</div>
      
      <!-- 大纲预览 -->
      <div class="outline-preview">
        <div class="outline-title">{{ outline.title || '未命名大纲' }}</div>
        <div class="slide-count">共 {{ outline.slides?.length || 0 }} 页</div>
        <div class="slides-list">
          <div v-for="(slide, i) in outline.slides" :key="i" class="slide-item">
            <span class="slide-num">{{ i + 1 }}</span>
            <span class="slide-type">[{{ slide.slide_type }}]</span>
            <span class="slide-title">{{ slide.title }}</span>
          </div>
        </div>
      </div>
      
      <JsonBlock title="outline.json" :value="outline" filename="outline.json" />
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useWorkflow } from '../composables/useWorkflow'
import ApiConfig from '../components/common/ApiConfig.vue'
import JsonBlock from '../components/common/JsonBlock.vue'

const { busy, err, teachingRequest, styleConfig, outline, reset, runWorkflow, normalizeStyleName } = useWorkflow()

const rawText = ref('')
const skipStyle = ref(false)
const styleName = ref('')

async function runOutline() {
  try {
    const opts = {
      user_text: rawText.value,
      stop_at: '3.3'
    }
    if (skipStyle.value) {
      const normalized = normalizeStyleName(styleName.value)
      if (!normalized) {
        err.value = '请输入 style_name'
        return
      }
      opts.style_name = normalized
    }
    await runWorkflow(opts)
  } catch (e) {
    err.value = e.message
  }
}
</script>

<style scoped>
.module-page { max-width: 900px; margin: 0 auto; padding: 20px; }
.module-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.badge { background: #7c3aed; color: white; padding: 4px 12px; border-radius: 8px; font-weight: 700; }
.desc { color: #6b7280; margin-bottom: 16px; }
.card { border: 1px solid #e5e7eb; border-radius: 14px; padding: 16px; background: #fff; margin-bottom: 16px; }
.card.highlight { border-color: #7c3aed; border-width: 2px; }
.h3 { font-size: 16px; font-weight: 700; margin-bottom: 12px; }
.textarea { width: 100%; min-height: 80px; border: 1px solid #d1d5db; border-radius: 10px; padding: 10px; font-size: 14px; }
.mode-select { display: flex; gap: 20px; margin: 12px 0; }
.mode-option { display: flex; align-items: center; gap: 6px; cursor: pointer; }
.style-name-input { margin: 12px 0; padding: 12px; background: #f9fafb; border-radius: 8px; }
.style-name-input label { font-weight: 600; margin-right: 10px; }
.style-name-input .input { width: 200px; border: 1px solid #d1d5db; border-radius: 6px; padding: 6px 10px; }
.hint { font-size: 12px; color: #6b7280; margin-top: 6px; }
.row { display: flex; gap: 10px; margin-top: 12px; }
.primary { background: #7c3aed; color: #fff; border: none; border-radius: 10px; padding: 10px 16px; cursor: pointer; font-weight: 600; }
.primary:disabled { opacity: 0.5; }
.btn { background: #fff; border: 1px solid #d1d5db; border-radius: 10px; padding: 10px 16px; cursor: pointer; }
.outline-preview { margin-bottom: 16px; padding: 16px; background: #f8fafc; border-radius: 10px; }
.outline-title { font-size: 18px; font-weight: 700; color: #1e293b; }
.slide-count { color: #6b7280; font-size: 13px; margin: 6px 0 12px; }
.slides-list { max-height: 300px; overflow-y: auto; }
.slide-item { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid #e5e7eb; }
.slide-num { background: #7c3aed; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600; }
.slide-type { color: #6b7280; font-size: 12px; min-width: 80px; }
.slide-title { font-weight: 500; }
.err { margin-top: 10px; color: #b91c1c; font-weight: 600; }
</style>
