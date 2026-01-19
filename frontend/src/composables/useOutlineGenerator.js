
import { ref, reactive, computed } from 'vue'
import { api } from '../api'

/**
 * Composable for Phase 6: Async Parallel Outline Expansion (Module 3.3)
 * 
 * Manages per-slide expansion status and content updates.
 */
export function useOutlineGenerator() {
    // Per-slide status: 'idle' | 'loading' | 'done' | 'error'
    const slideStatus = reactive({})

    // Error messages per slide
    const slideErrors = reactive({})

    // Session reference
    const sessionId = ref('')

    // Reference to the outline slides we are expanding
    const outlineSlides = ref([])

    // Progress tracking
    const totalSlides = ref(0)

    // Toast notifications
    const toasts = ref([])

    /**
     * Initialize for a set of slides (Outline Structure)
     */
    function initForStructure(slides, session_id) {
        // Reset state
        Object.keys(slideStatus).forEach(k => delete slideStatus[k])
        Object.keys(slideErrors).forEach(k => delete slideErrors[k])

        if (!slides) return

        sessionId.value = session_id
        outlineSlides.value = slides
        totalSlides.value = slides.length

        // Initialize all slides as 'idle'
        slides.forEach((slide, index) => {
            slideStatus[index] = 'idle'
            slideErrors[index] = null

            // If already has detailed bullets (e.g. from cache or legacy), mark as done?
            // For now, assume structure-only needs expansion.
            // Check if bullets is empty or dummy
            if (slide.bullets && slide.bullets.length > 0) {
                // Maybe it's already done? Let's check a flag or just assume 'idle' to allow re-expand
            }
        })
    }

    function addToast(message, type = 'success') {
        const id = Date.now()
        toasts.value.push({ id, message, type })
        setTimeout(() => toasts.value = toasts.value.filter(t => t.id !== id), 4000)
    }

    /**
     * Expand a single slide
     */
    async function expandSlide(slideIndex) {
        if (!sessionId.value) return

        slideStatus[slideIndex] = 'loading'
        slideErrors[slideIndex] = null

        try {
            const result = await api.expandSlide(sessionId.value, slideIndex)

            if (result.ok && result.slide) {
                slideStatus[slideIndex] = 'done'
                // Update the local slide object directly
                // Vue should react if outlineSlides is part of a reactive object
                if (outlineSlides.value[slideIndex]) {
                    Object.assign(outlineSlides.value[slideIndex], result.slide)
                }
                // addToast(`第 ${slideIndex + 1} 页大纲扩展完成`, 'success')
            } else {
                slideStatus[slideIndex] = 'error'
                slideErrors[slideIndex] = result.error || 'Expansion failed'
                addToast(`第 ${slideIndex + 1} 页扩展失败`, 'error')
            }
        } catch (e) {
            slideStatus[slideIndex] = 'error'
            slideErrors[slideIndex] = e.message || 'Network error'
            addToast(`第 ${slideIndex + 1} 页扩展出错`, 'error')
        }
    }

    /**
     * Expand all slides calls in parallel batches
     */
    async function expandAllSlides(concurrencyLimit = 5) {
        const indices = Object.keys(slideStatus).map(Number).filter(i => slideStatus[i] === 'idle' || slideStatus[i] === 'error')

        for (let i = 0; i < indices.length; i += concurrencyLimit) {
            const batch = indices.slice(i, i + concurrencyLimit)
            await Promise.all(batch.map(idx => expandSlide(idx)))
        }
    }

    function removeToast(id) {
        toasts.value = toasts.value.filter(t => t.id !== id)
    }

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

    const isExpanding = computed(() => {
        return Object.values(slideStatus).some(s => s === 'loading')
    })

    return {
        slideStatus,
        slideErrors,
        sessionId,
        toasts,
        progress,
        isExpanding,
        initForStructure,
        expandSlide,
        expandAllSlides,
        removeToast
    }
}
