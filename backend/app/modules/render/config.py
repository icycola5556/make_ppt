"""
Module 3.5: 配置定义 (Configs & Constants)
包含布局模板定义、不仅路径配置等。
"""
from pathlib import Path
from .core import LayoutConfig

# ============================================================================
# Path Constants
# ============================================================================

MODULE_DIR = Path(__file__).parent
TEMPLATE_DIR = MODULE_DIR / "templates"
SRC_STATIC_DIR = MODULE_DIR / "static"
SRC_STYLES_DIR = MODULE_DIR / "styles"

# ============================================================================
# Layout Definitions
# ============================================================================

VOCATIONAL_LAYOUTS = {
    # ========== 基础布局 ==========
    #纯标题页
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
    
    #标题+要点
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
    #左文右图
    "title_bullets_right_img": LayoutConfig(
        layout_id="title_bullets_right_img",
        display_name="左文右图（动态版）",
        description="最常用布局,左侧要点,右侧图片，支持动态比例",
        grid_template_areas='"title title" "bullets image"',
        # 支持动态变量
        grid_template_columns="var(--col-text, 3fr) var(--col-img, 2fr)",
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
        max_text_length=450, 
    ),
    
    #左图右步骤
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
    
    #左右对比
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
    
    #四宫格
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
    
    # ========== 新增多样化布局 ==========
    
    #表格对比
    "table_comparison": LayoutConfig(
        layout_id="table_comparison",
        display_name="表格对比",
        description="双列表格对比布局,适合参数/特性对比",
        grid_template_areas='"title title" "table table"',
        grid_template_columns="1fr 1fr",
        grid_template_rows="auto 1fr",
        gap="1.5rem",
        image_slots=[],
        suitable_slide_types=["comparison", "concept", "keypoints"],
        suitable_keywords=["对比", "参数", "特性", "比较", "表格", "数据"],
        max_bullets=8,
        max_text_length=500,
    ),
    
    #水平时间轴
    "timeline_horizontal": LayoutConfig(
        layout_id="timeline_horizontal",
        display_name="水平时间轴",
        description="横向时间线/流程展示,适合阶段性内容",
        grid_template_areas='"title title title" "step1 step2 step3"',
        grid_template_columns="1fr 1fr 1fr",
        grid_template_rows="auto 1fr",
        gap="1rem",
        image_slots=[],
        suitable_slide_types=["steps", "process", "history"],
        suitable_keywords=["阶段", "阶段", "历程", "发展", "时间", "演变"],
        max_bullets=6,
        max_text_length=300,
    ),
    
    #中心视觉
    "center_visual": LayoutConfig(
        layout_id="center_visual",
        display_name="中心视觉",
        description="大图居中,标题在上,说明在下",
        grid_template_areas='"title" "image" "caption"',
        grid_template_columns="1fr",
        grid_template_rows="auto 1fr auto",
        gap="1rem",
        image_slots=[
            {
                "position": "center",
                "x": 0.15,
                "y": 0.18,
                "w": 0.70,
                "h": 0.60,
                "aspect_ratio": "16:9",
                "default_style": "photo",
                "priority": 1,
            }
        ],
        suitable_slide_types=["concept", "demo", "showcase"],
        suitable_keywords=["展示", "核心", "重点", "关键", "主图"],
        max_bullets=3,
        max_text_length=200,
    ),
    
    #上下分栏
    "split_vertical": LayoutConfig(
        layout_id="split_vertical",
        display_name="上下分栏",
        description="上图下文或上文下图布局",
        grid_template_areas='"title" "top" "bottom"',
        grid_template_columns="1fr",
        grid_template_rows="auto 1fr 1fr",
        gap="1rem",
        image_slots=[
            {
                "position": "top",
                "x": 0.06,
                "y": 0.15,
                "w": 0.88,
                "h": 0.38,
                "aspect_ratio": "21:9",
                "default_style": "photo",
                "priority": 1,
            }
        ],
        suitable_slide_types=["concept", "intro", "overview"],
        suitable_keywords=["全景", "俯视", "概览", "场景"],
        max_bullets=4,
        max_text_length=250,
    ),
}
