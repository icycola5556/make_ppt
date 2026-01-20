<template>
  <div class="module-page">
    <div class="module-header">
      <span class="badge">3.4</span>
      <h2>内容生成模块</h2>
    </div>
    <p class="desc">基于大纲生成每页PPT的详细内容</p>

    <ApiConfig />

    <!-- V3: 缓存状态展示 -->
    <CacheStatus 
      active-step="3.4" 
      @use-cache="handleUseCache" 
    />

    <!-- V3: 缓存已加载提示 -->
    <section v-if="cacheLoaded && outline" class="card cache-loaded">
      <div class="h3">✅ 已加载 3.1+3.2+3.3 缓存</div>
      <div class="cache-info">
        <div class="info-item">
          <span class="label">学科：</span>
          <span class="value">{{ teachingRequest?.subject_info?.subject_name || '未指定' }}</span>
        </div>
        <div class="info-item">
          <span class="label">大纲标题：</span>
          <span class="value">{{ outline?.deck_title || outline?.title || '未命名' }}</span>
        </div>
        <div class="info-item">
          <span class="label">页数：</span>
          <span class="value">{{ outline?.slides?.length || 0 }} 页</span>
        </div>
      </div>
      <div class="row">
        <button class="primary" @click="runContentFromCache" :disabled="busy">
          基于缓存运行内容生成
        </button>
      </div>
      <div v-if="busy && currentStep" class="progress">⏳ {{ currentStep }}</div>
    </section>

    <!-- 输入区 -->
    <section class="card">
      <div class="h3">输入需求（完整流程 3.1→3.2→3.3→3.4）</div>
      <textarea class="textarea" v-model="rawText" placeholder="例如：给我一个机械专业「液压传动原理」的理论课课件，10页左右"></textarea>
      
      <div class="test-cases">
        <span class="label">测试案例：</span>
        <button class="test-btn" v-for="tc in testCaseList" :key="tc.label" @click="rawText = tc.text">
          {{ tc.label }}
        </button>
      </div>
      
      <div class="row">
        <button class="primary" @click="runContent" :disabled="busy || !rawText.trim()">
          运行内容生成
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

    <!-- 折叠的前置结果 -->
    <section v-if="teachingRequest && !needUserInput" class="card">
      <div class="h3">3.1 意图理解结果</div>
      <JsonBlock title="teaching_request.json" :value="teachingRequest" collapsed />
    </section>

    <section v-if="styleConfig" class="card">
      <div class="h3">3.2 风格配置结果</div>
      <JsonBlock title="style_config.json" :value="styleConfig" collapsed />
    </section>

    <section v-if="outline" class="card">
      <div class="h3">3.3 PPT大纲结果</div>
      <JsonBlock title="outline.json" :value="outline" collapsed />
    </section>

    <!-- 内容结果 -->
    <section v-if="deckContent" class="card highlight">
      <div class="h3">3.4 页面内容结果</div>
      
      <!-- 内容预览 -->
      <div class="content-preview">
        <div class="deck-title">{{ deckContent.title || '未命名课件' }}</div>
        <div class="page-count">共 {{ deckContent.pages?.length || 0 }} 页内容</div>
        
        <div class="pages-grid">
          <div v-for="(page, i) in deckContent.pages" :key="i" class="page-card">
            <div class="page-header">
              <span class="page-num">{{ i + 1 }}</span>
              <span class="page-title">{{ page.title }}</span>
            </div>
            <div class="page-elements">
              {{ page.elements?.length || 0 }} 个内容元素
            </div>
          </div>
        </div>
      </div>
      
      <JsonBlock title="deck_content.json" :value="deckContent" filename="deck_content.json" />
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useWorkflow } from '../composables/useWorkflow'
import { testCases } from '../composables/testCases'
import ApiConfig from '../components/common/ApiConfig.vue'
import JsonBlock from '../components/common/JsonBlock.vue'
import CacheStatus from '../components/common/CacheStatus.vue'

const { 
  busy, err, currentStep, needUserInput, questions, answers, 
  teachingRequest, styleConfig, outline, deckContent, 
  reset, runWorkflow,
  // V3: 缓存相关
  stepCache, loadFromCache, hasCache 
} = useWorkflow()

// V3: 缓存加载状态
const cacheLoaded = ref(false)

// V3: 处理使用缓存的事件
function handleUseCache(stepId) {
  console.log('[Module34] 使用缓存:', stepId)
  
  // 加载所有前置步骤的缓存
  if (stepId === '3.1' && hasCache('3.1')) {
    teachingRequest.value = loadFromCache('3.1')
    currentStep.value = '✅ 已加载 3.1 缓存'
  }
  
  if (stepId === '3.2' && hasCache('3.2')) {
    if (hasCache('3.1')) {
      teachingRequest.value = loadFromCache('3.1')
    }
    const cache32 = loadFromCache('3.2')
    styleConfig.value = cache32.styleConfig
    currentStep.value = '✅ 已加载 3.1+3.2 缓存'
  }
  
  if (stepId === '3.3' && hasCache('3.3')) {
    // 加载完整的前置缓存链: 3.1 + 3.2 + 3.3
    if (hasCache('3.1')) {
      teachingRequest.value = loadFromCache('3.1')
    }
    if (hasCache('3.2')) {
      const cache32 = loadFromCache('3.2')
      styleConfig.value = cache32.styleConfig
    }
    outline.value = loadFromCache('3.3')
    cacheLoaded.value = true
    currentStep.value = '✅ 已加载 3.1+3.2+3.3 缓存，可直接生成内容'
  }
}

// V3: 基于缓存运行内容生成
async function runContentFromCache() {
  if (!outline.value) {
    err.value = '未加载大纲缓存，无法运行'
    return
  }
  try {
    // 直接调用 3.4，使用已载入的缓存数据
    // _continue_to_3_4: true 确保状态显示为 "3.4 内容生成中..." 而不是其他
    await runWorkflow({ stop_at: '3.4', _continue_to_3_4: true })
    cacheLoaded.value = false  // 运行后重置状态
  } catch (e) {
    err.value = e.message
  }
}

const testCaseList = testCases
const rawText = ref('')

async function runContent() {
  try {
    await runWorkflow({ user_text: rawText.value, stop_at: '3.4' })
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
      stop_at: '3.4'
    })
  } catch (e) {
    err.value = e.message
  }
}
</script>

<style scoped>
.module-page { max-width: 900px; margin: 0 auto; padding: 20px; }
.module-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.badge { background: #dc2626; color: white; padding: 4px 12px; border-radius: 8px; font-weight: 700; }
.desc { color: #6b7280; margin-bottom: 16px; }
.card { border: 1px solid #e5e7eb; border-radius: 14px; padding: 16px; background: #fff; margin-bottom: 16px; }
.card.highlight { border-color: #dc2626; border-width: 2px; }
.card.warn { border-color: #f59e0b55; background: #fffbeb; }
.card.cache-loaded { border-color: #22c55e; background: #f0fdf4; }
.cache-info { display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 12px; }
.cache-info .info-item { display: flex; gap: 8px; }
.cache-info .label { color: #6b7280; font-size: 13px; }
.cache-info .value { font-weight: 600; font-size: 13px; color: #16a34a; }
.h3 { font-size: 16px; font-weight: 700; margin-bottom: 12px; }
.textarea { width: 100%; min-height: 80px; border: 1px solid #d1d5db; border-radius: 10px; padding: 10px; font-size: 14px; }
.row { display: flex; gap: 10px; margin-top: 12px; }
.primary { background: #dc2626; color: #fff; border: none; border-radius: 10px; padding: 10px 16px; cursor: pointer; font-weight: 600; }
.primary:disabled { opacity: 0.5; }
.btn { background: #fff; border: 1px solid #d1d5db; border-radius: 10px; padding: 10px 16px; cursor: pointer; }
.loading { margin-top: 12px; color: #6b7280; font-weight: 500; }
.content-preview { margin-bottom: 16px; padding: 16px; background: #fef2f2; border-radius: 10px; }
.deck-title { font-size: 18px; font-weight: 700; color: #1e293b; }
.page-count { color: #6b7280; font-size: 13px; margin: 6px 0 16px; }
.pages-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.page-card { background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; }
.page-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.page-num { background: #dc2626; color: white; width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 600; }
.page-title { font-weight: 600; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.page-elements { font-size: 12px; color: #6b7280; }
.test-cases { display: flex; gap: 8px; align-items: center; margin: 12px 0; flex-wrap: wrap; }
.test-btn { padding: 6px 12px; border: 1px dashed #9ca3af; border-radius: 6px; background: #f9fafb; cursor: pointer; font-size: 12px; }
.test-btn:hover { border-color: #dc2626; background: #fef2f2; color: #dc2626; }
.label { font-weight: 600; font-size: 13px; }
.qbox { margin: 12px 0; padding: 12px; border: 1px dashed #d1d5db; border-radius: 10px; background: #fff; }
.qtitle { font-weight: 600; margin-bottom: 8px; }
.options-group { display: flex; flex-wrap: wrap; gap: 8px; }
.option-btn { padding: 8px 14px; border: 2px solid #d1d5db; border-radius: 8px; background: #fff; cursor: pointer; }
.option-btn.active { border-color: #dc2626; background: #fef2f2; color: #dc2626; }
.input { width: 100%; border: 1px solid #d1d5db; border-radius: 8px; padding: 8px 10px; }
.progress { margin-top: 12px; color: #dc2626; font-weight: 600; animation: pulse 1.5s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
.err { margin-top: 10px; color: #b91c1c; font-weight: 600; }
</style>
