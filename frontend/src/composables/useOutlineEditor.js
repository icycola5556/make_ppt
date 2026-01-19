// useOutlineEditor.js - Composable for outline editing functionality
import { ref, reactive, computed } from 'vue'
import { api } from '../api'

/**
 * Composable for Phase 1: Interactive Outline Editor
 * 
 * Manages local state of slides array, tracks edits, and syncs with backend
 */
export function useOutlineEditor() {
    // Local copy of slides for editing
    const slides = ref([])

    // Track if there are unsaved changes
    const isDirty = ref(false)

    // Currently selected slide index for preview
    const selectedIndex = ref(null)

    // Saving state
    const saving = ref(false)
    const saveError = ref('')

    // Session reference
    const sessionId = ref('')

    /**
     * Initialize slides from outline object
     */
    function initFromOutline(outline, session_id) {
        if (!outline || !outline.slides) {
            slides.value = []
            return
        }
        // Deep clone to avoid mutating original
        slides.value = JSON.parse(JSON.stringify(outline.slides))
        sessionId.value = session_id
        isDirty.value = false
        selectedIndex.value = null
    }

    /**
     * Update a single slide
     */
    function updateSlide(index, data) {
        if (index < 0 || index >= slides.value.length) return

        const slide = slides.value[index]
        Object.assign(slide, data)

        // Re-index if needed
        slide.index = index
        isDirty.value = true
    }

    /**
     * Delete a slide
     */
    function deleteSlide(index) {
        if (index < 0 || index >= slides.value.length) return

        slides.value.splice(index, 1)

        // Re-index all slides
        slides.value.forEach((slide, i) => {
            slide.index = i
        })

        // Update selection
        if (selectedIndex.value === index) {
            selectedIndex.value = null
        } else if (selectedIndex.value !== null && selectedIndex.value > index) {
            selectedIndex.value--
        }

        isDirty.value = true
    }

    /**
     * Add a new blank slide
     */
    function addSlide() {
        const newSlide = {
            index: slides.value.length,
            slide_type: 'content',
            title: '新页面',
            bullets: [],
            notes: null,
            interactions: [],
            assets: []
        }
        slides.value.push(newSlide)
        isDirty.value = true

        // Select the new slide
        selectedIndex.value = slides.value.length - 1

        return newSlide
    }

    /**
     * Move a slide (for drag-and-drop reordering)
     */
    function moveSlide(fromIndex, toIndex) {
        if (fromIndex === toIndex) return
        if (fromIndex < 0 || fromIndex >= slides.value.length) return
        if (toIndex < 0 || toIndex >= slides.value.length) return

        const [removed] = slides.value.splice(fromIndex, 1)
        slides.value.splice(toIndex, 0, removed)

        // Re-index all slides
        slides.value.forEach((slide, i) => {
            slide.index = i
        })

        // Update selection if needed
        if (selectedIndex.value === fromIndex) {
            selectedIndex.value = toIndex
        } else if (selectedIndex.value !== null) {
            if (fromIndex < selectedIndex.value && toIndex >= selectedIndex.value) {
                selectedIndex.value--
            } else if (fromIndex > selectedIndex.value && toIndex <= selectedIndex.value) {
                selectedIndex.value++
            }
        }

        isDirty.value = true
    }

    /**
     * Save outline to backend
     */
    async function saveOutline() {
        if (!sessionId.value) {
            saveError.value = 'No session ID'
            return false
        }

        saving.value = true
        saveError.value = ''

        try {
            const result = await api.updateOutline(sessionId.value, slides.value)

            if (result.ok) {
                isDirty.value = false
                return true
            } else {
                saveError.value = result.error || 'Failed to save outline'
                return false
            }
        } catch (e) {
            saveError.value = e.message || 'Network error'
            return false
        } finally {
            saving.value = false
        }
    }

    /**
     * Select a slide for preview
     */
    function selectSlide(index) {
        if (index === null || (index >= 0 && index < slides.value.length)) {
            selectedIndex.value = index
        }
    }

    // Computed properties
    const slideCount = computed(() => slides.value.length)
    const selectedSlide = computed(() => {
        if (selectedIndex.value === null) return null
        return slides.value[selectedIndex.value] || null
    })

    return {
        // State
        slides,
        isDirty,
        selectedIndex,
        saving,
        saveError,
        sessionId,

        // Computed
        slideCount,
        selectedSlide,

        // Methods
        initFromOutline,
        updateSlide,
        deleteSlide,
        addSlide,
        moveSlide,
        saveOutline,
        selectSlide
    }
}
