// 工作流共享状态管理
import { ref, reactive, computed } from 'vue'
import { api, getApiBase, setApiBase } from '../api'

// 共享状态
const apiBase = ref(getApiBase())
const busy = ref(false)
const err = ref('')
const health = ref(null)
const sessionId = ref('')
const needUserInput = ref(false)
const questions = ref([])
const answers = reactive({})
const currentStep = ref('') // 当前执行步骤

// V2: 增强型进度状态 (借鉴 banana-slides)
const workflowProgress = reactive({
    currentModule: '',           // '3.1' | '3.2' | '3.3' | '3.4'
    moduleStatus: 'idle',        // 'idle' | 'running' | 'waiting' | 'done' | 'error'
    progress: {
        total: 0,
        completed: 0,
        percent: 0
    },
    messages: [],                // 滚动日志消息
})

// 追加日志消息 (最多保留50条)
function appendMessage(msg) {
    const timestamp = new Date().toLocaleTimeString('zh-CN', { hour12: false })
    workflowProgress.messages.push({
        timestamp,
        text: msg
    })
    // 保留最近50条
    if (workflowProgress.messages.length > 50) {
        workflowProgress.messages.shift()
    }
}

// 更新进度
function updateProgress(completed, total) {
    workflowProgress.progress.completed = completed
    workflowProgress.progress.total = total
    workflowProgress.progress.percent = total > 0 ? Math.round((completed / total) * 100) : 0
}

// 设置模块状态
function setModuleStatus(module, status) {
    workflowProgress.currentModule = module
    workflowProgress.moduleStatus = status
}

// ========================================
// V3: 步骤缓存 - 实现单步运行、结果复用
// ========================================
const stepCache = reactive({
    '3.1': null,  // TeachingRequest
    '3.2': null,  // { styleConfig, styleSamples }
    '3.3': null,  // PPTOutline
    '3.4': null,  // SlideDeckContent
})

// 缓存的会话ID（用于恢复会话）
const cachedSessionId = ref('')

// 保存步骤结果到缓存（同时保存sessionId）
function saveToCache(step, data, currentSessionId = null) {
    if (['3.1', '3.2', '3.3', '3.4'].includes(step)) {
        stepCache[step] = JSON.parse(JSON.stringify(data)) // 深拷贝
        // 同时保存当前的sessionId
        if (currentSessionId) {
            cachedSessionId.value = currentSessionId
        }
        console.log(`[缓存] 已保存 ${step} 结果, sessionId: ${cachedSessionId.value}`, stepCache[step])
    }
}

// 从缓存加载步骤结果
function loadFromCache(step) {
    return stepCache[step]
}

// 获取缓存的sessionId
function getCachedSessionId() {
    return cachedSessionId.value
}

// 检查是否有缓存
function hasCache(step) {
    return stepCache[step] !== null
}

// 检查是否有可用的缓存会话
function hasCachedSession() {
    return cachedSessionId.value && cachedSessionId.value.length > 0
}

// 清空指定步骤及其后续步骤的缓存
function clearCacheFrom(step) {
    const steps = ['3.1', '3.2', '3.3', '3.4']
    const idx = steps.indexOf(step)
    if (idx >= 0) {
        for (let i = idx; i < steps.length; i++) {
            stepCache[steps[i]] = null
        }
    }
    // 如果清空3.1，同时清空cachedSessionId
    if (step === '3.1') {
        cachedSessionId.value = ''
    }
}

// 恢复缓存的会话状态（用于从缓存继续）
function restoreFromCacheUpTo(targetStep) {
    const result = {
        sessionId: cachedSessionId.value,
        teachingRequest: null,
        styleConfig: null,
        styleSamples: [],
        outline: null,
        deckContent: null
    }

    // 按顺序加载缓存数据
    if (hasCache('3.1')) {
        result.teachingRequest = loadFromCache('3.1')
    }
    if (hasCache('3.2')) {
        const cache32 = loadFromCache('3.2')
        result.styleConfig = cache32.styleConfig
        result.styleSamples = cache32.styleSamples || []
    }
    if (targetStep >= '3.3' && hasCache('3.3')) {
        result.outline = loadFromCache('3.3')
    }
    if (targetStep >= '3.4' && hasCache('3.4')) {
        result.deckContent = loadFromCache('3.4')
    }

    return result
}

// 获取缓存摘要（用于UI展示）
function getCacheSummary() {
    return {
        '3.1': stepCache['3.1'] ? {
            subject: stepCache['3.1'].subject_info?.subject_name,
            kpCount: stepCache['3.1'].knowledge_points?.length || 0,
            slideCount: stepCache['3.1'].slide_requirements?.target_count
        } : null,
        '3.2': stepCache['3.2'] ? {
            styleName: stepCache['3.2'].styleConfig?.style_name,
            hasConfig: !!stepCache['3.2'].styleConfig
        } : null,
        '3.3': stepCache['3.3'] ? {
            title: stepCache['3.3'].deck_title || stepCache['3.3'].title,
            slideCount: stepCache['3.3'].slides?.length || 0
        } : null,
        '3.4': stepCache['3.4'] ? {
            hasContent: !!stepCache['3.4']
        } : null
    }
}

// 工作流结果
const teachingRequest = ref(null)
const styleConfig = ref(null)
const styleSamples = ref([])
const outline = ref(null)
const deckContent = ref(null)
const sessionState = ref(null)

// 测试模式
const testModes = [
    { value: 'full', label: '完整流程' },
    { value: '3.1', label: '仅 3.1 意图理解' },
    { value: '3.2', label: '仅 3.1→3.2' },
    { value: '3.1-3.3', label: '仅 3.1→3.3（跳过3.2）' },
    { value: '3.3', label: '3.1→3.3（3.1→3.2→3.3）' },
    { value: '3.4', label: '完整 3.1→3.4' },
]

const testModeDescriptions = {
    'full': '执行完整工作流（3.1→3.2→3.3→3.4），显示所有模块结果',
    '3.1': '仅执行模块3.1（意图理解），返回TeachingRequest结构化数据',
    '3.2': '执行到模块3.2（风格设计），返回意图+风格配置',
    '3.1-3.3': '从3.1直接到3.3（跳过3.2），需要手动输入style_name',
    '3.3': '执行3.1→3.2→3.3，返回意图+风格+大纲',
    '3.4': '执行完整流程，与"完整流程"相同',
}

const availableStyles = [
    { label: '理论课 (theory_clean)', value: 'theory_clean' },
    { label: '实训课 (practice_steps)', value: 'practice_steps' },
    { label: '复习课 (review_mindmap)', value: 'review_mindmap' },
]

// 测试案例
const testCases = [
    '给我一个机械专业「液压传动原理」的理论课课件，10页左右',
    '给我一个护理专业的讲解课件',
    '做一份土木专业「土石方工程量计算」「列项」两个知识点的课件，5页',
]

export function useWorkflow() {
    // API操作
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

    function reset(clearCache = false) {
        err.value = ''
        health.value = null
        sessionId.value = ''
        needUserInput.value = false
        questions.value = []
        Object.keys(answers).forEach(k => delete answers[k])
        teachingRequest.value = null
        styleConfig.value = null
        styleSamples.value = []
        outline.value = null
        deckContent.value = null
        sessionState.value = null
        currentStep.value = ''
        // V2: 重置增强型进度状态
        workflowProgress.currentModule = ''
        workflowProgress.moduleStatus = 'idle'
        workflowProgress.progress.total = 0
        workflowProgress.progress.completed = 0
        workflowProgress.progress.percent = 0
        workflowProgress.messages = []
        // V3: 可选清空缓存
        if (clearCache) {
            stepCache['3.1'] = null
            stepCache['3.2'] = null
            stepCache['3.3'] = null
            stepCache['3.4'] = null
        }
    }

    async function createSession() {
        const r = await api.createSession()
        sessionId.value = r.session_id || r.sessionId || r.session
        return sessionId.value
    }
    // ========================================
    // 状态消息映射表 (State Machine Pattern)
    // ========================================
    const STAGE_STATUS_MAP = {
        '3.1': '3.1 意图理解中...',
        '3.2': '3.2 风格设计中...',
        '3.3': '3.3 大纲生成中...',
        '3.4': '3.4 内容生成中...',
        'done': '完成'
    }

    // 3.1阶段的子状态映射
    const INTERACTION_STAGE_STATUS = {
        'confirm_goals': '大模型确认页数信息中...',
        'ask_config_modification': '等待用户确认...',
        'adjust_configurations': '等待用户确认...',
        'final_confirm': '等待用户确认...',
        'default': '3.1 意图理解中...'
    }

    // 根据sessionState的stage动态更新currentStep
    function updateCurrentStepFromSession() {
        if (!sessionState.value) {
            currentStep.value = STAGE_STATUS_MAP['done']
            return
        }

        const stage = sessionState.value.stage
        const teachingReq = sessionState.value.teaching_request

        // 处理3.1阶段的子状态
        if (stage === '3.1') {
            const interactionStage = teachingReq?.internal_interaction_stage || teachingReq?.interaction_stage
            
            // 优先检查交互阶段状态
            if (interactionStage && INTERACTION_STAGE_STATUS[interactionStage]) {
                currentStep.value = INTERACTION_STAGE_STATUS[interactionStage]
                return
            }
            
            // 检查是否有LLM推荐页数信息
            if (teachingReq?.slide_requirements?.llm_recommended_count) {
                currentStep.value = '大模型确认页数信息中...'
                return
            }
            
            // 检查是否需要用户输入
            if (needUserInput.value) {
                currentStep.value = '等待用户确认...'
                return
            }
            
            currentStep.value = STAGE_STATUS_MAP['3.1']
            return
        }

        // 其他阶段直接使用映射
        currentStep.value = STAGE_STATUS_MAP[stage] || STAGE_STATUS_MAP['done']
    }

    // 辅助函数：获取指定阶段的状态消息
    function getStatusForStage(stage) {
        return STAGE_STATUS_MAP[stage] || STAGE_STATUS_MAP['done']
    }

    async function runWorkflow({ user_text, answers: ans = {}, auto_fill_defaults = false, stop_at = null, style_name = null, _continue_to_3_3 = false, _continue_to_3_2 = false, _continue_to_3_4 = false }) {
        busy.value = true
        err.value = ''

        try {
            if (!sessionId.value) {
                currentStep.value = '正在创建会话...'
                await createSession()
            }

            // 如果是从3.2继续到3.3，立即设置状态为"3.3 大纲生成中..."，不要被覆盖
            if (_continue_to_3_3 && stop_at === '3.3') {
                currentStep.value = '3.3 大纲生成中...'
            }

            // 如果是从3.1缓存继续到3.2，立即设置状态为"3.2 风格设计中..."，不要被覆盖
            if (_continue_to_3_2 && stop_at === '3.2') {
                currentStep.value = '3.2 风格设计中...'
            }

            // 如果是从缓存继续到3.4，立即设置状态为"3.4 内容生成中..."，不要被覆盖
            if (_continue_to_3_4 && stop_at === '3.4') {
                currentStep.value = '3.4 内容生成中...'
            }

            // 检查是否是用户点击"确认，开始生成"（final_confirm）
            // 检查answers中是否包含final_confirm字段，且值为"确认"或"开始生成"
            const hasFinalConfirm = ans && ans.final_confirm && (
                String(ans.final_confirm).includes('确认') ||
                String(ans.final_confirm).includes('开始生成')
            )

            // 根据stop_at确定要执行的步骤
            // 如果是从3.2继续到3.3，保持状态为"3.3 大纲生成中..."，不要被覆盖
            if (_continue_to_3_3 && stop_at === '3.3') {
                // 已经在上面的if中设置了状态，这里保持不动
                // 不执行任何可能覆盖状态的操作
            } else if (_continue_to_3_2 && stop_at === '3.2') {
                // 已经在上面的if中设置了状态，这里保持不动
                // 不执行任何可能覆盖状态的操作
            } else if (_continue_to_3_4 && stop_at === '3.4') {
                // 已经在上面的if中设置了状态，这里保持不动
                // 不执行任何可能覆盖状态的操作
            } else if (sessionId.value && sessionState.value) {
                // 先尝试从已有session获取状态
                updateCurrentStepFromSession()
            } else {
                const isResuming = Object.keys(ans).length > 0 || auto_fill_defaults
                if (isResuming) {
                    // 如果是完整流程（stop_at='3.3'且没有style_name）且用户确认开始，应该进入3.2阶段
                    if (hasFinalConfirm && stop_at === '3.3' && !style_name) {
                        currentStep.value = '3.2 风格设计中...'
                    } else if (stop_at === '3.1') {
                        currentStep.value = '3.1 意图理解中...'
                    } else if (stop_at === '3.2') {
                        currentStep.value = '3.2 风格设计中...'
                    } else if (stop_at === '3.3') {
                        currentStep.value = '3.3 大纲生成中...'
                    } else if (stop_at === '3.4') {
                        currentStep.value = '3.4 内容生成中...'
                    } else {
                        currentStep.value = '正在执行...'
                    }
                } else {
                    currentStep.value = '3.1 意图理解中...'
                }
            }

            // 如果是从缓存继续到3.2/3.3/3.4，不要被后续逻辑覆盖状态
            if (!(_continue_to_3_3 && stop_at === '3.3') && !(_continue_to_3_2 && stop_at === '3.2') && !(_continue_to_3_4 && stop_at === '3.4')) {
                // 如果用户提交了final_confirm且是完整流程，立即显示3.2状态（无论是否有sessionState）
                if (hasFinalConfirm && stop_at === '3.3' && !style_name) {
                    currentStep.value = '3.2 风格设计中...'
                }

                // 检查用户是否提交了配置修改相关的答案
                // 如果用户提交了"不需要修改"或"需要修改"并确认，应该显示"大模型确认页数信息中..."
                const hasConfigModificationAnswer = ans && (
                    ans.need_config_modification === '不需要修改' ||
                    ans.confirm_all_adjustments === '确认，开始最终优化'
                )

                // 如果用户提交了配置修改确认，立即显示"大模型确认页数信息中..."
                if (hasConfigModificationAnswer && !hasFinalConfirm) {
                    currentStep.value = '大模型确认页数信息中...'
                }
            }

            // V2: 启动模拟进度动画（后端非流式，模拟进度提升用户体验）
            updateProgress(0, 100)
            let progressTimer = null
            let currentProgress = 0
            const startSimulatedProgress = () => {
                progressTimer = setInterval(() => {
                    // 从0%逐渐增加到90%，速度逐渐变慢
                    if (currentProgress < 90) {
                        const increment = Math.max(1, Math.floor((90 - currentProgress) / 10))
                        currentProgress = Math.min(90, currentProgress + increment)
                        updateProgress(currentProgress, 100)
                    }
                }, 300) // 每300ms更新一次
            }
            const stopSimulatedProgress = (success) => {
                if (progressTimer) {
                    clearInterval(progressTimer)
                    progressTimer = null
                }
                // 完成时设为100%
                updateProgress(success ? 100 : currentProgress, 100)
            }
            startSimulatedProgress()

            let res
            try {
                res = await api.runWorkflow(sessionId.value, user_text, ans, auto_fill_defaults, stop_at, style_name)
                stopSimulatedProgress(true)
            } catch (apiError) {
                stopSimulatedProgress(false)
                throw apiError
            }

            if (res.status === 'need_user_input') {
                needUserInput.value = true
                questions.value = res.questions || []
                for (const q of questions.value) {
                    if (!(q.key in answers)) answers[q.key] = ''
                }
                teachingRequest.value = res.teaching_request || null

                // 获取最新的session状态以确定当前阶段
                sessionState.value = await api.getSession(sessionId.value)

                // 根据interaction_stage判断具体状态
                const interactionStage = teachingRequest.value?.internal_interaction_stage || teachingRequest.value?.interaction_stage

                // 检查是否在页面冲突确认阶段（confirm_goals阶段）
                if (res.stage === '3.1' && interactionStage === 'confirm_goals') {
                    // 无论是否有LLM推荐信息，都显示"大模型确认页数信息中..."
                    currentStep.value = '大模型确认页数信息中...'
                }
                // 检查是否在配置修改阶段
                else if (interactionStage === 'ask_config_modification' ||
                    interactionStage === 'adjust_configurations') {
                    currentStep.value = '等待用户确认...'
                }
                // 检查是否有LLM推荐页数信息
                else if (res.stage === '3.1' && teachingRequest.value &&
                    teachingRequest.value.slide_requirements?.llm_recommended_count) {
                    currentStep.value = '大模型确认页数信息中...'
                } else {
                    currentStep.value = '等待用户确认...'
                }
            } else if (res.status === 'ok') {
                needUserInput.value = false
                teachingRequest.value = res.teaching_request || null
                styleConfig.value = res.style_config || null
                styleSamples.value = res.style_samples || []
                outline.value = res.outline || null
                deckContent.value = res.deck_content || null

                // V3: 自动保存到缓存（同时保存sessionId）
                const completedStage = res.stage || stop_at
                if (res.teaching_request) {
                    saveToCache('3.1', res.teaching_request, sessionId.value)
                }
                if (res.style_config) {
                    saveToCache('3.2', { styleConfig: res.style_config, styleSamples: res.style_samples || [] }, sessionId.value)
                }
                if (res.outline) {
                    saveToCache('3.3', res.outline, sessionId.value)
                }
                if (res.deck_content) {
                    saveToCache('3.4', res.deck_content, sessionId.value)
                }

                // 获取最新的session状态
                sessionState.value = await api.getSession(sessionId.value)

                // 如果是从3.2继续到3.3，保持状态为"3.3 大纲生成中..."，不要被覆盖
                if (_continue_to_3_3 && stop_at === '3.3') {
                    currentStep.value = '3.3 大纲生成中...'
                } else if (_continue_to_3_2 && stop_at === '3.2') {
                    // 如果是从3.1缓存继续到3.2，保持状态为"3.2 风格设计中..."，不要被覆盖
                    currentStep.value = '3.2 风格设计中...'
                } else if (_continue_to_3_4 && stop_at === '3.4') {
                    // 如果是从缓存继续到3.4，保持状态为"3.4 内容生成中..."，不要被覆盖
                    currentStep.value = '3.4 内容生成中...'
                } else {
                    // 根据响应的stage和sessionState动态设置状态信息
                    const stage = res.stage || sessionState.value?.stage
                    if (stage === '3.1') {
                        // 根据interaction_stage判断具体状态
                        const interactionStage = teachingRequest.value?.internal_interaction_stage || teachingRequest.value?.interaction_stage

                        // 检查是否在页面冲突确认阶段（confirm_goals阶段）
                        // 当用户提交"不需要修改"或"需要修改"并确认后，会进入confirm_goals阶段
                        // 此时应该显示"大模型确认页数信息中..."
                        if (interactionStage === 'confirm_goals') {
                            // 无论是否有LLM推荐信息，都显示"大模型确认页数信息中..."
                            currentStep.value = '大模型确认页数信息中...'
                        }
                        // 检查是否有LLM推荐页数信息（用户确认后，LLM正在确认页数）
                        else if (teachingRequest.value && teachingRequest.value.slide_requirements?.llm_recommended_count) {
                            currentStep.value = '大模型确认页数信息中...'
                        } else {
                            currentStep.value = '3.1 意图理解中...'
                        }
                    } else if (stage === '3.2') {
                        // 如果3.2已完成且有style_config，显示完成状态
                        if (styleConfig.value && !outline.value) {
                            currentStep.value = '3.2 风格设计完成，等待继续...'
                        } else {
                            currentStep.value = '3.2 风格设计中...'
                        }
                    } else if (stage === '3.3') {
                        // 确保状态是"3.3 大纲生成中..."
                        currentStep.value = '3.3 大纲生成中...'
                    } else if (stage === '3.4') {
                        currentStep.value = '3.4 内容生成中...'
                    } else {
                        currentStep.value = '完成'
                    }
                }
            } else if (res.status === 'error') {
                currentStep.value = ''
                throw new Error(res.message || 'workflow error')
            }

            return res
        } finally {
            busy.value = false
        }
    }

    const logsHref = computed(() => sessionId.value ? api.logsUrl(sessionId.value) : '#')

    return {
        // 状态
        apiBase,
        busy,
        err,
        health,
        sessionId,
        needUserInput,
        questions,
        answers,
        currentStep,  // 当前执行步骤
        // V2: 增强型进度状态
        workflowProgress,
        // V3: 步骤缓存
        stepCache,
        // 结果
        teachingRequest,
        styleConfig,
        styleSamples,
        outline,
        deckContent,
        sessionState,
        // 常量
        testModes,
        testModeDescriptions,
        testCases,
        availableStyles, // 样式选项
        // 方法
        checkHealth,
        reset,
        createSession,
        runWorkflow,
        setApiBase,
        logsHref,
        updateCurrentStepFromSession, // 导出以便外部调用
        // V2: 进度控制方法
        appendMessage,
        updateProgress,
        setModuleStatus,
        // V3: 缓存控制方法
        saveToCache,
        loadFromCache,
        hasCache,
        clearCacheFrom,
        getCacheSummary,
        // V3.1: 增强缓存恢复
        getCachedSessionId,
        hasCachedSession,
        restoreFromCacheUpTo,
    }
}
