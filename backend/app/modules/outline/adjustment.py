"""
3.3 PPT大纲生成 - 页面调整算法

智能合并精简策略
"""
from __future__ import annotations

from typing import List, Optional

from ...common.schemas import OutlineSlide, PPTOutline


def adjust_outline_to_target_count(outline: PPTOutline, target_count: Optional[int]) -> PPTOutline:
    """调整大纲页面数量以符合目标页数要求（智能合并精简策略）。
    
    实现三级优先级策略：
    1. 优先级1: 移除非教学必需页面（agenda, warning, qa）
    2. 优先级2: 合并同主题内容页（intro+concept, 案例页, 练习页）
    3. 优先级3: 精简内容（最后手段，确保不删除核心知识点页面）
    """
    if target_count is None:
        return outline
    
    slides = outline.slides.copy()
    current_count = len(slides)
    
    if current_count > target_count:
        # 优先级1: 移除非教学必需页面
        slides = _remove_non_essential_slides(slides, target_count)
        
        # 如果还不够，进行优先级2: 合并同主题内容页
        if len(slides) > target_count:
            slides = _merge_similar_slides(slides, target_count)
        
        # 如果还不够，进行优先级3: 精简内容（最后手段）
        if len(slides) > target_count:
            slides = _simplify_content_slides(slides, target_count)
    
    elif current_count < target_count:
        # 添加Q&A页面
        while len(slides) < target_count:
            qa_slide = OutlineSlide(
                index=len(slides) + 1,
                slide_type="qa",
                title="课堂互动 / Q&A",
                bullets=["问题1：____", "问题2：____"],
                interactions=["举手/弹幕提问"],
            )
            slides.append(qa_slide)
    
    # 重新索引
    for idx, slide in enumerate(slides, start=1):
        slide.index = idx
    
    # 创建新的大纲对象
    return PPTOutline(
        deck_title=outline.deck_title,
        subject=outline.subject,
        knowledge_points=outline.knowledge_points,
        teaching_scene=outline.teaching_scene,
        slides=slides,
    )


def _remove_non_essential_slides(slides: List[OutlineSlide], target_count: int) -> List[OutlineSlide]:
    """优先级1: 移除非教学必需页面。
    
    移除顺序：
    1. agenda（目录页）：内容可精简为封面页下方小字或并入objectives
    2. warning（注意页）：将易错点、安全警示嵌入对应steps或concept的bullets
    3. qa（问答页）：将互动问答内容并入summary作为"课后答疑"板块
    """
    result = []
    removed_count = 0
    target_removal = len(slides) - target_count
    
    # 按优先级移除
    removable_priority = ["agenda", "qa", "warning"]  # agenda优先级最高
    
    for slide in slides:
        if removed_count < target_removal and slide.slide_type in removable_priority:
            # 尝试将内容嵌入到相关页面
            if slide.slide_type == "warning":
                # 将warning内容嵌入到前面的concept或steps页面
                _embed_warning_content(result, slide)
            elif slide.slide_type == "qa":
                # 将qa内容嵌入到summary页面
                _embed_qa_content(result, slide)
            # agenda直接移除，不需要嵌入
            removed_count += 1
        else:
            result.append(slide)
    
    return result


def _merge_similar_slides(slides: List[OutlineSlide], target_count: int) -> List[OutlineSlide]:
    """优先级2: 合并同主题内容页。
    
    合并策略：
    1. 知识点导入+概念合并：将同一知识点的intro和concept合并为1页
    2. 多案例页合并：将相似案例合并为1页"典型案例对比分析"
    3. 练习页整合：将多个小题的exercises页合并为1页"综合巩固练习"
    """
    result = []
    i = 0
    
    while i < len(slides):
        current = slides[i]
        
        # 尝试合并intro和concept
        if current.slide_type == "intro" and i + 1 < len(slides):
            next_slide = slides[i + 1]
            if next_slide.slide_type == "concept":
                merged = _merge_intro_and_concept(current, next_slide)
                result.append(merged)
                i += 2
                continue
        
        # 尝试合并多个案例页
        if current.slide_type in ["exercises", "case_study"] and current.title.startswith("案例"):
            case_slides = [current]
            j = i + 1
            while j < len(slides) and slides[j].slide_type == current.slide_type:
                case_slides.append(slides[j])
                j += 1
            if len(case_slides) > 1:
                merged = _merge_case_slides(case_slides)
                result.append(merged)
                i = j
                continue
        
        # 尝试合并多个练习页
        if current.slide_type == "exercises":
            exercise_slides = [current]
            j = i + 1
            while j < len(slides) and slides[j].slide_type == "exercises":
                exercise_slides.append(slides[j])
                j += 1
            if len(exercise_slides) > 1:
                merged = _merge_exercise_slides(exercise_slides)
                result.append(merged)
                i = j
                continue
        
        result.append(current)
        i += 1
    
    # 如果合并后仍然超过目标，继续移除
    if len(result) > target_count:
        # 移除bridge、relations等过渡页
        result = [s for s in result if s.slide_type not in ["bridge", "relations"]]
    
    return result


def _simplify_content_slides(slides: List[OutlineSlide], target_count: int) -> List[OutlineSlide]:
    """优先级3: 精简内容（最后手段）。
    
    确保不删除核心知识点页面（cover, objectives, concept, summary）。
    优先精简非核心内容页。
    """
    result = []
    core_types = {"cover", "objectives", "concept", "summary"}
    removable_types = {"bridge", "relations", "intro"}
    
    # 先移除可移除类型
    for slide in slides:
        if len(result) >= target_count and slide.slide_type in removable_types:
            continue
        result.append(slide)
    
    # 如果还不够，从末尾移除非核心页面（但保留封面和目标）
    while len(result) > target_count and len(result) > 2:
        if result[-1].slide_type not in core_types:
            result.pop()
        else:
            break
    
    return result


def _merge_intro_and_concept(intro: OutlineSlide, concept: OutlineSlide) -> OutlineSlide:
    """合并知识点的导入和概念页。"""
    merged_title = f"{concept.title}——从案例看核心概念"
    merged_bullets = intro.bullets[:2] + concept.bullets[:3]  # 合并要点，限制数量
    merged_assets = (intro.assets or []) + (concept.assets or [])
    merged_interactions = (intro.interactions or []) + (concept.interactions or [])
    
    return OutlineSlide(
        index=intro.index,
        slide_type="concept",
        title=merged_title,
        bullets=merged_bullets,
        notes=concept.notes or intro.notes,
        assets=merged_assets[:3],  # 限制素材数量
        interactions=merged_interactions[:2],  # 限制互动数量
    )


def _merge_case_slides(case_slides: List[OutlineSlide]) -> OutlineSlide:
    """合并案例页。"""
    merged_title = "典型案例对比分析"
    merged_bullets = []
    for i, slide in enumerate(case_slides[:3], 1):  # 最多合并3个案例
        merged_bullets.append(f"案例{i}：{slide.title}")
        merged_bullets.extend(slide.bullets[:2])  # 每个案例取前2个要点
    
    merged_assets = []
    for slide in case_slides[:3]:
        merged_assets.extend(slide.assets or [])
    
    return OutlineSlide(
        index=case_slides[0].index,
        slide_type="case_study",
        title=merged_title,
        bullets=merged_bullets[:8],  # 限制总要点数
        notes="通过对比分析多个典型案例，加深理解",
        assets=merged_assets[:2],  # 限制素材数量
        interactions=case_slides[0].interactions or [],
    )


def _merge_exercise_slides(exercise_slides: List[OutlineSlide]) -> OutlineSlide:
    """合并练习页。"""
    merged_title = "综合巩固练习"
    merged_bullets = []
    for i, slide in enumerate(exercise_slides, 1):
        merged_bullets.append(f"【题型{i}】{slide.title}")
        merged_bullets.extend(slide.bullets[:2])  # 每个练习取前2个要点
    
    return OutlineSlide(
        index=exercise_slides[0].index,
        slide_type="exercises",
        title=merged_title,
        bullets=merged_bullets[:10],  # 限制总要点数
        notes="按题型分块展示，便于系统练习",
        assets=exercise_slides[0].assets or [],
        interactions=exercise_slides[0].interactions or [],
    )


def _embed_warning_content(slides: List[OutlineSlide], warning_slide: OutlineSlide) -> None:
    """将warning内容嵌入到相关页面。"""
    if not slides:
        return
    
    # 找到最近的concept或steps页面
    for slide in reversed(slides):
        if slide.slide_type in ["concept", "steps"]:
            # 将warning的要点添加到该页面的bullets
            warning_bullets = [f"⚠️ {b}" for b in warning_slide.bullets[:2]]
            slide.bullets.extend(warning_bullets)
            break


def _embed_qa_content(slides: List[OutlineSlide], qa_slide: OutlineSlide) -> None:
    """将qa内容嵌入到summary页面。"""
    # 找到summary页面
    for slide in reversed(slides):
        if slide.slide_type == "summary":
            # 将qa内容添加到summary作为"课后答疑"板块
            qa_section = ["课后答疑："]
            qa_section.extend(qa_slide.bullets[:3])
            slide.bullets.extend(qa_section)
            break
