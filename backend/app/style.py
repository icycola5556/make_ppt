from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .schemas import StyleConfig, StyleSampleSlide, TeachingRequest


STYLE_TEMPLATES = {
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


def choose_style(req: TeachingRequest) -> StyleConfig:
    if req.teaching_scene == "practice":
        base = STYLE_TEMPLATES["practice_steps"]
    elif req.teaching_scene == "review":
        base = STYLE_TEMPLATES["review_mindmap"]
    else:
        base = STYLE_TEMPLATES["theory_clean"]

    # If user requested warning marks, make warning more prominent
    color = dict(base["color"])
    if req.warning_mark and req.warning_color:
        # allow CSS color name or hex
        color["warning"] = req.warning_color

    cfg = StyleConfig(
        style_name=base["style_name"],
        color=color,
        font=dict(base["font"]),
        layout=dict(base["layout"]),
        imagery=dict(base["imagery"]),
    )
    return cfg


def build_style_samples(req: TeachingRequest, cfg: StyleConfig) -> List[StyleSampleSlide]:
    deck_title = " / ".join(req.knowledge_points) if req.knowledge_points else "课件"
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
