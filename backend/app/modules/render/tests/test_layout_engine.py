"""
测试 3.5 模块的布局选择引擎
"""

import pytest
from app.common.schemas import SlidePage, SlideElement, TeachingRequest
from app.modules.render.layout_engine import (
    resolve_layout,
    _map_by_slide_type,
    _match_by_keywords,
    _score_and_select,
    _calculate_text_length,
)


def test_map_by_slide_type():
    """测试 slide_type 强制映射"""
    assert _map_by_slide_type("title") == "title_only"
    assert _map_by_slide_type("cover") == "title_only"
    assert _map_by_slide_type("objectives") == "title_bullets"
    assert _map_by_slide_type("steps") == "operation_steps"
    assert _map_by_slide_type("comparison") == "concept_comparison"
    assert _map_by_slide_type("tools") == "grid_4"
    assert _map_by_slide_type("unknown_type") is None


def test_match_by_keywords():
    """测试关键词语义匹配"""
    # 测试步骤关键词
    page = SlidePage(
        index=1,
        slide_type="concept",
        title="操作步骤说明",
        elements=[],
    )
    assert _match_by_keywords(page) == "operation_steps"
    
    # 测试对比关键词
    page = SlidePage(
        index=2,
        slide_type="concept",
        title="正确与错误对比",
        elements=[],
    )
    assert _match_by_keywords(page) == "concept_comparison"
    
    # 测试工具关键词
    page = SlidePage(
        index=3,
        slide_type="concept",
        title="常用工具介绍",
        elements=[],
    )
    assert _match_by_keywords(page) == "grid_4"
    
    # 测试无匹配
    page = SlidePage(
        index=4,
        slide_type="concept",
        title="基本概念",
        elements=[],
    )
    assert _match_by_keywords(page) is None


def test_calculate_text_length():
    """测试文本长度计算"""
    page = SlidePage(
        index=1,
        slide_type="concept",
        title="测试标题",  # 4 字符
        elements=[
            SlideElement(
                id="elem1",
                type="text",
                content={"text": "这是一段测试文本"},  # 8 字符
            ),
            SlideElement(
                id="elem2",
                type="bullets",
                content={"items": ["要点1", "要点2", "要点3"]},  # 3+3+3 = 9 字符
            ),
        ],
    )
    # 总长度: 4 + 8 + 9 = 21
    assert _calculate_text_length(page) == 21


def test_score_and_select_practice_scene():
    """测试实训场景的布局选择"""
    req = TeachingRequest(
        subject="机械基础",
        knowledge_points=[],
        teaching_scene="practice",
        slide_requirements={"target_count": 10},
    )
    
    page = SlidePage(
        index=1,
        slide_type="concept",
        title="实训操作",
        elements=[
            SlideElement(
                id="elem1",
                type="bullets",
                content={"items": ["步骤1", "步骤2", "步骤3"]},
            ),
            SlideElement(
                id="elem2",
                type="image",
                content={"placeholder": True},
            ),
        ],
    )
    
    layout_id = _score_and_select(page, req)
    # 实训场景 + 1 张图片,应该选择包含图片的布局
    assert layout_id in ["operation_steps", "title_bullets_right_img"]


def test_score_and_select_multiple_images():
    """测试多图片场景的布局选择"""
    req = TeachingRequest(
        subject="机械基础",
        knowledge_points=[],
        teaching_scene="theory",
        slide_requirements={"target_count": 10},
    )
    
    page = SlidePage(
        index=1,
        slide_type="concept",
        title="工具展示",
        elements=[
            SlideElement(id=f"img{i}", type="image", content={"placeholder": True})
            for i in range(4)
        ],
    )
    
    layout_id = _score_and_select(page, req)
    # 4 张图片,应该选择 grid_4
    assert layout_id == "grid_4"


def test_resolve_layout_integration():
    """测试完整的布局选择流程"""
    req = TeachingRequest(
        subject="机械基础",
        knowledge_points=[],
        teaching_scene="theory",
        slide_requirements={"target_count": 10},
    )
    
    # 测试 1: slide_type 强制映射
    page = SlidePage(
        index=1,
        slide_type="title",
        title="课程标题",
        elements=[],
    )
    layout_id, image_slots = resolve_layout(page, req, 1)
    assert layout_id == "title_only"
    assert len(image_slots) == 0  # title_only 无图片插槽
    
    # 测试 2: 关键词匹配
    page = SlidePage(
        index=2,
        slide_type="concept",
        title="操作步骤详解",
        elements=[
            SlideElement(
                id="elem1",
                type="bullets",
                content={"items": ["步骤1", "步骤2"]},
            ),
        ],
    )
    layout_id, image_slots = resolve_layout(page, req, 2)
    assert layout_id == "operation_steps"
    assert len(image_slots) == 1  # operation_steps 有 1 个图片插槽


def test_text_overflow_check():
    """测试文本溢出检查"""
    req = TeachingRequest(
        subject="机械基础",
        knowledge_points=[],
        teaching_scene="theory",
        slide_requirements={"target_count": 10},
    )
    
    # 创建超长文本页面
    long_text = "这是一段很长的文本。" * 60  # 约 600 字符
    page = SlidePage(
        index=1,
        slide_type="concept",
        title="超长内容",
        elements=[
            SlideElement(
                id="elem1",
                type="text",
                content={"text": long_text},
            ),
        ],
    )
    
    layout_id, _ = resolve_layout(page, req, 1)
    # 超长文本应该降级到 title_bullets
    assert layout_id == "title_bullets"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
