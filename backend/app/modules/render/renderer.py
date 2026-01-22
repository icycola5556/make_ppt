"""
Module 3.5: HTML渲染器 (Renderer)
负责 Jinja2 模板渲染和静态资源管理。纯IO操作，不含API调用。
"""
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader

from ...common.schemas import SlideDeckContent, StyleConfig, TeachingRequest
from ...common.llm_client import LLMClient
from .core import RenderResult, extract_bullets
from .config import TEMPLATE_DIR, SRC_STATIC_DIR, SRC_STYLES_DIR
from .engine import LayoutEngine

class HTMLRenderer:
    """
    HTML 渲染器
    """

    @staticmethod
    async def render(
        deck_content: SlideDeckContent,
        style_config: StyleConfig,
        teaching_request: TeachingRequest,
        session_id: str,
        output_dir: str,
        llm: Optional[LLMClient] = None,
    ) -> RenderResult:
        """渲染主入口"""
        
        # 1. 准备 Jinja2
        env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
        
        slides_data = []
        all_image_slots = []
        layouts_used: Dict[str, int] = {}
        warnings = []
        
        # 2. 处理每一页 (Layout Decision)
        previous_layout = None
        for page in deck_content.pages:
            # 调用 Engine 决定布局
            layout_id, image_slots = await LayoutEngine.resolve_layout(
                page, teaching_request, page.index, previous_layout, llm
            )
            previous_layout = layout_id
            
            layouts_used[layout_id] = layouts_used.get(layout_id, 0) + 1
            all_image_slots.extend(image_slots)
            
            # 提取要点
            bullets = extract_bullets(page)
            
            # 动态样式变量
            dynamic_vars = HTMLRenderer._calculate_dynamic_layout_vars(
                len(page.title) + sum(len(b) for b in bullets), 
                layout_id
            )
            
            slides_data.append({
                "layout_id": layout_id,
                "slide_type": page.slide_type,
                "title": page.title,
                "bullets": bullets,
                "image_slots": image_slots,
                "dynamic_style": dynamic_vars,
            })
            
        # 3. 生成 CSS 变量
        css_variables = HTMLRenderer._generate_css_variables(style_config)
        
        # 4. 渲染 HTML
        template = env.get_template("base.html")
        html_content = template.render(
            deck_title=deck_content.deck_title,
            slides=slides_data,
            theme_name="professional",
            css_variables=css_variables,
            poll_script=HTMLRenderer._generate_polling_script(session_id, len(all_image_slots)),
        )
        
        # 5. 复制资源 (Assets)
        HTMLRenderer._copy_assets(output_dir)
        
        # 6. 保存文件
        out_path = Path(output_dir) / "index.html"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        return RenderResult(
            session_id=session_id,
            html_path=f"outputs/{session_id}/index.html",
            html_content=html_content,
            image_slots=all_image_slots,
            metadata={
                "total_pages": len(deck_content.pages),
                "layouts_used": layouts_used
            },
            warnings=warnings,
            total_pages=len(deck_content.pages),
            layouts_used=layouts_used
        )

    @staticmethod
    def _copy_assets(output_dir: str):
        try:
            target_static = Path(output_dir) / "static"
            if target_static.exists(): shutil.rmtree(target_static)
            if SRC_STATIC_DIR.exists(): shutil.copytree(SRC_STATIC_DIR, target_static)
            
            target_styles = Path(output_dir) / "styles"
            if target_styles.exists(): shutil.rmtree(target_styles)
            if SRC_STYLES_DIR.exists(): shutil.copytree(SRC_STYLES_DIR, target_styles)
        except Exception as e:
            print(f"[Render] ⚠️ Failed to copy assets: {e}")

    @staticmethod
    def _calculate_dynamic_layout_vars(text_len: int, layout_id: str) -> str:
        if layout_id == "title_bullets_right_img":
            if text_len < 150:
                return "--col-text: 1fr; --col-img: 1.5fr;"
            elif text_len > 400:
                return "--col-text: 2fr; --col-img: 1fr;"
            else:
                return "--col-text: 1.2fr; --col-img: 1fr;"
        return ""

    @staticmethod
    def _generate_css_variables(style: StyleConfig) -> str:
        colors = style.color
        font = style.font
        layout = style.layout
        
        return f"""
        /* Colors */
        --color-primary: {colors.primary};
        --color-secondary: {colors.secondary};
        --color-accent: {colors.accent};
        --color-text: {colors.text};
        --color-muted: {colors.muted};
        --color-background: {colors.background};
        --color-warning: {colors.warning};
        --color-surface: {colors.surface or 'rgba(255,255,255,0.8)'};
        --color-bg-gradient: {colors.background_gradient or 'none'};
        
        /* Fonts */
        --font-family-title: {font.title_family}, "PingFang SC", sans-serif;
        --font-family-body: {font.body_family}, "PingFang SC", sans-serif;
        --font-size-title: {font.title_size}px;
        --font-size-body: {font.body_size}px;
        --line-height-body: {font.line_height};
        
        /* Layout */
        --layout-border-radius: {layout.border_radius};
        --layout-alignment: {layout.alignment};
        """

    @staticmethod
    def _generate_polling_script(session_id: str, total_slots: int) -> str:
        # 简化的 polling script，引用旧版逻辑 (这里仅示意，实际应完整复制)
        # 为了节省 token，我这里会写入一个占位符，因为前端逻辑比较长
        # 实际代码中我会把 html_renderer.py 里的 _generate_polling_script 完整移过来
        # ⚠️ 这里为了完整性，我必须把完整脚本写回去，否则前端会挂
        
        return f"""
    <script>
        (function() {{
            const sessionId = "{session_id}";
            const totalSlots = {total_slots};
            const POLL_INTERVAL = 3000;
            let generationStarted = false;
            let isEmbedded = window.self !== window.top;
            let isOfflineMode = window.location.protocol === 'file:';
            
            console.log("[RenderEngine] Script initialized. Mode: " + 
                (isOfflineMode ? "Offline (Local File)" : (isEmbedded ? "Passive (Embedded)" : "Active (Standalone)")));

            document.addEventListener('DOMContentLoaded', function() {{
                if (isOfflineMode) {{
                    console.log("[RenderEngine] Offline mode detected, checking for local images...");
                    checkOfflineImages();
                    const generateBtn = document.getElementById('generateImagesBtn');
                    if (generateBtn) generateBtn.style.display = 'none';
                    const progressStatus = document.getElementById('imageProgressStatus');
                    if (progressStatus) progressStatus.textContent = '📂 离线模式 - 加载本地图片';
                }}
            }});

            function checkOfflineImages() {{
                const placeholders = document.querySelectorAll('.image-placeholder');
                placeholders.forEach(el => {{
                    const slotId = el.dataset.slotId;
                    if (!slotId || el.dataset.loaded) return;
                    const offlinePath = `./images/${{slotId}}.png`;
                    const img = new Image();
                    img.onload = function() {{ renderImage(el, offlinePath); }};
                    img.src = offlinePath;
                }});
            }}

            function renderImage(container, src) {{
                if (container.dataset.loaded) return;
                container.innerHTML = 
                    `<img src="${{src}}" 
                          style="width:100%;height:100%;object-fit:contain;
                                 border-radius:var(--layout-border-radius, 8px);opacity:0;transition:opacity 0.5s"
                          onload="this.style.opacity=1"
                          onerror="this.outerHTML='<div class=\\'error\\'>图片加载失败</div>'">`;
                container.dataset.loaded = "true";
                container.classList.remove('loading');
                container.classList.add('loaded');
            }}

            window.addEventListener('message', function(event) {{
                const data = event.data;
                if (data && data.type === 'IMAGE_STATUS_UPDATE' && data.sessionId === sessionId) {{
                    updateUIFromData(data.payload);
                }}
            }});
            
            setTimeout(() => {{
                if (!isEmbedded && !isOfflineMode) checkImageStatus();
            }}, 1000);
            
            window.startGeneration = async function() {{
                const btn = document.getElementById('generateImagesBtn');
                if (btn) btn.disabled = true;
                try {{
                    const response = await fetch(`/api/workflow/render/generate/${{sessionId}}`, {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }}
                    }});
                    const data = await response.json();
                    if (data.ok) {{
                        generationStarted = true;
                        if (btn) btn.textContent = '生成任务已启动...';
                        if (isEmbedded) {{
                            window.parent.postMessage({{ type: 'GENERATION_STARTED', sessionId: sessionId }}, '*');
                        }} else {{
                            checkImageStatus();
                        }}
                    }} else {{
                        alert('启动生成失败: ' + (data.error || 'Unknown error'));
                        if (btn) btn.disabled = false;
                    }}
                }} catch (e) {{
                    console.error('Failed to start generation:', e);
                    if (btn) btn.disabled = false;
                }}
            }};
            
            function updateUIFromData(data) {{
                const images = data.images || {{}};
                let done = 0, failed = 0, generating = 0;
                
                for (const [slotId, imageData] of Object.entries(images)) {{
                    if (imageData.status === 'done') {{
                        done++; updateSlotImage(slotId, imageData);
                    }} else if (imageData.status === 'failed') {{
                        failed++; showSlotError(slotId, imageData.error);
                    }} else if (imageData.status === 'generating') {{
                        generating++; showSlotLoading(slotId);
                    }}
                }}
                
                const total = data.total || totalSlots;
                _updateProgressBar(done + failed, total);
                _updateStatusPanel(done, failed, generating, total);
            }}
            
            function checkImageStatus() {{
                fetch(`/api/workflow/render/status/${{sessionId}}`)
                    .then(response => response.json())
                    .then(data => {{
                        if (data.ok) {{
                            updateUIFromData(data);
                            const done = Object.values(data.images || {{}}).filter(i => i.status === 'done').length;
                            const failed = Object.values(data.images || {{}}).filter(i => i.status === 'failed').length;
                            const total = data.total || totalSlots;
                            if (done + failed < total) setTimeout(checkImageStatus, POLL_INTERVAL);
                        }} else setTimeout(checkImageStatus, POLL_INTERVAL);
                    }})
                    .catch(e => setTimeout(checkImageStatus, POLL_INTERVAL));
            }}

            function _updateProgressBar(doneCount, total) {{
                const progressBar = document.getElementById('imageProgressBar');
                const progressText = document.getElementById('imageProgressText');
                if (progressBar && total > 0) {{
                    const percent = Math.round((doneCount / total) * 100);
                    progressBar.style.width = percent + '%';
                    progressBar.textContent = percent + '%';
                }}
                if (progressText) progressText.textContent = `${{doneCount}} / ${{total}}`;
            }}

            function _updateStatusPanel(done, failed, generating, total) {{
                const progressStatus = document.getElementById('imageProgressStatus');
                const generateBtn = document.getElementById('generateImagesBtn');
                if (!progressStatus) return;

                if (done === total && total > 0) {{
                    progressStatus.textContent = '✅ 图片生成完成！';
                    if (generateBtn) generateBtn.style.display = 'none';
                }} else if (failed > 0 && generating === 0) {{
                    progressStatus.textContent = `⚠️ ${{failed}}张图片生成失败`;
                    if (generateBtn) {{ generateBtn.disabled = false; generateBtn.textContent = '重试失败图片'; }}
                }} else if (generating > 0 || (done + failed > 0)) {{
                    progressStatus.textContent = `⏳ 正在生成... (${{done}} / ${{total}})`;
                    if (generateBtn) {{ generateBtn.disabled = true; generateBtn.textContent = '生成中...'; }}
                }}
            }}
            
            function updateSlotImage(slotId, imageData) {{
                const placeholder = document.querySelector(`.image-placeholder[data-slot-id="${{slotId}}"]`);
                if (!placeholder || placeholder.dataset.loaded) return;
                const imgSrc = imageData.url || `/api/workflow/render/image/${{sessionId}}/${{slotId}}`;
                renderImage(placeholder, imgSrc);
            }}
            
            function showSlotLoading(slotId) {{
                const placeholder = document.querySelector(`.image-placeholder[data-slot-id="${{slotId}}"]`);
                if (!placeholder || placeholder.dataset.loaded || placeholder.classList.contains('loading')) return;
                placeholder.innerHTML = `<div class="loading-container"><div class="loading-spinner"></div><p>正在生成...</p></div>`;
                placeholder.classList.add('loading');
            }}
            
            function showSlotError(slotId, error) {{
                const placeholder = document.querySelector(`.image-placeholder[data-slot-id="${{slotId}}"]`);
                if (!placeholder) return;
                placeholder.innerHTML = `<div class="error-container"><p>❌ 生成失败</p><button onclick="retrySlot('${{slotId}}')">重试</button></div>`;
                placeholder.classList.remove('loading');
                placeholder.dataset.loaded = "";
            }}
            
            window.retrySlot = function(slotId) {{
                fetch(`/api/workflow/render/retry/${{sessionId}}/${{slotId}}`, {{ method: 'POST' }})
                .then(r => r.json()).then(d => {{ if(d.ok) {{ showSlotLoading(slotId); if(!isEmbedded) checkImageStatus(); }} }});
            }};
        }})();
    </script>
        """
