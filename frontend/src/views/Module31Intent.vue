<template>
  <div class="module-page">
    <!-- 模块头部 -->
    <div class="module-header">
      <span class="module-badge">3.1</span>
      <div class="module-info">
        <h2 class="module-title">意图理解模块</h2>
        <p class="module-desc">从教师的自然语言输入中提取结构化教学需求</p>
      </div>
    </div>

    <ApiConfig />

    <!-- 输入区 -->
    <section class="glass-card">
      <h3 class="card-title">
        <span class="icon">📝</span>
        输入需求
      </h3>
      <div class="tip-box">
        <strong>默认配置：</strong>课时45分钟 | 含案例 | 含习题 | 含互动
      </div>
      <textarea
        class="textarea hover-lift"
        v-model="rawText"
        placeholder="例如：给我一个机械专业「液压传动原理」的理论课课件，10页左右"
      ></textarea>

      <div class="test-cases">
        <span class="label">测试案例：</span>
        <button
          class="test-btn"
          v-for="tc in testCaseList"
          :key="tc.label"
          @click="rawText = tc.text"
        >
          {{ tc.label }}
        </button>
      </div>
    </section>

    <!-- 模板选择区 -->
    <section class="glass-card">
      <h3 class="card-title">
        <span class="icon">🎨</span>
        选择设计模板
      </h3>
      <p class="template-hint">根据教学场景选择合适的模板风格，系统会自动推荐最佳选项</p>

      <div class="templates-grid">
        <div
          v-for="tpl in templates"
          :key="tpl.id"
          class="template-card"
          :class="{ active: selectedTemplate === tpl.id }"
          @click="selectedTemplate = tpl.id"
        >
          <div class="tpl-preview" :style="{ background: tpl.previewColor }">
            <span class="tpl-icon">{{ tpl.icon }}</span>
          </div>
          <div class="tpl-info">
            <div class="tpl-name">{{ tpl.name }}</div>
            <div class="tpl-desc">{{ tpl.desc }}</div>
            <div class="tpl-scene">适用于：{{ tpl.scene }}</div>
          </div>
          <div class="active-badge" v-if="selectedTemplate === tpl.id">✓</div>
        </div>
      </div>

      <div class="auto-select-hint" v-if="!selectedTemplate">
        <span class="hint-icon">💡</span>
        <span>未选择模板时，系统将根据教学场景自动推荐</span>
      </div>
    </section>

    <!-- 按钮区 -->
    <section class="glass-card">
      <div class="btn-group">
        <button class="btn btn-primary hover-lift" @click="runIntent" :disabled="busy || !rawText.trim()">
          <span v-if="busy" class="spinner-sm"></span>
          {{ busy ? '正在分析...' : '✨ 运行意图理解' }}
        </button>
        <button class="btn btn-secondary" @click="reset" :disabled="busy">重置</button>
      </div>

      <WorkflowProgress
        v-if="busy"
        :main-message="currentStep || '处理中...'"
        :current-step="currentStep"
        :messages="workflowProgress.messages"
        :progress="workflowProgress.progress"
      />
      <div v-if="err" class="error-message">{{ err }}</div>
    </section>

    <!-- 问答交互 -->
    <section v-if="needUserInput" class="glass-card" style="border-left: 4px solid var(--color-warning)">
      <h3 class="card-title">请确认或补充信息</h3>
      <div class="question-box" v-for="q in questions" :key="q.key">
        <div class="question-title">{{ q.question }}</div>
        <div v-if="q.options && q.options.length" class="options-group">
          <button
            v-for="opt in q.options" :key="opt"
            class="option-btn" :class="{ active: answers[q.key] === opt }"
            @click="answers[q.key] = opt"
          >{{ opt }}</button>
        </div>
        <input v-else class="input" v-model="answers[q.key]" :placeholder="q.placeholder || '请输入...'" />
      </div>
      <div class="btn-group">
        <button class="btn btn-primary" @click="submitAnswers(false)" :disabled="busy">提交并继续</button>
        <button class="btn btn-secondary" @click="submitAnswers(true)" :disabled="busy">使用默认值</button>
      </div>
    </section>

    <!-- 结果展示 -->
    <section v-if="teachingRequest" class="glass-card">
      <h3 class="card-title">
        <span class="icon">✅</span>
        意图理解结果
      </h3>
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
import { testCases } from '../composables/testCases'
import ApiConfig from '../components/common/ApiConfig.vue'
import JsonBlock from '../components/common/JsonBlock.vue'
import WorkflowProgress from '../components/common/WorkflowProgress.vue'

const {
  busy, err, currentStep, needUserInput, questions, answers,
  teachingRequest, reset, runWorkflow,
  workflowProgress, appendMessage
} = useWorkflow()

const testCaseList = testCases
const rawText = ref('')
const selectedTemplate = ref(null)

// 模板配置
const templates = [
  {
    id: 'theory_clean',
    name: '理论课风格',
    desc: '简洁清晰，重点突出',
    scene: '理论讲解、概念教学',
    icon: '📚',
    previewColor: 'linear-gradient(135deg, #3D5A80 0%, #5B8DB8 100%)'
  },
  {
    id: 'practice_steps',
    name: '实训课风格',
    desc: '步骤清晰，操作引导',
    scene: '实操训练、技能培养',
    icon: '🔧',
    previewColor: 'linear-gradient(135deg, #2D6A4F 0%, #52B788 100%)'
  },
  {
    id: 'review_mindmap',
    name: '复习课风格',
    desc: '结构化梳理，思维导图',
    scene: '复习回顾、知识整合',
    icon: '🧠',
    previewColor: 'linear-gradient(135deg, #5C4B7D 0%, #7E6BA8 100%)'
  }
]

async function runIntent() {
  try {
    const params = {
      user_text: rawText.value,
      stop_at: '3.1'
    }
    // 如果用户选择了模板，传递 style_name
    if (selectedTemplate.value) {
      params.style_name = selectedTemplate.value
    }
    await runWorkflow(params)
  } catch (e) {
    err.value = e.message
  }
}

async function submitAnswers(useDefaults) {
  try {
    const params = {
      user_text: rawText.value,
      answers: useDefaults ? {} : answers,
      auto_fill_defaults: useDefaults,
      stop_at: '3.1'
    }
    // 如果用户选择了模板，传递 style_name
    if (selectedTemplate.value) {
      params.style_name = selectedTemplate.value
    }
    await runWorkflow(params)
  } catch (e) {
    err.value = e.message
  }
}
</script>

<style scoped>
/* 模块页面容器 */
.module-page {
  --color-module: var(--color-31);
  --color-module-light: var(--color-31-light);
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

.module-badge {
  background: linear-gradient(135deg, var(--color-module) 0%, #818CF8 100%);
  color: var(--text-inverse);
  padding: var(--spacing-2) var(--spacing-4);
  border-radius: var(--radius-lg);
  font-weight: var(--font-weight-black);
  font-size: var(--font-size-lg);
  flex-shrink: 0;
  box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.3);
}

.module-info {
  flex: 1;
}

.module-title {
  font-family: var(--font-serif);
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-black);
  color: var(--color-brand);
  margin: 0 0 var(--spacing-2) 0;
  letter-spacing: -0.02em;
}

.module-desc {
  font-size: var(--font-size-lg);
  color: var(--text-secondary);
  line-height: var(--line-height-relaxed);
  margin: 0;
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

.card-title {
  font-family: var(--font-serif);
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-brand);
  margin-bottom: var(--spacing-6);
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.card-title::after {
  content: '';
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, var(--border-light) 0%, transparent 100%);
}

/* 提示框 */
.tip-box {
  background: var(--color-success-light);
  border: 1px solid var(--color-success);
  border-radius: var(--radius-md);
  padding: var(--spacing-3) var(--spacing-4);
  margin-bottom: var(--spacing-4);
  font-size: var(--font-size-sm);
  color: #166534;
}

/* 文本域 */
.textarea {
  width: 100%;
  min-height: 120px;
  padding: var(--spacing-4);
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

.textarea::placeholder {
  color: var(--text-placeholder);
}

/* 测试案例按钮组 */
.test-cases {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
  align-items: center;
  margin: var(--spacing-4) 0;
}

.test-cases .label {
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
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

/* 按钮组 */
.btn-group {
  display: flex;
  gap: var(--spacing-3);
  margin-top: var(--spacing-4);
}

/* 问答区域 */
.question-box {
  margin: var(--spacing-4) 0;
  padding: var(--spacing-4);
  border: 1px dashed var(--border-default);
  border-radius: var(--radius-lg);
  background: var(--bg-card);
}

.question-title {
  font-weight: var(--font-weight-semibold);
  margin-bottom: var(--spacing-3);
  color: var(--text-primary);
}

.options-group {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
}

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
  padding: var(--spacing-3) var(--spacing-4);
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

/* 结果展示区 */
.display-summary {
  background: var(--bg-input);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  padding: var(--spacing-4);
  margin-bottom: var(--spacing-4);
}

.display-summary pre {
  margin: 0;
  white-space: pre-wrap;
  font-family: inherit;
  font-size: var(--font-size-base);
  line-height: var(--line-height-relaxed);
  color: var(--text-primary);
}

/* 错误消息 */
.error-message {
  margin-top: var(--spacing-4);
  padding: var(--spacing-3) var(--spacing-4);
  background: var(--color-error-light);
  border: 1px solid var(--color-error);
  border-radius: var(--radius-md);
  color: var(--color-error);
  font-weight: var(--font-weight-medium);
}

/* 模板选择区域 */
.template-hint {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-4);
}

.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--spacing-4);
}

.template-card {
  position: relative;
  display: flex;
  flex-direction: column;
  border: 2px solid var(--border-default);
  border-radius: var(--radius-lg);
  background: var(--bg-card);
  cursor: pointer;
  transition: all var(--duration-fast);
  overflow: hidden;
}

.template-card:hover {
  border-color: var(--color-brand);
  transform: translateY(-2px);
  box-shadow: 0 8px 16px -4px rgba(0,0,0,0.1);
}

.template-card.active {
  border-color: var(--color-brand);
  background: var(--color-brand-light);
  box-shadow: 0 0 0 var(--focus-ring-width) var(--focus-ring-color);
}

.tpl-preview {
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tpl-icon {
  font-size: 2rem;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
}

.tpl-info {
  padding: var(--spacing-3) var(--spacing-4);
}

.tpl-name {
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-1);
}

.tpl-desc {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-2);
}

.tpl-scene {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  padding: var(--spacing-1) var(--spacing-2);
  background: var(--bg-input);
  border-radius: var(--radius-sm);
  display: inline-block;
}

.active-badge {
  position: absolute;
  top: var(--spacing-2);
  right: var(--spacing-2);
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--color-brand);
  color: var(--text-inverse);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-bold);
}

.auto-select-hint {
  margin-top: var(--spacing-4);
  padding: var(--spacing-3) var(--spacing-4);
  background: var(--bg-input);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.hint-icon {
  font-size: 1.2em;
}
</style>
