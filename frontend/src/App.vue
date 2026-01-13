<template>
  <div class="page">
    <header class="header">
      <div class="h1">PPT大纲工作流（模块 3.1 → 3.4）</div>
      <div class="sub">
        目标：从"用户需求"出发，优先交互补全关键信息，再生成风格配置、PPT大纲与页面内容（deck_content）；每一步均可在日志中回放。
      </div>
    </header>

    <section class="card">
      <div class="row">
        <div class="label">后端 API</div>
        <input class="input" v-model="apiBase" placeholder="http://localhost:8001" />
        <button class="primary" @click="checkHealth" :disabled="busy">连通性检测</button>
      </div>
      <div class="muted">提示：默认后端端口 8000；前端 dev 端口 5173。</div>
      <div v-if="health" class="ok">✅ 后端正常，LLM启用：{{ health.llm_enabled }}</div>
      <div v-if="err" class="err">❌ {{ err }}</div>
    </section>

    <!-- 模块测试选择器 -->
    <section class="card">
      <div class="h2">测试模式选择</div>
      <div class="mode-selector">
        <button 
          v-for="mode in testModes" 
          :key="mode.value"
          :class="['mode-btn', { active: testMode === mode.value }]"
          @click="testMode = mode.value"
        >
          {{ mode.label }}
        </button>
      </div>
      <div class="muted">
        {{ testModeDescription }}
      </div>
      <!-- Style Name 输入框（仅3.1->3.3模式显示） -->
      <div v-if="showStyleNameInput" class="style-name-input" style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
        <div class="row" style="align-items: flex-start;">
          <div class="label" style="min-width: 100px;">Style Name:</div>
          <div style="flex: 1;">
            <input 
              class="input" 
              v-model="styleName" 
              placeholder="可输入中文（理论课/实训课/复习课）或英文（theory_clean/practice_steps/review_mindmap）"
              style="width: 100%;"
            />
            <div class="muted" style="margin-top: 6px; font-size: 13px;">
              <strong>支持输入：</strong>
              <br />
              <span style="color: #059669;">中文：</span>理论课、实训课、复习课
              <br />
              <span style="color: #059669;">英文：</span>theory_clean、practice_steps、review_mindmap
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="card">
      <div class="h2">① 输入需求（模块 3.1）</div>
      
      <!-- 默认配置提示 -->
      <div class="tip-box">
        <strong>默认配置：</strong>课时45分钟 | 含案例 | 含习题 | 含互动
        <span class="muted">（如需调整，请在输入中说明）</span>
      </div>
      
      <textarea class="textarea" v-model="rawText" placeholder="例如：给我一个机械专业「液压传动原理」的理论课课件，10页左右"></textarea>
      
      <!-- 测试案例快速选择 -->
      <div class="test-cases">
        <span class="label">测试案例：</span>
        <button class="test-btn" @click="useTestCase(0)">完整输入</button>
        <button class="test-btn" @click="useTestCase(1)">缺少知识点</button>
        <button class="test-btn" @click="useTestCase(2)">页数冲突</button>
      </div>
      
      <div class="row">
        <button class="primary" @click="start" :disabled="busy || !rawText.trim()">
          {{ testMode === 'full' ? '开始完整流程' : `测试模块 ${testMode}` }}
        </button>
        <button class="btn" @click="reset" :disabled="busy">重置</button>
        <a v-if="sessionId" class="link" :href="logsHref" target="_blank" rel="noreferrer">下载日志 JSONL</a>
      </div>
      <div class="muted" v-if="sessionId">Session: {{ sessionId }}</div>
    </section>

    <section v-if="needUserInput" class="card warn">
      <div class="h2">② 请确认或补充信息</div>
      <div class="muted" v-if="teachingRequest">
        当前阶段：{{ getStageLabel(teachingRequest.interaction_stage) }}
      </div>

      <!-- 默认配置提示（在用户确认和补充阶段显示） -->
      <div v-if="teachingRequest && needUserInput && (teachingRequest.interaction_stage === 'supplement_and_config' || teachingRequest.interaction_stage === 'finalize_supplement')" class="tip-box warn">
        <strong>⚙️ 默认配置说明：</strong>如未特别说明，系统将按以下配置生成课件：
        <ul style="margin: 8px 0; padding-left: 20px;">
          <li>课时：45分钟</li>
          <li>应用案例：包含</li>
          <li>习题巩固：包含</li>
          <li>互动环节：包含</li>
        </ul>
        <span class="muted">💡 您可以在下方问题中调整上述配置</span>
      </div>

      <div class="qbox" v-for="q in questions" :key="q.key" v-show="shouldShowQuestion(q)" 
           :class="{ 'page-conflict': q.key === 'slide_count_adjust' }">
        <div class="qtitle">
          <pre class="question-text">{{ q.question }}</pre>
        </div>
        
        <!-- 页面冲突特殊显示 -->
        <div v-if="q.key === 'slide_count_adjust' && teachingRequest" class="page-conflict-info">
          <div class="conflict-stats">
            <div class="stat-item">
              <span class="stat-label">当前目标页数：</span>
              <span class="stat-value current">{{ teachingRequest.slide_requirements?.target_count || '未设置' }}</span>
            </div>
            <div class="stat-item" v-if="teachingRequest.slide_requirements?.min_count">
              <span class="stat-label">系统建议最小：</span>
              <span class="stat-value min">{{ teachingRequest.slide_requirements.min_count }}</span>
            </div>
            <div class="stat-item" v-if="q.recommended_count">
              <span class="stat-label">AI推荐页数：</span>
              <span class="stat-value recommended">{{ q.recommended_count }}</span>
            </div>
          </div>
          <div v-if="q.explanation" class="recommendation-explanation">
            <strong>💡 推荐理由：</strong>
            <p>{{ q.explanation }}</p>
          </div>
        </div>
        
        <!-- Select options -->
        <div v-if="q.options && q.options.length" class="options-group">
          <button 
            v-for="opt in q.options" 
            :key="opt" 
            class="option-btn"
            :class="{ active: answers[q.key] === opt }"
            @click="answers[q.key] = opt"
          >
            {{ opt }}
          </button>
        </div>
        
        <!-- 自定义页数输入框 -->
        <div v-if="q.key === 'custom_slide_count'" class="custom-count-input">
          <input 
            type="number"
            class="input" 
            v-model="answers[q.key]" 
            :placeholder="q.placeholder || '请输入页数...'"
            :min="teachingRequest?.slide_requirements?.min_count || 1"
          />
          <div class="input-hint" v-if="teachingRequest?.slide_requirements?.min_count">
            <span class="muted">提示：建议不少于 {{ teachingRequest.slide_requirements.min_count }} 页</span>
            <span class="muted" style="display: block; margin-top: 4px;">
              如果页数仍不够，系统会在后续进行智能调整
            </span>
          </div>
        </div>
        
        <!-- Text input (for text and list types) -->
        <input 
          v-else-if="!q.options || !q.options.length"
          class="input" 
          v-model="answers[q.key]" 
          :placeholder="q.placeholder || '请输入...'"
          :type="q.input_type === 'number' ? 'number' : 'text'"
        />
      </div>

      <div class="row">
        <button class="primary" @click="submitAnswers(false)" :disabled="busy || !canSubmit">提交并继续</button>
        <button class="btn" @click="submitAnswers(true)" :disabled="busy">使用默认值继续</button>
      </div>
    </section>

    <!-- 3.1 结果：意图理解（人类可读版本） -->
    <section v-if="teachingRequest && shouldShow('3.1')" class="card">
      <div class="h2">
        <span class="stage-badge">3.1</span> 意图理解结果
      </div>
      
      <!-- 人类可读摘要 -->
      <div v-if="teachingRequest.display_summary" class="display-summary">
        <pre>{{ teachingRequest.display_summary }}</pre>
      </div>
      
      <!-- 分隔线 -->
      <div class="divider">
        <span>JSON 格式（传给 3.2）</span>
      </div>
      
      <JsonBlock title="teaching_request.json" :value="teachingRequest" filename="teaching_request.json" />
    </section>

    <!-- 3.2 结果：风格配置 -->
    <section v-if="style && shouldShow('3.2')" class="card">
      <div class="h2">
        <span class="stage-badge">3.2</span> 风格配置结果
      </div>
      <JsonBlock title="style.json" :value="style" filename="style.json" />
    </section>

    <!-- 3.3 结果：PPT大纲 -->
    <section v-if="outline && shouldShow('3.3')" class="card">
      <div class="h2">
        <span class="stage-badge">3.3</span> PPT大纲结果
      </div>
      <JsonBlock title="outline.json" :value="outline" filename="outline.json" />
    </section>

    <!-- 3.4 结果：页面内容 -->
    <section v-if="deckContent && shouldShow('3.4')" class="card">
      <div class="h2">
        <span class="stage-badge">3.4</span> 页面内容结果
      </div>
      <JsonBlock title="deck_content.json" :value="deckContent" filename="deck_content.json" />
    </section>

    <section v-if="sessionState" class="card">
      <div class="h2">状态快照（便于你核对工作流输出）</div>
      <JsonBlock title="session_state.json" :value="sessionState" filename="session_state.json" />
    </section>

    <footer class="footer">
      <div class="muted">项目支持：日志回放、LLM审校（可选）、交互补全优先。</div>
    </footer>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import JsonBlock from './components/JsonBlock.vue'
import { api, getApiBase, setApiBase } from './api'

const apiBase = ref(getApiBase())
watch(apiBase, (v) => {
  setApiBase(v)
})

// 测试模式
const testModes = [
  { value: 'full', label: '完整流程' },
  { value: '3.1', label: '仅 3.1 意图理解' },
  { value: '3.2', label: '仅 3.1→3.2' },
  { value: '3.1-3.3', label: '仅 3.1→3.3（跳过3.2）' },
  { value: '3.3', label: '3.1→3.3（3.1→3.2→3.3）' },
  { value: '3.4', label: '完整 3.1→3.4' },
]
const testMode = ref('full')
const styleName = ref('')  // 用于测试模式 3.1->3.3（跳过3.2）

const testModeDescription = computed(() => {
  const descriptions = {
    'full': '执行完整工作流（3.1→3.2→3.3→3.4），显示所有模块结果',
    '3.1': '仅执行模块3.1（意图理解），返回TeachingRequest结构化数据',
    '3.2': '执行到模块3.2（风格设计），返回意图+风格配置',
    '3.1-3.3': '从3.1直接到3.3（跳过3.2），需要手动输入style_name',
    '3.3': '执行3.1→3.2→3.3，返回意图+风格+大纲',
    '3.4': '执行完整流程，与"完整流程"相同',
  }
  return descriptions[testMode.value] || ''
})

const showStyleNameInput = computed(() => {
  return testMode.value === '3.1-3.3'
})

// 中文到英文的style_name映射
const styleNameMap = {
  '理论课': 'theory_clean',
  '理论': 'theory_clean',
  'theory_clean': 'theory_clean',
  '实训课': 'practice_steps',
  '实训': 'practice_steps',
  'practice_steps': 'practice_steps',
  '复习课': 'review_mindmap',
  '复习': 'review_mindmap',
  'review_mindmap': 'review_mindmap',
}

// 将用户输入转换为英文style_name
function normalizeStyleName(input) {
  if (!input) return null
  const trimmed = input.trim()
  // 直接查找映射
  if (styleNameMap[trimmed]) {
    return styleNameMap[trimmed]
  }
  // 如果已经是有效的英文值，直接返回
  if (['theory_clean', 'practice_steps', 'review_mindmap'].includes(trimmed)) {
    return trimmed
  }
  // 如果找不到匹配，返回原值（让后端处理或报错）
  return trimmed
}

// 判断是否显示某个模块的结果
function shouldShow(stage) {
  if (testMode.value === 'full' || testMode.value === '3.4') return true
  if (testMode.value === '3.1-3.3') {
    // 对于3.1-3.3模式（跳过3.2），不显示3.2的结果
    if (stage === '3.2') return false
    const order = ['3.1', '3.2', '3.3', '3.4']
    const targetIdx = order.indexOf('3.3')
    const stageIdx = order.indexOf(stage)
    return stageIdx <= targetIdx
  }
  const order = ['3.1', '3.2', '3.3', '3.4']
  const targetIdx = order.indexOf(testMode.value)
  const stageIdx = order.indexOf(stage)
  return stageIdx <= targetIdx
}

// 测试案例
const testCases = [
  '给我一个机械专业「液压传动原理」的理论课课件，10页左右',
  '给我一个护理专业的讲解课件',
  '做一份土木专业「土石方工程量计算」「列项」两个知识点的课件，5页',
]

function useTestCase(index) {
  rawText.value = testCases[index] || testCases[0]
}

// 交互阶段标签
function getStageLabel(stage) {
  const labels = {
    'initial': '初步识别',
    'confirm_kp': '确认知识点',
    'confirm_pages': '确认页数',
    'confirm_goals': '确认教学目标',
    'final_confirm': '最终确认',
    'confirmed': '已确认'
  }
  return labels[stage] || stage
}

// 判断是否显示某个问题（用于条件依赖的问题）
function shouldShowQuestion(q) {
  // 自定义课时输入框只在选择"自定义"时显示
  if (q.key === 'custom_lesson_duration') {
    return answers['lesson_duration_config'] === '自定义'
  }
  // 自定义页数输入框只在选择"自定义页数"时显示
  if (q.key === 'custom_slide_count') {
    const slideAdjust = answers['slide_count_adjust']
    return slideAdjust && (slideAdjust.includes('自定义') || slideAdjust.includes('✏️'))
  }
  // 其他问题默认显示
  return true
}

// 是否可以提交（至少有一个问题有答案或者问题是可选的）
const canSubmit = computed(() => {
  if (!questions.value || questions.value.length === 0) return true
  return questions.value.every(q => {
    if (!q.required) return true
    return answers[q.key] && String(answers[q.key]).trim()
  })
})

const busy = ref(false)
const err = ref('')
const health = ref(null)

const rawText = ref('')
const sessionId = ref('')
const needUserInput = ref(false)
const questions = ref([])
const answers = reactive({})

const teachingRequest = ref(null)
const style = ref(null)
const outline = ref(null)
const deckContent = ref(null)
const sessionState = ref(null)

const logsHref = computed(() => sessionId.value ? api.logsUrl(sessionId.value) : '#')

async function checkHealth() {
  err.value = ''
  health.value = null
  busy.value = true
  try {
    health.value = await api.health()
  } catch (e) {
    err.value = e.message || String(e)
  } finally {
    busy.value = false
  }
}

function reset() {
  err.value = ''
  health.value = null
  sessionId.value = ''
  needUserInput.value = false
  questions.value = []
  Object.keys(answers).forEach(k => delete answers[k])
  teachingRequest.value = null
  style.value = null
  outline.value = null
  deckContent.value = null
  sessionState.value = null
}

async function start() {
  reset()
  busy.value = true
  err.value = ''
  try {
    const r = await api.createSession()
    sessionId.value = r.session_id || r.sessionId || r.session || r.session_id
    // 根据测试模式确定stop_at和style_name
    let stopAt = null
    let styleNameValue = null
    
    if (testMode.value === '3.1-3.3') {
      stopAt = '3.3'
      styleNameValue = normalizeStyleName(styleName.value)
      if (!styleNameValue) {
        err.value = '请先输入 style_name（可输入：理论课/实训课/复习课 或 theory_clean/practice_steps/review_mindmap）'
        busy.value = false
        return
      }
    } else if (testMode.value !== 'full' && testMode.value !== '3.4') {
      // 其他模式（包括旧的3.3模式），正常执行3.1->3.2->3.3
      stopAt = testMode.value
    }
    
    await runOnce({ 
      user_text: rawText.value, 
      answers: {}, 
      auto_fill_defaults: false, 
      stop_at: stopAt,
      style_name: styleNameValue
    })
  } catch (e) {
    err.value = e.message || String(e)
  } finally {
    busy.value = false
  }
}

async function submitAnswers(useDefaults) {
  busy.value = true
  err.value = ''
  try {
    // 根据测试模式确定stop_at和style_name
    let stopAt = null
    let styleNameValue = null
    
    if (testMode.value === '3.1-3.3') {
      stopAt = '3.3'
      styleNameValue = normalizeStyleName(styleName.value)
      if (!styleNameValue) {
        err.value = '请先输入 style_name（可输入：理论课/实训课/复习课 或 theory_clean/practice_steps/review_mindmap）'
        busy.value = false
        return
      }
    } else if (testMode.value !== 'full' && testMode.value !== '3.4') {
      // 其他模式（包括旧的3.3模式），正常执行3.1->3.2->3.3
      stopAt = testMode.value
    }
    
    await runOnce({ 
      user_text: rawText.value, 
      answers: useDefaults ? {} : answers, 
      auto_fill_defaults: useDefaults, 
      stop_at: stopAt,
      style_name: styleNameValue
    })
  } catch (e) {
    err.value = e.message || String(e)
  } finally {
    busy.value = false
  }
}

async function runOnce({ user_text, answers, auto_fill_defaults, stop_at, style_name }) {
  if (!sessionId.value) throw new Error('No session_id')
  const res = await api.runWorkflow(sessionId.value, user_text, answers, auto_fill_defaults, stop_at, style_name)
  if (res.status === 'need_user_input') {
    needUserInput.value = true
    questions.value = res.questions || []
    for (const q of questions.value) {
      if (!(q.key in answers)) answers[q.key] = ''
    }
    // Also capture teaching_request if available
    teachingRequest.value = res.teaching_request || null
  } else if (res.status === 'ok') {
    needUserInput.value = false
    teachingRequest.value = res.teaching_request || null
    style.value = res.style_config || null
    outline.value = res.outline || null
    deckContent.value = res.deck_content || null
  } else if (res.status === 'error') {
    throw new Error(res.message || 'workflow error')
  }
  sessionState.value = await api.getSession(sessionId.value)
}
</script>

<style scoped>
.page { max-width: 980px; margin: 0 auto; padding: 18px; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, 'Apple Color Emoji','Segoe UI Emoji'; color: #111827; }
.header { padding: 8px 2px 14px; }
.h1 { font-size: 22px; font-weight: 800; }
.h2 { font-size: 16px; font-weight: 700; margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }
.sub { margin-top: 6px; color:#4b5563; }
.card { border: 1px solid #e5e7eb; border-radius: 14px; padding: 14px; background:#fff; box-shadow: 0 1px 2px rgba(0,0,0,0.04); margin: 12px 0; }
.warn { border-color: #f59e0b55; background: #fffbeb; }
.row { display:flex; gap: 10px; align-items:center; flex-wrap: wrap; }
.label { font-weight: 600; }
.input { flex: 1; min-width: 240px; border: 1px solid #d1d5db; border-radius: 10px; padding: 8px 10px; }
.textarea { width: 100%; min-height: 120px; border: 1px solid #d1d5db; border-radius: 12px; padding: 10px; margin: 10px 0; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; font-size: 13px;}
.primary { background:#111827; color:#fff; border: 1px solid #111827; border-radius: 10px; padding: 9px 12px; cursor:pointer; }
.primary:disabled { opacity: .5; cursor:not-allowed; }
.btn { background:#fff; border: 1px solid #d1d5db; border-radius: 10px; padding: 9px 12px; cursor:pointer; }
.btn:hover { background:#f9fafb; }
.link { color:#2563eb; text-decoration:none; font-weight:600; }
.link:hover { text-decoration:underline; }
.muted { color:#6b7280; font-size: 13px; margin-top: 6px; }
.ok { margin-top: 8px; color:#065f46; font-weight: 600; }
.err { margin-top: 8px; color:#b91c1c; font-weight: 600; white-space: pre-wrap; }
.qbox { margin-top: 10px; padding: 10px; border: 1px dashed #d1d5db; border-radius: 12px; background:#fff; }
.qtitle { font-weight: 700; margin-bottom: 6px; }
.footer { margin-top: 16px; padding: 12px 0; }

/* 模块选择器样式 */
.mode-selector { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
.mode-btn { 
  padding: 8px 14px; 
  border: 2px solid #d1d5db; 
  border-radius: 8px; 
  background: #fff; 
  cursor: pointer; 
  font-weight: 500;
  transition: all 0.2s;
}
.mode-btn:hover { border-color: #9ca3af; background: #f9fafb; }
.mode-btn.active { 
  border-color: #2563eb; 
  background: #eff6ff; 
  color: #2563eb; 
  font-weight: 600;
}

/* 阶段标识 */
.stage-badge {
  background: #2563eb;
  color: white;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

/* 提示框 */
.tip-box {
  background: #f0fdf4;
  border: 1px solid #86efac;
  border-radius: 8px;
  padding: 8px 12px;
  margin-bottom: 10px;
  font-size: 13px;
  color: #166534;
}

/* 测试案例按钮 */
.test-cases {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.test-btn {
  padding: 6px 12px;
  border: 1px dashed #9ca3af;
  border-radius: 6px;
  background: #f9fafb;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}
.test-btn:hover {
  border-color: #2563eb;
  background: #eff6ff;
  color: #2563eb;
}

/* 人类可读摘要样式 */
.display-summary {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 16px;
}
.display-summary pre {
  margin: 0;
  white-space: pre-wrap;
  font-family: ui-sans-serif, system-ui, sans-serif;
  font-size: 14px;
  line-height: 1.6;
  color: #1e293b;
}

/* 分隔线 */
.divider {
  display: flex;
  align-items: center;
  margin: 16px 0;
  text-align: center;
}
.divider::before,
.divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px dashed #d1d5db;
}
.divider span {
  padding: 0 12px;
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

/* 问题文本样式 */
.question-text {
  margin: 0;
  white-space: pre-wrap;
  font-family: ui-sans-serif, system-ui, sans-serif;
  font-size: 14px;
  line-height: 1.6;
  color: #1f2937;
}

/* 选项按钮组 */
.options-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 10px;
}

.option-btn {
  padding: 10px 18px;
  border: 2px solid #d1d5db;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.option-btn:hover {
  border-color: #9ca3af;
  background: #f9fafb;
}

.option-btn.active {
  border-color: #2563eb;
  background: #eff6ff;
  color: #2563eb;
}

/* 页面冲突特殊样式 */
.qbox.page-conflict {
  border-color: #f59e0b;
  background: #fffbeb;
  border-width: 2px;
}

.page-conflict-info {
  margin: 12px 0;
  padding: 12px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #fde68a;
}

.conflict-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 12px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-label {
  font-size: 13px;
  color: #6b7280;
  font-weight: 500;
}

.stat-value {
  font-size: 16px;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 6px;
}

.stat-value.current {
  background: #fee2e2;
  color: #dc2626;
}

.stat-value.min {
  background: #dbeafe;
  color: #2563eb;
}

.stat-value.recommended {
  background: #d1fae5;
  color: #059669;
}

.recommendation-explanation {
  margin-top: 12px;
  padding: 10px;
  background: #f0fdf4;
  border-left: 3px solid #10b981;
  border-radius: 4px;
}

.recommendation-explanation strong {
  color: #059669;
  display: block;
  margin-bottom: 6px;
}

.recommendation-explanation p {
  margin: 0;
  color: #166534;
  font-size: 13px;
  line-height: 1.6;
}

.custom-count-input {
  margin-top: 10px;
}

.input-hint {
  margin-top: 8px;
  font-size: 12px;
}
</style>
