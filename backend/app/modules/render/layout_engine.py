"""
Module 3.5: 布局选择引擎

智能选择最适合的布局模板
"""

from typing import Tuple, List, Optional
from ...common.schemas import SlidePage, TeachingRequest
from .schemas import ImageSlotRequest
from .layout_configs import VOCATIONAL_LAYOUTS


def resolve_layout(
    page: SlidePage,
    teaching_request: TeachingRequest,
    page_index: int
) -> Tuple[str, List[ImageSlotRequest]]:
    """
    智能选择布局并生成图片插槽
    
    Args:
        page: 页面数据 (来自 3.4 模块)
        teaching_request: 教学需求 (来自 3.1 模块)
        page_index: 页面索引
    
    Returns:
        (layout_id, image_slots)
    """
    
    # === 第一层: slide_type 强制映射 ===
    layout_id = _map_by_slide_type(page.slide_type)
    if layout_id:
        return layout_id, _generate_image_slots(page, layout_id, page_index)
    
    # === 第二层: 关键词语义匹配 ===
    layout_id = _match_by_keywords(page)
    if layout_id:
        return layout_id, _generate_image_slots(page, layout_id, page_index)
    
    # === 第三层: 元素特征分析 + 计分 ===
    layout_id = _score_and_select(page, teaching_request)
    
    # === 第四层: 文本溢出检查和降级 ===
    layout_id = _check_text_overflow(page, layout_id)
    
    return layout_id, _generate_image_slots(page, layout_id, page_index)


def _map_by_slide_type(slide_type: str) -> Optional[str]:
    """slide_type 强制映射"""
    TYPE_LAYOUT_MAP = {
        # 通用
        "title": "title_only",
        "cover": "title_only",
        "bridge": "title_only",
        "objectives": "title_bullets",
        "summary": "title_bullets",
        "agenda": "title_bullets",
        
        # 职教专用
        "steps": "operation_steps",
        "practice": "operation_steps",
        "demo": "operation_steps",
        "comparison": "concept_comparison",
        "contrast": "concept_comparison",
        "tools": "grid_4",
        "equipment": "grid_4",
        "gallery": "grid_4",
    }
    return TYPE_LAYOUT_MAP.get(slide_type)


def _match_by_keywords(page: SlidePage) -> Optional[str]:
    """关键词语义匹配"""
    title_text = page.title.lower() if page.title else ""
    content_text = " ".join([str(e.content) for e in page.elements]).lower()
    full_text = f"{title_text} {content_text}"
    
    KEYWORD_PATTERNS = {
        "operation_steps": ["步骤", "操作", "流程", "方法", "怎么做", "如何", "实训"],
        "concept_comparison": ["对比", "区别", "正确", "错误", "vs", "比较", "优缺点"],
        "grid_4": ["工具", "设备", "部件", "类型", "分类"],
    }
    
    for layout_id, keywords in KEYWORD_PATTERNS.items():
        if any(kw in full_text for kw in keywords):
            return layout_id
    
    return None


def _score_and_select(page: SlidePage, req: TeachingRequest) -> str:
    """计分机制选择布局"""
    
    # 提取特征
    text_len = _calculate_text_length(page)
    has_bullets = any(e.type == "bullets" for e in page.elements)
    bullet_count = sum(len(e.content.get("items", [])) for e in page.elements if e.type == "bullets")
    image_count = sum(1 for e in page.elements if e.type in ["image", "diagram", "chart"])
    
    # 初始化分数
    scores = {layout_id: 0 for layout_id in VOCATIONAL_LAYOUTS.keys()}
    
    # 规则 1: 教学场景加分
    if req.teaching_scene == "practice":
        scores["operation_steps"] += 50
    elif req.teaching_scene == "theory":
        scores["title_bullets_right_img"] += 30
    
    # 规则 2: 图片数量
    if image_count >= 4:
        scores["grid_4"] += 100
    elif image_count >= 2:
        scores["concept_comparison"] += 50
    elif image_count == 1:
        scores["title_bullets_right_img"] += 40
        scores["operation_steps"] += 30
    
    # 规则 3: 要点数量
    if has_bullets:
        if bullet_count > 6:
            scores["title_bullets"] += 60
        else:
            scores["title_bullets"] += 40
            scores["title_bullets_right_img"] += 35
    
    # 规则 4: 文本长度
    if text_len > 400:
        scores["title_bullets"] -= 50  # 降低纯文本布局分数
    
    # 返回最高分
    return max(scores, key=scores.get)


def _check_text_overflow(page: SlidePage, layout_id: str) -> str:
    """检查文本溢出并降级"""
    text_len = _calculate_text_length(page)
    
    # 如果文本过长,强制降级
    if text_len > 500:
        return "title_bullets"  # 纯文本布局
    
    return layout_id


def _calculate_text_length(page: SlidePage) -> int:
    """计算页面文本总长度"""
    total = len(page.title) if page.title else 0
    for elem in page.elements:
        if elem.type in ["text", "bullets"]:
            if isinstance(elem.content, dict):
                if "text" in elem.content:
                    total += len(str(elem.content["text"]))
                if "items" in elem.content:
                    total += sum(len(str(item)) for item in elem.content["items"])
            else:
                total += len(str(elem.content))
    return total


def _generate_image_slots(
    page: SlidePage,
    layout_id: str,
    page_index: int
) -> List[ImageSlotRequest]:
    """
    根据布局生成图片插槽
    
    这是一个简化版本,完整实现在 placeholder_generator.py
    """
    from .placeholder_generator import create_image_placeholders_for_page
    return create_image_placeholders_for_page(page, layout_id, page_index)
