# modules/intent - 3.1 意图理解模块
# 负责用户输入解析、需求校验、交互问答

from .parser import (
    # 核心解析
    heuristic_parse,
    validate_and_build_questions,
    apply_user_answers,
    autofill_defaults,

    # 辅助函数
    detect_professional_category,
    calculate_min_slides,
    check_slide_count_conflict,

    # 显示和分布
    generate_display_summary,
    update_page_distribution,

    # LLM相关
    recommend_slide_count_with_llm,

    # 风格模板选择（从3.2迁移）
    select_style_name_by_scene,
)

__all__ = [
    # 核心解析
    "heuristic_parse",
    "validate_and_build_questions",
    "apply_user_answers",
    "autofill_defaults",

    # 辅助函数
    "detect_professional_category",
    "calculate_min_slides",
    "check_slide_count_conflict",

    # 显示和分布
    "generate_display_summary",
    "update_page_distribution",

    # LLM相关
    "recommend_slide_count_with_llm",

    # 风格模板选择（从3.2迁移）
    "select_style_name_by_scene",
]
