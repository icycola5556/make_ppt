# 「温润学府」前端设计系统文档 v2.0

> 专为高职教育用户设计的 UI 升级方案
>
> **v2.0 更新**：修复色彩语义冲突、增强无障碍支持、完善布局弹性、补充状态设计

---

## 1. 设计理念

### 1.1 目标用户画像

| 特征 | 描述 | 设计影响 |
|------|------|----------|
| **用户群体** | 高职院校教师、教育工作者 | 专业、稳重的视觉风格 |
| **年龄范围** | 35-55 岁为主 | 需要更大字号、更高对比度 |
| **技术水平** | 基础办公软件操作能力 | 交互按钮位置需一致，降低学习成本 |
| **使用环境** | 普通办公显示器 | 避免过低对比度的配色 |
| **核心诉求** | 易用、清晰、专业、稳定 | 明确的反馈、清晰的层级 |

### 1.2 设计原则

1. **温和亲切** - 暖色调背景，减少视觉疲劳
2. **层次清晰** - 通过色彩和阴影区分内容层级
3. **步骤明确** - 用流程指示器替代平铺 Tab，降低认知负担
4. **反馈及时** - 悬停、点击、加载、空状态都有明确反馈
5. **无障碍优先** - 确保所有文本满足 WCAG AA 对比度标准
6. **交互一致** - 主要操作按钮全局统一，不随页面变化

---

## 2. 色彩系统

### 2.1 核心原则：装饰色 vs 交互色 分离

> **重要设计决策**：模块主题色仅用于**装饰性元素**（图标、徽标、进度条、左侧标记条），
> **交互按钮**保持全局统一，避免用户每进一个页面都要重新寻找"哪个是确定按钮"。

```
┌─────────────────────────────────────────────────────────────┐
│  模块主题色（装饰性）          交互按钮色（统一）            │
│  ├── 步骤导航圆点              ├── 主按钮（品牌蓝）         │
│  ├── 卡片左侧标记条            ├── 次要按钮（中性灰）       │
│  ├── 进度条填充色              ├── 危险按钮（红色）         │
│  └── 模块图标背景              └── 禁用按钮（浅灰）         │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 品牌色（交互按钮专用）

所有主要交互按钮使用统一的品牌色，不随模块变化：

```css
/* 品牌主色 - 用于所有主要交互按钮 */
--color-brand: #2563EB;           /* 品牌蓝 */
--color-brand-hover: #1D4ED8;     /* 悬停态 */
--color-brand-active: #1E40AF;    /* 按下态 */
--color-brand-light: #DBEAFE;     /* 浅色背景 */
--color-brand-rgb: 37, 99, 235;   /* RGB 值 */
--color-brand-hsl: 217, 91%, 60%; /* HSL 值（便于调节明暗）*/
```

### 2.3 模块装饰色（仅用于视觉标识）

避免与状态色冲突，重新选择模块色：

| 模块 | 模块名称 | 主色值 | 浅色值 | 设计说明 |
|------|----------|--------|--------|----------|
| 3.1 | 意图理解 | `#6366F1` | `#E0E7FF` | 靛蓝 - 避开品牌蓝 |
| 3.2 | 风格设计 | `#0EA5E9` | `#E0F2FE` | 天蓝 - 避开成功绿 |
| 3.3 | 大纲生成 | `#8B5CF6` | `#EDE9FE` | 紫色 - 结构感 |
| 3.4 | 内容生成 | `#F97316` | `#FFEDD5` | 橙色 - 比琥珀更鲜艳，减少警告感 |
| 3.5 | 智能排版 | `#EC4899` | `#FCE7F3` | 粉色 - 美感呈现 |

**关键改动**：
- 3.2 从绿色改为天蓝，避免与"成功"状态混淆
- 3.4 从琥珀色 `#F59E0B` 改为橙色 `#F97316`，更鲜艳活力，减少警告感

### 2.4 状态色（语义明确，不与模块色重叠）

```css
/* 状态色 - 仅用于反馈结果 */
--color-success: #22C55E;    /* 成功 - 比模块色更亮的绿 */
--color-warning: #EAB308;    /* 警告 - 纯黄，与橙色区分 */
--color-error: #EF4444;      /* 错误 - 红色 */
--color-info: #3B82F6;       /* 信息 - 蓝色 */

/* 状态色 HSL（便于生成变体） */
--color-success-hsl: 142, 71%, 45%;
--color-warning-hsl: 48, 96%, 53%;
--color-error-hsl: 0, 84%, 60%;
```

### 2.5 基础色板（优化对比度）

```css
/* 页面背景 - 暖白调 */
--bg-page: #FAFAF8;
--bg-card: #FFFFFF;
--bg-input: #F5F5F4;
--bg-hover: #F0F0EE;      /* 悬停背景 */
--bg-disabled: #E5E5E3;   /* 禁用背景 */

/* 文字颜色 - 确保 WCAG AA 对比度 */
--text-primary: #1F2937;    /* 对比度 12.6:1 ✓ */
--text-secondary: #4B5563;  /* 对比度 7.5:1 ✓ (原 #6B7280 只有 5.0:1) */
--text-muted: #6B7280;      /* 对比度 5.0:1 ✓ (仅用于装饰性文字) */
--text-placeholder: #9CA3AF; /* 占位符 - 不要求高对比度 */

/* 边框颜色 */
--border-light: #E5E7EB;
--border-default: #D1D5DB;
--border-focus: var(--color-brand);
```

### 2.6 对比度速查表

| 文字类型 | 颜色 | 在 #FAFAF8 上的对比度 | WCAG 等级 |
|----------|------|----------------------|-----------|
| 主要文字 | #1F2937 | 12.6:1 | AAA |
| 次要文字 | #4B5563 | 7.5:1 | AAA |
| 辅助文字 | #6B7280 | 5.0:1 | AA |
| 占位符 | #9CA3AF | 3.0:1 | 仅装饰 |
| 品牌蓝按钮文字 | #FFFFFF on #2563EB | 7.1:1 | AAA |

---

## 3. 无障碍设计

### 3.1 标准模式 vs 高对比度模式

支持两种显示模式，通过 CSS 类切换：

```css
/* 标准模式（默认） */
:root {
  --font-size-base: 16px;     /* 从 15px 提升到 16px */
  --font-size-lg: 18px;
  --text-secondary: #4B5563;
}

/* 高对比度/大字号模式 */
:root.accessibility-mode {
  --font-size-base: 18px;
  --font-size-lg: 20px;
  --font-size-xl: 22px;
  --font-size-2xl: 28px;

  /* 更高对比度的文字 */
  --text-secondary: #374151;
  --text-muted: #4B5563;

  /* 更粗的边框 */
  --border-width: 2px;

  /* 更明显的焦点环 */
  --focus-ring-width: 4px;
}
```

### 3.2 切换控件

在设置或 Header 中提供切换按钮：

```vue
<template>
  <button
    class="accessibility-toggle"
    @click="toggleAccessibilityMode"
    aria-label="切换高对比度模式"
  >
    <span class="icon">👁</span>
    <span class="label">{{ isAccessibilityMode ? '标准模式' : '大字号模式' }}</span>
  </button>
</template>
```

### 3.3 字号规范（优化后）

| 用途 | 标准模式 | 高对比度模式 | 字重 | 行高 |
|------|----------|--------------|------|------|
| 页面标题 | 24px | 28px | Bold | 1.4 |
| 模块标题 | 20px | 22px | Medium | 1.4 |
| 卡片标题 | 18px | 20px | Medium | 1.5 |
| **正文** | **16px** | **18px** | Regular | 1.6 |
| 辅助文字 | 14px | 16px | Regular | 1.5 |
| 小标签 | 12px | 14px | Regular | 1.4 |

---

## 4. 布局系统

### 4.1 Grid 系统变量

```css
:root {
  /* Grid 列数 */
  --grid-cols: 12;
  --grid-gap: 24px;

  /* 容器宽度 */
  --container-sm: 640px;
  --container-md: 768px;
  --container-lg: 1024px;
  --container-xl: 1280px;
  --container-2xl: 1536px;

  /* 侧边栏宽度 */
  --sidebar-width: 280px;
  --sidebar-collapsed: 64px;
}
```

### 4.2 响应式断点系统

```css
/* 断点变量（供 JS 使用） */
:root {
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1280px;
  --breakpoint-2xl: 1536px;
}

/* 响应式媒体查询 */
@media (min-width: 1536px) { /* 2xl - 大桌面 */ }
@media (min-width: 1280px) { /* xl - 桌面 */ }
@media (min-width: 1024px) { /* lg - 小桌面/大平板 */ }
@media (min-width: 768px)  { /* md - 平板 */ }
@media (min-width: 640px)  { /* sm - 大手机 */ }
```

### 4.3 页面布局模式

#### 模式 A：居中内容区（3.1 - 3.4 模块）

```css
.layout-centered {
  max-width: var(--container-lg);  /* 1024px */
  margin: 0 auto;
  padding: 0 var(--spacing-6);
}
```

#### 模式 B：全屏工作台（3.5 渲染模块）

```css
.layout-workbench {
  display: grid;
  grid-template-columns: var(--sidebar-width) 1fr;
  height: calc(100vh - var(--header-height));

  /* 控制面板 */
  .control-panel {
    width: var(--sidebar-width);
    overflow-y: auto;
    border-right: 1px solid var(--border-light);
    padding: var(--spacing-4);
  }

  /* 预览区 - 铺满剩余空间 */
  .preview-area {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg-page);
    overflow: auto;
  }
}

/* 可折叠侧边栏 */
.layout-workbench.sidebar-collapsed {
  grid-template-columns: var(--sidebar-collapsed) 1fr;
}
```

### 4.4 PPT 预览区自适应

```css
.ppt-preview-container {
  /* 保持 16:9 宽高比 */
  aspect-ratio: 16 / 9;
  width: 100%;
  max-width: 1280px;  /* 限制最大宽度 */
  max-height: calc(100vh - 200px);  /* 留出控制区高度 */

  /* 居中显示 */
  margin: auto;

  /* 预览内容缩放 */
  .preview-content {
    transform-origin: center center;
    /* 缩放比例由 JS 根据容器大小动态计算 */
  }
}
```

---

## 5. Z-Index 层级管理

### 5.1 层级变量定义

```css
:root {
  /* 基础层级 */
  --z-base: 0;
  --z-dropdown: 100;
  --z-sticky: 200;
  --z-fixed: 300;
  --z-modal-backdrop: 400;
  --z-modal: 500;
  --z-popover: 600;
  --z-tooltip: 700;
  --z-toast: 800;
  --z-max: 9999;
}
```

### 5.2 层级使用规范

| 层级 | 变量 | 使用场景 |
|------|------|----------|
| 0 | `--z-base` | 普通内容 |
| 100 | `--z-dropdown` | 下拉菜单、Select 选项 |
| 200 | `--z-sticky` | 粘性表头、侧边栏 |
| 300 | `--z-fixed` | 固定 Header、底部操作栏 |
| 400 | `--z-modal-backdrop` | 模态框遮罩 |
| 500 | `--z-modal` | 模态框内容 |
| 600 | `--z-popover` | 弹出层（确认框等） |
| 700 | `--z-tooltip` | 提示气泡 |
| 800 | `--z-toast` | Toast 通知 |
| 9999 | `--z-max` | 最高层级（慎用） |

---

## 6. 动画与过渡

### 6.1 时间变量

```css
:root {
  /* 过渡时长 */
  --duration-instant: 50ms;    /* 即时反馈（如按钮按下） */
  --duration-fast: 150ms;      /* 快速过渡（如悬停效果） */
  --duration-normal: 250ms;    /* 常规过渡 */
  --duration-slow: 400ms;      /* 缓慢过渡（如模态框） */
  --duration-loading: 1500ms;  /* 加载动画周期 */

  /* 缓动函数 */
  --easing-default: cubic-bezier(0.4, 0, 0.2, 1);
  --easing-in: cubic-bezier(0.4, 0, 1, 1);
  --easing-out: cubic-bezier(0, 0, 0.2, 1);
  --easing-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);
  --easing-smooth: cubic-bezier(0.45, 0, 0.55, 1);  /* 用于骨架屏 */
}
```

### 6.2 骨架屏加载动画

PPT 生成可能需要几十秒，骨架屏动画需要节奏适中：

```css
/* 骨架屏 - 波浪动画（推荐） */
@keyframes skeleton-wave {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

.skeleton {
  background: linear-gradient(
    90deg,
    var(--bg-input) 0%,
    var(--bg-hover) 50%,
    var(--bg-input) 100%
  );
  background-size: 200% 100%;
  animation: skeleton-wave var(--duration-loading) var(--easing-smooth) infinite;
  border-radius: var(--radius-md);
}

/* 骨架屏变体 */
.skeleton-text {
  height: 1em;
  margin-bottom: 0.5em;
}

.skeleton-title {
  height: 1.5em;
  width: 60%;
}

.skeleton-card {
  height: 120px;
}
```

### 6.3 Spinner 加载指示器

```css
@keyframes spin {
  to { transform: rotate(360deg); }
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid var(--border-light);
  border-top-color: var(--color-brand);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* 大号 Spinner（用于页面级加载） */
.spinner-lg {
  width: 48px;
  height: 48px;
  border-width: 4px;
}
```

---

## 7. 空状态设计

### 7.1 空状态组件规范

```vue
<template>
  <div class="empty-state">
    <div class="empty-icon">
      <!-- SVG 图标 -->
    </div>
    <h3 class="empty-title">暂无大纲内容</h3>
    <p class="empty-desc">请先在上一步完成风格设计，然后生成大纲</p>
    <button class="btn-primary" @click="handleAction">
      返回风格设计
    </button>
  </div>
</template>
```

### 7.2 空状态图标风格

统一使用**线性图标 + 柔和配色**：

```css
.empty-icon {
  width: 120px;
  height: 120px;
  margin: 0 auto var(--spacing-6);

  /* 图标容器背景 */
  background: var(--color-brand-light);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-icon svg {
  width: 64px;
  height: 64px;
  stroke: var(--color-brand);
  stroke-width: 1.5;
  fill: none;
}
```

### 7.3 空状态场景定义

| 场景 | 图标 | 标题 | 描述 | 操作按钮 |
|------|------|------|------|----------|
| 大纲为空 | 📄 文档图标 | 暂无大纲 | 请先生成大纲 | 生成大纲 |
| 内容为空 | 📝 编辑图标 | 暂无内容 | 请先完成大纲生成 | 返回大纲 |
| 生成失败 | ⚠️ 警告图标 | 生成失败 | {错误信息} | 重新生成 |
| 无搜索结果 | 🔍 搜索图标 | 未找到结果 | 尝试其他关键词 | 清除搜索 |
| 网络错误 | 🌐 网络图标 | 网络连接失败 | 请检查网络设置 | 重试 |

### 7.4 SVG 图标集

```html
<!-- 空文档图标 -->
<svg viewBox="0 0 64 64" class="empty-icon-svg">
  <rect x="12" y="8" width="40" height="48" rx="4" />
  <line x1="20" y1="20" x2="44" y2="20" />
  <line x1="20" y1="28" x2="44" y2="28" />
  <line x1="20" y1="36" x2="36" y2="36" />
</svg>

<!-- 生成失败图标 -->
<svg viewBox="0 0 64 64" class="empty-icon-svg">
  <circle cx="32" cy="32" r="24" />
  <line x1="32" y1="20" x2="32" y2="36" />
  <circle cx="32" cy="44" r="2" fill="currentColor" />
</svg>
```

---

## 8. 通用透明度变量

```css
:root {
  /* 透明度 */
  --opacity-disabled: 0.5;      /* 禁用状态 */
  --opacity-hover-overlay: 0.04; /* 悬停遮罩 */
  --opacity-active-overlay: 0.08; /* 按下遮罩 */
  --opacity-backdrop: 0.5;      /* 模态框背景遮罩 */
  --opacity-skeleton: 0.7;      /* 骨架屏 */
}

/* 禁用状态通用样式 */
.disabled,
[disabled] {
  opacity: var(--opacity-disabled);
  cursor: not-allowed;
  pointer-events: none;
}
```

---

## 9. 组件规范

### 9.1 按钮组件（统一交互色）

#### 主按钮（全局统一品牌蓝）

```css
.btn-primary {
  /* 使用统一的品牌色，不随模块变化 */
  background: var(--color-brand);
  color: #FFFFFF;
  padding: 12px 24px;
  border-radius: var(--radius-md);
  font-weight: 500;
  font-size: var(--font-size-base);
  border: none;
  cursor: pointer;
  transition: all var(--duration-fast) var(--easing-default);
}

.btn-primary:hover {
  background: var(--color-brand-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(var(--color-brand-rgb), 0.3);
}

.btn-primary:active {
  background: var(--color-brand-active);
  transform: translateY(0);
}

.btn-primary:disabled {
  opacity: var(--opacity-disabled);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}
```

#### 次要按钮（中性灰，不随模块变化）

```css
.btn-secondary {
  background: var(--bg-card);
  color: var(--text-primary);
  padding: 12px 24px;
  border-radius: var(--radius-md);
  font-weight: 500;
  border: 1px solid var(--border-default);
  transition: all var(--duration-fast) var(--easing-default);
}

.btn-secondary:hover {
  background: var(--bg-hover);
  border-color: var(--border-default);
}
```

#### 危险按钮

```css
.btn-danger {
  background: var(--color-error);
  color: #FFFFFF;
  /* 其他样式同 .btn-primary */
}
```

### 9.2 卡片组件（模块色仅用于左侧标记条）

```css
.card-base {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-6);
  box-shadow: var(--shadow-card);

  /* 左侧装饰条使用模块色 */
  border-left: 4px solid var(--color-module);

  transition: box-shadow var(--duration-fast),
              transform var(--duration-fast);
}

.card-base:hover {
  box-shadow: var(--shadow-hover);
  transform: translateY(-2px);
}
```

### 9.3 输入框组件

```css
.input-base {
  width: 100%;
  padding: 12px 16px;
  background: var(--bg-input);
  border: 2px solid transparent;
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);
  color: var(--text-primary);
  transition: all var(--duration-fast);
}

.input-base:focus {
  outline: none;
  background: var(--bg-card);
  border-color: var(--color-brand);  /* 使用品牌色，不是模块色 */
  box-shadow: 0 0 0 4px var(--color-brand-light);
}

.input-base::placeholder {
  color: var(--text-placeholder);
}

/* 高对比度模式下的焦点环 */
.accessibility-mode .input-base:focus {
  box-shadow: 0 0 0 var(--focus-ring-width) var(--color-brand-light);
}
```

---

## 10. 步骤导航组件

### 10.1 设计更新

- 步骤圆点使用各自的模块装饰色（仅装饰）
- 点击区域足够大（适合触屏和高龄用户）
- 已完成步骤显示 ✓ 图标

### 10.2 组件结构

```vue
<template>
  <nav class="step-progress" role="navigation" aria-label="流程步骤">
    <div
      v-for="(step, index) in steps"
      :key="step.id"
      class="step-item"
      :class="{
        'completed': index < currentStep,
        'active': index === currentStep,
        'pending': index > currentStep
      }"
      @click="navigateTo(index)"
      role="button"
      :aria-current="index === currentStep ? 'step' : undefined"
      tabindex="0"
    >
      <div
        class="step-indicator"
        :style="{ '--step-color': step.color }"
      >
        <span v-if="index < currentStep" class="check-icon">✓</span>
        <span v-else>{{ index + 1 }}</span>
      </div>
      <div class="step-label">{{ step.label }}</div>
    </div>

    <!-- 进度条 -->
    <div class="progress-bar" aria-hidden="true">
      <div
        class="progress-fill"
        :style="{ width: progressWidth }"
      ></div>
    </div>
  </nav>
</template>
```

---

## 11. 完整 tokens.css

```css
:root {
  /* ===== 品牌色（交互按钮专用）===== */
  --color-brand: #2563EB;
  --color-brand-hover: #1D4ED8;
  --color-brand-active: #1E40AF;
  --color-brand-light: #DBEAFE;
  --color-brand-rgb: 37, 99, 235;
  --color-brand-hsl: 217, 91%, 60%;

  /* ===== 模块装饰色（仅用于视觉标识）===== */
  --color-31: #6366F1;
  --color-31-light: #E0E7FF;
  --color-31-hsl: 239, 84%, 67%;

  --color-32: #0EA5E9;
  --color-32-light: #E0F2FE;
  --color-32-hsl: 199, 89%, 48%;

  --color-33: #8B5CF6;
  --color-33-light: #EDE9FE;
  --color-33-hsl: 258, 90%, 66%;

  --color-34: #F97316;
  --color-34-light: #FFEDD5;
  --color-34-hsl: 25, 95%, 53%;

  --color-35: #EC4899;
  --color-35-light: #FCE7F3;
  --color-35-hsl: 330, 81%, 60%;

  /* ===== 状态颜色 ===== */
  --color-success: #22C55E;
  --color-success-light: #DCFCE7;
  --color-warning: #EAB308;
  --color-warning-light: #FEF9C3;
  --color-error: #EF4444;
  --color-error-light: #FEE2E2;
  --color-info: #3B82F6;
  --color-info-light: #DBEAFE;

  /* ===== 页面背景 ===== */
  --bg-page: #FAFAF8;
  --bg-card: #FFFFFF;
  --bg-input: #F5F5F4;
  --bg-hover: #F0F0EE;
  --bg-disabled: #E5E5E3;

  /* ===== 文字颜色（WCAG AA 合规）===== */
  --text-primary: #1F2937;
  --text-secondary: #4B5563;
  --text-muted: #6B7280;
  --text-placeholder: #9CA3AF;

  /* ===== 边框颜色 ===== */
  --border-light: #E5E7EB;
  --border-default: #D1D5DB;
  --border-focus: var(--color-brand);

  /* ===== 字体 ===== */
  --font-primary: "Alibaba PuHuiTi", -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
  --font-size-xs: 12px;
  --font-size-sm: 14px;
  --font-size-base: 16px;
  --font-size-lg: 18px;
  --font-size-xl: 20px;
  --font-size-2xl: 24px;

  /* ===== 间距 ===== */
  --spacing-1: 4px;
  --spacing-2: 8px;
  --spacing-3: 12px;
  --spacing-4: 16px;
  --spacing-5: 20px;
  --spacing-6: 24px;
  --spacing-8: 32px;
  --spacing-10: 40px;
  --spacing-12: 48px;

  /* ===== 圆角 ===== */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;

  /* ===== 阴影 ===== */
  --shadow-card: 0 1px 3px rgba(0, 0, 0, 0.05),
                 0 1px 2px rgba(0, 0, 0, 0.03);
  --shadow-hover: 0 4px 12px rgba(0, 0, 0, 0.08),
                  0 2px 4px rgba(0, 0, 0, 0.04);
  --shadow-modal: 0 20px 40px rgba(0, 0, 0, 0.15);

  /* ===== 动画 ===== */
  --duration-instant: 50ms;
  --duration-fast: 150ms;
  --duration-normal: 250ms;
  --duration-slow: 400ms;
  --duration-loading: 1500ms;

  --easing-default: cubic-bezier(0.4, 0, 0.2, 1);
  --easing-in: cubic-bezier(0.4, 0, 1, 1);
  --easing-out: cubic-bezier(0, 0, 0.2, 1);
  --easing-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);
  --easing-smooth: cubic-bezier(0.45, 0, 0.55, 1);

  /* ===== 透明度 ===== */
  --opacity-disabled: 0.5;
  --opacity-hover-overlay: 0.04;
  --opacity-active-overlay: 0.08;
  --opacity-backdrop: 0.5;

  /* ===== Z-Index 层级 ===== */
  --z-base: 0;
  --z-dropdown: 100;
  --z-sticky: 200;
  --z-fixed: 300;
  --z-modal-backdrop: 400;
  --z-modal: 500;
  --z-popover: 600;
  --z-tooltip: 700;
  --z-toast: 800;
  --z-max: 9999;

  /* ===== 布局 ===== */
  --header-height: 64px;
  --sidebar-width: 280px;
  --sidebar-collapsed: 64px;
  --container-lg: 1024px;
  --container-xl: 1280px;

  /* ===== 无障碍 ===== */
  --focus-ring-width: 3px;
}

/* ===== 高对比度/大字号模式 ===== */
:root.accessibility-mode {
  --font-size-base: 18px;
  --font-size-lg: 20px;
  --font-size-xl: 22px;
  --font-size-2xl: 28px;
  --text-secondary: #374151;
  --text-muted: #4B5563;
  --focus-ring-width: 4px;
}
```

---

## 12. 模块页面应用模板

```vue
<template>
  <div class="module-page">
    <!-- 设置模块装饰色（仅用于左侧标记条、进度条等） -->
    <div class="module-content">
      <!-- 内容区 -->
    </div>
  </div>
</template>

<style scoped>
.module-page {
  /* 模块装饰色 - 仅用于装饰性元素 */
  --color-module: var(--color-33);
  --color-module-light: var(--color-33-light);
}

/* 卡片左侧标记条使用模块色 */
.card {
  border-left-color: var(--color-module);
}

/* 按钮仍然使用统一的品牌色 */
.btn-primary {
  background: var(--color-brand); /* 不是 var(--color-module) */
}
</style>
```

---

## 13. 验证清单

### 功能测试
- [ ] 字体正确加载
- [ ] 步骤导航正常工作
- [ ] 各模块显示对应装饰色
- [ ] **所有主按钮颜色一致（品牌蓝）**
- [ ] 卡片悬停效果正常
- [ ] 输入框聚焦高亮正常
- [ ] 高对比度模式切换正常

### 无障碍测试
- [ ] 所有文本对比度 >= 4.5:1
- [ ] 焦点环清晰可见
- [ ] 键盘导航可用
- [ ] 高对比度模式下字号增大

### 响应式测试
- [ ] 桌面端 (1920px)
- [ ] 笔记本 (1366px)
- [ ] 平板 (768px)
- [ ] 3.5 模块全屏工作台布局正常

### 状态测试
- [ ] 骨架屏动画流畅（不卡顿、不太快）
- [ ] 空状态图标显示正确
- [ ] Toast 层级正确（不被遮挡）
- [ ] Modal 层级正确

---

## 更新日志

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2026-01-2 | v1.0 | 初始设计系统文档 |
| 2026-01-26 | v2.0 | 修复色彩语义冲突、增强无障碍、完善布局、补充状态设计 |

### v2.0 主要改动

1. **色彩系统重构**
   - 分离装饰色和交互色
   - 主按钮统一使用品牌蓝
   - 调整 3.2 和 3.4 模块色避免与状态色冲突

2. **无障碍增强**
   - 正文字号从 15px 提升到 16px
   - 次要文字对比度从 5.0:1 提升到 7.5:1
   - 新增高对比度/大字号模式

3. **布局系统**
   - 新增 Grid 系统变量
   - 3.5 模块采用全屏工作台布局
   - PPT 预览区自适应宽高比

4. **状态设计**
   - 定义骨架屏波浪动画（1.5s 周期）
   - 统一空状态组件规范
   - 统一 SVG 图标风格

5. **工程规范**
   - 新增 z-index 层级管理
   - 新增透明度变量
   - 新增 HSL 色值（便于调节）

---

> 文档维护：前端开发团队
> 最后更新：2026-01-26
