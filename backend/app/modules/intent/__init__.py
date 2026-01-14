# modules/intent - 3.1 意图理解模块
# 负责解析用户输入、验证需求、构建问题、LLM推荐页数

from .parser import heuristic_parse
from .validator import validate_and_build_questions, apply_user_answers, autofill_defaults
from .recommender import recommend_slide_count_with_llm
from .display import generate_display_summary, generate_final_confirm_summary, update_page_distribution

__all__ = [
    "heuristic_parse",
    "validate_and_build_questions",
    "apply_user_answers",
    "autofill_defaults",
    "recommend_slide_count_with_llm",
    "generate_display_summary",
    "generate_final_confirm_summary",
    "update_page_distribution",
]
