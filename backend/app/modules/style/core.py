"""
3.2 PPT风格设计 - 核心算法

包含风格匹配算法和样例生成
"""
from __future__ import annotations

from typing import List

from ...common.schemas import StyleConfig, StyleSampleSlide, TeachingRequest
from .templates import STYLE_TEMPLATES


def choose_style(req: TeachingRequest) -> StyleConfig:
    """
    根据教学需求选择并生成风格配置。
    
    Args:
        req: 教学需求对象
        
    Returns:
        StyleConfig: 完整的风格配置
    """
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
    """
    生成风格样例页面供预览。
    
    Args:
        req: 教学需求对象
        cfg: 风格配置
        
    Returns:
        List[StyleSampleSlide]: 3个样例页面（封面/内容/步骤）
    """
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
