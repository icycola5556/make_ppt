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
from ...common import LLMClient
from ...prompts.style import STYLE_REFINE_PROMPT
import json

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
            "primary": "#3D5A80",
            "secondary": "#F0F4F8",
            "accent": "#5B8DB8",
            "muted": "#98B4C8",
            "text": "#1A202C",
            "background": "#FFFFFF",
            "warning": "#E53E3E",
            "surface": "#F8FAFC",
            "background_gradient": "linear-gradient(135deg, #FDFBFB 0%, #EBF0F5 100%)",
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
            "primary": "#2D6A4F",
            "secondary": "#E9F5EC",
            "accent": "#52B788",
            "muted": "#8FBCA8",
            "text": "#1A202C",
            "background": "#FFFFFF",
            "warning": "#E53E3E",
            "surface": "#F5FAF7",
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
            "primary": "#5C4B7D",
            "secondary": "#F5F3F8",
            "accent": "#7E6BA8",
            "muted": "#A8A0BC",
            "text": "#1A202C",
            "background": "#FFFFFF",
            "warning": "#E53E3E",
            "surface": "#FAF9FC",
            "background_gradient": "linear-gradient(to top, #F3E7E9 0%, #E3EEFF 100%)",
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
    # 1. Engineering: Steel Blue family (Stability, Precision)
    # 主色与强调色保持蓝色系协调
    "engineering": {
        "primary": "#4A6FA5",   # Morandi Blue
        "secondary": "#F0F4F8", # Cool Grey Surface
        "accent": "#6B9BD1",    # Lighter Steel Blue (同色系提亮)
        "muted": "#8898AA",     # Steel Grey
        "background_gradient": "linear-gradient(135deg, #F5F7FA 0%, #C3CFE2 100%)"
    },
    # 2. Medical: Teal family (Healing, Calm)
    # 青绿色系统一
    "medical": {
        "primary": "#5F9EA0",   # Cadet Blue / Sage
        "secondary": "#F5FFFA", # Mint Cream
        "accent": "#7EC8C8",    # Light Teal (同色系提亮)
        "muted": "#9EB2B5",     # Greyish Teal
        "background_gradient": "linear-gradient(to top, #e6e9f0 0%, #eef1f5 100%)" 
    },
    # 3. Agriculture: Green family (Growth, Nature)
    # 绿色系从深到浅
    "agriculture": {
        "primary": "#556B2F",   # Dark Olive Green
        "secondary": "#FFFFF0", # Ivory
        "accent": "#7BA05B",    # Moss Green (同色系提亮)
        "muted": "#8FBC8F",     # Dark Sea Green
        "background_gradient": "linear-gradient(120deg, #fdfbfb 0%, #ebedee 100%)"
    },
    # 4. Arts: Rose/Mauve family (Creativity, Humanism)
    # 玫瑰色系协调
    "arts": {
        "primary": "#B06579",   # Dusty Rose
        "secondary": "#FFF5F7", # Lavender Blush
        "accent": "#D4899D",    # Light Rose (同色系提亮)
        "muted": "#BC8F8F",     # Rosy Brown
        "background_gradient": "linear-gradient(to top, #fad0c4 0%, #ffd1ff 100%)"
    },
    # 5. Business: Navy Blue family (Trust, Professionalism)
    # 深蓝色系统一，不用金色
    "business": {
        "primary": "#3E517A",   # Muted Navy
        "secondary": "#F8F9FA", # Off White
        "accent": "#6B82A8",    # Light Navy (同色系提亮)
        "muted": "#708090",     # Slate Grey
        "background_gradient": "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)"
    },
    # 6. Science: Purple/Indigo family (Mystery, Depth)
    # 紫色系从深到浅
    "science": {
        "primary": "#483D8B",   # Dark Slate Blue
        "secondary": "#F5F5F5", # White Smoke
        "accent": "#7B68EE",    # Medium Slate Blue (同色系提亮)
        "muted": "#778899",     # Light Slate Grey
        "background_gradient": "linear-gradient(to top, #cfd9df 0%, #e2ebf0 100%)"
    },
    # 7. Civil: Terracotta/Brown family (Structure, Grounded)
    # 棕色暖色系
    "civil": {
        "primary": "#A0522D",   # Sienna
        "secondary": "#FAF0E6", # Linen
        "accent": "#C4835A",    # Light Sienna (同色系提亮)
        "muted": "#D2B48C",     # Tan
        "background_gradient": "linear-gradient(to right, #ece9e6, #ffffff)"
    },
    # 8. Transportation: Steel Blue family (Speed, Flow)
    # 钢蓝色统一
    "transportation": {
        "primary": "#4682B4",   # Steel Blue
        "secondary": "#F0F8FF", # Alice Blue
        "accent": "#87CEEB",    # Sky Blue (同色系提亮)
        "muted": "#A9A9A9",     # Dark Grey
        "background_gradient": "linear-gradient(to top, #e6e9f0 0%, #eef1f5 100%)"
    },
    # 9. Tourism: Coral/Salmon family (Warmth, Leisure)
    # 暖橙色系
    "tourism": {
        "primary": "#E9967A",   # Dark Salmon
        "secondary": "#FFFAF0", # Floral White
        "accent": "#FFB299",    # Light Coral (同色系提亮)
        "muted": "#D2B48C",     # Tan
        "background_gradient": "linear-gradient(to top, #fff1eb 0%, #ffecd2 100%)"
    },
    # 10. Food: Warm Brown/Orange family (Appetizing, Natural)
    # 暖棕橙色系
    "food": {
        "primary": "#D2691E",   # Chocolate
        "secondary": "#FFF8DC", # Cornsilk
        "accent": "#E8A64C",    # Warm Orange (同色系提亮)
        "muted": "#DEB887",     # Burlywood
        "background_gradient": "linear-gradient(120deg, #ffecd2 0%, #fcb69f 100%)"
    },
    # 11. Textile: Purple/Lavender family (Softness, Fabric)
    # 紫色系统一
    "textile": {
        "primary": "#9F79EE",   # Muted Purple
        "secondary": "#FFF0F5", # Lavender Blush
        "accent": "#B8A0E8",    # Light Lavender (同色系提亮)
        "muted": "#D8BFD8",     # Thistle
        "background_gradient": "linear-gradient(to top, #e8e0f0 0%, #f8f0ff 100%)"
    },
    # 12. Resources: Slate Grey family (Earth, Solidity)
    # 灰色系统一
    "resources": {
        "primary": "#475569",   # Slate 600
        "secondary": "#F1F5F9", # Slate 100
        "accent": "#64748B",    # Slate 500 (同色系提亮)
        "muted": "#CBD5E1",     # Slate 300
        "background_gradient": "linear-gradient(135deg, #e0eaec 0%, #f0f7f9 100%)"
    },
    # 13. Water: Cyan/Teal family (Fluidity, Clarity)
    # 青蓝色系
    "water": {
        "primary": "#008B8B",   # Dark Cyan
        "secondary": "#F0FFFF", # Azure
        "accent": "#20B2AA",    # Light Sea Green (同色系提亮)
        "muted": "#5F9EA0",     # Cadet Blue
        "background_gradient": "linear-gradient(to top, #accbee 0%, #e7f0fd 100%)"
    },
    # 14. Media: Red family (Boldness, Attention)
    # 红色系统一
    "media": {
        "primary": "#B22222",   # Firebrick
        "secondary": "#FFFAFA", # Snow
        "accent": "#DC4545",    # Bright Red (同色系提亮)
        "muted": "#808080",     # Grey
        "background_gradient": "linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%)"
    },
    # 15. Public Security: Dark Grey/Blue family (Authority, Safety)
    # 深灰蓝色系
    "public-security": {
        "primary": "#2F4F4F",   # Dark Slate Gray
        "secondary": "#F5F5F5", # White Smoke
        "accent": "#4F6F6F",    # Light Slate (同色系提亮)
        "muted": "#A9A9A9",     # Dark Gray
        "background_gradient": "linear-gradient(to top, #cfd9df 0%, #e2ebf0 100%)"
    },
    # 16. Public Service: Green family (Service, Approachable)
    # 绿色系统一
    "public-service": {
        "primary": "#2E8B57",   # Sea Green
        "secondary": "#F0FFF0", # Honeydew
        "accent": "#50C878",    # Emerald (同色系提亮)
        "muted": "#8FBC8F",     # Dark Sea Green
        "background_gradient": "linear-gradient(120deg, #e8f5e8 0%, #f0fff0 100%)"
    },
    # 17. Sports: Blue family (Energy, Activity)
    # 蓝色系统一，不用对比橙色
    "sports": {
        "primary": "#4169E1",   # Royal Blue
        "secondary": "#F0F8FF", # Alice Blue
        "accent": "#6B8CE8",    # Light Royal Blue (同色系提亮)
        "muted": "#6495ED",     # Cornflower Blue
        "background_gradient": "linear-gradient(to right, #e0f0ff 0%, #f0f8ff 100%)"
    },
}

# Fixups for gradients to ensure text readability (mostly dark text on light bg)
# Water
PROFESSIONAL_PALETTES["water"]["background_gradient"] = "linear-gradient(to top, #accbee 0%, #e7f0fd 100%)"
# Civil (Concrete)
PROFESSIONAL_PALETTES["civil"]["background_gradient"] = "linear-gradient(to right, #ece9e6, #ffffff)"
# Media (Clean modern)
PROFESSIONAL_PALETTES["media"]["background_gradient"] = "linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%)"
# Sports (Less neon)
PROFESSIONAL_PALETTES["sports"]["background_gradient"] = "linear-gradient(120deg, #e0c3fc 0%, #8ec5fc 100%)" # Cool activity


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


def get_luminance(hex_color: str) -> float:
    """Calculate relative luminance for WCAG contrast check."""
    if not hex_color or not hex_color.startswith("#"):
        return 0.5
    try:
        hex_color = hex_color.lstrip("#")
        req_rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        rgb = [c / 255.0 for c in req_rgb]
        srgb = [(c / 12.92) if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
        return 0.2126 * srgb[0] + 0.7152 * srgb[1] + 0.0722 * srgb[2]
    except Exception:
        return 0.5

def check_contrast(text_color: str, bg_color: str) -> bool:
    """Check if contrast ratio >= 3:1 (WCAG AA Large Text)."""
    l1 = get_luminance(text_color)
    l2 = get_luminance(bg_color)
    ratio = (l1 + 0.05) / (l2 + 0.05) if l1 > l2 else (l2 + 0.05) / (l1 + 0.05)
    return ratio >= 3.0

async def refine_style_with_llm(
    session_id: str,
    current_config: StyleConfig,
    feedback: str,
    llm: LLMClient,
    logger
) -> Tuple[StyleConfig, List[str]]:
    """Refine style based on user feedback using LLM."""
    
    # 1. Prepare Prompt
    current_json = current_config.model_dump_json()
    prompt = STYLE_REFINE_PROMPT.replace("Current Config", current_json).replace("User Feedback", feedback)
    
    # 2. Call LLM
    try:
        response = await llm.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7 # Allow some creativity for "Generative Mode"
        )
        
        # 3. Parse JSON Patch
        # Remove potential markdown block
        json_str = response.strip()
        if json_str.startswith("```"):
            json_str = json_str.split("\n", 1)[1].rsplit("\n", 1)[0]
            
        patch = json.loads(json_str)
        
        # 4. Merge Patch
        # Deep merge helper or simple dict update? Pydantic can handle partial updates via copy+update
        # But we need to handle nested dicts (color, font, etc.)
        current_dict = current_config.model_dump()
        
        def deep_update(d, u):
            for k, v in u.items():
                if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                    deep_update(d[k], v)
                else:
                    d[k] = v
        
        deep_update(current_dict, patch)
        
        # 5. Validate & Rehydrate
        new_config = StyleConfig(**current_dict)
        
        # 6. Safety Check (Contrast)
        warnings = []
        if new_config.color:
            # Check Text vs Background
            if not check_contrast(new_config.color.text, new_config.color.background):
                warnings.append(f"文字与背景对比度过低 (Text: {new_config.color.text}, Bg: {new_config.color.background})")
            
            # Check Muted vs Background if strictly needed, or Primary vs Background
            if not check_contrast(new_config.color.primary, new_config.color.background):
                warnings.append("主色与背景对比度较低，可能影响标题识别")
            
            # Check Warning visibility
            if not check_contrast(new_config.color.warning, new_config.color.background):
                 warnings.append("警示色不明显")
        
        return new_config, warnings

    except Exception as e:
        logger.emit(session_id, "3.2", "refine_error", {"error": str(e)})
        # Return original if failed
        return current_config, [f"调整失败: {str(e)}"]

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
