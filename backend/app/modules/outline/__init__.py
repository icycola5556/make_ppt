# modules/outline - 3.3 PPT大纲生成模块
# 负责结构化大纲生成、LLM智能规划、页面冲突调整

# 暂时从原始位置导入以保持兼容性
from ...outline import generate_outline, generate_outline_with_llm

__all__ = ["generate_outline", "generate_outline_with_llm"]
