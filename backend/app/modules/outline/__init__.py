# modules/outline - 3.3 PPT大纲生成模块
# 负责结构化大纲生成、LLM智能规划、页面冲突调整

from .core import (
    generate_outline,
    generate_outline_with_llm,
    generate_outline_from_distribution,
)

__all__ = [
    "generate_outline",
    "generate_outline_with_llm",
    "generate_outline_from_distribution",
]
