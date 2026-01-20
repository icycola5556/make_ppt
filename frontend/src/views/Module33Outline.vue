<template>
  <div class="module-page">
    <div class="module-header">
      <span class="badge">3.3</span>
      <h2>大纲生成模块</h2>
    </div>
    <p class="desc">基于教学需求和风格配置生成PPT结构化大纲</p>

    <ApiConfig />
    
    <!-- V3: 缓存状态展示 -->
    <CacheStatus 
      active-step="3.3" 
      @use-cache="handleUseCache" 
    />

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
        <button class="primary" @click="runOutline" :disabled="busy || outlineGenerator.isExpanding.value || !rawText.trim()">
          {{ (busy || outlineGenerator.isExpanding.value) ? '生成中...' : '运行大纲生成' }}
        </button>
        <button class="btn" @click="reset" :disabled="busy || outlineGenerator.isExpanding.value">重置</button>
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

    <!-- 风格配置结果（非跳过模式）- 完整交互功能 -->
    <!-- 显示条件：有styleConfig且未跳过3.2 -->
    <section v-if="currentStyleConfig && !skipStyle" class="card highlight">
      <div class="h3">3.2 风格配置结果</div>
      
      <div class="style-info" v-if="currentStyleConfig">
        <div class="info-item">
          <span class="label">风格名称：</span>
          <span class="value">{{ currentStyleConfig.style_name }}</span>
        </div>
        <div class="info-item">
          <span class="label">字体：</span>
          <span class="value">{{ currentStyleConfig.font?.title_family }} / {{ currentStyleConfig.font?.body_family }}</span>
        </div>
        <div class="info-item">
          <span class="label">布局密度：</span>
          <span class="value">{{ currentStyleConfig.layout?.density }}</span>
        </div>
      </div>
      
      <!-- 大模型的选择理由或设计思路 -->
      <div v-if="styleReasoning" class="reasoning-box">
        <div class="reasoning-header">
          <span class="reasoning-icon">🤖</span>
          <span class="reasoning-title">AI 设计理由</span>
        </div>
        <div class="reasoning-content">{{ styleReasoning }}</div>
      </div>

      <!-- 风格预览 -->
      <div class="h4">配色方案</div>
      <div class="style-preview" v-if="currentStyleConfig?.color">
        <div class="color-palette-grid">
          <!-- 主色系 -->
          <div class="palette-row">
            <div class="color-group-label" :style="{color: currentStyleConfig.color.muted}">品牌色系</div>
            <div class="color-item large" :style="{ background: currentStyleConfig.color.primary, color: getTextColor(currentStyleConfig.color.primary) }">
                <span class="color-label">主色 Primary</span>
                <span class="color-value">{{ currentStyleConfig.color.primary }}</span>
            </div>
            <div class="color-item" :style="{ background: currentStyleConfig.color.secondary, color: getTextColor(currentStyleConfig.color.secondary) }">
                <span class="color-label">辅助 Secondary</span>
                <span class="color-value">{{ currentStyleConfig.color.secondary }}</span>
            </div>
             <div class="color-item" :style="{ background: currentStyleConfig.color.accent, color: getTextColor(currentStyleConfig.color.accent) }">
                <span class="color-label">强调 Accent</span>
                <span class="color-value">{{ currentStyleConfig.color.accent }}</span>
            </div>
          </div>

          <!-- 功能色系 -->
           <div class="palette-row">
             <div class="color-group-label" :style="{color: currentStyleConfig.color.muted}">功能色系</div>
             <div class="color-item" :style="{ background: currentStyleConfig.color.text, color: getTextColor(currentStyleConfig.color.text) }">
                <span class="color-label">文本 Text</span>
                <span class="color-value">{{ currentStyleConfig.color.text }}</span>
            </div>
             <div class="color-item" :style="{ background: currentStyleConfig.color.muted, color: getTextColor(currentStyleConfig.color.muted) }">
                <span class="color-label">弱化 Muted</span>
                <span class="color-value">{{ currentStyleConfig.color.muted }}</span>
            </div>
             <div class="color-item" :style="{ background: currentStyleConfig.color.warning, color: getTextColor(currentStyleConfig.color.warning) }">
                <span class="color-label">警示 Warning</span>
                <span class="color-value">{{ currentStyleConfig.color.warning }}</span>
            </div>
          </div>

          <!-- 背景色系 -->
           <div class="palette-row">
             <div class="color-group-label" :style="{color: currentStyleConfig.color.muted}">背景色系</div>
             <div class="color-item" :style="{ background: currentStyleConfig.color.background, color: getTextColor(currentStyleConfig.color.background), border: '1px solid #eee' }">
                <span class="color-label">背景 Bkg</span>
                <span class="color-value">{{ currentStyleConfig.color.background }}</span>
            </div>
             <div class="color-item" :style="{ background: currentStyleConfig.color.surface || '#fff', color: getTextColor(currentStyleConfig.color.surface || '#fff'), border: '1px solid #eee' }">
                <span class="color-label">卡片 Surface</span>
                <span class="color-value">{{ currentStyleConfig.color.surface || '-' }}</span>
            </div>
            <div class="color-item wide" v-if="currentStyleConfig.color.background_gradient" :style="{ background: currentStyleConfig.color.background_gradient, color: '#000' }">
                <span class="color-label">渐变 Gradient</span>
            </div>
          </div>
        </div>

        <!-- 组件应用预览 -->
        <div class="usage-showcase" :style="{ background: currentStyleConfig.color.background, fontFamily: currentStyleConfig.font.body_family }">
            <div class="showcase-label" :style="{ color: currentStyleConfig.color.muted }">组件应用预览</div>
            <div class="showcase-row">
                <!-- 1. 卡片与文本层次 -->
                <div class="preview-card" :style="{ 
                    background: currentStyleConfig.color.surface || '#fff', 
                    color: currentStyleConfig.color.text,
                    borderRadius: currentStyleConfig.layout?.border_radius || '0px',
                    boxShadow: getShadowStyle(currentStyleConfig.layout?.box_shadow)
                }">
                    <div class="pc-head" :style="{ color: currentStyleConfig.color.primary, fontFamily: currentStyleConfig.font.title_family }">Card Title</div>
                    <div class="pc-body">Normal text content example.</div>
                    <div class="pc-muted" :style="{ color: currentStyleConfig.color.muted }">Muted info: Secondary text with lower contrast.</div>
                </div>

                <!-- 2. 状态提示 -->
                <div class="preview-group">
                    <div class="preview-alert" :style="{ 
                        background: currentStyleConfig.color.warning, 
                        color: '#fff',
                        borderRadius: currentStyleConfig.layout?.border_radius || '0px'
                    }">
                        <span class="icon">⚠️</span> Warning / Alert Message
                    </div>
                    <div class="preview-btn" :style="{ 
                        background: currentStyleConfig.color.accent, 
                        color: '#fff',
                        borderRadius: currentStyleConfig.layout?.border_radius || '0px'
                    }">
                        Accent Button
                    </div>
                </div>
            </div>
        </div>
      </div>
      
      <!-- 风格微调交互区 (Style Refinement) -->
      <div class="refine-section" v-if="currentStyleConfig">
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
        
        <div class="refine-box">
          <textarea 
            class="refine-input" 
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
            <button class="primary-btn" @click="handleRefine" :disabled="refineBusy || !refineText.trim()">
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
      <div v-if="currentStyleSamples && currentStyleSamples.length" class="samples-section">
        <div class="h4">样例幻灯片预览</div>
        <div class="samples-grid">
          <div class="sample-slide" v-for="(slide, idx) in currentStyleSamples" :key="idx"
               :style="{ 
                 background: currentStyleConfig.color.background,
                 color: currentStyleConfig.color.text,
                 fontFamily: currentStyleConfig.font.body_family
               }">
            <div class="slide-header" :style="{ borderBottom: `2px solid ${currentStyleConfig.color.primary}` }">
              <span class="slide-kind">{{ slide.kind }}</span>
            </div>
            <div class="slide-title" :style="{ 
              color: currentStyleConfig.color.primary, 
              fontFamily: getFontStack(currentStyleConfig.font.title_family),
              fontSize: `${Math.min(currentStyleConfig.font.title_size / 2.5, 18)}px`
            }">
              {{ slide.title }}
            </div>
            <ul class="slide-bullets">
              <li v-for="(bullet, bIdx) in slide.bullets" :key="bIdx">{{ bullet }}</li>
            </ul>
            <div class="slide-notes" v-if="slide.notes" :style="{ color: currentStyleConfig.color.muted }">
              备注: {{ slide.notes }}
            </div>
          </div>
        </div>
      </div>
      
      <JsonBlock title="style_config.json" :value="currentStyleConfig" filename="style_config.json" collapsed />
      
      <!-- 继续到3.3的按钮（完整流程且3.2已完成但3.3未完成时显示） -->
      <!-- 显示条件：有styleConfig但没有outline，且stage=3.2（完整流程模式） -->
      <div v-if="!outline && currentStyleConfig && (sessionState?.stage === '3.2' || (!sessionState && styleConfig)) && !skipStyle" class="continue-section">
        <div class="continue-hint">✨ 风格配置已生成，可以继续生成大纲</div>
        <button class="primary continue-btn" @click="continueToOutline" :disabled="busy || outlineGenerator.isExpanding.value">
          {{ (busy || outlineGenerator.isExpanding.value) ? '生成中...' : '继续生成大纲 (3.3)' }}
        </button>
      </div>
    </section>

    <!-- 大纲结果 -->
    <section v-if="outline" class="card highlight">
      <div class="h3">3.3 PPT大纲结果</div>
      
      <!-- 大纲预览 -->
      <!-- 大纲预览 (Parallel Generation UI) -->
      <div class="outline-preview">
        <div class="outline-header">
            <div class="outline-title">{{ outline.deck_title || outline.title || '未命名大纲' }}</div>
            <div class="slide-count">共 {{ outline.slides?.length || 0 }} 页</div>
        </div>
        
        <!-- Progress Bar for Expansion -->
        <div v-if="outlineGenerator.isExpanding.value || outlineGenerator.progress.value.completed > 0" class="expansion-progress">
             <div class="progress-info">
                <span>生成详情中... {{ outlineGenerator.progress.value.completed }} / {{ outlineGenerator.progress.value.total }}</span>
                <span>{{ outlineGenerator.progress.value.percent }}%</span>
             </div>
             <div class="progress-track">
                <div class="progress-fill" :style="{ width: outlineGenerator.progress.value.percent + '%' }"></div>
             </div>
        </div>

        <div class="slides-list">
          <div v-for="(slide, i) in outline.slides" :key="i" class="slide-item" :class="{ 'is-loading': outlineGenerator.slideStatus[i] === 'loading' }">
            <span class="slide-num">{{ i + 1 }}</span>
            <div class="slide-info">
              <div class="slide-row-1">
                  <span class="slide-type">{{ getSlideTypeLabel(slide.slide_type) }}</span>
                  <span class="slide-title">{{ slide.title }}</span>
                  <!-- Status Icon -->
                  <span class="slide-status-icon">
                      <span v-if="outlineGenerator.slideStatus[i] === 'loading'" class="spin">🔄</span>
                      <span v-else-if="outlineGenerator.slideStatus[i] === 'done'">✅</span>
                      <span v-else-if="outlineGenerator.slideStatus[i] === 'error'" title="生成失败">❌</span>
                  </span>
              </div>
              <span v-if="getSlideTypeDescription(slide.slide_type)" class="slide-desc">{{ getSlideTypeDescription(slide.slide_type) }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <JsonBlock title="outline.json" :value="outline" filename="outline.json" />
      
      <!-- 2-Stage Workflow Entry -->
      <div class="workflow-entry">
        <div class="workflow-hint">✨ 想要编辑大纲或生成详细内容？</div>
        <button class="primary workflow-btn" @click="goToOutlineEditor">
          📋 进入大纲编辑器
        </button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkflow } from '../composables/useWorkflow'
import { useOutlineGenerator } from '../composables/useOutlineGenerator'
import { testCases } from '../composables/testCases'
import ApiConfig from '../components/common/ApiConfig.vue'
import JsonBlock from '../components/common/JsonBlock.vue'
import CacheStatus from '../components/common/CacheStatus.vue'
import { api, getApiBase } from '../api'

const router = useRouter()

const { 
  busy, err, currentStep, needUserInput, questions, answers, 
  teachingRequest, styleConfig, styleSamples, sessionId, sessionState, outline, 
  reset, runWorkflow, availableStyles,
  // V3: 缓存相关
  stepCache, loadFromCache, hasCache 
} = useWorkflow()

const outlineGenerator = useOutlineGenerator()

// Monitor outline updates for generator initialization
watch(outline, (newOutline) => {
    if (newOutline && newOutline.slides && sessionId.value) {
        // If we just got a new outline (structure), init the generator
        // But be careful not to reset if we are already generating
        // We can check if status is empty
        if (Object.keys(outlineGenerator.slideStatus).length === 0) {
            outlineGenerator.initForStructure(newOutline.slides, sessionId.value)
        }
    }
})

// V3: 处理使用缓存的事件
function handleUseCache(stepId) {
  console.log('[Module33] 使用缓存:', stepId)
  
  if (stepId === '3.1' && hasCache('3.1')) {
    // 加载 3.1 缓存到当前状态
    teachingRequest.value = loadFromCache('3.1')
    currentStep.value = '✅ 已加载 3.1 缓存，可继续执行 3.2 或 3.3'
  }
  
  if (stepId === '3.2' && hasCache('3.2')) {
    // 加载 3.2 缓存（包含 3.1）
    if (hasCache('3.1')) {
      teachingRequest.value = loadFromCache('3.1')
    }
    const cache32 = loadFromCache('3.2')
    styleConfig.value = cache32.styleConfig
    styleSamples.value = cache32.styleSamples || []
    currentStep.value = '✅ 已加载 3.1+3.2 缓存，可直接执行 3.3'
  }
  
  if (stepId === '3.3' && hasCache('3.3')) {
    // 加载 3.3 缓存（包含 3.1+3.2）
    if (hasCache('3.1')) {
      teachingRequest.value = loadFromCache('3.1')
    }
    if (hasCache('3.2')) {
      const cache32 = loadFromCache('3.2')
      styleConfig.value = cache32.styleConfig
      styleSamples.value = cache32.styleSamples || []
    }
    outline.value = loadFromCache('3.3')
    currentStep.value = '✅ 已加载完整大纲缓存'
  }
}

const testCaseList = testCases
const rawText = ref('')
const skipStyle = ref(false)
const styleName = ref('theory_clean')


async function runOutline() {
    // Clear previous errors/state
    err.value = null
    outline.value = null
    
    try {
        busy.value = true
        
        // Check if we need to run 3.1/3.2 first, or just generate outline
        const needsSetup = !sessionId.value || (!styleConfig.value && !skipStyle.value)
        
        if (needsSetup) {
            // Need rawText for initial setup
            if (!rawText.value.trim()) {
                err.value = '请先输入课程需求'
                return
            }
            
            const stopAt = skipStyle.value ? '3.1' : '3.2'
            
            // Use composable's runWorkflow which handles session creation
            await runWorkflow({
                user_text: rawText.value,
                answers: answers.value,
                auto_fill_defaults: true, 
                stop_at: stopAt
            })
            
            if (needUserInput.value) {
                busy.value = false
                return // Wait for user input
            }
        }
        
        // If we reached here, 3.1/3.2 are done. Start 3.3 parallel generation.
        await generateParallelOutline()
        
    } catch (e) {
        err.value = e.message
    } finally {
        busy.value = false
    }
}

async function submitAnswers(useDefaults) {
    try {
        busy.value = true
        const stopAt = skipStyle.value ? '3.1' : '3.2'
        
        await runWorkflow({
            user_text: rawText.value,
            answers: useDefaults ? {} : answers.value,
            auto_fill_defaults: useDefaults,
            stop_at: stopAt
        })
        
        if (needUserInput.value) {
             busy.value = false
             return // Still need input (e.g. multi-round)
        }
        
        // If Q&A finished, proceed to generation
        await generateParallelOutline()
        
    } catch (e) {
        err.value = e.message
    } finally {
        busy.value = false
    }
}

async function generateParallelOutline() {
    currentStep.value = '阶段 2: 正在生成大纲结构...'
    
    // Call Structure Endpoint
    const structRes = await api.generateOutlineStructure(sessionId.value, skipStyle.value ? null : styleName.value)
    
    if (structRes.ok && structRes.outline) {
        outline.value = structRes.outline
        currentStep.value = '阶段 3: 正在并行扩展详情...'
        
        // Init Generator
        outlineGenerator.initForStructure(outline.value.slides, sessionId.value)
        
        // Run Expansion (this updates backend session state)
        await outlineGenerator.expandAllSlides(5) // Concurrency 5
        
        // Reload session to get updated outline with bullets
        await refreshState()
        
        currentStep.value = '✅ 大纲生成完成'
    } else {
        err.value = structRes.error || '大纲结构生成失败'
    }
}

async function refreshState() {
    if(!sessionId.value) return
    const s = await api.getSession(sessionId.value)
    if(s) {
        sessionState.value = s
        teachingRequest.value = s.teaching_request
        if(s.style_config) styleConfig.value = s.style_config
        if(s.outline) outline.value = s.outline
    }
}

// Override or redirect the original continueToOutline if needed
async function continueToOutline() {
    await runOutline()
}

// Other existing functions...
// --- Style Refinement State (3.2交互功能) ---
const refineText = ref('')
const refineBusy = ref(false)
const styleHistory = ref([])  // For undo functionality
const showRefineWarning = ref(false)
const refineWarnings = ref([])
const pendingRefineConfig = ref(null)
const styleReasoning = ref('')  // 大模型的选择理由或设计思路

// slide_type 数据（从API加载）
const slideTypesData = ref(null)
const slideTypeMap = computed(() => {
  if (!slideTypesData.value) return {}
  const map = {}
  for (const st of slideTypesData.value.slide_types || []) {
    map[st.slide_type] = {
      name: st.name,
      description: st.description,
      instruction: st.instruction
    }
  }
  return map
})

// 计算当前的styleConfig（优先使用响应中的，其次使用sessionState中的）
const currentStyleConfig = computed(() => {
  return styleConfig.value || sessionState.value?.style_config || null
})

// 计算当前的styleSamples（优先使用响应中的，其次使用sessionState中的）
const currentStyleSamples = computed(() => {
  return styleSamples.value && styleSamples.value.length > 0 
    ? styleSamples.value 
    : (sessionState.value?.style_samples || [])
})

// 监听sessionState变化，确保styleConfig和styleSamples同步更新
watch(sessionState, (newState) => {
  if (newState) {
    // 如果响应中没有styleConfig，但从sessionState中获取到了，则更新
    if (!styleConfig.value && newState.style_config) {
      styleConfig.value = newState.style_config
    }
    if ((!styleSamples.value || styleSamples.value.length === 0) && newState.style_samples) {
      styleSamples.value = newState.style_samples
    }
  }
}, { deep: true })

// 加载slide_type数据
onMounted(async () => {
  try {
    slideTypesData.value = await api.getSlideTypes()
  } catch (e) {
    console.error('Failed to load slide types:', e)
    // 降级到硬编码的映射
    slideTypesData.value = { slide_types: [] }
  }
})

function getSlideTypeLabel(type) {
  return slideTypeMap.value[type]?.name || type
}

function getSlideTypeDescription(type) {
  return slideTypeMap.value[type]?.description || ''
}

// --- Style Helper Functions (3.2交互功能) ---
function getTextColor(hexColor) {
  if (!hexColor || typeof hexColor !== 'string' || !hexColor.startsWith('#')) return '#000'
  const hex = hexColor.replace('#', '')
  const r = parseInt(hex.substr(0, 2), 16)
  const g = parseInt(hex.substr(2, 2), 16)
  const b = parseInt(hex.substr(4, 2), 16)
  const yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000
  return (yiq >= 128) ? '#000' : '#fff'
}

function getShadowStyle(shadowType) {
    if (shadowType === 'soft') return '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
    if (shadowType === 'hard') return '4px 4px 0px 0px rgba(0,0,0,0.2)'
    return 'none'
}

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

// --- Style Refinement Handlers (3.2交互功能) ---
async function handleRefine() {
  if (!refineText.value.trim() || refineBusy.value) return
  
  refineBusy.value = true
  try {
    // Save current state for undo
    if (currentStyleConfig.value) {
      styleHistory.value.push(JSON.parse(JSON.stringify(currentStyleConfig.value)))
    }
    
    const base = getApiBase()
    const res = await fetch(`${base}/api/workflow/style/refine`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId.value,
        feedback: refineText.value
      })
    })
    const data = await res.json()
    
    // 保存大模型的理由
    if (data.reasoning) {
      styleReasoning.value = data.reasoning
    }
    
    if (data.warnings && data.warnings.length > 0) {
      // Show warning dialog
      refineWarnings.value = data.warnings
      pendingRefineConfig.value = data.style_config
      showRefineWarning.value = true
      // 如果有理由，也保存到 pending 中
      if (data.reasoning) {
        styleReasoning.value = data.reasoning
      }
    } else {
      // Apply new config directly
      styleConfig.value = data.style_config
      if (data.style_samples && data.style_samples.length > 0) {
        styleSamples.value = data.style_samples
      }
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
    const base = getApiBase()
    await fetch(`${base}/api/workflow/style/sync`, {
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
  // 保留 reasoning，因为已经应用了配置
}



function goToOutlineEditor() {
  router.push('/outline-editor')
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
.slide-item { display: flex; align-items: flex-start; gap: 10px; padding: 8px 0; border-bottom: 1px solid #e5e7eb; }
.slide-num { background: #7c3aed; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600; flex-shrink: 0; }
.slide-info { display: flex; flex-direction: column; gap: 4px; flex: 1; }
.slide-type { color: #7c3aed; font-size: 12px; font-weight: 600; }
.slide-title { font-weight: 500; color: #1e293b; }
.slide-desc { color: #6b7280; font-size: 11px; line-height: 1.4; }
.test-cases { display: flex; gap: 8px; align-items: center; margin: 12px 0; flex-wrap: wrap; }
.test-btn { padding: 6px 12px; border: 1px dashed #9ca3af; border-radius: 6px; background: #f9fafb; cursor: pointer; font-size: 12px; }
.test-btn:hover { border-color: #7c3aed; background: #f5f3ff; color: #7c3aed; }
.label { font-weight: 600; font-size: 13px; }
.progress { margin-top: 12px; color: #7c3aed; font-weight: 600; animation: pulse 1.5s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
.err { margin-top: 10px; color: #b91c1c; font-weight: 600; }

/* 继续到3.3的按钮样式 */
.continue-section {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 2px dashed #e2e8f0;
  text-align: center;
}
.continue-hint {
  color: #6b7280;
  font-size: 14px;
  margin-bottom: 16px;
}
.continue-btn {
  font-size: 16px;
  padding: 12px 24px;
  min-width: 200px;
}

/* 3.2 风格配置样式 */
.h4 { font-size: 14px; font-weight: 600; margin: 16px 0 8px; color: #374151; }
.style-info { display: flex; gap: 24px; margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px dashed #e5e7eb; }
.info-item { display: flex; flex-direction: column; gap: 4px; }
.info-item .label { font-size: 12px; color: #6b7280; }
.info-item .value { font-weight: 600; font-size: 14px; }

.style-preview { margin-bottom: 16px; }
.color-palette-grid { display: flex; flex-direction: column; gap: 16px; margin-bottom: 24px; }
.palette-row { display: flex; flex-wrap: wrap; gap: 12px; align-items: stretch; }
.color-group-label { 
    writing-mode: vertical-rl; 
    font-size: 12px; 
    font-weight: 700; 
    text-transform: uppercase; 
    letter-spacing: 6px;
    height: auto;
    min-height: 60px;
    text-align: center;
    opacity: 0.6;
    padding: 10px 4px;
    display: flex; align-items: center; justify-content: center;
    border-right: 2px solid rgba(0,0,0,0.05);
    margin-right: 4px;
}
.color-item { 
    flex: 1; 
    min-width: 100px; 
    height: 70px; 
    border-radius: 10px; 
    position: relative;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    border: 1px solid rgba(0,0,0,0.05);
}
.color-item.large { flex: 1.5; min-width: 140px; }
.color-item.wide { flex: 2; min-width: 200px; }
.color-item .color-label { font-size: 10px; opacity: 0.8; margin-top: auto; padding-bottom: 4px; font-weight: 700; }
.color-item .color-value { font-size: 12px; font-weight: 700; font-family: monospace; letter-spacing: 0.5px; opacity: 0.8; }

.usage-showcase { margin-top: 24px; padding: 24px; border-radius: 12px; border: 1px solid rgba(0,0,0,0.06); }
.showcase-label { font-size: 11px; margin-bottom: 16px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.5; }
.showcase-row { display: flex; gap: 24px; flex-wrap: wrap; }
.preview-card {
  flex: 1;
  min-width: 240px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.pc-head { font-weight: 700; font-size: 18px; line-height: 1.3; }
.pc-body { font-size: 14px; opacity: 0.8; line-height: 1.5; }
.pc-muted { font-size: 12px; margin-top: auto; padding-top: 12px; border-top: 1px dashed rgba(0,0,0,0.1); }

.preview-group { display: flex; flex-direction: column; gap: 12px; min-width: 200px; justify-content: center; }
.preview-alert {
  padding: 12px 16px;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}
.preview-btn {
  padding: 12px 20px;
  font-size: 13px;
  font-weight: 600;
  text-align: center;
  cursor: pointer;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}
.preview-alert .icon { font-size: 16px; }

/* Refinement Section */
.refine-section {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px dashed #e2e8f0;
}

.refine-box {
  background: linear-gradient(to bottom, #f8fafc, #fff);
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.refine-input {
  width: 100%;
  min-height: 80px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 12px;
  font-size: 14px;
  line-height: 1.6;
  resize: vertical;
  margin-bottom: 12px;
  transition: all 0.2s;
  background: #fff;
}

.refine-input:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.refine-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.history-actions .icon-btn {
  background: none;
  border: 1px solid transparent;
  color: #64748b;
  font-size: 13px;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.history-actions .icon-btn:hover:not(:disabled) {
  background: #f1f5f9;
  color: #334155;
}

.history-actions .icon-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.primary-btn {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: white;
  border: none;
  padding: 8px 20px;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(79, 70, 229, 0.2);
  transition: all 0.2s;
}

.primary-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(79, 70, 229, 0.3);
}

.primary-btn:disabled {
  opacity: 0.7;
  cursor: wait;
}

/* Tooltip */
.tooltip-container {
  display: inline-block;
  position: relative;
  margin-left: 8px;
  cursor: help;
}

.tooltip-icon {
  font-size: 12px;
  background: #eff6ff;
  color: #3b82f6;
  padding: 2px 8px;
  border-radius: 12px;
  border: 1px solid #bfdbfe;
}

.tooltip-content {
  visibility: hidden;
  opacity: 0;
  position: absolute;
  bottom: 150%;
  left: 50%;
  transform: translateX(-50%);
  width: 280px;
  background: #1e293b;
  color: #fff;
  padding: 12px;
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.5;
  z-index: 100;
  transition: all 0.2s;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

.tooltip-content::after {
  content: "";
  position: absolute;
  top: 100%;
  left: 50%;
  margin-left: -6px;
  border-width: 6px;
  border-style: solid;
  border-color: #1e293b transparent transparent transparent;
}

.tooltip-container:hover .tooltip-content {
  visibility: visible;
  opacity: 1;
  bottom: 120%;
}

.tooltip-content ul {
  margin: 0;
  padding-left: 16px;
  text-align: left;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 480px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  animation: modalPop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes modalPop {
  from { transform: scale(0.9); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

.modal-header.warning {
  background: #fef2f2;
  color: #dc2626;
  padding: 16px 24px;
  font-weight: 600;
  font-size: 18px;
  border-bottom: 1px solid #fee2e2;
}

.modal-body {
  padding: 24px;
  color: #334155;
}

.modal-body ul {
  background: #fff1f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  padding: 12px 12px 12px 32px;
  color: #be123c;
  margin: 16px 0;
}

.modal-footer {
  padding: 16px 24px;
  background: #f8fafc;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn.danger {
  background: #dc2626;
  color: white;
  border: none;
}
.btn.danger:hover {
  background: #b91c1c;
}

/* Reasoning Box */
.reasoning-box {
  margin-top: 20px;
  padding: 16px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border: 1px solid #bae6fd;
  border-radius: 8px;
  border-left: 4px solid #0ea5e9;
}

.reasoning-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 600;
  color: #0369a1;
  font-size: 14px;
}

.reasoning-icon {
  font-size: 18px;
}

.reasoning-title {
  font-size: 15px;
}

.reasoning-content {
  color: #0c4a6e;
  line-height: 1.6;
  font-size: 14px;
  white-space: pre-wrap;
  word-break: break-word;
}

/* Samples Section */
.samples-section {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px dashed #e2e8f0;
}

.samples-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }
.sample-slide { border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; aspect-ratio: 16/9; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); font-size: 12px; }
.slide-header { display: flex; justify-content: space-between; margin-bottom: 8px; padding-bottom: 4px; }
.slide-kind { font-size: 10px; text-transform: uppercase; opacity: 0.6; }
.slide-title { font-size: 14px; font-weight: bold; margin-bottom: 8px; line-height: 1.3; }
.slide-bullets { padding-left: 16px; margin: 0; flex: 1; }
.slide-bullets li { margin-bottom: 4px; }
.slide-notes { margin-top: auto; font-size: 10px; border-top: 1px dashed #ccc; padding-top: 4px; }

/* 2-Stage Workflow Entry Styles */
.workflow-entry {
  margin-top: 24px;
  padding: 24px;
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  border-radius: 12px;
  text-align: center;
  border: 1px solid #c7d2fe;
}

.workflow-hint {
  font-size: 16px;
  font-weight: 600;
  color: #4f46e5;
  margin-bottom: 16px;
}

/* Parallel Generation Styles */
.expansion-progress {
  padding: 12px 16px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 8px;
  border-radius: 8px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
}

.progress-track {
  height: 6px;
  background: #cbd5e1;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #a855f7);
  transition: width 0.3s ease;
}

.slide-row-1 {
    display: flex;
    justify-content: flex-start;
    align-items: center;
    width: 100%;
    gap: 8px;
}

.slide-status-icon {
    margin-left: auto;
    font-size: 14px;
}

.spin {
    display: inline-block;
    animation: spin 1s linear infinite;
}

.slide-item.is-loading {
    background: #f8fafc;
    border-color: #c7d2fe;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.workflow-btn {
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 600;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.4);
}

.workflow-btn:hover {
  background: #4f46e5;
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.4);
}
</style>
