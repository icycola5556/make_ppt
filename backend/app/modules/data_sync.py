"""
跨模块数据同步工具
负责不同模块间数据格式的转换和同步，特别是从 3.4 内容层到 3.3/3.5 结构层的映射。
"""
from typing import List, Dict, Any

def sync_visual_suggestions_to_assets(
    outline_slide: Any,  # OutlineSlide Object
    visual_suggestions: List[str],
    page_title: str
) -> Any:
    """
    将 3.4 生成的 visual_suggestions (Prompt字符串列表)
    同步回 3.3 的 assets (结构化字典列表)
    """
    if not visual_suggestions:
        return outline_slide

    # 清空旧的 assets (因为 3.4 的内容更新、更准)
    new_assets = []

    for suggestion in visual_suggestions:
        # 解析建议文本，提取关键信息
        asset_type, theme, description = _parse_visual_suggestion(suggestion, page_title)

        asset = {
            "type": asset_type,
            "theme": theme,
            "description": description, # 这是最重要的字段，承载了高质量 Prompt
            "size": "16:9",  # 默认值，Engine 会根据 Layout 覆盖它
            "style": "photorealistic", # 默认值，Services 会覆盖它
            "source": "3.4_content_gen"
        }
        new_assets.append(asset)

    # 更新对象
    outline_slide.assets = new_assets
    return outline_slide


def _parse_visual_suggestion(suggestion: str, page_title: str) -> tuple[str, str, str]:
    """
    解析建议字符串。
    预期格式: "[Subject], [Style], [Composition]..."
    或者普通自然语言描述。
    """
    text = suggestion.strip()

    # 1. 简单的类型推断
    lower_text = text.lower()
    if any(k in lower_text for k in ["diagram", "schematic", "blueprint", "chart", "graph"]):
        asset_type = "diagram"
    elif any(k in lower_text for k in ["icon", "symbol", "vector"]):
        asset_type = "icon"
    else:
        asset_type = "image" # 默认为照片/插图

    # 2. 提取主题 (Theme) - 取前 15 个字或第一个逗号前的内容
    first_part = text.split(",")[0].split("，")[0]
    theme = first_part[:20] + "..." if len(first_part) > 20 else first_part

    # 3. 描述 (Description) - 就是完整的建议文本
    # 如果文本太短，拼上标题增强上下文
    description = text
    if len(description) < 10:
        description = f"{page_title}: {description}"

    return asset_type, theme, description
