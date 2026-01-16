"""
测试 3.5 模块的图片插槽生成器
"""

import pytest
from app.common.schemas import SlidePage, SlideElement
from app.modules.render.placeholder_generator import (
    create_image_placeholders_for_page,
    _extract_theme_from_page,
    _extract_keywords,
    _build_context,
    _infer_visual_style,
)
from app.modules.render.schemas import ImageStyle


def test_extract_theme_from_page_with_placeholder():
    """测试从页面中提取主题 - 有 placeholder"""
    page = SlidePage(
        index=1,
        slide_type="concept",
        title="液压系统原理",
        elements=[
            SlideElement(
                id="elem1",
                type="image",
                content={
                    "placeholder": True,
                    "theme": "液压系统工作原理图",
                },
            ),
        ],
    )
    
    theme = _extract_theme_from_page(page, {})
    assert theme == "液压系统工作原理图"


def test_extract_theme_from_page_without_placeholder():
    """测试从页面中提取主题 - 无 placeholder"""
    page = SlidePage(
        index=1,
        slide_type="concept",
        title="机械传动装置",
        elements=[
            SlideElement(
                id="elem1",
                type="text",
                content={"text": "这是文本内容"},
            ),
        ],
    )
    
    theme = _extract_theme_from_page(page, {})
    assert theme == "机械传动装置"


def test_extract_keywords():
    """测试关键词提取"""
    keywords = _extract_keywords("液压系统工作原理", "液压缸结构图")
    
    # 应该包含关键词,不包含停用词
    assert len(keywords) > 0
    assert all(len(kw) > 1 for kw in keywords)  # 所有关键词长度 > 1
    assert "的" not in keywords  # 停用词应被过滤
    assert "是" not in keywords


def test_build_context():
    """测试上下文构建"""
    page = SlidePage(
        index=1,
        slide_type="concept",
        title="液压系统原理",
        elements=[
            SlideElement(
                id="elem1",
                type="bullets",
                content={
                    "items": [
                        "液压缸的工作原理",
                        "压力控制方法",
                        "常见故障排除",
                    ]
                },
            ),
        ],
    )
    
    context = _build_context(page)
    assert "液压系统原理" in context
    assert "液压缸的工作原理" in context
    assert "压力控制方法" in context
    # 最多 3 个要点
    assert context.count("|") <= 3


def test_infer_visual_style():
    """测试视觉风格推断"""
    # 测试从 slot_def 获取
    slot_def = {"default_style": "photo"}
    assert _infer_visual_style("concept", slot_def) == ImageStyle.PHOTO
    
    # 测试从 slide_type 推断
    assert _infer_visual_style("concept", {}) == ImageStyle.SCHEMATIC
    assert _infer_visual_style("steps", {}) == ImageStyle.DIAGRAM
    assert _infer_visual_style("warning", {}) == ImageStyle.WARNING
    assert _infer_visual_style("cover", {}) == ImageStyle.ILLUSTRATION
    
    # 测试默认值
    assert _infer_visual_style("unknown", {}) == ImageStyle.PHOTO


def test_create_image_placeholders_for_page():
    """测试完整的图片插槽生成流程"""
    page = SlidePage(
        index=1,
        slide_type="concept",
        title="液压系统原理",
        elements=[
            SlideElement(
                id="elem1",
                type="image",
                content={
                    "placeholder": True,
                    "theme": "液压系统工作原理图",
                },
            ),
            SlideElement(
                id="elem2",
                type="bullets",
                content={
                    "items": [
                        "液压缸的工作原理",
                        "压力控制方法",
                    ]
                },
            ),
        ],
    )
    
    # 使用 title_bullets_right_img 布局 (1 个图片插槽)
    slots = create_image_placeholders_for_page(page, "title_bullets_right_img", 1)
    
    assert len(slots) == 1
    slot = slots[0]
    
    # 验证基本字段
    assert slot.slot_id == "page1_slot0"
    assert slot.page_index == 1
    assert slot.theme == "液压系统工作原理图"
    assert len(slot.keywords) > 0
    assert "液压系统原理" in slot.context
    
    # 验证布局位置
    assert slot.layout_position == "right_half"
    assert 0 <= slot.x <= 1
    assert 0 <= slot.y <= 1
    assert 0 <= slot.w <= 1
    assert 0 <= slot.h <= 1
    
    # 验证视觉约束
    assert slot.visual_style in ImageStyle
    assert slot.aspect_ratio.value == "4:3"


def test_create_image_placeholders_grid_4():
    """测试四宫格布局的图片插槽生成"""
    page = SlidePage(
        index=2,
        slide_type="tools",
        title="常用工具展示",
        elements=[],
    )
    
    slots = create_image_placeholders_for_page(page, "grid_4", 2)
    
    # grid_4 应该有 4 个图片插槽
    assert len(slots) == 4
    
    # 验证每个插槽的位置不同
    positions = [slot.layout_position for slot in slots]
    assert len(set(positions)) == 4  # 4 个不同的位置
    assert "top_left" in positions
    assert "top_right" in positions
    assert "bottom_left" in positions
    assert "bottom_right" in positions


def test_create_image_placeholders_no_slots():
    """测试无图片插槽的布局"""
    page = SlidePage(
        index=1,
        slide_type="title",
        title="课程标题",
        elements=[],
    )
    
    slots = create_image_placeholders_for_page(page, "title_only", 1)
    
    # title_only 应该没有图片插槽
    assert len(slots) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
