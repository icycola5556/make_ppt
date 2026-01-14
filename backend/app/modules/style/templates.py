"""
3.2 PPT风格设计 - 模板定义

定义3套基础风格模板（理论课/实训课/复习课）
"""
from __future__ import annotations

from typing import Any, Dict

# 3套基础场景模板，决定布局结构和字体排印
STYLE_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "theory_clean": {
        "style_name": "theory_clean",
        "color": {
            "primary": "#1F4E79",
            "secondary": "#F3F5F7",
            "accent": "#2E75B6",
            "text": "#111827",
            "background": "#FFFFFF",
            "warning": "#DC2626",
        },
        "font": {
            "title_family": "Microsoft YaHei",
            "body_family": "Microsoft YaHei",
            "title_size": 36,
            "body_size": 22,
            "line_height": 1.2,
        },
        "layout": {
            "density": "comfortable",
            "notes_area": True,
            "alignment": "left",
            "header_rule": True,
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
            "text": "#0F172A",
            "background": "#FFFFFF",
            "warning": "#DC2626",
        },
        "font": {
            "title_family": "Microsoft YaHei",
            "body_family": "Microsoft YaHei",
            "title_size": 34,
            "body_size": 22,
            "line_height": 1.15,
        },
        "layout": {
            "density": "compact",
            "notes_area": True,
            "alignment": "left",
            "steps_panel": True,
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
            "text": "#111827",
            "background": "#FFFFFF",
            "warning": "#DC2626",
        },
        "font": {
            "title_family": "Microsoft YaHei",
            "body_family": "Microsoft YaHei",
            "title_size": 34,
            "body_size": 22,
            "line_height": 1.2,
        },
        "layout": {
            "density": "comfortable",
            "notes_area": False,
            "alignment": "center",
            "mindmap": True,
        },
        "imagery": {
            "image_style": "diagram",
            "icon_style": "linear",
            "chart_preference": ["mindmap", "table"],
        },
    },
}
