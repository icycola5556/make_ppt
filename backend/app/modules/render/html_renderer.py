"""
Module 3.5: HTML 渲染引擎

使用 Jinja2 模板生成 HTML 幻灯片
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader

from ...common.schemas import SlideDeckContent, SlidePage, StyleConfig, TeachingRequest
from ...common.llm_client import LLMClient
from .schemas import RenderResult, ImageSlotRequest
from .layout_engine import resolve_layout


# 模板目录
TEMPLATE_DIR = Path(__file__).parent / "templates"


async def render_html_slides(
    deck_content: SlideDeckContent,
    style_config: StyleConfig,
    teaching_request: TeachingRequest,
    session_id: str,
    output_dir: str,
    llm: Optional[LLMClient] = None,
) -> RenderResult:
    """
    渲染 HTML 幻灯片 (Async)

    Args:
        deck_content: 3.4 模块输出的内容
        style_config: 3.2 模块输出的风格配置
        teaching_request: 3.1 模块输出的教学需求
        session_id: 会话 ID
        output_dir: 输出目录
        llm: LLM客户端 (可选)

    Returns:
        RenderResult: 渲染结果,包含 HTML 路径和图片插槽
    """

    # 初始化 Jinja2 环境
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))

    # 准备渲染数据
    slides_data = []
    all_image_slots = []
    layouts_used: Dict[str, int] = {}
    warnings = []

    # 处理每一页
    for page in deck_content.pages:
        # 选择布局并生成图片插槽 (Async call)
        layout_id, image_slots = await resolve_layout(
            page, teaching_request, page.index, llm
        )

        # 统计布局使用
        layouts_used[layout_id] = layouts_used.get(layout_id, 0) + 1

        # 提取要点
        bullets = _extract_bullets(page)

        # 检测文本溢出
        text_warnings = _check_text_overflow(page, layout_id)
        warnings.extend(text_warnings)

        # 构建页面数据
        slide_data = {
            "layout_id": layout_id,
            "slide_type": page.slide_type,
            "title": page.title,
            "bullets": bullets,
            "image_slots": image_slots,
        }
        slides_data.append(slide_data)
        all_image_slots.extend(image_slots)

    # 生成 CSS Variables
    css_variables = _generate_css_variables(style_config)

    # 渲染 HTML
    template = env.get_template("base.html")
    html_content = template.render(
        deck_title=deck_content.deck_title,
        slides=slides_data,
        theme_name="professional",
        css_variables=css_variables,
        poll_script=_generate_polling_script(session_id, len(all_image_slots)),
    )

    # 保存 HTML 文件
    output_path = Path(output_dir) / f"{session_id}.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 返回结果
    return RenderResult(
        session_id=session_id,
        html_path=str(output_path),
        html_content=html_content,
        image_slots=all_image_slots,
        metadata={
            "total_pages": len(deck_content.pages),
            "layouts_used": layouts_used,
            "total_image_slots": len(all_image_slots),
        },
        warnings=warnings,
        total_pages=len(deck_content.pages),
        layouts_used=layouts_used,
    )


def _generate_polling_script(session_id: str, total_slots: int = 0) -> str:
    """生成用于轮询或接收图片状态的 JS 脚本 (支持 Passive 模式)"""
    return f"""
    <script>
        (function() {{
            const sessionId = "{session_id}";
            const totalSlots = {total_slots};
            const POLL_INTERVAL = 3000;
            let generationStarted = false;
            let isEmbedded = window.self !== window.top;
            
            console.log("[RenderEngine] Script initialized. Mode: " + (isEmbedded ? "Passive (Embedded)" : "Active (Standalone)"));

            // 1. 监听来自父窗口 (Vue) 的消息
            window.addEventListener('message', function(event) {{
                // 简单的来源验证，如果需要的话可以增加
                const data = event.data;
                if (data && data.type === 'IMAGE_STATUS_UPDATE' && data.sessionId === sessionId) {{
                    console.log("[RenderEngine] Received status update from parent");
                    updateUIFromData(data.payload);
                }}
            }});
            
            // 2. 页面加载后初始化
            setTimeout(() => {{
                if (!isEmbedded) {{
                    checkImageStatus(); // 如果不是内嵌模式，主动开始轮询
                }}
            }}, 1000);
            
            // 触发生成 (API 调用保持不变，但增加通知父窗口的逻辑)
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
                        
                        // 如果在 iframe 中，通知父窗口开始轮询
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
                let done = 0;
                let failed = 0;
                let generating = 0;
                
                for (const [slotId, imageData] of Object.entries(images)) {{
                    if (imageData.status === 'done') {{
                        done++;
                        updateSlotImage(slotId, imageData);
                    }} else if (imageData.status === 'failed') {{
                        failed++;
                        showSlotError(slotId, imageData.error);
                    }} else if (imageData.status === 'generating') {{
                        generating++;
                        showSlotLoading(slotId);
                    }}
                }}
                
                const total = data.total || totalSlots;
                _updateProgressBar(done + failed, total);
                _updateStatusPanel(done, failed, generating, total);
            }}
            
            function checkImageStatus() {{
                if (isEmbedded && generationStarted) {{
                     // 如果在内嵌模式下已经知道父窗口在轮询了，这里可以停止主动轮询
                     // 但为了鲁棒性，如果有必要也可以双重检查
                }}
                
                fetch(`/api/workflow/render/status/${{sessionId}}`)
                    .then(response => response.json())
                    .then(data => {{
                        if (data.ok) {{
                            updateUIFromData(data);
                            
                            const total = data.total || totalSlots;
                            const done = Object.values(data.images || {{}}).filter(i => i.status === 'done').length;
                            const failed = Object.values(data.images || {{}}).filter(i => i.status === 'failed').length;
                            
                            if (done + failed < total) {{
                                setTimeout(checkImageStatus, POLL_INTERVAL);
                            }}
                        }} else {{
                            setTimeout(checkImageStatus, POLL_INTERVAL);
                        }}
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
                if (progressText) {{
                    progressText.textContent = `${{doneCount}} / ${{total}}`;
                }}
            }}

            function _updateStatusPanel(done, failed, generating, total) {{
                const progressStatus = document.getElementById('imageProgressStatus');
                const progressLabel = document.getElementById('imageProgressLabel');
                const generateBtn = document.getElementById('generateImagesBtn');
                
                if (!progressStatus) return;

                if (done === total && total > 0) {{
                    progressStatus.textContent = '✅ 图片生成完成！';
                    if (progressLabel) progressLabel.textContent = '已完成';
                    if (generateBtn) generateBtn.style.display = 'none';
                }} else if (failed > 0 && generating === 0) {{
                    progressStatus.textContent = `⚠️ ${{failed}}张图片生成失败`;
                    if (generateBtn) {{
                        generateBtn.disabled = false;
                        generateBtn.textContent = '重试失败图片';
                    }}
                }} else if (generating > 0 || (done + failed > 0 && done + failed < total)) {{
                    progressStatus.textContent = `⏳ 正在生成... (${{done}} / ${{total}})`;
                    if (progressLabel) progressLabel.textContent = '生成中...';
                    if (generateBtn) {{
                        generateBtn.disabled = true;
                        generateBtn.textContent = '生成中...';
                    }}
                }}
            }}
            
            function updateSlotImage(slotId, imageData) {{
                const placeholder = document.querySelector(`.image-placeholder[data-slot-id="${{slotId}}"]`);
                if (!placeholder || placeholder.dataset.loaded) return;
                
                placeholder.innerHTML = 
                    `<img src="/api/workflow/render/image/${{sessionId}}/${{slotId}}" 
                          style="width:100%;height:100%;object-fit:contain;
                                 border-radius:var(--layout-border-radius, 8px);opacity:0;transition:opacity 0.5s"
                          onload="this.style.opacity=1"
                          onerror="this.outerHTML='<div class=\\'error\\'>图片加载失败</div>'">`;
                placeholder.dataset.loaded = "true";
                placeholder.classList.remove('loading');
                placeholder.classList.add('loaded');
            }}
            
            function showSlotLoading(slotId) {{
                const placeholder = document.querySelector(`.image-placeholder[data-slot-id="${{slotId}}"]`);
                if (!placeholder || placeholder.dataset.loaded || placeholder.classList.contains('loading')) return;
                
                placeholder.innerHTML = `
                    <div class="loading-container">
                        <div class="loading-spinner"></div>
                        <p>正在生成...</p>
                    </div>
                `;
                placeholder.classList.add('loading');
            }}
            
            function showSlotError(slotId, error) {{
                const placeholder = document.querySelector(`.image-placeholder[data-slot-id="${{slotId}}"]`);
                if (!placeholder) return;
                
                placeholder.innerHTML = `
                    <div class="error-container">
                        <p>❌ 生成失败</p>
                        <button onclick="retrySlot('${{slotId}}')">重试</button>
                    </div>
                `;
                placeholder.classList.remove('loading');
                placeholder.dataset.loaded = ""; // 允许重试加载
            }}
            
            window.retrySlot = function(slotId) {{
                fetch(`/api/workflow/render/retry/${{sessionId}}/${{slotId}}`, {{
                    method: 'POST'
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.ok) {{
                        showSlotLoading(slotId);
                        if (!isEmbedded) checkImageStatus();
                    }}
                }});
            }};
        }})();
    </script>
    """


def _extract_bullets(page: SlidePage) -> List[str]:
    """从页面元素中提取要点列表 (与 layout_engine 逻辑保持一致)"""
    bullets = []

    for elem in page.elements:
        if elem.type == "bullets" and isinstance(elem.content, dict):
            items = elem.content.get("items", [])
            bullets.extend([str(i) for i in items])
        elif elem.type == "text" and isinstance(elem.content, dict):
            text = elem.content.get("text", "")
            if text:
                bullets.append(str(text))
        elif elem.type == "quiz" and isinstance(elem.content, dict):
             # 处理练习题/测验内容的提取
             question = elem.content.get("question", "")
             if question:
                 bullets.append(str(question))
        elif not isinstance(elem.content, dict) and elem.content:
            bullets.append(str(elem.content))

    return bullets


def _check_text_overflow(page: SlidePage, layout_id: str) -> List[str]:
    """检测文本溢出并生成警告"""
    warnings = []

    # 标题长度检查
    if len(page.title) > 50:
        warnings.append(
            f"页面 {page.index}: 标题过长 ({len(page.title)} 字符),可能溢出"
        )

    # 要点数量检查
    bullets = _extract_bullets(page)
    max_bullets = {
        "title_bullets": 10,
        "title_bullets_right_img": 8,
        "operation_steps": 6,
        "concept_comparison": 4,
        "grid_4": 4,
    }.get(layout_id, 10)

    if len(bullets) > max_bullets:
        warnings.append(
            f"页面 {page.index}: 要点过多 ({len(bullets)} 个,建议 ≤ {max_bullets}),可能溢出"
        )

    # 单个要点长度检查
    for i, bullet in enumerate(bullets):
        if len(bullet) > 100:
            warnings.append(
                f"页面 {page.index}: 要点 {i + 1} 过长 ({len(bullet)} 字符),可能溢出"
            )

    return warnings


def _generate_css_variables(style_config: StyleConfig) -> str:
    """从 StyleConfig 生成完整的 CSS Variables"""

    colors = style_config.color
    font = style_config.font
    layout = style_config.layout

    css_vars = f"""
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
        --font-family-title: {font.title_family}, "PingFang SC", "Microsoft YaHei", sans-serif;
        --font-family-body: {font.body_family}, "PingFang SC", "Microsoft YaHei", sans-serif;
        --font-size-title: {font.title_size}px;
        --font-size-body: {font.body_size}px;
        --line-height-body: {font.line_height};

        /* Layout & Aesthetics */
        --layout-border-radius: {layout.border_radius};
        --layout-box-shadow: {
            '0 10px 30px rgba(0,0,0,0.1)' if layout.box_shadow == 'soft' 
            else '0 4px 8px rgba(0,0,0,0.2)' if layout.box_shadow == 'hard' 
            else 'none'
        };
        --layout-alignment: {layout.alignment};
    """

    return css_vars
