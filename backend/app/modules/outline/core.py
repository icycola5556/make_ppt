from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from ...common.schemas import OutlineSlide, PPTOutline, TeachingRequest


def _deck_title(req: TeachingRequest) -> str:
    """生成课件标题"""
    kps = req.kp_names
    if kps:
        if len(kps) == 1:
            return kps[0]
        return "、".join(kps)
    return "知识点课件"


# ============================================================================
# LLM智能规划系统提示词
# ============================================================================

OUTLINE_PLANNING_SYSTEM_PROMPT = """你是高职课程PPT大纲智能规划专家，负责根据教学需求生成结构化的课件大纲。

## 核心职责
1. **智能页面规划**：根据知识点数量、难度、教学场景，合理分配页面数量和类型
2. **教学逻辑编排**：按照"封面→目标→导入→讲解→案例→练习→总结"的逻辑顺序组织内容
3. **素材占位定义**：为每页预定义图片、图表等素材需求
4. **互动设计优化**：根据教学场景和知识点特点，设计合适的互动环节

## 页面类型体系
系统支持以下12种页面类型（slide_type）：
- **cover**: 封面页（课件标题页）
- **agenda**: 目录页（教学内容导航，可选）
- **objectives**: 目标页（教学目标展示）
- **intro**: 导入页（情景引入/问题导入）
- **concept**: 概念页（核心概念定义）
- **steps**: 步骤页（操作步骤说明，实训课）
- **warning**: 注意页（安全警示/易错点）
- **exercises**: 练习页（习题/巩固练习）
- **summary**: 总结页（知识点归纳）
- **relations**: 联系页（知识关联图）
- **bridge**: 过渡页（衔接页）
- **qa**: 问答页（互动问答页）

## 页面分配原则

### 固定页面（必须包含）
- 封面(cover): 1页
- 目标(objectives): 1页
- 总结(summary): 1页

### 知识点内容页分配
- **简单知识点(easy)**: 1-2页（概念定义 + 要点解析）
- **中等知识点(medium)**: 2-3页（导入 + 概念定义 + 要点解析）
- **困难知识点(hard)**: 3-4页（导入 + 概念定义 + 要点解析 + 深入讲解）

### 场景特定页面
- **理论课(theory)**: 导入页、概念页、要点解析页、案例页（可选）、练习页（可选）
- **实训课(practice)**: 任务映射页、准备页、步骤页（多个）、注意事项页、巩固页
- **复习课(review)**: 复习路线页、知识框架页、知识点回顾页、易错点页、典型题页

### 特殊需求页面
- **案例页**: 根据 special_requirements.cases.count 决定（最多3页）
- **练习页**: 根据 special_requirements.exercises.total_count 决定（每页约3道题）
- **互动页**: 根据 special_requirements.interaction.types 决定（每类型1页，最多2页）

## 素材占位定义规范
每页的assets字段应包含素材占位信息：
```json
{
  "type": "image|diagram|chart|icon",
  "theme": "素材主题描述（如'液压系统原理图'）",
  "size": "small|medium|large|16:9|4:3|1:1",
  "style": "photo|illustration|schematic|mindmap|flow"
}
```

## 互动设计规范
interactions字段应包含具体的互动设计：
- 理论课：提问、案例分析、小组讨论
- 实训课：操作演示、随堂提问、学员提交
- 复习课：投票、抢答、现场作答

## 输出要求
1. 严格按照JSON Schema输出，确保所有字段完整
2. 页面序号从1开始（index字段）
3. 每页的bullets应包含3-5个核心要点
4. 标题应具体明确，体现教学重点
5. 确保页面数量符合target_count要求（如果指定）

只输出JSON对象，不要解释。"""


# ============================================================================
# 确定性生成（Fallback）
# ============================================================================

def generate_outline(req: TeachingRequest, style_name: str | None = None) -> PPTOutline:
    """Generate a slide-level outline following 方案 3.3.
    
    This is a deterministic baseline. If LLM is enabled, the workflow may
    ask LLM to rewrite titles/bullets, but the structure is controlled here.
    """

    title = _deck_title(req)
    subj = req.subject or "未指定学科"
    kps = req.kp_names or ["未指定知识点"]

    slides: List[OutlineSlide] = []

    def add(slide_type: str, title: str, bullets: List[str], notes: str | None = None, 
            assets: List[Dict[str, Any]] | None = None, interactions: List[str] | None = None):
        slides.append(
            OutlineSlide(
                index=len(slides) + 1,
                slide_type=slide_type,
                title=title,
                bullets=bullets,
                notes=notes,
                assets=assets or [],
                interactions=interactions or [],
            )
        )

    # --- Common slides ---
    add(
        "cover",
        f"{subj}：{title}",
        [
            "授课人：_____",
            "时间：_____",
            f"教学场景：{req.teaching_scene}",
        ],
        notes="封面信息可在前端编辑区直接改。",
    )

    # Objectives
    goals = req.teaching_objectives
    goal_bullets = []
    if goals.knowledge:
        goal_bullets.append(f"知识目标：{'；'.join(goals.knowledge)}")
    if goals.ability:
        goal_bullets.append(f"能力目标：{'；'.join(goals.ability)}")
    if goals.literacy:
        goal_bullets.append(f"素养目标：{'；'.join(goals.literacy)}")

    add("objectives", "教学目标", goal_bullets or ["（待补充）"], notes="可根据班级学情进一步细化。")

    # Scene-specific templates
    if req.teaching_scene == "practice":
        add(
            "mapping",
            "知识点与实训任务对应",
            [
                "本次实训任务：_____",
                "对应知识点：" + "、".join(kps),
                "达标标准：_____",
            ],
            assets=[{"type": "diagram", "theme": "knowledge_to_task_mapping", "size": "16:9"}],
        )
        add(
            "prep",
            "实训准备",
            [
                "工具/材料：_____",
                "安全检查：_____",
                "环境要求：_____",
            ],
            assets=[{"type": "icon", "theme": "tools_and_safety", "size": "1:1"}],
        )
        # Steps
        step_count = 3
        for i in range(1, step_count + 1):
            add(
                "steps",
                f"实训步骤 {i}",
                [
                    f"操作要点：步骤{i}的关键动作/顺序",
                    "质量要点：如何判断做对了",
                    "对应知识点：_____",
                ],
                assets=[{"type": "image", "theme": f"practice_step_{i}", "size": "16:9"}],
            )

        warn_title = "注意事项 / 警示" if req.warning_mark else "注意事项"
        warn_bullets = [
            "高风险点：_____",
            "常见错误：_____",
            "纠正方法：_____",
        ]
        interactions = ["随堂提问：你认为最容易出错的步骤是？"] if req.include_interaction else []
        add(
            "warning",
            warn_title,
            warn_bullets,
            assets=[{"type": "icon", "theme": "warning", "size": "1:1"}],
            interactions=interactions,
        )

        if req.include_exercises:
            add(
                "exercises",
                "实训巩固 / 自测",
                [
                    "自测题1：_____",
                    "自测题2：_____",
                    "评分要点：_____",
                ],
                interactions=["学员提交：拍照/勾选完成情况"] if req.include_interaction else [],
            )

        add("summary", "实训总结", ["本次实训关键点回顾", "常见问题与改进建议", "拓展任务：_____"], notes="可追加作业或拓展练习。")

    elif req.teaching_scene == "review":
        add(
            "agenda",
            "复习路线",
            [
                "知识结构梳理",
                "典型题与方法总结",
                "易错点与纠错",
            ],
        )
        add(
            "relations",
            "知识结构框架",
            ["主干：____", "分支：____", "关键关系：____"],
            assets=[{"type": "diagram", "theme": "knowledge_framework", "size": "16:9", "style": "mindmap"}],
        )
        for kp in kps:
            add(
                "concept",
                f"知识点回顾：{kp}",
                ["定义/结论", "关键条件", "典型应用"],
            )

        add(
            "warning",
            "易错点清单",
            ["易错点1：____", "易错点2：____", "纠错方法：____"],
            interactions=["投票：你最不确定的是哪一类题？"] if req.include_interaction else [],
        )

        add(
            "exercises",
            "典型题讲解",
            ["题目：____", "思路：____", "答案：____"],
        )

        if req.include_exercises:
            add(
                "exercises",
                "随堂练习",
                ["练习1：____", "练习2：____", "参考答案：____"],
                interactions=["现场作答区"] if req.include_interaction else [],
            )

        add("summary", "复习小结", ["结构回顾", "方法总结", "考前提醒/建议"], notes="可加入时间分配与复盘提示。")

    else:
        # theory (default)
        add(
            "intro",
            "导入：为什么要学这个知识点？",
            [
                "真实场景/岗位任务引入",
                "本节课解决什么问题",
                "与后续知识/技能的联系",
            ],
            assets=[{"type": "image", "theme": "scene_intro", "size": "16:9", "style": "photo"}],
            interactions=["提问：你在哪些场景见过它？"] if req.include_interaction else [],
        )

        if len(kps) >= 2:
            add(
                "relations",
                "知识点关联框架",
                ["知识点之间的先后/并列关系", "关键连接：____", "学习路径：____"],
                assets=[{"type": "diagram", "theme": "knowledge_relations", "size": "16:9", "style": "flow"}],
            )

        for kp in kps:
            add(
                "concept",
                f"核心概念：{kp}",
                ["定义", "组成/特征", "关键术语解释"],
                assets=[{"type": "diagram", "theme": f"{kp}_definition", "size": "4:3", "style": "schematic"}],
            )
            add(
                "concept",
                f"要点解析：{kp}",
                ["要点1：____", "要点2：____", "要点3：____"],
            )

        if req.include_cases:
            add(
                "exercises",
                "案例应用",
                ["案例背景：____", "分析：____", "结论：____"],
                assets=[{"type": "image", "theme": "case_image", "size": "16:9", "style": "photo"}],
            )

        if req.include_exercises:
            add(
                "exercises",
                "习题巩固",
                ["题目1：____", "题目2：____", "参考答案/解析：____"],
                interactions=["现场作答区"] if req.include_interaction else [],
            )

        add(
            "summary",
            "总结",
            ["本节课你应该会：____", "关键记忆点：____", "下节课预告：____"],
        )

    # Adjust to slide_count (simple): trim optional slides or pad with Q&A
    target = req.slide_count or len(slides)
    if len(slides) > target:
        # Remove optional types in this order
        removable = {"agenda", "relations", "warning", "exercises"}
        i = len(slides) - 1
        while len(slides) > target and i >= 0:
            if slides[i].slide_type in removable:
                slides.pop(i)
            i -= 1
        # If still too long, truncate from the end but keep cover/objectives
        while len(slides) > target and len(slides) > 2:
            slides.pop()

    while len(slides) < target:
        add(
            "qa",
            "课堂互动 / Q&A",
            ["问题1：____", "问题2：____"],
            interactions=["举手/弹幕提问"] if req.include_interaction else [],
        )

    # re-index
    for idx, s in enumerate(slides, start=1):
        s.index = idx

    return PPTOutline(
        deck_title=f"{subj}：{title}",
        subject=subj,
        knowledge_points=kps,
        teaching_scene=req.teaching_scene,
        slides=slides,
    )


# ============================================================================
# LLM智能规划生成
# ============================================================================

async def generate_outline_with_llm(
    req: TeachingRequest,
    style_name: Optional[str],
    llm: Any,  # LLMClient
    logger: Any,  # WorkflowLogger
    session_id: str,
) -> PPTOutline:
    """使用LLM进行智能规划生成PPT大纲。
    
    此函数会：
    1. 评估知识点难度和教学逻辑
    2. 智能分配页面数量和类型
    3. 生成合适的互动设计和素材需求
    4. 优化标题和要点表述
    
    Args:
        req: 教学需求（3.1模块输出）
        style_name: 风格名称（3.2模块输出）
        llm: LLM客户端
        logger: 日志记录器
        session_id: 会话ID
        
    Returns:
        PPTOutline: 优化后的PPT大纲
    """
    
    if not llm.is_enabled():
        # LLM未启用，使用确定性生成
        return generate_outline(req, style_name)
    
    # 构建用户输入消息
    user_payload = {
        "teaching_request": {
            "subject": req.subject,
            "professional_category": req.professional_category,
            "teaching_scene": req.teaching_scene,
            "knowledge_points": [
                {
                    "name": kp.name,
                    "type": kp.type,
                    "difficulty_level": kp.difficulty_level,
                    "is_core": getattr(kp, "is_core", True),
                    "estimated_teaching_time_min": getattr(kp, "estimated_teaching_time_min", None),
                }
                for kp in req.knowledge_points
            ],
            "teaching_objectives": {
                "knowledge": req.teaching_objectives.knowledge,
                "ability": req.teaching_objectives.ability,
                "literacy": req.teaching_objectives.literacy,
            },
            "slide_requirements": {
                "target_count": req.slide_requirements.target_count,
                "min_count": req.slide_requirements.min_count,
                "max_count": req.slide_requirements.max_count,
                "lesson_duration_min": req.slide_requirements.lesson_duration_min,
            },
            "special_requirements": {
                "cases": {
                    "enabled": req.special_requirements.cases.enabled,
                    "count": req.special_requirements.cases.count,
                    "case_type": getattr(req.special_requirements.cases, "case_type", None),
                },
                "exercises": {
                    "enabled": req.special_requirements.exercises.enabled,
                    "total_count": req.special_requirements.exercises.total_count,
                },
                "interaction": {
                    "enabled": req.special_requirements.interaction.enabled,
                    "types": req.special_requirements.interaction.types,
                },
                "warnings": {
                    "enabled": req.special_requirements.warnings.enabled,
                },
            },
            "estimated_page_distribution": req.estimated_page_distribution.model_dump() if req.estimated_page_distribution else None,
        },
        "style_name": style_name,
    }
    
    user_msg = json.dumps(user_payload, ensure_ascii=False, indent=2)
    
    # 获取JSON Schema
    schema_hint = PPTOutline.model_json_schema()
    schema_str = json.dumps(schema_hint, ensure_ascii=False, indent=2)
    
    # 记录日志
    logger.emit(session_id, "3.3", "llm_planning_prompt", {
        "system": OUTLINE_PLANNING_SYSTEM_PROMPT,
        "user": user_payload,
        "schema_hint": schema_hint,
    })
    
    try:
        # 调用LLM进行智能规划
        parsed, meta = await llm.chat_json(
            OUTLINE_PLANNING_SYSTEM_PROMPT,
            user_msg,
            schema_str,
            temperature=0.3,  # 稍高的温度以获得更多创意
        )
        
        logger.emit(session_id, "3.3", "llm_planning_response", meta)
        
        # 验证并返回结果
        outline = PPTOutline.model_validate(parsed)
        
        # 后处理：确保页面数量符合要求
        outline = _adjust_outline_to_target_count(outline, req.slide_requirements.target_count)
        
        return outline
        
    except Exception as e:
        # LLM调用失败，降级到确定性生成
        logger.emit(session_id, "3.3", "llm_planning_error", {
            "error": str(e),
            "fallback_to_deterministic": True,
        })
        return generate_outline(req, style_name)


def _adjust_outline_to_target_count(outline: PPTOutline, target_count: Optional[int]) -> PPTOutline:
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
