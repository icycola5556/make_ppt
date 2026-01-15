"""
Module 3.5: 图片插槽生成器

从页面内容提取语义信息,生成图片插槽请求
"""

from typing import List
import jieba
from ...common.schemas import SlidePage
from .schemas import ImageSlotRequest, ImageStyle, AspectRatio
from .layout_configs import VOCATIONAL_LAYOUTS


def create_image_placeholders_for_page(
    page: SlidePage,
    layout_id: str,
    page_index: int
) -> List[ImageSlotRequest]:
    """
    根据布局生成图片插槽
    
    Args:
        page: 页面数据
        layout_id: 布局ID
        page_index: 页面索引
    
    Returns:
        图片插槽列表
    """
    
    layout_config = VOCATIONAL_LAYOUTS.get(layout_id)
    if not layout_config or not layout_config.image_slots:
        return []
    
    slots = []
    
    # 从布局配置获取插槽定义
    for i, slot_def in enumerate(layout_config.image_slots):
        # 构建语义信息
        theme = _extract_theme_from_page(page, slot_def)
        keywords = _extract_keywords(page.title, theme)
        context = _build_context(page)
        visual_style = _infer_visual_style(page.slide_type, slot_def)
        
        slot = ImageSlotRequest(
            slot_id=f"page{page_index}_slot{i}",
            page_index=page_index,
            theme=theme,
            keywords=keywords,
            context=context,
            visual_style=visual_style,
            aspect_ratio=AspectRatio(slot_def.get("aspect_ratio", "4:3")),
            layout_position=slot_def["position"],
            x=slot_def["x"],
            y=slot_def["y"],
            w=slot_def["w"],
            h=slot_def["h"],
            priority=slot_def.get("priority", 1),
        )
        slots.append(slot)
    
    return slots


def _extract_theme_from_page(page: SlidePage, slot_def: dict) -> str:
    """从页面内容提取图片主题"""
    
    # 优先使用页面元素中的 image placeholder theme
    for elem in page.elements:
        if elem.type in ["image", "diagram", "chart"]:
            if isinstance(elem.content, dict) and elem.content.get("placeholder"):
                return elem.content.get("theme", page.title)
    
    # 否则使用页面标题
    return page.title


def _extract_keywords(title: str, theme: str) -> List[str]:
    """提取关键词"""
    text = f"{title} {theme}"
    words = jieba.cut(text, cut_all=False)
    
    # 停用词过滤
    stopwords = {"的", "是", "和", "与", "或", "在", "了", "有", "为", "以", "及", "等", "中"}
    keywords = [w for w in words if len(w) > 1 and w not in stopwords]
    
    return list(set(keywords))[:5]  # 最多 5 个关键词


def _build_context(page: SlidePage) -> str:
    """构建上下文描述"""
    context_parts = [page.title]
    
    # 添加要点内容
    for elem in page.elements:
        if elem.type == "bullets" and isinstance(elem.content, dict):
            items = elem.content.get("items", [])
            context_parts.extend(items[:3])  # 最多 3 个要点
    
    return " | ".join(context_parts)


def _infer_visual_style(slide_type: str, slot_def: dict) -> ImageStyle:
    """推断图片视觉风格"""
    
    # 从 slot_def 获取默认风格
    if "default_style" in slot_def:
        return ImageStyle(slot_def["default_style"])
    
    # 根据 slide_type 推断
    STYLE_MAP = {
        "concept": ImageStyle.SCHEMATIC,
        "steps": ImageStyle.DIAGRAM,
        "warning": ImageStyle.WARNING,
        "cover": ImageStyle.ILLUSTRATION,
        "title": ImageStyle.ILLUSTRATION,
    }
    
    return STYLE_MAP.get(slide_type, ImageStyle.PHOTO)
