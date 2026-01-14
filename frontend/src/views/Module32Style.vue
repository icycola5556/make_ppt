<template>
  <div class="module-page">
    <div class="module-header">
      <span class="badge">3.2</span>
      <h2>风格设计模块</h2>
    </div>
    <p class="desc">基于教学场景和专业领域生成PPT风格配置</p>

    <ApiConfig />

    <!-- 输入区 -->
    <section class="card">
      <div class="h3">输入需求（将先执行3.1再执行3.2）</div>
      <textarea class="textarea" v-model="rawText" placeholder="例如：给我一个机械专业「液压传动原理」的理论课课件"></textarea>
      
      <div class="test-cases">
        <span class="label">测试案例：</span>
        <button class="test-btn" v-for="tc in testCaseList" :key="tc.label" @click="rawText = tc.text">
          {{ tc.label }}
        </button>
      </div>
      
      <div class="row">
        <button class="primary" @click="runStyle" :disabled="busy || !rawText.trim()">
          运行风格设计
        </button>
        <button class="btn" @click="reset" :disabled="busy">重置</button>
      </div>
      <div v-if="err" class="err">❌ {{ err }}</div>
    </section>

    <!-- 意图理解结果 -->
    <section v-if="teachingRequest" class="card">
      <div class="h3">3.1 意图理解结果</div>
      <JsonBlock title="teaching_request.json" :value="teachingRequest" filename="teaching_request.json" collapsed />
    </section>

    <!-- 风格配置结果 -->
    <section v-if="styleConfig" class="card highlight">
      <div class="h3">3.2 风格配置结果</div>
      
      <!-- 风格预览 -->
      <div class="style-preview" v-if="styleConfig.color">
        <div class="color-palette">
          <div class="color-item" v-for="(value, key) in styleConfig.color" :key="key" :style="{ background: value }">
            <span class="color-label">{{ key }}</span>
            <span class="color-value">{{ value }}</span>
          </div>
        </div>
      </div>
      
      <JsonBlock title="style_config.json" :value="styleConfig" filename="style_config.json" />
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useWorkflow } from '../composables/useWorkflow'
import { testCases } from '../composables/testCases'
import ApiConfig from '../components/common/ApiConfig.vue'
import JsonBlock from '../components/common/JsonBlock.vue'

const { busy, err, teachingRequest, styleConfig, reset, runWorkflow } = useWorkflow()

const testCaseList = testCases
const rawText = ref('')

async function runStyle() {
  try {
    await runWorkflow({ user_text: rawText.value, stop_at: '3.2' })
  } catch (e) {
    err.value = e.message
  }
}
</script>

<style scoped>
.module-page { max-width: 900px; margin: 0 auto; padding: 20px; }
.module-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.badge { background: #059669; color: white; padding: 4px 12px; border-radius: 8px; font-weight: 700; }
.desc { color: #6b7280; margin-bottom: 16px; }
.card { border: 1px solid #e5e7eb; border-radius: 14px; padding: 16px; background: #fff; margin-bottom: 16px; }
.card.highlight { border-color: #059669; border-width: 2px; }
.h3 { font-size: 16px; font-weight: 700; margin-bottom: 12px; }
.textarea { width: 100%; min-height: 80px; border: 1px solid #d1d5db; border-radius: 10px; padding: 10px; font-size: 14px; }
.row { display: flex; gap: 10px; margin-top: 12px; }
.primary { background: #059669; color: #fff; border: none; border-radius: 10px; padding: 10px 16px; cursor: pointer; font-weight: 600; }
.primary:disabled { opacity: 0.5; }
.btn { background: #fff; border: 1px solid #d1d5db; border-radius: 10px; padding: 10px 16px; cursor: pointer; }
.style-preview { margin-bottom: 16px; }
.color-palette { display: flex; flex-wrap: wrap; gap: 10px; }
.color-item { width: 100px; height: 60px; border-radius: 8px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; text-shadow: 0 1px 2px rgba(0,0,0,0.5); font-size: 11px; }
.color-label { font-weight: 700; }
.color-value { opacity: 0.8; }
.test-cases { display: flex; gap: 8px; align-items: center; margin: 12px 0; flex-wrap: wrap; }
.test-btn { padding: 6px 12px; border: 1px dashed #9ca3af; border-radius: 6px; background: #f9fafb; cursor: pointer; font-size: 12px; }
.test-btn:hover { border-color: #059669; background: #ecfdf5; color: #059669; }
.label { font-weight: 600; font-size: 13px; }
.err { margin-top: 10px; color: #b91c1c; font-weight: 600; }
</style>
