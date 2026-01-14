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
      
      <div class="test-cases">
        <span class="label">测试案例：</span>
        <button class="test-btn" v-for="tc in testCaseList" :key="tc.label" @click="rawText = tc.text">
          {{ tc.label }}
        </button>
      </div>
      
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
        <select class="input select" v-model="styleName">
          <option v-for="s in availableStyles" :key="s.value" :value="s.value">
            {{ s.label }}
          </option>
        </select>
      </div>
      
      <div class="row">
        <button class="primary" @click="runOutline" :disabled="busy || !rawText.trim()">
          运行大纲生成
        </button>
        <button class="btn" @click="reset" :disabled="busy">重置</button>
      </div>
      <div v-if="busy && currentStep" class="progress">⏳ {{ currentStep }}</div>
      <div v-if="err" class="err">❌ {{ err }}</div>
    </section>

    <!-- 问答交互（意图确认阶段） -->
    <section v-if="needUserInput" class="card warn">
      <div class="h3">请确认或补充信息</div>
      <div class="qbox" v-for="q in questions" :key="q.key">
        <div class="qtitle">{{ q.question }}</div>
        <div v-if="q.options && q.options.length" class="options-group">
          <button 
            v-for="opt in q.options" :key="opt"
            class="option-btn" :class="{ active: answers[q.key] === opt }"
            @click="answers[q.key] = opt"
          >{{ opt }}</button>
        </div>
        <input v-else class="input" v-model="answers[q.key]" :placeholder="q.placeholder || '请输入...'" />
      </div>
      <div class="row">
        <button class="primary" @click="submitAnswers(false)" :disabled="busy">提交并继续</button>
        <button class="btn" @click="submitAnswers(true)" :disabled="busy">使用默认值</button>
      </div>
    </section>

    <!-- 意图理解结果 -->
    <section v-if="teachingRequest && !needUserInput" class="card">
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
        <div class="outline-title">{{ outline.deck_title || outline.title || '未命名大纲' }}</div>
        <div class="slide-count">共 {{ outline.slides?.length || 0 }} 页</div>
        <div class="slides-list">
          <div v-for="(slide, i) in outline.slides" :key="i" class="slide-item">
            <span class="slide-num">{{ i + 1 }}</span>
            <span class="slide-type">{{ getSlideTypeLabel(slide.slide_type) }}</span>
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
import { testCases } from '../composables/testCases'
import ApiConfig from '../components/common/ApiConfig.vue'
import JsonBlock from '../components/common/JsonBlock.vue'

const { busy, err, currentStep, needUserInput, questions, answers, teachingRequest, styleConfig, outline, reset, runWorkflow, normalizeStyleName, availableStyles } = useWorkflow()

const testCaseList = testCases
const rawText = ref('')
const skipStyle = ref(false)
const styleName = ref('theory_clean')

// slide_type 中文翻译
const slideTypeLabels = {
  'cover': '封面',
  'objectives': '教学目标',
  'intro': '导入',
  'concept': '概念讲解',
  'bridge': '过渡衔接',
  'relations': '案例分析',
  'case': '案例展示',
  'exercise': '练习题',
  'summary': '总结',
  'qa': '问答互动',
  'ending': '结束页',
  'reference': '参考资料'
}

function getSlideTypeLabel(type) {
  return slideTypeLabels[type] || type
}

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

async function submitAnswers(useDefaults) {
  try {
    const opts = {
      user_text: rawText.value,
      answers: useDefaults ? {} : answers,
      auto_fill_defaults: useDefaults,
      stop_at: '3.3'
    }
    if (skipStyle.value) {
      const normalized = normalizeStyleName(styleName.value)
      if (normalized) opts.style_name = normalized
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
.card.warn { border-color: #f59e0b55; background: #fffbeb; }
.h3 { font-size: 16px; font-weight: 700; margin-bottom: 12px; }
.qbox { margin: 12px 0; padding: 12px; border: 1px dashed #d1d5db; border-radius: 10px; background: #fff; }
.qtitle { font-weight: 600; margin-bottom: 8px; }
.options-group { display: flex; flex-wrap: wrap; gap: 8px; }
.option-btn { padding: 8px 14px; border: 2px solid #d1d5db; border-radius: 8px; background: #fff; cursor: pointer; }
.option-btn.active { border-color: #7c3aed; background: #f5f3ff; color: #7c3aed; }
.input { width: 100%; border: 1px solid #d1d5db; border-radius: 8px; padding: 8px 10px; }
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
.test-cases { display: flex; gap: 8px; align-items: center; margin: 12px 0; flex-wrap: wrap; }
.test-btn { padding: 6px 12px; border: 1px dashed #9ca3af; border-radius: 6px; background: #f9fafb; cursor: pointer; font-size: 12px; }
.test-btn:hover { border-color: #7c3aed; background: #f5f3ff; color: #7c3aed; }
.label { font-weight: 600; font-size: 13px; }
.progress { margin-top: 12px; color: #7c3aed; font-weight: 600; animation: pulse 1.5s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
.err { margin-top: 10px; color: #b91c1c; font-weight: 600; }
</style>
