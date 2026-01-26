<template>
  <div class="module-page">
    <div class="module-header">
      <span class="badge">3.2</span>
      <h2>风格设计模块</h2>
    </div>
    <p class="desc">基于教学场景和专业领域生成PPT风格配置</p>

    <ApiConfig />

    <!-- V3: 缓存状态展示 -->
    <CacheStatus 
      active-step="3.2" 
      @use-cache="handleUseCache" 
    />

    <!-- V3: 缓存已加载提示 -->
    <section v-if="cacheLoaded && teachingRequest" class="glass-card cache-loaded">
      <div class="h3">✅ 已加载 3.1 缓存</div>
      <div class="cache-info">
        <div class="info-item">
          <span class="label">学科：</span>
          <span class="value">{{ teachingRequest.subject_info?.subject_name || '未指定' }}</span>
        </div>
        <div class="info-item">
          <span class="label">知识点：</span>
          <span class="value">{{ teachingRequest.knowledge_points?.map(kp => kp.name).join('、') || '无' }}</span>
        </div>
        <div class="info-item">
          <span class="label">场景：</span>
          <span class="value">{{ teachingRequest.teaching_scenario?.scene_type || 'unknown' }}</span>
        </div>
      </div>
      <div class="row">
        <button class="primary hover-lift" @click="runStyleFromCache" :disabled="busy">
          基于缓存运行风格设计
        </button>
      </div>
      <div v-if="busy && currentStep" class="progress">⏳ {{ currentStep }}</div>
    </section>

    <!-- 风格模版选择 -->
    <section class="glass-card">
      <div class="h3">
        <span class="icon">🎨</span>
        选择设计模版 (Template)
      </div>
      
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
          </div>
          <div class="active-badge" v-if="selectedTemplate === tpl.id">✓</div>
        </div>
      </div>
    </section>

    <!-- 输入区 -->
    <section class="glass-card">
      <div class="h3">
        <span class="icon">📝</span>
        输入需求（将先执行3.1再执行3.2）
      </div>
      <textarea class="textarea hover-lift" v-model="rawText" placeholder="例如：给我一个机械专业「液压传动原理」的理论课课件"></textarea>
      
      <div class="test-cases">
        <span class="label">测试案例：</span>
        <button class="test-btn" v-for="tc in testCaseList" :key="tc.label" @click="rawText = tc.text">
          {{ tc.label }}
        </button>
      </div>
      
      <div class="row">
        <button class="primary hover-lift" @click="runStyle" :disabled="busy || !rawText.trim()">
          ✨ 运行风格设计
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

    <!-- 意图理解结果 -->
    <section v-if="teachingRequest && !needUserInput" class="glass-card">
      <div class="h3">3.1 意图理解结果</div>
      <JsonBlock title="teaching_request.json" :value="teachingRequest" filename="teaching_request.json" collapsed />
    </section>

    <!-- 风格配置结果 -->
    <section v-if="styleConfig" class="glass-card highlight">
      <div class="h3">
        <span class="icon">🎨</span>
        3.2 风格配置结果
      </div>
      
      <div class="style-info">
        <div class="info-item">
          <span class="label">风格名称：</span>
          <span class="value">{{ styleConfig.style_name }}</span>
        </div>
        <div class="info-item">
          <span class="label">字体：</span>
          <span class="value">{{ styleConfig.font?.title_family }} / {{ styleConfig.font?.body_family }}</span>
        </div>
        <div class="info-item">
          <span class="label">布局密度：</span>
          <span class="value">{{ styleConfig.layout?.density }}</span>
        </div>
      </div>

      <!-- 风格预览 -->
      <div class="h4">配色方案</div>
      <div class="style-preview" v-if="styleConfig.color">
        <div class="color-palette-grid">
          <!-- 主色系 -->
          <div class="palette-row">
            <div class="color-group-label" :style="{color: styleConfig.color.muted}">品牌色系</div>
            <div class="color-item large" :style="{ background: styleConfig.color.primary, color: getTextColor(styleConfig.color.primary) }">
                <span class="color-label">主色 Primary</span>
                <span class="color-value">{{ styleConfig.color.primary }}</span>
            </div>
            <div class="color-item" :style="{ background: styleConfig.color.secondary, color: getTextColor(styleConfig.color.secondary) }">
                <span class="color-label">辅助 Secondary</span>
                <span class="color-value">{{ styleConfig.color.secondary }}</span>
            </div>
             <div class="color-item" :style="{ background: styleConfig.color.accent, color: getTextColor(styleConfig.color.accent) }">
                <span class="color-label">强调 Accent</span>
                <span class="color-value">{{ styleConfig.color.accent }}</span>
            </div>
          </div>

          <!-- 功能色系 -->
           <div class="palette-row">
             <div class="color-group-label" :style="{color: styleConfig.color.muted}">功能色系</div>
             <div class="color-item" :style="{ background: styleConfig.color.text, color: getTextColor(styleConfig.color.text) }">
                <span class="color-label">文本 Text</span>
                <span class="color-value">{{ styleConfig.color.text }}</span>
            </div>
             <div class="color-item" :style="{ background: styleConfig.color.muted, color: getTextColor(styleConfig.color.muted) }">
                <span class="color-label">弱化 Muted</span>
                <span class="color-value">{{ styleConfig.color.muted }}</span>
            </div>
             <div class="color-item" :style="{ background: styleConfig.color.warning, color: getTextColor(styleConfig.color.warning) }">
                <span class="color-label">警示 Warning</span>
                <span class="color-value">{{ styleConfig.color.warning }}</span>
            </div>
          </div>

          <!-- 背景色系 -->
           <div class="palette-row">
             <div class="color-group-label" :style="{color: styleConfig.color.muted}">背景色系</div>
             <div class="color-item" :style="{ background: styleConfig.color.background, color: getTextColor(styleConfig.color.background), border: '1px solid #eee' }">
                <span class="color-label">背景 Bkg</span>
                <span class="color-value">{{ styleConfig.color.background }}</span>
            </div>
             <div class="color-item" :style="{ background: styleConfig.color.surface || '#fff', color: getTextColor(styleConfig.color.surface || '#fff'), border: '1px solid #eee' }">
                <span class="color-label">卡片 Surface</span>
                <span class="color-value">{{ styleConfig.color.surface || '-' }}</span>
            </div>
            <div class="color-item wide" v-if="styleConfig.color.background_gradient" :style="{ background: styleConfig.color.background_gradient, color: '#000' }">
                <span class="color-label">渐变 Gradient</span>
            </div>
          </div>
        </div>

        <!-- 组件应用预览 (Usage Showcase) -->
        <div class="usage-showcase glass-card" :style="{ background: styleConfig.color.background, fontFamily: styleConfig.font.body_family }">
            <div class="showcase-label" :style="{ color: styleConfig.color.muted }">组件应用预览</div>
            <div class="showcase-row">
                <!-- 1. 卡片与文本层次 -->
                <div class="preview-card card-tilted" :style="{ 
                    background: styleConfig.color.surface || '#fff', 
                    color: styleConfig.color.text,
                    borderRadius: styleConfig.layout?.border_radius || '0px',
                    boxShadow: getShadowStyle(styleConfig.layout?.box_shadow)
                }">
                    <div class="pc-head" :style="{ color: styleConfig.color.primary, fontFamily: styleConfig.font.title_family }">Card Title</div>
                    <div class="pc-body">Normal text content example.</div>
                    <div class="pc-muted" :style="{ color: styleConfig.color.muted }">Muted info: Secondary text with lower contrast.</div>
                </div>

                <!-- 2. 状态提示 -->
                <div class="preview-group">
                    <div class="preview-alert" :style="{ 
                        background: styleConfig.color.warning, 
                        color: '#fff',
                        borderRadius: styleConfig.layout?.border_radius || '0px'
                    }">
                        <span class="icon">⚠️</span> Warning / Alert Message
                    </div>
                    <div class="preview-btn pulse-accent" :style="{ 
                        background: styleConfig.color.accent, 
                        color: '#fff',
                        borderRadius: styleConfig.layout?.border_radius || '0px'
                    }">
                        Accent Button
                    </div>
                </div>
            </div>
        </div>
      </div>
      
      <!-- 风格微调交互区 (Style Refinement) -->
      <div class="refine-section" v-if="styleConfig">
        <div class="h4">
          <span>✨ 风格微调 (AI Designer)</span>
          <div class="tooltip-container">
            <span class="tooltip-icon">💡 支持修改项</span>
            <div class="tooltip-content">
              <ul>
                <li><strong>色彩:</strong> "换个暖色调", "背景深一点", "主色改成#ff0000"</li>
                <li><strong>字体:</strong> "标题用黑体", "正文大一点"</li>
                <li><strong>布局:</strong> "更宽松一点", "卡片圆角大一点"</li>
                <li><strong>风格:</strong> "赛博朋克风", "极简风格"</li>
              </ul>
            </div>
          </div>
        </div>
        
        <div class="refine-box glass-card" style="padding: var(--spacing-4); border: 1px solid var(--color-brand-light)">
          <textarea 
            class="refine-input hover-lift" 
            v-model="refineText" 
            placeholder="对当前风格不满意？试试告诉我：'换个更有科技感的配色' 或 '标题字号加大'..."
            :disabled="refineBusy"
            @keydown.enter.ctrl.prevent="handleRefine"
          ></textarea>
          
          <div class="refine-actions">
            <div class="history-actions">
              <button class="icon-btn" @click="undoStyle" :disabled="styleHistory.length === 0" title="撤销 (Undo)">
                ↩️ 撤销
              </button>
            </div>
            <button class="primary-btn hover-lift" @click="handleRefine" :disabled="refineBusy || !refineText.trim()">
              {{ refineBusy ? '调整中...' : '✨ 确认调整' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 警告确认弹窗 -->
      <div v-if="showRefineWarning" class="modal-overlay">
        <div class="modal">
          <div class="modal-header warning">⚠️ 风格调整警告</div>
          <div class="modal-body">
            <p>AI 检测到调整后的风格存在潜在问题：</p>
            <ul>
              <li v-for="(w, i) in refineWarnings" :key="i">{{ w }}</li>
            </ul>
            <p>这可能会影响演示文稿的可读性。是否仍要应用此修改？</p>
          </div>
          <div class="modal-footer">
            <button class="btn" @click="cancelRefine">取消修改</button>
            <button class="btn danger" @click="confirmRefine">确认应用 (风险)</button>
          </div>
        </div>
      </div>
      
      <!-- 样例幻灯片 -->
      <div v-if="styleSamples && styleSamples.length" class="samples-section">
        <div class="h4">样例幻灯片预览</div>
        <div class="samples-grid">
          <div class="sample-slide" v-for="(slide, idx) in styleSamples" :key="idx"
               :style="{ 
                 background: styleConfig.color.background,
                 color: styleConfig.color.text,
                 fontFamily: styleConfig.font.body_family
               }">
            <div class="slide-header" :style="{ borderBottom: `2px solid ${styleConfig.color.primary}` }">
              <span class="slide-kind">{{ slide.kind }}</span>
            </div>
            <div class="slide-title" :style="{ 
              color: styleConfig.color.primary, 
              fontFamily: getFontStack(styleConfig.font.title_family),
              fontSize: `${Math.min(styleConfig.font.title_size / 2.5, 18)}px`
            }">
              {{ slide.title }}
            </div>
            <ul class="slide-bullets">
              <li v-for="(bullet, bIdx) in slide.bullets" :key="bIdx">{{ bullet }}</li>
            </ul>
            <div class="slide-notes" v-if="slide.notes" :style="{ color: styleConfig.color.muted }">
              备注: {{ slide.notes }}
            </div>
          </div>
        </div>
      </div>
      
      <JsonBlock title="style_config.json" :value="styleConfig" filename="style_config.json" />
    </section>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useWorkflow } from '../composables/useWorkflow'
import { testCases } from '../composables/testCases'
import ApiConfig from '../components/common/ApiConfig.vue'
import JsonBlock from '../components/common/JsonBlock.vue'
import CacheStatus from '../components/common/CacheStatus.vue'

const { 
  busy, err, currentStep, needUserInput, questions, answers, 
  teachingRequest, styleConfig, styleSamples, sessionId, reset, runWorkflow,
  // V3: 缓存相关
  stepCache, loadFromCache, hasCache 
} = useWorkflow()

// V3: 缓存加载状态
const cacheLoaded = ref(false)

// V3: 处理使用缓存的事件
function handleUseCache(stepId) {
  console.log('[Module32] 使用缓存:', stepId)
  
  if (stepId === '3.1' && hasCache('3.1')) {
    // 加载 3.1 缓存到当前状态
    teachingRequest.value = loadFromCache('3.1')
    cacheLoaded.value = true
    currentStep.value = '✅ 已加载 3.1 缓存，可点击下方按钮运行风格设计'
  }
}

// Template state
const selectedTemplate = ref('business')
const templates = [
  { id: 'business', name: '商务专业', desc: '整洁权威，适合汇报', icon: '👔', previewColor: '#1e3a8a' },
  { id: 'tech', name: '现代科技', desc: '深色极客，适合技术', icon: '💻', previewColor: '#0f172a' },
  { id: 'consulting', name: '咨询精英', desc: '极简黑白，逻辑清晰', icon: '📊', previewColor: '#ffffff' },
  { id: 'flow', name: '流程演示', desc: '色彩鲜明，强调步骤', icon: '🌊', previewColor: '#ecfdf5' },
]

// V3: 基于缓存运行风格设计
async function runStyleFromCache() {
  if (!teachingRequest.value) {
    err.value = '未加载缓存，无法运行'
    return
  }
  try {
    // 直接调用 3.2，使用已载入的 teachingRequest
    await runWorkflow({ 
        stop_at: '3.2', 
        _continue_to_3_2: true,
        style_name: selectedTemplate.value 
    })
    cacheLoaded.value = false  // 运行后重置状态
  } catch (e) {
    err.value = e.message
  }
}

const testCaseList = testCases
const rawText = ref('')

// --- Style Refinement State ---
const refineText = ref('')
const refineBusy = ref(false)
const styleHistory = ref([])  // For undo functionality
const showRefineWarning = ref(false)
const refineWarnings = ref([])
const pendingRefineConfig = ref(null)

const orderedColorKeys = ['primary', 'secondary', 'accent', 'muted', 'text', 'background', 'surface', 'warning', 'background_gradient']
const colorLabels = {
  primary: '主色',
  secondary: '辅助色',
  accent: '强调色',
  muted: '弱化色',
  text: '文本色',
  background: '背景色',
  surface: '卡片色',
  warning: '警示色',
  background_gradient: '背景渐变'
}

function getShadowStyle(shadowType) {
    if (shadowType === 'soft') return '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
    if (shadowType === 'hard') return '4px 4px 0px 0px rgba(0,0,0,0.2)'
    return 'none'
}

// Simple logic to decide text color on color chips
// 字体栈映射，确保中文字体有备选方案
const FONT_STACK_MAP = {
  '黑体': '"SimHei", "Heiti SC", "Microsoft YaHei", sans-serif',
  'SimHei': '"SimHei", "Heiti SC", "Microsoft YaHei", sans-serif',
  '宋体': '"SimSun", "Songti SC", serif',
  'SimSun': '"SimSun", "Songti SC", serif',
  '楷体': '"KaiTi", "Kaiti SC", serif',
  'KaiTi': '"KaiTi", "Kaiti SC", serif',
  '微软雅黑': '"Microsoft YaHei", "PingFang SC", sans-serif',
  'Microsoft YaHei': '"Microsoft YaHei", "PingFang SC", sans-serif',
}

function getFontStack(fontFamily) {
  if (!fontFamily) return 'sans-serif'
  return FONT_STACK_MAP[fontFamily] || `"${fontFamily}", sans-serif`
}

function getTextColor(hexColor) {
  if (!hexColor || typeof hexColor !== 'string' || !hexColor.startsWith('#')) return '#000'
  const hex = hexColor.replace('#', '')
  const r = parseInt(hex.substr(0, 2), 16)
  const g = parseInt(hex.substr(2, 2), 16)
  const b = parseInt(hex.substr(4, 2), 16)
  const yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000
  return (yiq >= 128) ? '#000' : '#fff'
}

async function runStyle() {
  try {
    await runWorkflow({ 
        user_text: rawText.value, 
        stop_at: '3.2',
        style_name: selectedTemplate.value
    })
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
      stop_at: '3.2',
      style_name: selectedTemplate.value
    })
  } catch (e) {
    err.value = e.message
  }
}

// --- Style Refinement Handlers ---
async function handleRefine() {
  if (!refineText.value.trim() || refineBusy.value) return
  
  refineBusy.value = true
  try {
    // Save current state for undo
    if (styleConfig.value) {
      styleHistory.value.push(JSON.parse(JSON.stringify(styleConfig.value)))
    }
    
    const res = await fetch(`http://localhost:8000/api/workflow/style/refine`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId.value,
        feedback: refineText.value
      })
    })
    const data = await res.json()
    
    if (data.warnings && data.warnings.length > 0) {
      // Show warning dialog
      refineWarnings.value = data.warnings
      pendingRefineConfig.value = data.style_config
      showRefineWarning.value = true
    } else {
      // Apply new config directly
      styleConfig.value = data.style_config
      styleSamples.value = data.style_samples || []
      refineText.value = ''
    }
  } catch (e) {
    err.value = e.message
  } finally {
    refineBusy.value = false
  }
}

async function undoStyle() {
  if (styleHistory.value.length === 0) return
  const previousConfig = styleHistory.value.pop()
  styleConfig.value = previousConfig
  
  // 同步撤销状态到后端，确保下次 refine 使用正确的基础配置
  try {
    await fetch(`http://localhost:8000/api/workflow/style/sync`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId.value,
        style_config: previousConfig
      })
    })
  } catch (e) {
    console.warn('Failed to sync undo to backend:', e)
    // 即使同步失败，本地撤销仍然生效
  }
}

function cancelRefine() {
  showRefineWarning.value = false
  refineWarnings.value = []
  pendingRefineConfig.value = null
  // Pop the history entry we added
  if (styleHistory.value.length > 0) {
    styleHistory.value.pop()
  }
}

function confirmRefine() {
  if (pendingRefineConfig.value) {
    styleConfig.value = pendingRefineConfig.value
    refineText.value = ''
  }
  showRefineWarning.value = false
  refineWarnings.value = []
  pendingRefineConfig.value = null
}
</script>

<style scoped>
/* 模块页面容器 */
.module-page {
  --color-module: var(--color-32);
  --color-module-light: var(--color-32-light);
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
  background: linear-gradient(135deg, var(--color-module) 0%, #38BDF8 100%);
  color: var(--text-inverse);
  padding: var(--spacing-2) var(--spacing-4);
  border-radius: var(--radius-lg);
  font-weight: var(--font-weight-black);
  font-size: var(--font-size-lg);
  flex-shrink: 0;
  box-shadow: 0 4px 6px -1px rgba(14, 165, 233, 0.3);
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

.cache-info { display: flex; flex-wrap: wrap; gap: var(--spacing-4); margin-bottom: var(--spacing-3); }
.cache-info .info-item { display: flex; gap: var(--spacing-2); }
.cache-info .label { color: var(--text-secondary); font-size: var(--font-size-sm); }
.cache-info .value { font-weight: var(--font-weight-semibold); font-size: var(--font-size-sm); color: var(--color-success); }

.h3 {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  margin: 0 0 var(--spacing-4) 0;
}

.h4 {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  margin: var(--spacing-4) 0 var(--spacing-2);
  color: var(--text-primary);
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

/* 风格信息 */
.style-info {
  display: flex;
  gap: var(--spacing-6);
  margin-bottom: var(--spacing-4);
  padding-bottom: var(--spacing-4);
  border-bottom: 1px dashed var(--border-light);
}

.info-item { display: flex; flex-direction: column; gap: var(--spacing-1); }
.info-item .label { font-size: var(--font-size-xs); color: var(--text-secondary); }
.info-item .value { font-weight: var(--font-weight-semibold); font-size: var(--font-size-base); }

.style-preview { margin-bottom: var(--spacing-4); }
.color-palette { display: flex; flex-wrap: wrap; gap: var(--spacing-3); }
.color-item {
  width: 100px;
  height: 60px;
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-xs);
  border: 1px solid rgba(0,0,0,0.05);
}
.color-label { font-weight: var(--font-weight-bold); opacity: 0.9; }
.color-value { opacity: 0.8; font-family: var(--font-mono); }

/* 样例幻灯片 */
.samples-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: var(--spacing-4);
}

.sample-slide {
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: var(--spacing-4);
  aspect-ratio: 16/9;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: var(--shadow-card);
  font-size: var(--font-size-xs);
}

.slide-header { display: flex; justify-content: space-between; margin-bottom: var(--spacing-2); padding-bottom: var(--spacing-1); }
.slide-kind { font-size: var(--font-size-xs); text-transform: uppercase; opacity: 0.6; }
.slide-title { font-size: var(--font-size-base); font-weight: var(--font-weight-bold); margin-bottom: var(--spacing-2); line-height: var(--line-height-snug); }
.slide-bullets { padding-left: var(--spacing-4); margin: 0; flex: 1; }
.slide-bullets li { margin-bottom: var(--spacing-1); }
.slide-notes { margin-top: auto; font-size: var(--font-size-xs); border-top: 1px dashed var(--border-light); padding-top: var(--spacing-1); }

/* 测试案例按钮组 */
.test-cases {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
}

/* 模版选择网格 */
.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--spacing-4);
  margin-top: var(--spacing-4);
}

.template-card {
  border: 2px solid transparent;
  border-radius: var(--radius-lg);
  background: var(--bg-card);
  overflow: hidden;
  cursor: pointer;
  transition: all var(--duration-fast);
  position: relative;
  box-shadow: var(--shadow-sm);
}

.template-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
}

.template-card.active {
  border-color: var(--color-brand);
  box-shadow: 0 0 0 2px var(--color-brand-light);
}

.tpl-preview {
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
}

.tpl-info {
  padding: var(--spacing-3);
}

.tpl-name {
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-1);
}

.tpl-desc {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

.active-badge {
  position: absolute;
  top: var(--spacing-2);
  right: var(--spacing-2);
  background: var(--color-brand);
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
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
.progress { margin-top: var(--spacing-3); color: var(--color-module); font-weight: var(--font-weight-semibold); animation: pulse 1.5s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
.err { margin-top: var(--spacing-3); color: var(--color-error); font-weight: var(--font-weight-semibold); }

/* 组件应用预览 */
.usage-showcase {
  margin-top: var(--spacing-6);
  padding: var(--spacing-6);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-light);
}

.showcase-label {
  font-size: var(--font-size-xs);
  margin-bottom: var(--spacing-4);
  font-weight: var(--font-weight-bold);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  opacity: 0.5;
}

.showcase-row { display: flex; gap: var(--spacing-6); flex-wrap: wrap; }

.preview-card {
  flex: 1;
  min-width: 240px;
  padding: var(--spacing-5);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.pc-head { font-weight: var(--font-weight-bold); font-size: var(--font-size-lg); line-height: var(--line-height-snug); }
.pc-body { font-size: var(--font-size-base); opacity: 0.8; line-height: var(--line-height-relaxed); }
.pc-muted { font-size: var(--font-size-xs); margin-top: auto; padding-top: var(--spacing-3); border-top: 1px dashed rgba(0,0,0,0.1); }

.preview-group { display: flex; flex-direction: column; gap: var(--spacing-3); min-width: 200px; justify-content: center; }

.preview-alert {
  padding: var(--spacing-3) var(--spacing-4);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  box-shadow: var(--shadow-card);
}

.preview-btn {
  padding: var(--spacing-3) var(--spacing-5);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  text-align: center;
  cursor: pointer;
  box-shadow: var(--shadow-card);
}

.preview-alert .icon { font-size: var(--font-size-lg); }

/* 配色网格 */
.color-palette-grid { display: flex; flex-direction: column; gap: var(--spacing-4); margin-bottom: var(--spacing-6); }
.palette-row { display: flex; flex-wrap: wrap; gap: var(--spacing-3); align-items: stretch; }

.color-group-label {
  writing-mode: vertical-rl;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  text-transform: uppercase;
  letter-spacing: 6px;
  height: auto;
  min-height: 60px;
  text-align: center;
  opacity: 0.6;
  padding: var(--spacing-3) var(--spacing-1);
  display: flex;
  align-items: center;
  justify-content: center;
  border-right: 2px solid rgba(0,0,0,0.05);
  margin-right: var(--spacing-1);
}

.color-item {
  flex: 1;
  min-width: 100px;
  height: 70px;
  border-radius: var(--radius-md);
  position: relative;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.color-item.large { flex: 1.5; min-width: 140px; }
.color-item.wide { flex: 2; min-width: 200px; }

.color-item .color-label { font-size: var(--font-size-xs); opacity: 0.8; margin-top: auto; padding-bottom: var(--spacing-1); }
.color-item .color-value { font-size: var(--font-size-xs); font-weight: var(--font-weight-bold); font-family: var(--font-mono); letter-spacing: 0.5px; }
/* 风格微调区域 */
.refine-section {
  margin-top: var(--spacing-6);
  padding-top: var(--spacing-6);
  border-top: 1px dashed var(--border-light);
}

.refine-box {
  background: linear-gradient(to bottom, var(--bg-input), var(--bg-card));
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  padding: var(--spacing-4);
  box-shadow: var(--shadow-card);
}

.refine-input {
  width: 100%;
  min-height: 80px;
  border: 2px solid transparent;
  border-radius: var(--radius-md);
  padding: var(--spacing-3);
  font-size: var(--font-size-base);
  line-height: var(--line-height-relaxed);
  resize: vertical;
  margin-bottom: var(--spacing-3);
  transition: all var(--duration-fast);
  background: var(--bg-card);
}

.refine-input:focus {
  outline: none;
  border-color: var(--color-brand);
  box-shadow: 0 0 0 var(--focus-ring-width) var(--focus-ring-color);
}

.refine-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.history-actions .icon-btn {
  background: none;
  border: 1px solid transparent;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  padding: var(--spacing-2) var(--spacing-3);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-fast);
}

.history-actions .icon-btn:hover:not(:disabled) {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.history-actions .icon-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.primary-btn {
  background: var(--color-brand);
  color: var(--text-inverse);
  border: none;
  padding: var(--spacing-2) var(--spacing-5);
  border-radius: var(--radius-md);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
  transition: all var(--duration-fast);
}

.primary-btn:hover:not(:disabled) {
  background: var(--color-brand-hover);
  transform: translateY(-1px);
  box-shadow: var(--shadow-elevated);
}

.primary-btn:disabled {
  opacity: 0.7;
  cursor: wait;
}

/* 工具提示 */
.tooltip-container {
  display: inline-block;
  position: relative;
  margin-left: var(--spacing-2);
  cursor: help;
}

.tooltip-icon {
  font-size: var(--font-size-xs);
  background: var(--color-brand-light);
  color: var(--color-brand);
  padding: var(--spacing-1) var(--spacing-2);
  border-radius: var(--radius-full);
  border: 1px solid var(--color-brand-light);
}

.tooltip-content {
  visibility: hidden;
  opacity: 0;
  position: absolute;
  bottom: 150%;
  left: 50%;
  transform: translateX(-50%);
  width: 280px;
  background: var(--text-primary);
  color: var(--text-inverse);
  padding: var(--spacing-3);
  border-radius: var(--radius-md);
  font-size: var(--font-size-xs);
  line-height: var(--line-height-relaxed);
  z-index: var(--z-dropdown);
  transition: all var(--duration-fast);
  box-shadow: var(--shadow-elevated);
}

.tooltip-content::after {
  content: "";
  position: absolute;
  top: 100%;
  left: 50%;
  margin-left: -6px;
  border-width: 6px;
  border-style: solid;
  border-color: var(--text-primary) transparent transparent transparent;
}

.tooltip-container:hover .tooltip-content {
  visibility: visible;
  opacity: 1;
  bottom: 120%;
}

.tooltip-content ul {
  margin: 0;
  padding-left: var(--spacing-4);
  text-align: left;
}

/* 模态框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--modal-backdrop);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  backdrop-filter: blur(4px);
}

.modal {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 480px;
  box-shadow: var(--shadow-elevated);
  overflow: hidden;
  animation: modalPop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes modalPop {
  from { transform: scale(0.9); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

.modal-header.warning {
  background: var(--color-error-light);
  color: var(--color-error);
  padding: var(--spacing-4) var(--spacing-6);
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-lg);
  border-bottom: 1px solid var(--color-error-light);
}

.modal-body {
  padding: var(--spacing-6);
  color: var(--text-primary);
}

.modal-body ul {
  background: var(--color-error-light);
  border: 1px solid var(--color-error);
  border-radius: var(--radius-md);
  padding: var(--spacing-3) var(--spacing-3) var(--spacing-3) var(--spacing-8);
  color: var(--color-error);
  margin: var(--spacing-4) 0;
}

.modal-footer {
  padding: var(--spacing-4) var(--spacing-6);
  background: var(--bg-input);
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-3);
}

.btn.danger {
  background: var(--color-error);
  color: var(--text-inverse);
  border: none;
}

.btn.danger:hover {
  background: #B91C1C;
}
</style>
