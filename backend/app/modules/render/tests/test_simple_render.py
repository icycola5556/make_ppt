"""
简化的端到端测试 - 直接测试 HTML 渲染

跳过复杂的 schema 创建,直接测试核心渲染逻辑
"""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))

from app.common.schemas import SlideDeckContent, SlidePage, SlideElement
from app.modules.render.engine import LayoutEngine
from app.modules.render.core import extract_bullets
from app.modules.render.renderer import HTMLRenderer
from jinja2 import Environment, FileSystemLoader


@pytest.mark.asyncio
async def test_simple_render():
    """简化的渲染测试"""
    print("=" * 60)
    print("简化渲染测试")
    print("=" * 60)
    
    # 创建简单的页面数据
    pages = [
        SlidePage(
            index=1,
            slide_type="title",
            title="液压系统工作原理",
            layout={"template": "one-column"},
            elements=[],
            speaker_notes="",
        ),
        SlidePage(
            index=2,
            slide_type="objectives",
            title="教学目标",
            layout={"template": "one-column"},
            elements=[
                SlideElement(
                    id="elem1",
                    type="bullets",
                    x=0.1, y=0.2, w=0.8, h=0.7,
                    content={"items": ["目标1", "目标2", "目标3"]},
                    style={"role": "body"},
                ),
            ],
            speaker_notes="",
        ),
    ]
    
    deck = SlideDeckContent(deck_title="测试课件", pages=pages)
    
    print(f"\n✓ 创建了 {len(pages)} 页测试数据")
    
    # 测试要点提取
    bullets = extract_bullets(pages[1])
    print(f"✓ 提取要点: {bullets}")
    
    # 测试模板渲染 (需要模拟 LayoutEngine 和 CSS 变量)
    # 这里我们只测试模板加载和基本渲染，不做完整流程
    
    # 模拟 render 中的一些步骤
    # 1. 布局选择
    # 注意: resolve_layout 是 async 的
    layout_id, _ = await LayoutEngine.resolve_layout(pages[0], None, 1) # None for teaching_request if allowed, check implementation
    # resolve_layout 需要 teaching_request，这里需要构造一个简单的 mock
    class MockRequest:
        subject_info = type('obj', (object,), {'subject_name': 'test'})
        teaching_scene = 'theory'
        
    layout_id, _ = await LayoutEngine.resolve_layout(pages[0], MockRequest(), 1)
    
    print(f"✓ 布局选择: {layout_id}")

    template_dir = Path(__file__).parents[1] / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template("layouts/title_only.html")
    
    html = template.render(slide={"title": "测试标题"})
    print(f"✓ 模板渲染成功: {len(html)} 字符")
    
    print("\n" + "=" * 60)
    print("测试通过!")
    print("=" * 60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_simple_render())
