<template>
  <div class="demo-page">
    <div class="container">
      <!-- 头部 -->
      <header class="page-header slide-up">
        <h1>智绘课堂 <span class="text-gradient">Design System</span></h1>
        <p class="subtitle">Frontend Design Concept: Warm, Bold & Memorable</p>
        <div class="header-actions">
          <button class="btn btn-primary hover-lift">
            <span class="icon">✨</span> Experience Now
          </button>
          <button class="btn btn-secondary">Documentation</button>
        </div>
      </header>

      <!-- 1. 色彩展示 -->
      <section class="section slide-up" style="animation-delay: 100ms">
        <h2 class="section-title text-underline-accent">Brand Colors</h2>
        <div class="color-grid">
          <!-- Primary -->
          <div class="color-card bg-primary text-white card-tilted">
            <div class="color-info">
              <span class="color-name">Deep Teal</span>
              <span class="color-hex">#0D4C4A</span>
              <span class="color-usage">Primary Brand</span>
            </div>
          </div>
          <div class="color-card bg-primary-light text-white">
             <div class="color-info">
              <span class="color-name">Teal Light</span>
              <span class="color-hex">#1A6B68</span>
              <span class="color-usage">Hover State</span>
            </div>
          </div>
          <!-- Accent -->
          <div class="color-card bg-accent text-white pulse-accent">
            <div class="color-info">
              <span class="color-name">Warm Amber</span>
              <span class="color-hex">#D97706</span>
              <span class="color-usage">Accent / CTA</span>
            </div>
          </div>
          <div class="color-card bg-accent-light text-dark">
             <div class="color-info">
              <span class="color-name">Amber Light</span>
              <span class="color-hex">#FEF3C7</span>
              <span class="color-usage">Highlights</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 2. 排版展示 -->
      <section class="section slide-up" style="animation-delay: 200ms">
        <h2 class="section-title text-underline-accent">Typography</h2>
        <div class="glass-card p-6">
          <h1 class="display-text mb-4">Make Learning <span class="text-gradient">Beautiful</span></h1>
          <h2 class="mb-3">Heading Level 2 - 思源黑体 Bold</h2>
          <h3 class="mb-3">Heading Level 3 - Modern & Clean</h3>
          <p class="lead mb-4">
             "智绘课堂" 运用前沿 AI 技术，帮助教师在几分钟内生成精美的教学 PPT。
             <span class="text-gradient">让 AI 成为你的教学助手。</span>
          </p>
          <p class="text-muted">
            Small text / Muted text example. Designed for legibility and comfort.
          </p>
        </div>
      </section>

      <!-- 3. 卡片效果 -->
      <section class="section slide-up" style="animation-delay: 300ms">
        <h2 class="section-title text-underline-accent">Cards & Effects</h2>
        <div class="grid-3">
          <!-- Tilted Card -->
          <div class="card card-tilted">
             <div class="module-badge bg-primary mb-4">Unique</div>
            <h3 class="card-title">Tilted Card</h3>
            <p class="card-desc">
              Breaking the grid with a subtle -2deg rotation. 
              Interactive hover state restores balance.
            </p>
          </div>

          <!-- Glass Card -->
          <div class="card glass-card hover-lift">
             <div class="module-badge bg-accent mb-4">Glassmorphism</div>
            <h3 class="card-title">Glass Card</h3>
            <p class="card-desc">
              Frosted glass effect with background blur.
              Perfect for layering over detailed backgrounds.
            </p>
          </div>

          <!-- Hover Lift Card -->
          <div class="card hover-lift">
            <div class="module-badge bg-secondary mb-4">Interactive</div>
            <h3 class="card-title">Hover Lift</h3>
            <p class="card-desc">
              Smooth elevation change on hover to suggest interactivity.
              Uses the new shadow system.
            </p>
          </div>
        </div>
      </section>

      <!-- 4. 按钮与交互 -->
      <section class="section slide-up" style="animation-delay: 400ms">
         <h2 class="section-title text-underline-accent">Buttons & Inputs</h2>
         <div class="glass-card p-6">
            <div class="flex gap-4 mb-6 flex-wrap">
              <button class="btn btn-primary">Primary Button</button>
              <button class="btn btn-primary hover-lift">Lift Button</button>
              <button class="btn btn-secondary">Secondary</button>
              <button class="btn btn-ghost">Ghost Button</button>
              <button class="btn btn-danger">Danger</button>
            </div>
            
            <div class="divider"></div>

            <div class="grid-2 gap-6">
               <div class="form-group">
                  <label class="label">Input Field</label>
                  <input type="text" class="input" placeholder="Type something..." />
               </div>
               <div class="form-group">
                  <label class="label">Input with Error</label>
                  <input type="text" class="input input-error" value="Invalid Value" />
               </div>
            </div>
         </div>
      </section>

      <!-- 5. 模块标识 (原有系统兼容性测试) -->
      <section class="section slide-up" style="animation-delay: 500ms">
         <h2 class="section-title text-underline-accent">Module Compatibility</h2>
         <div class="flex gap-4 flex-wrap">
            <span class="badge" style="background: var(--color-31); color: white">3.1 Intent</span>
            <span class="badge" style="background: var(--color-32); color: white">3.2 Style</span>
            <span class="badge" style="background: var(--color-33); color: white">3.3 Outline</span>
            <span class="badge" style="background: var(--color-34); color: white">3.4 Content</span>
            <span class="badge" style="background: var(--color-35); color: white">3.5 Render</span>
         </div>
      </section>

    </div>
  </div>
</template>

<style scoped>
.demo-page {
  min-height: 100vh;
  padding: 4rem 0;
}

.page-header {
  text-align: center;
  margin-bottom: 5rem;
}

.page-header h1 {
  font-size: 3.5rem;
  font-weight: 900;
  margin-bottom: 1rem;
  color: var(--color-brand);
}

.subtitle {
  font-size: 1.5rem;
  color: var(--text-secondary);
  margin-bottom: 2rem;
}

.section {
  margin-bottom: 5rem;
}

.section-title {
  font-size: 2rem;
  font-weight: 800;
  margin-bottom: 2rem;
  color: var(--text-primary);
}

/* Color Grid */
.color-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.color-card {
  height: 160px;
  border-radius: var(--radius-xl);
  padding: 1.5rem;
  display: flex;
  align-items: flex-end;
  transition: all 0.3s ease;
}

.color-info {
  display: flex;
  flex-direction: column;
}

.color-name { font-weight: bold; font-size: 1.1rem; }
.color-hex { opacity: 0.8; font-family: monospace; }
.color-usage { font-size: 0.8rem; opacity: 0.6; margin-top: 0.25rem; text-transform: uppercase; letter-spacing: 0.5px; }

/* Utility Backgrounds */
.bg-primary { background: var(--color-brand); }
.bg-primary-light { background: var(--color-brand-hover); }
.bg-accent { background: var(--color-accent); }
.bg-accent-light { background: var(--color-accent-light); }
.bg-secondary { background: var(--color-secondary); }

.text-white { color: white; }
.text-dark { color: var(--text-primary); }

/* Typography */
.display-text {
  font-size: 3rem;
  font-weight: 900;
  line-height: 1.1;
  color: var(--color-brand);
}

.lead {
  font-size: 1.25rem;
  color: var(--text-secondary);
  line-height: 1.6;
}

.p-6 { padding: 2rem; }

/* Grid Layouts */
.grid-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
}

.grid-2 {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 2rem;
}

@media (max-width: 768px) {
  .grid-3, .grid-2 { grid-template-columns: 1fr; }
  .page-header h1 { font-size: 2.5rem; }
}

.slide-up {
  animation: slide-up 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) both;
}
</style>
