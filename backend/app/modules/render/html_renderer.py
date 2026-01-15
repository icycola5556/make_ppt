"""
Module 3.5: HTML 渲染引擎

使用 Jinja2 模板生成 HTML 幻灯片
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Dict, Any
from jinja2 import Environment, FileSystemLoader

from ...common.schemas import SlideDeckContent, SlidePage, StyleConfig, TeachingRequest
from .schemas import RenderResult, ImageSlotRequest
from .layout_engine import resolve_layout


# 模板目录
TEMPLATE_DIR = Path(__file__).parent / "templates"


def render_html_slides(
    deck_content: SlideDeckContent,
    style_config: StyleConfig,
    teaching_request: TeachingRequest,
    session_id: str,
    output_dir: str
) -> RenderResult:
    """
    渲染 HTML 幻灯片
    
    Args:
        deck_content: 3.4 模块输出的内容
        style_config: 3.2 模块输出的风格配置
        teaching_request: 3.1 模块输出的教学需求
        session_id: 会话 ID
        output_dir: 输出目录
    
    Returns:
        RenderResult: 渲染结果,包含 HTML 路径和图片插槽
    """
    
    # 初始化 Jinja2 环境
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    
    # 准备渲染数据
    slides_data = []
    all_image_slots = []
    layouts_used = {}
    warnings = []
    
    # 处理每一页
    for page in deck_content.pages:
        # 选择布局并生成图片插槽
        layout_id, image_slots = resolve_layout(page, teaching_request, page.index)
        
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
        theme_name="professional",  # 默认主题
        css_variables=css_variables,
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
        },
        warnings=warnings,
        total_pages=len(deck_content.pages),
        layouts_used=layouts_used,
    )


def _extract_bullets(page: SlidePage) -> List[str]:
    """从页面元素中提取要点列表"""
    bullets = []
    
    for elem in page.elements:
        if elem.type == "bullets" and isinstance(elem.content, dict):
            items = elem.content.get("items", [])
            bullets.extend(items)
        elif elem.type == "text" and isinstance(elem.content, dict):
            text = elem.content.get("text", "")
            if text:
                bullets.append(text)
    
    return bullets


def _check_text_overflow(page: SlidePage, layout_id: str) -> List[str]:
    """检测文本溢出并生成警告"""
    warnings = []
    
    # 标题长度检查
    if len(page.title) > 50:
        warnings.append(f"页面 {page.index}: 标题过长 ({len(page.title)} 字符),可能溢出")
    
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
                f"页面 {page.index}: 要点 {i+1} 过长 ({len(bullet)} 字符),可能溢出"
            )
    
    return warnings


def _generate_css_variables(style_config: StyleConfig) -> str:
    """从 StyleConfig 生成 CSS Variables"""
    
    colors = style_config.color_palette
    
    css_vars = f"""
        --color-primary: {colors.primary};
        --color-secondary: {colors.secondary};
        --color-accent: {colors.accent};
        --color-text: {colors.text};
        --color-muted: {colors.muted};
        --color-background: {colors.background};
        --color-warning: {colors.warning};
    """
    
    return css_vars
