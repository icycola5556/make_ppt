// useContentGenerator.js - Composable for async parallel content generation
import { ref, reactive, computed } from 'vue'
import { api } from '../api'

/**
 * Composable for Phase 2: Async Parallel Content Generation
 * 
 * Manages per-slide generation status and content with concurrency control
 */
export function useContentGenerator() {
    // Per-slide status: 'idle' | 'loading' | 'done' | 'error'
    const slideStatus = reactive({})

    // Generated content per slide
    const generatedContent = reactive({})

    // Error messages per slide
    const slideErrors = reactive({})

    // Session reference
    const sessionId = ref('')

    // Progress tracking
    const totalSlides = ref(0)

    // Toast notifications
    const toasts = ref([])

    /**
     * Initialize for a set of slides
     */
    function initForSlides(outline, session_id) {
        // Reset state
        Object.keys(slideStatus).forEach(k => delete slideStatus[k])
        Object.keys(generatedContent).forEach(k => delete generatedContent[k])
        Object.keys(slideErrors).forEach(k => delete slideErrors[k])

        if (!outline || !outline.slides) return

        sessionId.value = session_id
        totalSlides.value = outline.slides.length

        // Initialize all slides as 'idle'
        outline.slides.forEach((slide, index) => {
            slideStatus[index] = 'idle'
            generatedContent[index] = null
            slideErrors[index] = null
        })
    }

    /**
     * Add toast notification
     */
    function addToast(message, type = 'success') {
        const id = Date.now()
        toasts.value.push({ id, message, type })

        // Auto-remove after 4 seconds
        setTimeout(() => {
            toasts.value = toasts.value.filter(t => t.id !== id)
        }, 4000)
    }

    /**
     * Generate content for a single slide
     */
    async function generateSlide(slideIndex, context = null) {
        if (!sessionId.value) return

        slideStatus[slideIndex] = 'loading'
        slideErrors[slideIndex] = null

        try {
            const result = await api.generateSlideContent(sessionId.value, slideIndex, context)

            if (result.ok && result.content) {
                slideStatus[slideIndex] = 'done'
                generatedContent[slideIndex] = result.content
                addToast(`第 ${slideIndex + 1} 页内容生成完成`, 'success')
            } else {
                slideStatus[slideIndex] = 'error'
                slideErrors[slideIndex] = result.error || 'Generation failed'
                addToast(`第 ${slideIndex + 1} 页生成失败`, 'error')
            }
        } catch (e) {
            slideStatus[slideIndex] = 'error'
            slideErrors[slideIndex] = e.message || 'Network error'
            addToast(`第 ${slideIndex + 1} 页生成出错`, 'error')
        }
    }

    /**
     * Generate all slides with concurrency control
     */
    async function generateAllSlides(concurrencyLimit = 3) {
        const indices = Object.keys(slideStatus).map(Number).filter(i => slideStatus[i] === 'idle')

        // Simple concurrency control using batches
        for (let i = 0; i < indices.length; i += concurrencyLimit) {
            const batch = indices.slice(i, i + concurrencyLimit)
            await Promise.all(batch.map(idx => generateSlide(idx)))
        }
    }

    /**
     * Regenerate a specific slide
     */
    async function regenerateSlide(slideIndex) {
        slideStatus[slideIndex] = 'idle'
        generatedContent[slideIndex] = null
        slideErrors[slideIndex] = null

        await generateSlide(slideIndex)
    }

    /**
     * Update generated content (for manual editing)
     */
    function updateContent(slideIndex, content) {
        if (generatedContent[slideIndex]) {
            Object.assign(generatedContent[slideIndex], content)
        } else {
            generatedContent[slideIndex] = content
        }
    }

    /**
     * Remove a toast notification
     */
    function removeToast(id) {
        toasts.value = toasts.value.filter(t => t.id !== id)
    }

    // Computed properties
    const progress = computed(() => {
        const total = totalSlides.value
        if (total === 0) return { completed: 0, total: 0, percent: 0 }

        const completed = Object.values(slideStatus).filter(s => s === 'done').length
        return {
            completed,
            total,
            percent: Math.round((completed / total) * 100)
        }
    })

    const isGenerating = computed(() => {
        return Object.values(slideStatus).some(s => s === 'loading')
    })

    const allCompleted = computed(() => {
        return totalSlides.value > 0 && progress.value.completed === totalSlides.value
    })

    return {
        // State
        slideStatus,
        generatedContent,
        slideErrors,
        sessionId,
        totalSlides,
        toasts,

        // Computed
        progress,
        isGenerating,
        allCompleted,

        // Methods
        initForSlides,
        generateSlide,
        generateAllSlides,
        regenerateSlide,
        updateContent,
        addToast,
        removeToast
    }
}
