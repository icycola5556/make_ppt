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
      <JsonBlock title="teaching_request.json" :value="teachingRequest" filename="teaching_request.json" collapsed />
    </section>

    <!-- 风格配置结果 -->
    <section v-if="styleConfig" class="card highlight">
      <div class="h3">3.2 风格配置结果</div>
      
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
        <div class="usage-showcase" :style="{ background: styleConfig.color.background, fontFamily: styleConfig.font.body_family }">
            <div class="showcase-label" :style="{ color: styleConfig.color.muted }">组件应用预览</div>
            <div class="showcase-row">
                <!-- 1. 卡片与文本层次 -->
                <div class="preview-card" :style="{ 
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
                    <div class="preview-btn" :style="{ 
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
            <div class="slide-title" :style="{ color: styleConfig.color.primary, fontFamily: styleConfig.font.title_family }">
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

const { busy, err, currentStep, needUserInput, questions, answers, teachingRequest, styleConfig, styleSamples, reset, runWorkflow } = useWorkflow()

const testCaseList = testCases
const rawText = ref('')

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
    await runWorkflow({ user_text: rawText.value, stop_at: '3.2' })
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
      stop_at: '3.2'
    })
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
.card.warn { border-color: #f59e0b55; background: #fffbeb; }
.h3 { font-size: 16px; font-weight: 700; margin-bottom: 12px; }
.h4 { font-size: 14px; font-weight: 600; margin: 16px 0 8px; color: #374151; }
.textarea { width: 100%; min-height: 80px; border: 1px solid #d1d5db; border-radius: 10px; padding: 10px; font-size: 14px; }
.row { display: flex; gap: 10px; margin-top: 12px; }
.primary { background: #059669; color: #fff; border: none; border-radius: 10px; padding: 10px 16px; cursor: pointer; font-weight: 600; }
.primary:disabled { opacity: 0.5; }
.btn { background: #fff; border: 1px solid #d1d5db; border-radius: 10px; padding: 10px 16px; cursor: pointer; }
.qbox { margin: 12px 0; padding: 12px; border: 1px dashed #d1d5db; border-radius: 10px; background: #fff; }
.qtitle { font-weight: 600; margin-bottom: 8px; }
.options-group { display: flex; flex-wrap: wrap; gap: 8px; }
.option-btn { padding: 8px 14px; border: 2px solid #d1d5db; border-radius: 8px; background: #fff; cursor: pointer; }
.option-btn.active { border-color: #059669; background: #ecfdf5; color: #059669; }
.input { width: 100%; border: 1px solid #d1d5db; border-radius: 8px; padding: 8px 10px; }

.style-info { display: flex; gap: 24px; margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px dashed #e5e7eb; }
.info-item { display: flex; flex-direction: column; gap: 4px; }
.info-item .label { font-size: 12px; color: #6b7280; }
.info-item .value { font-weight: 600; font-size: 14px; }

.style-preview { margin-bottom: 16px; }
.color-palette { display: flex; flex-wrap: wrap; gap: 10px; }
.color-item { width: 100px; height: 60px; border-radius: 8px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 11px; border: 1px solid rgba(0,0,0,0.05); }
.color-label { font-weight: 700; opacity: 0.9; }
.color-value { opacity: 0.8; font-family: monospace; }

.samples-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }
.sample-slide { border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; aspect-ratio: 16/9; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); font-size: 12px; }
.slide-header { display: flex; justify-content: space-between; margin-bottom: 8px; padding-bottom: 4px; }
.slide-kind { font-size: 10px; text-transform: uppercase; opacity: 0.6; }
.slide-title { font-size: 14px; font-weight: bold; margin-bottom: 8px; line-height: 1.3; }
.slide-bullets { padding-left: 16px; margin: 0; flex: 1; }
.slide-bullets li { margin-bottom: 4px; }
.slide-notes { margin-top: auto; font-size: 10px; border-top: 1px dashed #ccc; padding-top: 4px; }

.test-cases { display: flex; gap: 8px; align-items: center; margin: 12px 0; flex-wrap: wrap; }
.test-btn { padding: 6px 12px; border: 1px dashed #9ca3af; border-radius: 6px; background: #f9fafb; cursor: pointer; font-size: 12px; }
.test-btn:hover { border-color: #059669; background: #ecfdf5; color: #059669; }
.label { font-weight: 600; font-size: 13px; }
.progress { margin-top: 12px; color: #059669; font-weight: 600; animation: pulse 1.5s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
.err { margin-top: 10px; color: #b91c1c; font-weight: 600; }

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
}
.color-item.large { flex: 1.5; min-width: 140px; }
.color-item.wide { flex: 2; min-width: 200px; }

.color-item .color-label { font-size: 10px; opacity: 0.8; margin-top: auto; padding-bottom: 4px; }
.color-item .color-value { font-size: 12px; font-weight: 700; font-family: monospace; letter-spacing: 0.5px; }
</style>
