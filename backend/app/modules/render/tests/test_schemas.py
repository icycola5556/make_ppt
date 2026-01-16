"""
测试 3.5 模块的数据模型
"""

import pytest
from app.modules.render.schemas import (
    ImageSlotRequest,
    RenderResult,
    LayoutConfig,
    ImageStyle,
    AspectRatio,
    ColorConstraint,
)


def test_image_slot_request_creation():
    """测试 ImageSlotRequest 创建"""
    slot = ImageSlotRequest(
        slot_id="test_slot_1",
        page_index=1,
        theme="液压系统原理图",
        keywords=["液压", "系统", "原理"],
        context="液压系统工作原理 | 液压缸结构",
        visual_style=ImageStyle.SCHEMATIC,
        aspect_ratio=AspectRatio.STANDARD,
        layout_position="right_half",
        x=0.6,
        y=0.2,
        w=0.35,
        h=0.7,
    )
    
    assert slot.slot_id == "test_slot_1"
    assert slot.page_index == 1
    assert slot.theme == "液压系统原理图"
    assert len(slot.keywords) == 3
    assert slot.visual_style == ImageStyle.SCHEMATIC
    assert slot.aspect_ratio == AspectRatio.STANDARD


def test_image_slot_request_to_rag_query():
    """测试 to_rag_query 方法"""
    slot = ImageSlotRequest(
        slot_id="test_slot_1",
        page_index=1,
        theme="液压系统",
        keywords=["液压缸", "工作原理"],
        context="液压系统工作原理",
        visual_style=ImageStyle.SCHEMATIC,
        aspect_ratio=AspectRatio.STANDARD,
        layout_position="right_half",
        x=0.6,
        y=0.2,
        w=0.35,
        h=0.7,
        min_resolution=(1024, 768),
        color_constraint=ColorConstraint.WHITE_BG,
        fallback_query="hydraulic system",
    )
    
    query = slot.to_rag_query()
    
    assert "query" in query
    assert "液压系统" in query["query"]
    assert "液压缸" in query["query"]
    assert query["filters"]["style"] == "schematic"
    assert query["filters"]["min_width"] == 1024
    assert query["filters"]["min_height"] == 768
    assert query["filters"]["color_constraint"] == "white_bg"
    assert query["context"] == "液压系统工作原理"
    assert query["fallback_query"] == "hydraulic system"
    assert query["top_k"] == 3


def test_image_style_enum():
    """测试 ImageStyle 枚举"""
    assert ImageStyle.PHOTO.value == "photo"
    assert ImageStyle.SCHEMATIC.value == "schematic"
    assert ImageStyle.DIAGRAM.value == "diagram"
    assert ImageStyle.ICON.value == "icon"
    assert ImageStyle.WARNING.value == "warning"
    assert ImageStyle.ILLUSTRATION.value == "illustration"


def test_aspect_ratio_enum():
    """测试 AspectRatio 枚举"""
    assert AspectRatio.SQUARE.value == "1:1"
    assert AspectRatio.LANDSCAPE.value == "16:9"
    assert AspectRatio.PORTRAIT.value == "9:16"
    assert AspectRatio.WIDE.value == "21:9"
    assert AspectRatio.STANDARD.value == "4:3"


def test_layout_config_creation():
    """测试 LayoutConfig 创建"""
    config = LayoutConfig(
        layout_id="test_layout",
        display_name="测试布局",
        description="这是一个测试布局",
        grid_template_areas='"title" "content"',
        grid_template_columns="1fr",
        grid_template_rows="auto 1fr",
        image_slots=[
            {
                "position": "center",
                "x": 0.3,
                "y": 0.3,
                "w": 0.4,
                "h": 0.4,
            }
        ],
        suitable_slide_types=["concept", "intro"],
        suitable_keywords=["概念", "介绍"],
        max_bullets=6,
        max_text_length=400,
    )
    
    assert config.layout_id == "test_layout"
    assert config.display_name == "测试布局"
    assert len(config.image_slots) == 1
    assert len(config.suitable_slide_types) == 2
    assert config.max_bullets == 6


def test_render_result_creation():
    """测试 RenderResult 创建"""
    result = RenderResult(
        session_id="test_session",
        html_path="/path/to/output.html",
        image_slots=[],
        metadata={"render_time": 1.5},
        warnings=["文本可能溢出"],
        total_pages=10,
        layouts_used={"title_bullets_right_img": 5, "operation_steps": 3},
    )
    
    assert result.session_id == "test_session"
    assert result.html_path == "/path/to/output.html"
    assert len(result.image_slots) == 0
    assert result.total_pages == 10
    assert result.layouts_used["title_bullets_right_img"] == 5
    assert len(result.warnings) == 1


def test_image_slot_request_validation():
    """测试 ImageSlotRequest 字段验证"""
    # 测试坐标范围验证 (0-1)
    with pytest.raises(Exception):  # Pydantic 会抛出 ValidationError
        ImageSlotRequest(
            slot_id="test",
            page_index=1,
            theme="test",
            layout_position="center",
            x=1.5,  # 超出范围
            y=0.5,
            w=0.3,
            h=0.3,
        )
    
    # 测试优先级范围验证 (1-5)
    with pytest.raises(Exception):
        ImageSlotRequest(
            slot_id="test",
            page_index=1,
            theme="test",
            layout_position="center",
            x=0.5,
            y=0.5,
            w=0.3,
            h=0.3,
            priority=10,  # 超出范围
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
