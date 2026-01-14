from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ...common.schemas import (
    AnimationConfig,
    ColorConfig,
    FontConfig,
    ImageryConfig,
    LayoutConfig,
    StyleConfig,
    StyleSampleSlide,
    TeachingRequest,
)

# ... (STYLE_TEMPLATES omitted for brevity, assuming replace_file_content handles boundaries correctly. 
# Wait, I need to touch imports at top and choose_style at bottom.
# I will make two edits or use multi_replace if they are far apart.
# They are far apart (Lines 5 and 188). I will use MultiReplace.)


"""
样式模板定义模块。

该模块定义了不同教学场景下的视觉风格配置。
STYLE_TEMPLATES 字典中的每个键代表一种特定的教学风格，其配置项包括：

- style_name: 样式的唯一标识名称。
- color: 颜色方案配置。
    - primary: 主色调，用于核心组件和标题。
    - secondary: 辅助背景色或次要元素颜色。
    - accent: 强调色，用于突出显示关键信息。
    - muted: 弱化颜色，用于次要文本或装饰线。
    - text: 主要正文颜色。
    - background: 幻灯片全局背景色。
    - warning: 警告或错误提示的颜色。
- font: 字体与排版配置。
    - title_family: 标题字体系列。
    - body_family: 正文字体系列。
    - title_size: 标题字号大小。
    - body_size: 正文字号大小。
    - line_height: 文本行间距倍数。
- layout: 页面布局配置。
    - density: 内容分布密度（如 'comfortable' 舒适, 'compact' 紧凑）。
    - notes_area: 是否在页面中预留讲师备注区域。
    - alignment: 文本对齐方式（如 'left', 'center'）。
    - header_rule: 是否在页眉下方显示分割线。
    - steps_panel: 是否启用步骤引导面板，用于展示多步骤教学流程的进度。
- imagery: 视觉素材偏好配置。
    - image_style: 推荐的配图风格（如 'clean_diagram', 'photo'）。
    - icon_style: 图标的视觉风格（如 'linear', 'instruction'）。
    - chart_preference: 优先选用的图表或可视化类型列表。
"""

STYLE_TEMPLATES = {
    "theory_clean": {
        "style_name": "theory_clean",
        "color": {
            "primary": "#1F4E79",
            "secondary": "#F3F5F7",
            "accent": "#2E75B6",
            "muted": "#94A3B8",
            "text": "#111827",
            "background": "#FFFFFF",
            "warning": "#DC2626",
            "surface": "#FFFFFF",
            "background_gradient": "linear-gradient(135deg, #FDFBFB 0%, #EBEDEE 100%)",
        },
        "font": {
            "title_family": "Microsoft YaHei",
            "body_family": "Microsoft YaHei",
            "code_family": "Consolas, 'Courier New', monospace",
            "title_size": 36,
            "body_size": 22,
            "line_height": 1.2,
        },
        "layout": {
            "density": "comfortable",
            "notes_area": True,
            "alignment": "left",
            "header_rule": True,
            "border_radius": "8px",
            "box_shadow": "soft",
        },
        "animation": {
            "transition": "slide",
            "element_entry": "fade-up",
        },
        "imagery": {
            "image_style": "clean_diagram",
            "icon_style": "linear",
            "chart_preference": ["mindmap", "flow", "table"],
        },
    },
    "practice_steps": {
        "style_name": "practice_steps",
        "color": {
            "primary": "#166534",
            "secondary": "#F0FDF4",
            "accent": "#22C55E",
            "muted": "#9CA3AF",
            "text": "#0F172A",
            "background": "#FFFFFF",
            "warning": "#DC2626",
            "surface": "#F8FAFC",
            "background_gradient": None,
        },
        "font": {
            "title_family": "Microsoft YaHei",
            "body_family": "Microsoft YaHei",
            "code_family": "Consolas, monospace",
            "title_size": 34,
            "body_size": 22,
            "line_height": 1.15,
        },
        "layout": {
            "density": "compact",
            "notes_area": True,
            "alignment": "left",
            "header_rule": False,
            "steps_panel": True,
            "border_radius": "4px",
            "box_shadow": "none",
        },
        "animation": {
            "transition": "fade",
            "element_entry": "none",
        },
        "imagery": {
            "image_style": "photo_or_step_diagram",
            "icon_style": "instruction",
            "chart_preference": ["flow", "table"],
        },
    },
    "review_mindmap": {
        "style_name": "review_mindmap",
        "color": {
            "primary": "#4C1D95",
            "secondary": "#F5F3FF",
            "accent": "#7C3AED",
            "muted": "#A78BFA",
            "text": "#111827",
            "background": "#FFFFFF",
            "warning": "#DC2626",
            "surface": "#FFFFFF",
            "background_gradient": "linear-gradient(to top, #f3e7e9 0%, #e3eeff 99%, #e3eeff 100%)",
        },
        "font": {
            "title_family": "Microsoft YaHei",
            "body_family": "Microsoft YaHei",
            "code_family": "Consolas, monospace",
            "title_size": 34,
            "body_size": 22,
            "line_height": 1.2,
        },
        "layout": {
            "density": "comfortable",
            "notes_area": False,
            "alignment": "center",
            "mindmap": True,
            "header_rule": True,
            "border_radius": "12px",
            "box_shadow": "hard",
        },
        "animation": {
            "transition": "zoom",
            "element_entry": "typewriter",
        },
        "imagery": {
            "image_style": "diagram",
            "icon_style": "linear",
            "chart_preference": ["mindmap", "table"],
        },
    },
}

PROFESSIONAL_PALETTES = {
    "engineering": {"primary": "#1F4E79", "secondary": "#F1F5F9", "accent": "#0EA5E9", "muted": "#94A3B8"},
    "medical": {"primary": "#0D9488", "secondary": "#F0FDFA", "accent": "#14B8A6", "muted": "#9CA3AF"},
    "agriculture": {"primary": "#15803D", "secondary": "#F0FDF4", "accent": "#84CC16", "muted": "#71717A"},
    "arts": {"primary": "#BE123C", "secondary": "#FFF1F2", "accent": "#FB7185", "muted": "#A1A1AA"},
    "business": {"primary": "#1E3A8A", "secondary": "#EFF6FF", "accent": "#F59E0B", "muted": "#6B7280"},
    "science": {"primary": "#6D28D9", "secondary": "#F5F3FF", "accent": "#8B5CF6", "muted": "#A78BFA"},
    "civil": {"primary": "#9A3412", "secondary": "#FFEDD5", "accent": "#EA580C", "muted": "#A8A29E"},
    "transportation": {"primary": "#0369A1", "secondary": "#E0F2FE", "accent": "#38BDF8", "muted": "#94A3B8"},
    "tourism": {"primary": "#EA580C", "secondary": "#FFF7ED", "accent": "#FDBA74", "muted": "#D6D3D1"},
    "food": {"primary": "#D97706", "secondary": "#FEF3C7", "accent": "#FCD34D", "muted": "#D4D4D8"},
    "textile": {"primary": "#C026D3", "secondary": "#FAE8FF", "accent": "#E879F9", "muted": "#D8B4FE"},
    "resources": {"primary": "#475569", "secondary": "#F8FAFC", "accent": "#64748B", "muted": "#94A3B8"},
    "water": {"primary": "#0891B2", "secondary": "#ECFEFF", "accent": "#06B6D4", "muted": "#A5F3FC"},
    "media": {"primary": "#DC2626", "secondary": "#FEF2F2", "accent": "#EF4444", "muted": "#FCA5A5"},
    "public-security": {"primary": "#172554", "secondary": "#F0F9FF", "accent": "#3B82F6", "muted": "#64748B"},
    "public-service": {"primary": "#059669", "secondary": "#ECFDF5", "accent": "#34D399", "muted": "#9CA3AF"},
    "sports": {"primary": "#2563EB", "secondary": "#EFF6FF", "accent": "#FBBF24", "muted": "#93C5FD"},
}


def choose_style(req: TeachingRequest) -> StyleConfig:
    # 1. Select base template
    if req.teaching_scene == "practice":
        base = STYLE_TEMPLATES["practice_steps"]
    elif req.teaching_scene == "review":
        base = STYLE_TEMPLATES["review_mindmap"]
    else:
        base = STYLE_TEMPLATES["theory_clean"]

    # 2. Copy base color to avoid mutating the global template
    color = dict(base["color"])

    # 3. Apply professional palette if available
    prof_category = req.professional_category
    if prof_category in PROFESSIONAL_PALETTES:
        palette = PROFESSIONAL_PALETTES[prof_category]
        color.update(palette)

    # 4. Handle warnings overrides
    # If user requested warnings, we ensure warning color is present (it is in base)
    # If they customized it, we overwrite
    if req.special_requirements.warnings.enabled:
        if req.special_requirements.warnings.color:
            color["warning"] = req.special_requirements.warnings.color

    cfg = StyleConfig(
        style_name=base["style_name"],
        color=ColorConfig(**color),
        font=FontConfig(**base["font"]),
        layout=LayoutConfig(**base["layout"]),
        imagery=ImageryConfig(**base["imagery"]),
        animation=AnimationConfig(**base.get("animation", {})),
    )
    return cfg


def build_style_samples(req: TeachingRequest, cfg: StyleConfig) -> List[StyleSampleSlide]:
    kp_names = [kp.name for kp in req.knowledge_points]
    deck_title = " / ".join(kp_names) if kp_names else "课件"
    if req.teaching_scene == "practice":
        return [
            StyleSampleSlide(kind="cover", title=f"{req.subject or ''}：{deck_title}", bullets=["实训课件", "步骤清晰 | 风险提示"]),
            StyleSampleSlide(kind="content", title="知识点与实训目标", bullets=["本次实训目标", "对应知识点", "评价标准/达标要求"]),
            StyleSampleSlide(kind="steps", title="实训步骤示例", bullets=["步骤1：…（要点）", "步骤2：…（要点）", "注意事项：…（警示）"]),
        ]

    if req.teaching_scene == "review":
        return [
            StyleSampleSlide(kind="cover", title=f"{req.subject or ''}：{deck_title} 复习课", bullets=["结构化梳理 | 典型题"]),
            StyleSampleSlide(kind="content", title="知识结构框架", bullets=["主干概念", "关键关系", "易错点"]),
            StyleSampleSlide(kind="steps", title="典型题/方法总结", bullets=["题型A：…", "题型B：…", "通用策略：…"]),
        ]

    return [
        StyleSampleSlide(kind="cover", title=f"{req.subject or ''}：{deck_title}", bullets=["理论课件", "简洁清晰 | 重点突出"]),
        StyleSampleSlide(kind="content", title="核心概念页示例", bullets=["定义", "关键要点", "常见误区/注意"]),
        StyleSampleSlide(kind="steps", title="案例/习题页示例", bullets=["情境描述", "分析步骤", "小结"]),
    ]
