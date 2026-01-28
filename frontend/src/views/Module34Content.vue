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
    <section v-if="cacheLoaded && outline" class="glass-card cache-loaded">
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
    <section class="glass-card">
      <div class="h3">
        <span class="icon">📝</span>
        输入需求（完整流程 3.1→3.2→3.3→3.4）
      </div>
      <textarea class="textarea hover-lift" v-model="rawText" placeholder="例如：给我一个机械专业「液压传动原理」的理论课课件，10页左右"></textarea>
      
      <div class="test-cases">
        <span class="label">测试案例：</span>
        <button class="test-btn" v-for="tc in testCaseList" :key="tc.label" @click="rawText = tc.text">
          {{ tc.label }}
        </button>
      </div>
      
      <div class="row">
        <button class="primary hover-lift" @click="runContent" :disabled="busy || !rawText.trim()">
          {{ busy ? '生成中...' : '✨ 运行内容生成' }}
        </button>
        <button class="btn" @click="reset" :disabled="busy">重置</button>
      </div>
      <div v-if="busy && currentStep" class="progress">⏳ {{ currentStep }}</div>
      <div v-if="err" class="err">❌ {{ err }}</div>
    </section>

    <!-- 问答交互（意图确认阶段） -->
    <section v-if="needUserInput" class="glass-card warn" style="border-left: 4px solid var(--color-warning)">
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
        <button class="primary hover-lift" @click="submitAnswers(false)" :disabled="busy">提交并继续</button>
        <button class="btn" @click="submitAnswers(true)" :disabled="busy">使用默认值</button>
      </div>
    </section>

    <!-- 折叠的前置结果 -->
    <section v-if="teachingRequest && !needUserInput" class="glass-card">
      <div class="h3">3.1 意图理解结果</div>
      <JsonBlock title="teaching_request.json" :value="teachingRequest" collapsed />
    </section>

    <section v-if="styleConfig" class="glass-card">
      <div class="h3">3.2 风格配置结果</div>
      <JsonBlock title="style_config.json" :value="styleConfig" collapsed />
    </section>

    <section v-if="outline" class="glass-card">
      <div class="h3">3.3 PPT大纲结果</div>
      <JsonBlock title="outline.json" :value="outline" collapsed />
    </section>

    <!-- 内容结果 -->
    <section v-if="deckContent" class="glass-card highlight">
      <div class="h3">
        <span class="icon">📄</span>
        3.4 页面内容结果
      </div>
      
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
/* 模块页面容器 */
.module-page {
  --color-module: var(--color-34);
  --color-module-light: var(--color-34-light);
  max-width: 900px;
  margin: 0 auto;
  padding: var(--spacing-6);
  animation: slide-up 0.5s ease-out;
}

/* 模块头部 */
.module-header {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-4);
  margin-bottom: var(--spacing-8);
  position: relative;
}

.badge {
  background: linear-gradient(135deg, var(--color-module) 0%, #FCA5A5 100%);
  color: var(--text-inverse);
  padding: var(--spacing-2) var(--spacing-4);
  border-radius: var(--radius-lg);
  font-weight: var(--font-weight-black);
  font-size: var(--font-size-lg);
  flex-shrink: 0;
  box-shadow: 0 4px 6px -1px rgba(249, 115, 22, 0.3);
}

.module-header h2 {
  font-family: var(--font-serif);
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-black);
  color: var(--color-brand);
  margin: 0;
  letter-spacing: -0.02em;
}

.desc {
  font-size: var(--font-size-lg);
  color: var(--text-secondary);
  line-height: var(--line-height-relaxed);
  margin: 0 0 var(--spacing-6) 0;
}

/* 卡片样式 */
.card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-6);
  margin-bottom: var(--spacing-4);
  box-shadow: var(--shadow-card);
  border: 1px solid var(--border-light);
}

/* 玻璃态卡片 */
.glass-card {
  background: rgba(255, 255, 255, 0.85); 
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: var(--radius-xl);
  padding: var(--spacing-8);
  margin-bottom: var(--spacing-6);
  box-shadow: 0 20px 40px -20px rgba(0,0,0,0.05);
  transition: all var(--duration-normal) var(--ease-out);
}

.glass-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 30px 60px -20px rgba(13, 76, 74, 0.1);
  border-color: var(--color-brand-light);
}

.card.highlight {
  border-left: 4px solid var(--color-module);
}

.card.warn {
  border-left: 4px solid var(--color-warning);
  background: var(--color-warning-light);
}

.card.cache-loaded {
  border-left: 4px solid var(--color-success);
  background: var(--color-success-light);
}

.cache-info { display: flex; flex-wrap: wrap; gap: var(--spacing-4); margin-bottom: var(--spacing-3); }
.cache-info .info-item { display: flex; gap: var(--spacing-2); }
.cache-info .label { color: var(--text-secondary); font-size: var(--font-size-sm); }
.cache-info .value { font-weight: var(--font-weight-semibold); font-size: var(--font-size-sm); color: var(--color-success); }

.h3 {
  font-family: var(--font-serif);
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-brand);
  margin-bottom: var(--spacing-6);
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.h3::after {
  content: '';
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, var(--border-light) 0%, transparent 100%);
}

/* 文本域 */
.textarea {
  width: 100%;
  min-height: 80px;
  padding: var(--spacing-3);
  font-family: inherit;
  font-size: var(--font-size-base);
  color: var(--text-primary);
  background: var(--bg-input);
  border: 2px solid transparent;
  border-radius: var(--radius-md);
  line-height: var(--line-height-relaxed);
  resize: vertical;
  transition: all var(--duration-fast);
}

.textarea:focus {
  outline: none;
  background: var(--bg-card);
  border-color: var(--color-brand);
  box-shadow: 0 0 0 var(--focus-ring-width) var(--focus-ring-color);
}

.row { display: flex; gap: var(--spacing-3); margin-top: var(--spacing-3); }

/* 按钮 - 统一使用品牌色 */
.primary {
  background: var(--color-brand);
  color: var(--text-inverse);
  border: none;
  border-radius: var(--radius-md);
  padding: var(--spacing-3) var(--spacing-4);
  cursor: pointer;
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-base);
  transition: all var(--duration-fast);
}

.primary:hover:not(:disabled) {
  background: var(--color-brand-hover);
  transform: translateY(-1px);
  box-shadow: var(--shadow-elevated);
}

.primary:disabled { opacity: 0.5; cursor: not-allowed; }

.btn {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: var(--spacing-3) var(--spacing-4);
  cursor: pointer;
  font-size: var(--font-size-base);
  color: var(--text-primary);
  transition: all var(--duration-fast);
}

.btn:hover:not(:disabled) {
  background: var(--bg-hover);
  border-color: var(--border-default);
}

.loading { margin-top: var(--spacing-3); color: var(--text-secondary); font-weight: var(--font-weight-medium); }

/* 内容预览 */
.content-preview {
  margin-bottom: var(--spacing-4);
  padding: var(--spacing-4);
  background: var(--color-module-light);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-light);
}

.deck-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  font-family: var(--font-serif);
}

.page-count {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  margin: var(--spacing-2) 0 var(--spacing-4);
}

.pages-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--spacing-3);
}

.page-card {
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: var(--spacing-3);
  transition: all var(--duration-fast);
  backdrop-filter: blur(4px);
}

.page-card:hover {
  transform: translateY(-2px);
  background: #fff;
  box-shadow: var(--shadow-sm);
  border-color: var(--color-module);
}

.page-header { display: flex; align-items: center; gap: var(--spacing-2); margin-bottom: var(--spacing-2); }

.page-num {
  background: var(--color-module);
  color: var(--text-inverse);
  width: 24px;
  height: 24px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.page-title {
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--text-primary);
}

.page-elements { font-size: var(--font-size-xs); color: var(--text-secondary); }

/* 测试案例按钮组 */
.test-cases {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
  align-items: center;
  margin: var(--spacing-3) 0;
}

.test-btn {
  padding: var(--spacing-2) var(--spacing-3);
  border: 1px dashed var(--border-default);
  border-radius: var(--radius-md);
  background: var(--bg-input);
  cursor: pointer;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  transition: all var(--duration-fast);
}

.test-btn:hover {
  border-color: var(--color-module);
  background: var(--color-module-light);
  color: var(--color-module);
}

.label { font-weight: var(--font-weight-semibold); font-size: var(--font-size-sm); }

/* 问答区域 */
.qbox {
  margin: var(--spacing-3) 0;
  padding: var(--spacing-3);
  border: 1px dashed var(--border-default);
  border-radius: var(--radius-lg);
  background: var(--bg-card);
}

.qtitle {
  font-weight: var(--font-weight-semibold);
  margin-bottom: var(--spacing-2);
  color: var(--text-primary);
}

.options-group { display: flex; flex-wrap: wrap; gap: var(--spacing-2); }

.option-btn {
  padding: var(--spacing-2) var(--spacing-4);
  border: 2px solid var(--border-default);
  border-radius: var(--radius-md);
  background: var(--bg-card);
  cursor: pointer;
  font-size: var(--font-size-base);
  transition: all var(--duration-fast);
}

.option-btn:hover {
  border-color: var(--color-brand);
}

.option-btn.active {
  border-color: var(--color-brand);
  background: var(--color-brand-light);
  color: var(--color-brand);
}

/* 输入框 */
.input {
  width: 100%;
  padding: var(--spacing-2) var(--spacing-3);
  font-family: inherit;
  font-size: var(--font-size-base);
  color: var(--text-primary);
  background: var(--bg-input);
  border: 2px solid transparent;
  border-radius: var(--radius-md);
  transition: all var(--duration-fast);
}

.input:focus {
  outline: none;
  background: var(--bg-card);
  border-color: var(--color-brand);
  box-shadow: 0 0 0 var(--focus-ring-width) var(--focus-ring-color);
}

.progress { margin-top: var(--spacing-3); color: var(--color-module); font-weight: var(--font-weight-semibold); animation: pulse 1.5s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
.err { margin-top: var(--spacing-3); color: var(--color-error); font-weight: var(--font-weight-semibold); }
</style>
