"""
简化的端到端测试 - 直接测试 HTML 渲染

跳过复杂的 schema 创建,直接测试核心渲染逻辑
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))

from app.common.schemas import SlideDeckContent, SlidePage, SlideElement
from app.modules.render.layout_engine import resolve_layout
from app.modules.render.html_renderer import _extract_bullets, _generate_css_variables
from jinja2 import Environment, FileSystemLoader


def test_simple_render():
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
    bullets = _extract_bullets(pages[1])
    print(f"✓ 提取要点: {bullets}")
    
    # 测试模板渲染
    template_dir = Path(__file__).parents[1] / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template("layouts/title_only.html")
    
    html = template.render(slide={"title": "测试标题"})
    print(f"✓ 模板渲染成功: {len(html)} 字符")
    
    print("\n" + "=" * 60)
    print("测试通过!")
    print("=" * 60)


if __name__ == "__main__":
    test_simple_render()
