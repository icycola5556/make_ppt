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

// style_name映射
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

function normalizeStyleName(input) {
    if (!input) return null
    const trimmed = input.trim()
    if (styleNameMap[trimmed]) return styleNameMap[trimmed]
    if (['theory_clean', 'practice_steps', 'review_mindmap'].includes(trimmed)) return trimmed
    return trimmed
}

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

    async function runWorkflow({ user_text, answers: ans = {}, auto_fill_defaults = false, stop_at = null, style_name = null }) {
        busy.value = true
        err.value = ''

        try {
            if (!sessionId.value) {
                currentStep.value = '正在创建会话...'
                await createSession()
            }

            // 根据stop_at确定要执行的步骤
            currentStep.value = '3.1 意图理解中...'

            const res = await api.runWorkflow(sessionId.value, user_text, ans, auto_fill_defaults, stop_at, style_name)

            if (res.status === 'need_user_input') {
                currentStep.value = '等待用户确认...'
                needUserInput.value = true
                questions.value = res.questions || []
                for (const q of questions.value) {
                    if (!(q.key in answers)) answers[q.key] = ''
                }
                teachingRequest.value = res.teaching_request || null
            } else if (res.status === 'ok') {
                needUserInput.value = false
                teachingRequest.value = res.teaching_request || null
                styleConfig.value = res.style_config || null
                outline.value = res.outline || null
                deckContent.value = res.deck_content || null
                currentStep.value = '完成'
            } else if (res.status === 'error') {
                currentStep.value = ''
                throw new Error(res.message || 'workflow error')
            }

            sessionState.value = await api.getSession(sessionId.value)
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
        outline,
        deckContent,
        sessionState,
        // 常量
        testModes,
        testModeDescriptions,
        testCases,
        // 方法
        checkHealth,
        reset,
        createSession,
        runWorkflow,
        normalizeStyleName,
        setApiBase,
        logsHref,
    }
}
