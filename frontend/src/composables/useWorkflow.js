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

    function reset() {
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
    }

    async function createSession() {
        const r = await api.createSession()
        sessionId.value = r.session_id || r.sessionId || r.session
        return sessionId.value
    }

    // 根据sessionState的stage动态更新currentStep
    function updateCurrentStepFromSession() {
        if (!sessionState.value) {
            // 如果没有sessionState，尝试从响应中获取stage
            currentStep.value = '完成'
            return
        }

        const stage = sessionState.value.stage
        const teachingReq = sessionState.value.teaching_request

        if (stage === '3.1') {
            // 根据interaction_stage判断具体状态
            const interactionStage = teachingReq?.internal_interaction_stage || teachingReq?.interaction_stage
            
            // 检查是否在页面冲突确认阶段（confirm_goals阶段）
            if (interactionStage === 'confirm_goals') {
                // 如果已经有LLM推荐信息，说明LLM正在或已经确认页数
                if (teachingReq?.slide_requirements?.llm_recommended_count || 
                    teachingReq?.interaction_metadata?._llm_recommendation_explanation) {
                    currentStep.value = '大模型确认页数信息中...'
                } else {
                    // 正在等待LLM确认页数
                    currentStep.value = '大模型确认页数信息中...'
                }
            } 
            // 检查是否在配置修改阶段（等待用户确认配置）
            else if (interactionStage === 'ask_config_modification' || 
                     interactionStage === 'adjust_configurations') {
                currentStep.value = '等待用户确认...'
            }
            // 检查是否有LLM推荐页数信息（用户确认后，LLM正在确认页数）
            else if (teachingReq && teachingReq.slide_requirements && 
                (teachingReq.slide_requirements.llm_recommended_count || 
                 teachingReq.interaction_metadata?._llm_recommendation_explanation)) {
                currentStep.value = '大模型确认页数信息中...'
            } else if (needUserInput.value) {
                currentStep.value = '等待用户确认...'
            } else {
                currentStep.value = '3.1 意图理解中...'
            }
        } else if (stage === '3.2') {
            currentStep.value = '3.2 风格设计中...'
        } else if (stage === '3.3') {
            currentStep.value = '3.3 大纲生成中...'
        } else if (stage === '3.4') {
            currentStep.value = '3.4 内容生成中...'
        } else {
            currentStep.value = '完成'
        }
    }

    async function runWorkflow({ user_text, answers: ans = {}, auto_fill_defaults = false, stop_at = null, style_name = null, _continue_to_3_3 = false }) {
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
            
            // 如果是从3.2继续到3.3，不要被后续逻辑覆盖状态
            if (!(_continue_to_3_3 && stop_at === '3.3')) {
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

            const res = await api.runWorkflow(sessionId.value, user_text, ans, auto_fill_defaults, stop_at, style_name)

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
                
                // 获取最新的session状态
                sessionState.value = await api.getSession(sessionId.value)
                
                // 如果是从3.2继续到3.3，保持状态为"3.3 大纲生成中..."，不要被覆盖
                if (_continue_to_3_3 && stop_at === '3.3') {
                    currentStep.value = '3.3 大纲生成中...'
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
    }
}
