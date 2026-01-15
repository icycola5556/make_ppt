"""
测试 3.5 模块 - 端到端测试

使用模拟的 3.4 输出数据测试 HTML 渲染
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parents[3]))

from app.common.schemas import (
    SlideDeckContent,
    SlidePage,
    SlideElement,
    StyleConfig,
    ColorConfig,
    FontConfig,
    LayoutConfig as StyleLayoutConfig,
    ImageryConfig,
    TeachingRequest,
    KnowledgePoint,
)
from app.modules.render import render_html_slides


def create_mock_slide_deck() -> SlideDeckContent:
    """创建模拟的 3.4 输出数据"""
    
    pages = [
        # 封面页
        SlidePage(
            index=1,
            slide_type="title",
            title="液压系统工作原理",
            layout={"template": "one-column"},
            elements=[
                SlideElement(
                    id="elem1",
                    type="text",
                    x=0.1, y=0.4, w=0.8, h=0.2,
                    content={"text": "授课人: 张老师"},
                    style={"role": "body"},
                ),
            ],
            speaker_notes="",
        ),
        
        # 教学目标页
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
                    content={
                        "items": [
                            "知识目标：掌握液压系统的基本组成和工作原理",
                            "能力目标：能够识别液压系统的主要部件",
                            "素养目标：培养安全操作意识和规范操作习惯",
                        ]
                    },
                    style={"role": "body"},
                ),
            ],
            speaker_notes="",
        ),
        
        # 概念讲解页 (左文右图)
        SlidePage(
            index=3,
            slide_type="concept",
            title="液压系统的组成",
            layout={"template": "two-column"},
            elements=[
                SlideElement(
                    id="elem1",
                    type="bullets",
                    x=0.05, y=0.2, w=0.5, h=0.7,
                    content={
                        "items": [
                            "动力元件：液压泵,提供压力油",
                            "执行元件：液压缸、液压马达",
                            "控制元件：各种阀,控制流量和压力",
                            "辅助元件：油箱、滤油器、管路等",
                        ]
                    },
                    style={"role": "body"},
                ),
                SlideElement(
                    id="elem2",
                    type="image",
                    x=0.6, y=0.2, w=0.35, h=0.7,
                    content={
                        "placeholder": True,
                        "kind": "diagram",
                        "theme": "液压系统组成示意图",
                        "prompt": "液压系统的主要组成部件示意图",
                    },
                    style={"role": "visual"},
                ),
            ],
            speaker_notes="重点讲解各部件的作用",
        ),
        
        # 操作步骤页 (左图右步骤)
        SlidePage(
            index=4,
            slide_type="steps",
            title="液压系统启动步骤",
            layout={"template": "two-column"},
            elements=[
                SlideElement(
                    id="elem1",
                    type="image",
                    x=0.05, y=0.2, w=0.4, h=0.7,
                    content={
                        "placeholder": True,
                        "kind": "photo",
                        "theme": "液压系统操作面板",
                        "prompt": "液压系统控制面板实拍照片",
                    },
                    style={"role": "visual"},
                ),
                SlideElement(
                    id="elem2",
                    type="bullets",
                    x=0.5, y=0.2, w=0.45, h=0.7,
                    content={
                        "items": [
                            "检查油箱油位,确保油量充足",
                            "检查各连接部位,确保无泄漏",
                            "启动液压泵,观察压力表读数",
                            "调节溢流阀,设定系统压力",
                            "试运行,检查系统工作是否正常",
                        ]
                    },
                    style={"role": "body"},
                ),
            ],
            speaker_notes="强调安全操作规范",
        ),
        
        # 对比页
        SlidePage(
            index=5,
            slide_type="comparison",
            title="正确操作 vs 错误操作",
            layout={"template": "two-column"},
            elements=[
                SlideElement(
                    id="elem1",
                    type="image",
                    x=0.05, y=0.2, w=0.42, h=0.6,
                    content={
                        "placeholder": True,
                        "kind": "photo",
                        "theme": "正确的液压系统操作姿势",
                        "prompt": "工人正确操作液压设备的照片",
                    },
                    style={"role": "visual"},
                ),
                SlideElement(
                    id="elem2",
                    type="text",
                    x=0.05, y=0.82, w=0.42, h=0.1,
                    content={"text": "✓ 正确操作"},
                    style={"role": "body"},
                ),
                SlideElement(
                    id="elem3",
                    type="image",
                    x=0.53, y=0.2, w=0.42, h=0.6,
                    content={
                        "placeholder": True,
                        "kind": "warning",
                        "theme": "错误的液压系统操作",
                        "prompt": "液压设备错误操作示例",
                    },
                    style={"role": "visual"},
                ),
                SlideElement(
                    id="elem4",
                    type="text",
                    x=0.53, y=0.82, w=0.42, h=0.1,
                    content={"text": "✗ 错误操作"},
                    style={"role": "body"},
                ),
            ],
            speaker_notes="",
        ),
        
        # 工具展示页 (四宫格)
        SlidePage(
            index=6,
            slide_type="tools",
            title="常用液压工具",
            layout={"template": "grid"},
            elements=[
                SlideElement(
                    id="elem1",
                    type="image",
                    x=0.05, y=0.2, w=0.42, h=0.35,
                    content={
                        "placeholder": True,
                        "kind": "photo",
                        "theme": "液压扳手",
                        "prompt": "液压扳手工具照片",
                    },
                    style={"role": "visual"},
                ),
                SlideElement(
                    id="elem2",
                    type="image",
                    x=0.53, y=0.2, w=0.42, h=0.35,
                    content={
                        "placeholder": True,
                        "kind": "photo",
                        "theme": "液压千斤顶",
                        "prompt": "液压千斤顶照片",
                    },
                    style={"role": "visual"},
                ),
                SlideElement(
                    id="elem3",
                    type="image",
                    x=0.05, y=0.6, w=0.42, h=0.35,
                    content={
                        "placeholder": True,
                        "kind": "photo",
                        "theme": "液压钳",
                        "prompt": "液压钳工具照片",
                    },
                    style={"role": "visual"},
                ),
                SlideElement(
                    id="elem4",
                    type="image",
                    x=0.53, y=0.6, w=0.42, h=0.35,
                    content={
                        "placeholder": True,
                        "kind": "photo",
                        "theme": "压力表",
                        "prompt": "液压系统压力表照片",
                    },
                    style={"role": "visual"},
                ),
            ],
            speaker_notes="",
        ),
        
        # 总结页
        SlidePage(
            index=7,
            slide_type="summary",
            title="课程总结",
            layout={"template": "one-column"},
            elements=[
                SlideElement(
                    id="elem1",
                    type="bullets",
                    x=0.1, y=0.2, w=0.8, h=0.7,
                    content={
                        "items": [
                            "掌握了液压系统的基本组成",
                            "学会了液压系统的启动步骤",
                            "了解了正确与错误的操作方式",
                            "认识了常用的液压工具",
                        ]
                    },
                    style={"role": "body"},
                ),
            ],
            speaker_notes="",
        ),
    ]
    
    return SlideDeckContent(
        deck_title="液压系统工作原理",
        pages=pages,
    )


def create_mock_style_config() -> StyleConfig:
    """创建模拟的风格配置"""
    return StyleConfig(
        style_name="professional",
        color=ColorConfig(
            primary="#2c3e50",
            secondary="#34495e",
            accent="#3498db",
            text="#2c3e50",
            muted="#ecf0f1",
            background="#ffffff",
            warning="#e74c3c",
        ),
        font=FontConfig(
            title_font="PingFang SC",
            body_font="PingFang SC",
            title_size=48,
            body_size=24,
        ),
        layout=StyleLayoutConfig(
            slide_width=1920,
            slide_height=1080,
            margin=60,
        ),
        imagery=ImageryConfig(
            style="photo",
            color_tone="neutral",
        ),
    )


def create_mock_teaching_request() -> TeachingRequest:
    """创建模拟的教学需求"""
    from app.common.schemas import (
        KnowledgePointDetail,
        TeachingObjectivesDetail,
        SlideRequirementsDetail,
        SpecialRequirementsDetail,
        CasesDetail,
        ExercisesDetail,
        InteractionDetail,
        WarningsDetail,
    )
    
    return TeachingRequest(
        user_input_text="液压系统工作原理",
        teaching_scenario="practice",
        professional_category="机械制造",
        knowledge_points=[
            KnowledgePointDetail(
                name="液压系统工作原理",
                type="concept",
                difficulty_level="medium",
            ),
        ],
        teaching_objectives=TeachingObjectivesDetail(
            knowledge=["掌握液压系统的基本组成和工作原理"],
            ability=["能够识别液压系统的主要部件"],
            literacy=["培养安全操作意识和规范操作习惯"],
        ),
        slide_requirements=SlideRequirementsDetail(
            target_count=7,
            min_count=5,
            max_count=10,
            lesson_duration_min=45,
        ),
        special_requirements=SpecialRequirementsDetail(
            cases=CasesDetail(enabled=False, count=0),
            exercises=ExercisesDetail(enabled=False, total_count=0),
            interaction=InteractionDetail(enabled=False, types=[]),
            warnings=WarningsDetail(enabled=True),
        ),
    )


def test_render():
    """测试渲染流程"""
    print("=" * 60)
    print("开始测试 3.5 模块 HTML 渲染")
    print("=" * 60)
    
    # 创建模拟数据
    print("\n1. 创建模拟数据...")
    deck_content = create_mock_slide_deck()
    style_config = create_mock_style_config()
    teaching_request = create_mock_teaching_request()
    
    print(f"   - 页面数量: {len(deck_content.pages)}")
    print(f"   - 风格主题: {style_config.style_name}")
    print(f"   - 教学场景: {teaching_request.teaching_scene}")
    
    # 渲染 HTML
    print("\n2. 渲染 HTML...")
    output_dir = Path(__file__).parents[3] / "data" / "outputs"
    
    result = render_html_slides(
        deck_content=deck_content,
        style_config=style_config,
        teaching_request=teaching_request,
        session_id="test_render_001",
        output_dir=str(output_dir),
    )
    
    print(f"   ✓ HTML 文件: {result.html_path}")
    print(f"   ✓ 总页数: {result.total_pages}")
    print(f"   ✓ 图片插槽数: {len(result.image_slots)}")
    
    # 显示布局使用统计
    print("\n3. 布局使用统计:")
    for layout_id, count in result.layouts_used.items():
        print(f"   - {layout_id}: {count} 页")
    
    # 显示图片插槽信息
    print(f"\n4. 图片插槽详情 ({len(result.image_slots)} 个):")
    for slot in result.image_slots[:5]:  # 只显示前 5 个
        print(f"   - {slot.slot_id}: {slot.theme}")
        print(f"     关键词: {', '.join(slot.keywords)}")
        print(f"     风格: {slot.visual_style.value}, 宽高比: {slot.aspect_ratio.value}")
    
    if len(result.image_slots) > 5:
        print(f"   ... 还有 {len(result.image_slots) - 5} 个插槽")
    
    # 显示警告
    if result.warnings:
        print(f"\n5. 警告信息 ({len(result.warnings)} 条):")
        for warning in result.warnings:
            print(f"   ⚠️  {warning}")
    else:
        print("\n5. ✓ 无警告")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
    print(f"\n请在浏览器中打开: {result.html_path}")
    
    return result


if __name__ == "__main__":
    test_render()
