"""
大纲验证与自动修正模块
负责检查大纲是否满足用户指定的约束条件，并自动修正缺失的内容
"""
from typing import List, Tuple, Any
from ...common.schemas import PPTOutline, OutlineSlide, TeachingRequest


def validate_outline_constraints(
    outline: PPTOutline,
    req: TeachingRequest
) -> Tuple[bool, List[str]]:
    """验证大纲是否满足用户指定的约束条件

    Args:
        outline: 生成的大纲
        req: 用户的教学需求

    Returns:
        (is_valid, warnings): 是否有效，警告列表
    """
    warnings = []

    # 1. 验证案例页数量
    if req.special_requirements.cases.enabled:
        expected_cases = req.special_requirements.cases.count
        case_slides = [
            s for s in outline.slides
            if s.slide_type in ["case", "case_study"]
        ]
        actual_cases = len(case_slides)

        if actual_cases != expected_cases:
            warnings.append(
                f"⚠️ 案例页数量不匹配: 用户要求{expected_cases}个，实际生成{actual_cases}个"
            )
            # 严重错误，返回False
            if abs(actual_cases - expected_cases) > 1:
                return False, warnings

    # 2. 验证习题页存在性和题目数量
    if req.special_requirements.exercises.enabled:
        expected_total = req.special_requirements.exercises.total_count
        exercise_slides = [
            s for s in outline.slides
            if s.slide_type in ["exercises", "quiz"]
        ]

        if len(exercise_slides) == 0:
            warnings.append(
                f"⚠️ 缺少习题页，用户要求包含{expected_total}道题"
            )
            return False, warnings

        # 统计实际题目数量（通过bullets数量估算）
        actual_questions = sum(len(s.bullets) for s in exercise_slides)
        if actual_questions < expected_total * 0.8:  # 允许20%误差
            warnings.append(
                f"⚠️ 习题数量可能不足: 用户要求{expected_total}道，实际约{actual_questions}道"
            )

    # 3. 验证思政内容
    if req.special_requirements.ideological_education.enabled:
        ideological_slides = [
            s for s in outline.slides
            if s.slide_type == "ideological_summary" or "思政" in s.title
        ]

        if len(ideological_slides) == 0:
            warnings.append("⚠️ 缺少思政教育内容，但用户启用了思政融入")

    # 4. 验证页面总数
    total_slides = len(outline.slides)
    min_count = req.slide_requirements.min_count or 0
    max_count = req.slide_requirements.max_count or 100

    if total_slides < min_count:
        warnings.append(
            f"⚠️ 页面总数不足: 最少需要{min_count}页，实际{total_slides}页"
        )
        return False, warnings

    if total_slides > max_count:
        warnings.append(
            f"⚠️ 页面总数超标: 最多{max_count}页，实际{total_slides}页"
        )

    return True, warnings


def auto_correct_outline(
    outline: PPTOutline,
    req: TeachingRequest,
    logger: Any,
    session_id: str
) -> PPTOutline:
    """自动修正大纲，补充缺失的页面

    Args:
        outline: 待修正的大纲
        req: 用户的教学需求
        logger: 日志记录器
        session_id: 会话ID

    Returns:
        修正后的大纲
    """

    # 1. 补充缺失的案例页
    if req.special_requirements.cases.enabled:
        expected_cases = req.special_requirements.cases.count
        current_cases = [s for s in outline.slides if s.slide_type in ["case", "case_study"]]

        if len(current_cases) < expected_cases:
            missing_count = expected_cases - len(current_cases)
            logger.emit(session_id, "3.3", "auto_adding_cases", {
                "missing_count": missing_count
            })

            # 在summary页之前插入案例页
            summary_index = next(
                (i for i, s in enumerate(outline.slides) if s.slide_type == "summary"),
                len(outline.slides)
            )

            for i in range(missing_count):
                case_slide = OutlineSlide(
                    index=summary_index + i,
                    slide_type="case",
                    title=f"补充案例{len(current_cases) + i + 1}：{req.knowledge_points[0].name if req.knowledge_points else '应用示例'}",
                    bullets=[
                        "案例背景：（待补充具体情境）",
                        "问题描述：（待补充问题）",
                        "分析过程：（待补充分析步骤）",
                        "解决方案：（待补充方案）",
                        "总结提升：（待补充知识点总结）"
                    ],
                    notes="自动生成的案例页，请在编辑器中完善内容",
                    assets=[],
                    interactions=[]
                )
                outline.slides.insert(summary_index + i, case_slide)

    # 2. 补充缺失的习题页
    if req.special_requirements.exercises.enabled:
        expected_total = req.special_requirements.exercises.total_count
        current_exercises = [s for s in outline.slides if s.slide_type in ["exercises", "quiz"]]

        if len(current_exercises) == 0:
            logger.emit(session_id, "3.3", "auto_adding_exercises", {
                "total_count": expected_total
            })

            # 在summary页之前插入习题页
            summary_index = next(
                (i for i, s in enumerate(outline.slides) if s.slide_type == "summary"),
                len(outline.slides)
            )

            exercise_slide = OutlineSlide(
                index=summary_index,
                slide_type="exercises",
                title="习题巩固",
                bullets=[
                    f"题目{i+1}：（待补充具体题目）"
                    for i in range(expected_total)
                ],
                notes="自动生成的习题页，请在编辑器中完善题目内容",
                assets=[],
                interactions=[]
            )
            outline.slides.insert(summary_index, exercise_slide)

    # 3. 补充缺失的思政内容（如果是dedicated_section模式）
    if req.special_requirements.ideological_education.enabled:
        if req.special_requirements.ideological_education.integration_method == "dedicated_section":
            # 检查是否已有思政总结页
            has_ideological = any(
                s.slide_type == "ideological_summary" or "思政" in s.title
                for s in outline.slides
            )

            if not has_ideological:
                logger.emit(session_id, "3.3", "auto_adding_ideological", {
                    "focus_points": req.special_requirements.ideological_education.focus_points
                })

                # 在summary页之前插入思政总结页
                summary_index = next(
                    (i for i, s in enumerate(outline.slides) if s.slide_type == "summary"),
                    len(outline.slides)
                )

                ideological_slide = OutlineSlide(
                    index=summary_index,
                    slide_type="ideological_summary",
                    title="课程思政总结",
                    bullets=[
                        f"{point}：（待补充具体内容）"
                        for point in req.special_requirements.ideological_education.focus_points
                    ],
                    notes="自动生成的思政总结页，请在编辑器中完善内容",
                    assets=[],
                    interactions=[]
                )
                outline.slides.insert(summary_index, ideological_slide)

    # 重新编号
    for i, slide in enumerate(outline.slides, start=1):
        slide.index = i

    return outline
