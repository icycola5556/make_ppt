"""
Module 3.5: 布局配置定义

定义 6 种 MVP 核心布局模板
"""

from .schemas import LayoutConfig

# ============================================================================
# MVP 阶段: 6 种核心布局
# ============================================================================

VOCATIONAL_LAYOUTS = {
    # ========== 基础布局 ==========
    
    "title_only": LayoutConfig(
        layout_id="title_only",
        display_name="纯标题页",
        description="封面或过渡页,仅包含标题",
        grid_template_areas='"title"',
        grid_template_columns="1fr",
        grid_template_rows="1fr",
        gap="0",
        image_slots=[],
        suitable_slide_types=["title", "cover", "bridge"],
        suitable_keywords=[],
        max_bullets=0,
        max_text_length=50,
    ),
    
    "title_bullets": LayoutConfig(
        layout_id="title_bullets",
        display_name="标题+要点",
        description="目录、总结页,包含标题和要点列表",
        grid_template_areas='"title title" "bullets bullets"',
        grid_template_columns="1fr 1fr",
        grid_template_rows="auto 1fr",
        gap="2rem",
        image_slots=[],
        suitable_slide_types=["objectives", "summary", "agenda"],
        suitable_keywords=["目标", "总结", "目录", "回顾"],
        max_bullets=8,
        max_text_length=400,
    ),
    
    # ========== 职教核心布局 ==========
    
    "title_bullets_right_img": LayoutConfig(
        layout_id="title_bullets_right_img",
        display_name="左文右图",
        description="最常用布局,左侧要点,右侧图片",
        grid_template_areas='"title title" "bullets image"',
        grid_template_columns="3fr 2fr",
        grid_template_rows="auto 1fr",
        gap="2rem",
        image_slots=[
            {
                "position": "right_half",
                "x": 0.62,
                "y": 0.20,
                "w": 0.32,
                "h": 0.72,
                "aspect_ratio": "4:3",
                "default_style": "photo",
                "priority": 1,
            }
        ],
        suitable_slide_types=["concept", "intro", "keypoints"],
        suitable_keywords=["概念", "定义", "介绍", "要点"],
        max_bullets=6,
        max_text_length=350,
    ),
    
    "operation_steps": LayoutConfig(
        layout_id="operation_steps",
        display_name="左图右步骤",
        description="实训核心布局,左侧图片,右侧操作步骤",
        grid_template_areas='"title title" "image steps"',
        grid_template_columns="2fr 3fr",
        grid_template_rows="auto 1fr",
        gap="2rem",
        image_slots=[
            {
                "position": "left_half",
                "x": 0.06,
                "y": 0.20,
                "w": 0.36,
                "h": 0.72,
                "aspect_ratio": "4:3",
                "default_style": "photo",
                "priority": 1,
            }
        ],
        suitable_slide_types=["steps", "practice", "demo"],
        suitable_keywords=["步骤", "操作", "流程", "方法", "实训"],
        max_bullets=5,
        max_text_length=300,
    ),
    
    "concept_comparison": LayoutConfig(
        layout_id="concept_comparison",
        display_name="左右对比",
        description="对比布局,左右两侧各一个图片或文本块",
        grid_template_areas='"title title" "left right"',
        grid_template_columns="1fr 1fr",
        grid_template_rows="auto 1fr",
        gap="2rem",
        image_slots=[
            {
                "position": "left_half",
                "x": 0.06,
                "y": 0.20,
                "w": 0.42,
                "h": 0.72,
                "aspect_ratio": "4:3",
                "default_style": "photo",
                "priority": 1,
            },
            {
                "position": "right_half",
                "x": 0.52,
                "y": 0.20,
                "w": 0.42,
                "h": 0.72,
                "aspect_ratio": "4:3",
                "default_style": "photo",
                "priority": 1,
            },
        ],
        suitable_slide_types=["comparison", "contrast"],
        suitable_keywords=["对比", "比较", "区别", "正确", "错误", "vs", "优缺点"],
        max_bullets=4,
        max_text_length=250,
    ),
    
    "grid_4": LayoutConfig(
        layout_id="grid_4",
        display_name="四宫格",
        description="四宫格布局,展示工具、设备或知识点",
        grid_template_areas='"title title" "img1 img2" "img3 img4"',
        grid_template_columns="1fr 1fr",
        grid_template_rows="auto 1fr 1fr",
        gap="1.5rem",
        image_slots=[
            {
                "position": "top_left",
                "x": 0.06,
                "y": 0.25,
                "w": 0.42,
                "h": 0.32,
                "aspect_ratio": "4:3",
                "default_style": "photo",
                "priority": 1,
            },
            {
                "position": "top_right",
                "x": 0.52,
                "y": 0.25,
                "w": 0.42,
                "h": 0.32,
                "aspect_ratio": "4:3",
                "default_style": "photo",
                "priority": 1,
            },
            {
                "position": "bottom_left",
                "x": 0.06,
                "y": 0.60,
                "w": 0.42,
                "h": 0.32,
                "aspect_ratio": "4:3",
                "default_style": "photo",
                "priority": 2,
            },
            {
                "position": "bottom_right",
                "x": 0.52,
                "y": 0.60,
                "w": 0.42,
                "h": 0.32,
                "aspect_ratio": "4:3",
                "default_style": "photo",
                "priority": 2,
            },
        ],
        suitable_slide_types=["tools", "equipment", "gallery"],
        suitable_keywords=["工具", "设备", "部件", "类型", "分类"],
        max_bullets=4,
        max_text_length=200,
    ),
}


def get_layout(layout_id: str) -> LayoutConfig:
    """获取布局配置"""
    return VOCATIONAL_LAYOUTS.get(layout_id)



def get_all_layouts() -> dict[str, LayoutConfig]:
    """获取所有布局配置"""
    return VOCATIONAL_LAYOUTS


def get_layout_schema_for_llm() -> list[dict]:
    """
    Export simplified layout registry for LLM Layout Decision Agent.
    
    Returns:
        List of simplified layout definitions
    """
    schemas = []
    
    for layout_id, config in VOCATIONAL_LAYOUTS.items():
        # Count image slots
        img_count = len(config.image_slots)
        
        # Prepare schema
        schema = {
            "layout_id": layout_id,
            "name": config.display_name,
            "description": config.description,
            "requirements": {
                "image_slots": img_count,
                "text_structure": "bullets" if config.max_bullets and config.max_bullets > 0 else "paragraph",
                "max_items": config.max_bullets or 0
            },
            "suitable_for": config.suitable_keywords
        }
        schemas.append(schema)
        
    return schemas
