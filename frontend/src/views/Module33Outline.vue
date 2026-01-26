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
      class="glass-card"
      @use-cache="handleUseCache" 
    />

    <!-- 输入区 -->
    <section class="glass-card">
      <div class="h3">
        <span class="icon">📝</span>
        输入需求
      </div>
      <textarea class="textarea hover-lift" v-model="rawText" placeholder="例如：给我一个机械专业「液压传动原理」的理论课课件，10页左右"></textarea>
      
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
        <button class="primary hover-lift" @click="runOutline" :disabled="busy || outlineGenerator.isExpanding.value || !rawText.trim()">
          {{ (busy || outlineGenerator.isExpanding.value) ? '生成中...' : '✨ 运行大纲生成' }}
        </button>
        <button class="btn" @click="reset" :disabled="busy || outlineGenerator.isExpanding.value">重置</button>
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
      <JsonBlock title="teaching_request.json" :value="teachingRequest" collapsed />
    </section>

    <!-- 风格配置结果（非跳过模式）- 完整交互功能 -->
    <!-- 显示条件：有styleConfig且未跳过3.2 -->
    <section v-if="currentStyleConfig && !skipStyle" class="glass-card highlight">
      <div class="h3">
        <span class="icon">🎨</span>
        3.2 风格配置结果
      </div>
      
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
        <div class="usage-showcase glass-card" :style="{ background: currentStyleConfig.color.background, fontFamily: currentStyleConfig.font.body_family }">
            <div class="showcase-label" :style="{ color: currentStyleConfig.color.muted }">组件应用预览</div>
            <div class="showcase-row">
                <!-- 1. 卡片与文本层次 -->
                <div class="preview-card card-tilted" :style="{ 
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
                    <div class="preview-btn pulse-accent" :style="{ 
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
        <div class="modal glass-card">
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
        <button class="primary continue-btn hover-lift" @click="continueToOutline" :disabled="busy || outlineGenerator.isExpanding.value">
          {{ (busy || outlineGenerator.isExpanding.value) ? '生成中...' : '继续生成大纲 (3.3)' }}
        </button>
      </div>
    </section>

    <!-- 大纲结果 -->
    <section v-if="outline" class="glass-card highlight">
      <div class="h3">
        <span class="icon">📑</span>
        3.3 PPT大纲结果
      </div>
      
      <!-- 大纲预览 (Parallel Generation UI) -->
      <div class="outline-preview">
        <div class="outline-header">
            <div class="outline-title text-gradient">{{ outline.deck_title || outline.title || '未命名大纲' }}</div>
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
          <div v-for="(slide, i) in outline.slides" :key="i" class="slide-item hover-lift" :class="{ 'is-loading': outlineGenerator.slideStatus[i] === 'loading' }">
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
        <button class="primary workflow-btn hover-lift" @click="goToOutlineEditor">
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
    const structRes = await api.generateOutlineStructure(sessionId.value, skipStyle.value ? styleName.value : styleConfig.value?.style_name)
    
    if (structRes.ok && structRes.outline) {
        outline.value = structRes.outline
        currentStep.value = '阶段 3: 正在并行扩展详情...'
        
        // Init Generator
        outlineGenerator.initForStructure(outline.value.slides, sessionId.value)
        
        // Run Expansion (this updates backend session state)
        await outlineGenerator.expandAllSlides(5) // Concurrency 5
        
        // 扩展完成后，进行assets后处理（生成描述、补充字段）
        currentStep.value = '阶段 4: 正在处理图片资源...'
        try {
            const postProcessRes = await api.postProcessOutline(sessionId.value)
            if (postProcessRes.ok && postProcessRes.outline) {
                outline.value = postProcessRes.outline
            }
        } catch (e) {
            console.warn('Assets后处理失败:', e)
            // 即使后处理失败，也继续流程
        }
        
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

// 前端兜底映射：即使 API 数据缺失，也能正确显示中文
const SLIDE_TYPE_FALLBACK_MAP = {
  'intro': '导入',
  'cover': '封面', 
  'title': '封面',
  'objectives': '目标',
  'concept': '概念',
  'content': '内容',
  'steps': '步骤',
  'practice': '实践',
  'comparison': '对比',
  'case': '案例',
  'case_compare': '案例对比',
  'tools': '工具',
  'summary': '总结',
  'bridge': '过渡',
  'transition': '过渡',
  'agenda': '议程',
  'qa': '问答',
  'exercise': '练习',
  'exercises': '练习',
  'discussion': '讨论',
  'warning': '注意',
  'reference': '参考',
  'principle': '原理',
  'process': '流程',
  'structure': '结构',
  'chart': '图表',
  'data': '数据',
  'map': '地图',
  'appendix': '附录',
  'subtitle': '副标题',
}

function getSlideTypeLabel(type) {
  // 1. 优先使用 API 返回的映射
  if (slideTypeMap.value[type]?.name) {
    return slideTypeMap.value[type].name
  }
  // 2. 使用前端硬编码的 fallback 映射
  if (SLIDE_TYPE_FALLBACK_MAP[type]) {
    return SLIDE_TYPE_FALLBACK_MAP[type]
  }
  // 3. 最终 fallback: 显示通用标签 "页面"（不显示英文）
  return '页面'
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
/* 模块页面容器 */
.module-page {
  --color-module: var(--color-33);
  --color-module-light: var(--color-33-light);
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
  background: linear-gradient(135deg, var(--color-module) 0%, #A78BFA 100%);
  color: var(--text-inverse);
  padding: var(--spacing-2) var(--spacing-4);
  border-radius: var(--radius-lg);
  font-weight: var(--font-weight-black);
  font-size: var(--font-size-lg);
  flex-shrink: 0;
  box-shadow: 0 4px 6px -1px rgba(139, 92, 246, 0.3);
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

/* 标题样式 */
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

/* 大纲生成特有样式 */
.mode-select {
  display: flex;
  gap: var(--spacing-4);
  margin: var(--spacing-3) 0;
  background: var(--bg-input);
  padding: var(--spacing-2);
  border-radius: var(--radius-md);
}

.mode-option {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  cursor: pointer;
  padding: var(--spacing-2) var(--spacing-3);
  border-radius: var(--radius-md);
  transition: background var(--duration-fast);
}

.mode-option:hover {
  background: var(--bg-card);
}

.style-name-input { display: flex; align-items: center; gap: var(--spacing-3); margin-bottom: var(--spacing-3); }
.select { width: auto; min-width: 200px; }

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

/* AI 理由展示框 */
.reasoning-box {
  background-color: var(--bg-input);
  border-radius: var(--radius-md);
  padding: var(--spacing-4);
  margin-bottom: var(--spacing-6);
  border-left: 4px solid var(--color-brand);
}

.reasoning-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-2);
}

.reasoning-icon { font-size: 1.2em; }
.reasoning-title { font-weight: var(--font-weight-bold); color: var(--text-primary); font-size: var(--font-size-sm); }
.reasoning-content { color: var(--text-secondary); font-size: var(--font-size-sm); line-height: 1.6; }


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

/* 大纲预览 */
.outline-preview {
  margin-bottom: var(--spacing-4);
}

.outline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-4);
  padding-bottom: var(--spacing-4);
  border-bottom: 2px solid var(--border-light);
}

.outline-title { font-size: var(--font-size-xl); font-weight: var(--font-weight-bold); }
.slide-count { font-size: var(--font-size-sm); color: var(--text-secondary); background: var(--bg-input); padding: 4px 8px; border-radius: 12px; }

/* Expansion Progress */
.expansion-progress { margin-bottom: var(--spacing-4); background: var(--bg-input); padding: var(--spacing-3); border-radius: var(--radius-md); border: 1px solid var(--border-light); }
.progress-info { display: flex; justify-content: space-between; font-size: var(--font-size-xs); margin-bottom: var(--spacing-2); color: var(--text-secondary); font-weight: 600; }
.progress-track { height: 6px; background: var(--border-light); border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; background: var(--color-success); transition: width 0.3s ease; }

.slides-list { display: flex; flex-direction: column; gap: var(--spacing-3); }
.slide-item { display: flex; gap: var(--spacing-3); padding: var(--spacing-3); border: 1px solid var(--border-light); border-radius: var(--radius-md); background: var(--bg-card); transition: all 0.2s; }
.slide-item:hover { border-color: var(--color-module); box-shadow: var(--shadow-sm); }
.slide-item.is-loading { border-color: var(--color-warning); background: var(--color-warning-light); }
.slide-num { width: 24px; height: 24px; background: var(--bg-input); color: var(--text-muted); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: var(--font-size-xs); font-weight: bold; flex-shrink: 0; }
.slide-info { flex: 1; display: flex; flex-direction: column; gap: 4px; }
.slide-row-1 { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.slide-type { font-size: var(--font-size-xs); background: var(--color-module-light); color: var(--color-module); padding: 2px 6px; border-radius: 4px; font-weight: 500; }
.slide-title { font-weight: var(--font-weight-bold); font-size: var(--font-size-base); }
.slide-status-icon { margin-left: auto; font-size: 14px; }
.spin { display: inline-block; animation: spin 1s linear infinite; }
@keyframes spin { 100% { transform: rotate(360deg); } }
.slide-desc { font-size: var(--font-size-sm); color: var(--text-secondary); }

/* Workflow Entry */
.workflow-entry { margin-top: var(--spacing-6); padding: var(--spacing-4); background: var(--bg-input); border-radius: var(--radius-lg); text-align: center; border: 1px dashed var(--color-module); }
.workflow-hint { font-size: var(--font-size-base); font-weight: 500; margin-bottom: var(--spacing-3); color: var(--text-primary); }
.workflow-btn { width: auto; display: inline-flex; align-items: center; gap: 8px; }

.continue-section { margin-top: var(--spacing-6); padding-top: var(--spacing-4); border-top: 1px dashed var(--border-light); text-align: center; }
.continue-hint { margin-bottom: var(--spacing-3); color: var(--text-secondary); font-size: var(--font-size-sm); }
.continue-btn { width: 100%; max-width: 300px; }

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
.progress { margin-top: var(--spacing-3); color: var(--color-module); font-weight: var(--font-weight-semibold); animation: pulse 1.5s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
.err { margin-top: var(--spacing-3); color: var(--color-error); font-weight: var(--font-weight-semibold); }

/* 继续到3.3的按钮样式 */
.continue-section {
  margin-top: var(--spacing-6);
  padding-top: var(--spacing-6);
  border-top: 2px dashed var(--border-light);
  text-align: center;
}

.continue-hint {
  color: var(--text-secondary);
  font-size: var(--font-size-base);
  margin-bottom: var(--spacing-4);
}

.continue-btn {
  font-size: var(--font-size-lg);
  padding: var(--spacing-3) var(--spacing-6);
  min-width: 200px;
}

/* 3.2 风格配置样式 */
.h4 {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  margin: var(--spacing-4) 0 var(--spacing-2);
  color: var(--text-primary);
}

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
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-xs);
  border: 1px solid rgba(0,0,0,0.05);
}

.color-item.large { flex: 1.5; min-width: 140px; }
.color-item.wide { flex: 2; min-width: 200px; }
.color-item .color-label { font-size: var(--font-size-xs); opacity: 0.8; margin-top: auto; padding-bottom: var(--spacing-1); font-weight: var(--font-weight-bold); }
.color-item .color-value { font-size: var(--font-size-xs); font-weight: var(--font-weight-bold); font-family: var(--font-mono); letter-spacing: 0.5px; opacity: 0.8; }

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

/* AI 设计理由框 */
.reasoning-box {
  margin-top: var(--spacing-5);
  padding: var(--spacing-4);
  background: linear-gradient(135deg, var(--color-brand-light) 0%, #E0F2FE 100%);
  border: 1px solid var(--color-brand-light);
  border-radius: var(--radius-md);
  border-left: 4px solid var(--color-brand);
}

.reasoning-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-3);
  font-weight: var(--font-weight-semibold);
  color: var(--color-brand);
  font-size: var(--font-size-base);
}

.reasoning-icon { font-size: var(--font-size-lg); }
.reasoning-title { font-size: var(--font-size-base); }

.reasoning-content {
  color: var(--text-primary);
  line-height: var(--line-height-relaxed);
  font-size: var(--font-size-base);
  white-space: pre-wrap;
  word-break: break-word;
}

/* 样例幻灯片区域 */
.samples-section {
  margin-top: var(--spacing-6);
  padding-top: var(--spacing-6);
  border-top: 1px dashed var(--border-light);
}

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

/* 工作流入口 */
.workflow-entry {
  margin-top: var(--spacing-6);
  padding: var(--spacing-6);
  background: linear-gradient(135deg, var(--color-brand-light) 0%, #E0E7FF 100%);
  border-radius: var(--radius-lg);
  text-align: center;
  border: 1px solid var(--color-brand-light);
}

.workflow-hint {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-brand);
  margin-bottom: var(--spacing-4);
}

/* 并行生成进度样式 */
.expansion-progress {
  padding: var(--spacing-3) var(--spacing-4);
  background: var(--bg-input);
  border-bottom: 1px solid var(--border-light);
  margin-bottom: var(--spacing-2);
  border-radius: var(--radius-md);
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--spacing-2);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  font-weight: var(--font-weight-medium);
}

.progress-track {
  height: 6px;
  background: var(--border-light);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-brand), var(--color-module));
  transition: width 0.3s ease;
}

.slide-row-1 {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  width: 100%;
  gap: var(--spacing-2);
}

.slide-status-icon {
  margin-left: auto;
  font-size: var(--font-size-base);
}

.spin {
  display: inline-block;
  animation: spin 1s linear infinite;
}

.slide-item.is-loading {
  background: var(--bg-input);
  border-color: var(--color-brand-light);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.workflow-btn {
  padding: var(--spacing-3) var(--spacing-6);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  background: var(--color-brand);
  color: var(--text-inverse);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-fast);
  box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.4);
}

.workflow-btn:hover {
  background: var(--color-brand-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-elevated);
}
</style>
