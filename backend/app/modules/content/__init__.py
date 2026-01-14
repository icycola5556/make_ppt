# modules/content - 3.4 PPT内容生成模块
# 负责逐页内容生成、LLM优化、内容校验

from .core import build_base_deck, refine_with_llm, validate_deck

__all__ = ["build_base_deck", "refine_with_llm", "validate_deck"]
