<template>
  <div class="module-page">
    <div class="module-header">
      <span class="badge">3.1</span>
      <h2>意图理解模块</h2>
    </div>
    <p class="desc">从教师的自然语言输入中提取结构化教学需求</p>

    <ApiConfig />

    <!-- 输入区 -->
    <section class="card">
      <div class="h3">输入需求</div>
      <div class="tip-box">
        <strong>默认配置：</strong>课时45分钟 | 含案例 | 含习题 | 含互动
      </div>
      <textarea class="textarea" v-model="rawText" placeholder="例如：给我一个机械专业「液压传动原理」的理论课课件，10页左右"></textarea>
      
      <div class="test-cases">
        <span class="label">测试案例：</span>
        <button class="test-btn" v-for="(tc, i) in testCases" :key="i" @click="rawText = tc">
          {{ ['完整输入', '缺少知识点', '页数冲突'][i] }}
        </button>
      </div>

      <div class="row">
        <button class="primary" @click="runIntent" :disabled="busy || !rawText.trim()">
          运行意图理解
        </button>
        <button class="btn" @click="reset" :disabled="busy">重置</button>
      </div>
      <div v-if="err" class="err">❌ {{ err }}</div>
    </section>

    <!-- 问答交互 -->
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

    <!-- 结果展示 -->
    <section v-if="teachingRequest" class="card">
      <div class="h3">意图理解结果</div>
      <div v-if="teachingRequest.display_summary" class="display-summary">
        <pre>{{ teachingRequest.display_summary }}</pre>
      </div>
      <JsonBlock title="teaching_request.json" :value="teachingRequest" filename="teaching_request.json" />
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useWorkflow } from '../composables/useWorkflow'
import ApiConfig from '../components/common/ApiConfig.vue'
import JsonBlock from '../components/common/JsonBlock.vue'

const {
  busy, err, needUserInput, questions, answers,
  teachingRequest, testCases, reset, runWorkflow
} = useWorkflow()

const rawText = ref('')

async function runIntent() {
  try {
    await runWorkflow({ user_text: rawText.value, stop_at: '3.1' })
  } catch (e) {
    err.value = e.message
  }
}

async function submitAnswers(useDefaults) {
  try {
    await runWorkflow({
      user_text: rawText.value,
      answers: useDefaults ? {} : answers,
      auto_fill_defaults: useDefaults,
      stop_at: '3.1'
    })
  } catch (e) {
    err.value = e.message
  }
}
</script>

<style scoped>
.module-page { max-width: 900px; margin: 0 auto; padding: 20px; }
.module-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.badge { background: #2563eb; color: white; padding: 4px 12px; border-radius: 8px; font-weight: 700; }
.desc { color: #6b7280; margin-bottom: 16px; }
.card { border: 1px solid #e5e7eb; border-radius: 14px; padding: 16px; background: #fff; margin-bottom: 16px; }
.card.warn { border-color: #f59e0b55; background: #fffbeb; }
.h3 { font-size: 16px; font-weight: 700; margin-bottom: 12px; }
.tip-box { background: #f0fdf4; border: 1px solid #86efac; border-radius: 8px; padding: 8px 12px; margin-bottom: 12px; font-size: 13px; color: #166534; }
.textarea { width: 100%; min-height: 100px; border: 1px solid #d1d5db; border-radius: 10px; padding: 10px; font-size: 14px; }
.row { display: flex; gap: 10px; margin-top: 12px; }
.primary { background: #111827; color: #fff; border: none; border-radius: 10px; padding: 10px 16px; cursor: pointer; font-weight: 600; }
.primary:disabled { opacity: 0.5; }
.btn { background: #fff; border: 1px solid #d1d5db; border-radius: 10px; padding: 10px 16px; cursor: pointer; }
.test-cases { display: flex; gap: 8px; align-items: center; margin: 12px 0; }
.test-btn { padding: 6px 12px; border: 1px dashed #9ca3af; border-radius: 6px; background: #f9fafb; cursor: pointer; font-size: 12px; }
.test-btn:hover { border-color: #2563eb; background: #eff6ff; color: #2563eb; }
.label { font-weight: 600; font-size: 13px; }
.qbox { margin: 12px 0; padding: 12px; border: 1px dashed #d1d5db; border-radius: 10px; background: #fff; }
.qtitle { font-weight: 600; margin-bottom: 8px; }
.options-group { display: flex; flex-wrap: wrap; gap: 8px; }
.option-btn { padding: 8px 14px; border: 2px solid #d1d5db; border-radius: 8px; background: #fff; cursor: pointer; }
.option-btn.active { border-color: #2563eb; background: #eff6ff; color: #2563eb; }
.input { width: 100%; border: 1px solid #d1d5db; border-radius: 8px; padding: 8px 10px; }
.display-summary { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px; margin-bottom: 12px; }
.display-summary pre { margin: 0; white-space: pre-wrap; font-family: sans-serif; font-size: 14px; line-height: 1.6; }
.err { margin-top: 10px; color: #b91c1c; font-weight: 600; }
</style>
