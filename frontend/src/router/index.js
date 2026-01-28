import { createRouter, createWebHistory } from 'vue-router'
import Module31Intent from '../views/Module31Intent.vue'
import Module33Outline from '../views/Module33Outline.vue'
import Module34Content from '../views/Module34Content.vue'
import Module35Render from '../views/Module35Render.vue'
import OutlineEditorView from '../views/OutlineEditorView.vue'
import ContentGeneratorView from '../views/ContentGeneratorView.vue'

const routes = [
    { path: '/design-demo', name: 'DesignSystemDemo', component: () => import('../views/DesignSystemDemo.vue') },
    { path: '/', redirect: '/3.1' },
    { path: '/3.1', name: 'Module3.1', component: Module31Intent },
    // 3.2 风格设计已移除，功能已合并到 3.1 意图识别
    { path: '/3.2', redirect: '/3.3' }, // 兼容旧链接
    { path: '/3.3', name: 'Module3.3', component: Module33Outline },
    { path: '/3.4', name: 'Module3.4', component: Module34Content },
    { path: '/3.5', name: 'Module3.5', component: Module35Render },
    // 2-Stage Interactive Workflow
    { path: '/outline-editor', name: 'OutlineEditor', component: OutlineEditorView },
    { path: '/content-generator', name: 'ContentGenerator', component: ContentGeneratorView },
]

const router = createRouter({
    history: createWebHistory(),
    routes,
})

export default router
