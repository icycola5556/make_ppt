from __future__ import annotations

import json
import math
import re
from typing import Any, Dict, List, Optional, Tuple

from .schemas import (
    ProfessionalCategory, Question, TeachingRequest,
    SubjectInfo, KnowledgePointDetail, KnowledgeStructure, TeachingScenarioDetail,
    TeachingObjectivesStructured, SlideRequirementsDetail, CaseRequirement,
    ExerciseRequirement, InteractionRequirement, WarningRequirement,
    SpecialRequirementsDetailed, PageDistribution, ParsingMetadata
)
from .standards import default_goals


def _assess_kp_difficulty(kp_name: str, user_text: str) -> str:
    """评估知识点难度（备用函数，与workflow.py中的逻辑保持一致）"""
    if not kp_name:
        return "medium"

    name_lower = kp_name.lower()
    text_lower = user_text.lower()

    # 简单难度关键词
    easy_keywords = ["基本概念", "定义", "简介", "概述", "基础", "入门"]
    # 困难难度关键词
    hard_keywords = ["计算", "公式", "推导", "分析", "设计", "优化", "高级", "复杂", "深入"]

    # 检查是否包含困难关键词
    if any(kw in name_lower or kw in text_lower for kw in hard_keywords):
        return "hard"

    # 检查是否包含简单关键词
    if any(kw in name_lower or kw in text_lower for kw in easy_keywords):
        return "easy"

    # 基于名称长度和复杂度判断
    if len(kp_name) > 15 or "原理" in kp_name or "系统" in kp_name:
        return "hard"
    elif len(kp_name) < 6 or "概念" in kp_name or "定义" in kp_name:
        return "easy"
    else:
        return "medium"


# ============================================================================
# Professional Category Recognition
# ============================================================================

# Keywords mapping to professional categories (based on 30 PPT analysis)
PROFESSIONAL_KEYWORDS: Dict[str, List[str]] = {
        "engineering": ["机械", "电气", "汽修", "数控", "建筑", "焊接", "模具", "工程", "制造", "工业"],
        "medical": ["护理", "医学", "药学", "康复", "临床", "解剖", "医生", "医疗", "卫生"],
        "agriculture": ["农业", "林业", "园艺", "畜牧", "森林", "生态", "种植", "养殖"],
        "arts": ["设计", "艺术", "语文", "音乐", "舞蹈", "思政", "教育", "美术", "设计"],
        "business": ["会计", "电商", "金融", "物流", "营销", "管理", "财务", "商务"],
        "science": ["数学", "物理", "化学", "计算机", "网页", "编程", "信息技术", "程序"],
        "civil": ["土木", "桥梁", "施工", "道路", "隧道", "建工", "市政"],
        "transportation": ["铁道", "城轨", "民航", "航海", "汽车运用", "物流配送", "港口运输", "交通"],
        "tourism": ["旅游", "酒店", "导游", "会展", "烹饪", "景区", "餐饮"],
        "food": ["食品", "制药", "加工", "检测", "粮食", "药材"],
        "textile": ["纺织", "服装", "印刷", "包装", "家具", "皮革", "服饰"],
        "resources": ["地质", "测绘", "矿业", "石油", "环保", "环境", "安全技术", "探矿"],
        "water": ["水利", "水电", "水文", "港航", "水产"],
        "media": ["新闻", "采编", "影视", "多媒体", "新媒体", "出版", "广播"],
        "public-security": ["公安", "刑事", "司法", "法律", "矫正", "安防", "警察"],
        "public-service": ["人力资源", "社工", "社会工作", "老年服务", "家政", "婚庆", "公共服务"],
        "sports": ["体育", "运动", "训练", "健身", "体育教育", "裁判"],
    }

# Slide count coefficient by category (from research)
CATEGORY_SLIDE_COEFFICIENT: Dict[str, float] = {
    "engineering": 1.0,
    "medical": 1.0,
    "agriculture": 1.0,
    "arts": 1.2,
    "business": 1.0,
    "science": 0.8,
    "civil": 1.3,
    "unknown": 1.0,
}


def detect_professional_category(text: str, subject: Optional[str] = None) -> ProfessionalCategory:
    """Detect professional category from text and subject.
    
    Returns the category with highest keyword match count.
    """
    combined = f"{text} {subject or ''}".lower()
    
    scores: Dict[str, int] = {}
    for category, keywords in PROFESSIONAL_KEYWORDS.items():
        scores[category] = sum(1 for kw in keywords if kw in combined)
    
    if max(scores.values()) == 0:
        return "unknown"
    
    return max(scores, key=scores.get)  # type: ignore


def calculate_min_slides(
    knowledge_points: List[KnowledgePointDetail],
    include_exercises: bool = True,
    professional_category: ProfessionalCategory = "unknown",
) -> int:
    """Calculate minimum recommended slide count based on research."""
    kp_count = len(knowledge_points) or 1
    
    # Base pages: cover(1) + intro(1-2) + objectives(1) + summary(2)
    base_pages = 5
    
    # Content pages: ~3-4 per knowledge point
    content_pages = kp_count * 3
    
    # Exercise pages
    exercise_pages = 0
    if include_exercises:
        exercise_pages = max(1, math.ceil(kp_count / 2))
    
    # Calculate total
    total = base_pages + content_pages + exercise_pages
    
    # Apply category coefficient
    coef = CATEGORY_SLIDE_COEFFICIENT.get(professional_category, 1.0)
    adjusted = int(math.ceil(total * coef))
    
    return max(6, adjusted)  # Minimum 6 pages


def check_slide_count_conflict(req: TeachingRequest) -> bool:
    """Check if user-specified slide count is less than minimum needed."""
    if req.slide_requirements.target_count is None:
        return False
    if req.slide_requirements.min_count is None:
        return False
    return req.slide_requirements.target_count < req.slide_requirements.min_count


# ============================================================================
# LLM推荐页数功能
# ============================================================================

async def recommend_slide_count_with_llm(
    req: TeachingRequest,
    llm: Any,  # LLMClient
    logger: Any,  # WorkflowLogger
    session_id: str,
) -> Tuple[Optional[int], Optional[str]]:
    """使用LLM分析教学需求，推荐合适的页数范围。
    
    Args:
        req: 教学需求对象
        llm: LLM客户端
        logger: 日志记录器
        session_id: 会话ID
        
    Returns:
        (recommended_count, explanation): 推荐的页数和说明
        如果LLM未启用或调用失败，返回(None, None)
    """
    if not llm.is_enabled():
        return None, None
    
    system_prompt = """你是高职教学课件页数规划专家。请根据教学需求分析，推荐合适的课件页数。

## 分析维度
1. **知识点复杂度**：考虑知识点数量、难度、类型（理论/实操）
2. **教学内容量**：概念讲解、案例展示、练习巩固等各部分所需页数
3. **教学场景特点**：理论课、实训课、复习课的不同需求
4. **特殊需求**：案例数、习题数、互动环节等对页数的影响

## 推荐原则
- 确保核心教学内容完整，不遗漏关键知识点
- 平衡内容深度和教学时间
- 考虑高职学生的认知特点，避免信息过载
- 为互动和练习预留合理空间

## 输出要求
返回JSON格式：
{
  "recommended_count": 整数（推荐的最小页数）,
  "explanation": "推荐理由的详细说明（中文）"
}

只输出JSON，不要解释。"""

    user_payload = {
        "knowledge_points": [
            {
                "name": kp.name,
                "type": kp.type,
                "difficulty_level": kp.difficulty_level,
            }
            for kp in req.knowledge_points
        ],
        "teaching_scene": req.teaching_scenario.scene_type,
        "target_count": req.slide_requirements.target_count,
        "min_count": req.slide_requirements.min_count,
        "special_requirements": {
            "cases": {
                "enabled": req.special_requirements.cases.enabled,
                "count": req.special_requirements.cases.count,
            },
            "exercises": {
                "enabled": req.special_requirements.exercises.enabled,
                "total_count": req.special_requirements.exercises.total_count,
            },
            "interaction": {
                "enabled": req.special_requirements.interaction.enabled,
            },
        },
        "estimated_distribution": req.estimated_page_distribution.model_dump() if req.estimated_page_distribution else None,
    }
    
    user_msg = json.dumps(user_payload, ensure_ascii=False, indent=2)
    
    schema_hint = {
        "type": "object",
        "properties": {
            "recommended_count": {"type": "integer", "description": "推荐的页数"},
            "explanation": {"type": "string", "description": "推荐理由说明"},
        },
        "required": ["recommended_count", "explanation"],
    }
    schema_str = json.dumps(schema_hint, ensure_ascii=False, indent=2)
    
    try:
        logger.emit(session_id, "3.1", "llm_recommend_slide_count", {
            "system": system_prompt,
            "user": user_payload,
        })
        
        parsed, meta = await llm.chat_json(
            system_prompt,
            user_msg,
            schema_str,
            temperature=0.3,
        )
        
        logger.emit(session_id, "3.1", "llm_recommend_slide_count_response", meta)
        
        recommended_count = parsed.get("recommended_count")
        explanation = parsed.get("explanation")
        
        # 确保推荐页数不小于最小页数
        if recommended_count and req.slide_requirements.min_count:
            recommended_count = max(recommended_count, req.slide_requirements.min_count)
        
        return recommended_count, explanation
        
    except Exception as e:
        logger.emit(session_id, "3.1", "llm_recommend_slide_count_error", {
            "error": str(e),
        })
        return None, None


# ============================================================================
# Human-Readable Display Summary Generation
# ============================================================================

# Professional category display names (Chinese)
CATEGORY_DISPLAY_NAMES = {
    "engineering": "工科/工程类",
    "medical": "医学/护理类",
    "agriculture": "农林类",
    "arts": "人文艺术类",
    "business": "商科类",
    "science": "理科类",
    "civil": "土木桥梁类",
    "unknown": "未知"
}

# Teaching scene display names
SCENE_DISPLAY_NAMES = {
    "theory": "理论讲解课",
    "practice": "实训操作课",
    "review": "复习巩固课",
    "unknown": "未指定"
}


def update_page_distribution(req: TeachingRequest) -> None:
    """Calculate and update estimated page distribution based on current request state.
    
    改进的页面分配算法：
    - 封面/目标/总结: 各1页（固定）
    - 导入: 1页
    - 概念定义: 每个知识点1页
    - 讲解: 根据知识点难度（easy=1页, medium=2页, hard=3页）
    - 案例: 每个案例1页（最多3页）
    - 习题: 每3道题1页，向上取整
    - 互动: 根据互动类型数量（每类型1页，最多2页）
    """
    import math
    
    kp_count = len(req.knowledge_points) or 1
    
    # 讲解页数：根据知识点难度动态计算
    # easy=1页, medium=2页, hard=3页
    DIFFICULTY_PAGES = {"easy": 1, "medium": 2, "hard": 3}
    explanation_pages = 0
    for kp in req.knowledge_points:
        difficulty = kp.difficulty_level or "medium"
        explanation_pages += DIFFICULTY_PAGES.get(difficulty, 2)
    # 确保至少有基础页数
    if explanation_pages == 0:
        explanation_pages = kp_count * 2
    
    # 案例页数：每个案例1页，但最多3页（超过则合并展示）
    case_count = req.special_requirements.cases.count if req.special_requirements.cases.enabled else 0
    case_pages = min(case_count, 3) if case_count > 0 else 0
    
    # 习题页数：每页约3道题，向上取整
    exercise_count = req.special_requirements.exercises.total_count if req.special_requirements.exercises.enabled else 0
    EXERCISES_PER_PAGE = 3
    exercise_pages = math.ceil(exercise_count / EXERCISES_PER_PAGE) if exercise_count > 0 else 0
    
    # 互动页数：根据互动类型数量（每种类型1页，最多2页）
    interaction_types = req.special_requirements.interaction.types if req.special_requirements.interaction.enabled else []
    interaction_pages = min(len(interaction_types), 2) if interaction_types else 0
    
    dist = PageDistribution(
        cover=1,
        objectives=1,
        introduction=1,
        concept_definition=kp_count,
        explanation=explanation_pages,
        case_study=case_pages,
        exercises=exercise_pages,
        interaction=interaction_pages,
        summary=1
    )
    req.estimated_page_distribution = dist


def generate_display_summary(req: TeachingRequest) -> str:
    """Generate human-readable summary for user display."""
    lines = []
    
    # Header
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("📋 课件需求确认")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")
    
    # Basic info
    subject = req.subject_info.subject_name or "未指定"
    category = CATEGORY_DISPLAY_NAMES.get(req.subject_info.subject_category, "未知")
    lines.append(f"📚 授课学科：{subject}（{category}）")
    if req.subject_info.sub_field:
        lines.append(f"   专业领域：{req.subject_info.sub_field}")
    lines.append("")
    
    # Knowledge points
    kp_count = len(req.knowledge_points)
    lines.append(f"📖 核心知识点（{kp_count}个）")
    if kp_count == 0:
        lines.append("   • （未识别到知识点，需要您补充）")
    else:
        for kp in req.knowledge_points:
            diff = {"easy": "简单", "medium": "中等", "hard": "较难"}.get(kp.difficulty_level, "未知")
            type_str = {"theory": "理论型", "practice": "实操型", "mixed": "混合型"}.get(kp.type, "理论型")
            lines.append(f"   • {kp.name}（{type_str}，难度：{diff}）")
    
    struct = req.knowledge_structure
    rel_type = {"single": "单一知识点", "parallel": "并列关系", "progressive": "递进关系", "causal": "因果关系"}.get(struct.relation_type, "未定义")
    lines.append(f"\n🔗 知识点关联：{rel_type}" + (f" - {struct.relation_description}" if struct.relation_description else ""))
    lines.append("")
    
    # Teaching goals
    lines.append("🎯 教学目标")
    goals = req.teaching_objectives
    if goals.knowledge:
        lines.append("   知识目标：")
        for g in goals.knowledge: lines.append(f"   • {g}")
    if goals.ability:
        lines.append("   能力目标：")
        for g in goals.ability: lines.append(f"   • {g}")
    if goals.literacy:
        lines.append("   素养目标：")
        for g in goals.literacy: lines.append(f"   • {g}")
    
    if goals.auto_generated:
        lines.append("\n   💡 (系统根据学科和场景自动生成)")
    lines.append("")
    
    # Teaching scene
    scene_label = req.teaching_scenario.scene_label or SCENE_DISPLAY_NAMES.get(req.teaching_scenario.scene_type, "未指定")
    lines.append(f"🏫 教学场景：{scene_label}")
    lines.append("")
    
    # Slide requirements
    slide_info = f"目标{req.slide_requirements.target_count or '待定'}页"
    if req.slide_requirements.min_count:
        slide_info += f"（范围{req.slide_requirements.min_count}-{req.slide_requirements.max_count or (req.slide_requirements.min_count + 2)}页）"
    lines.append(f"📄 课件页数：{slide_info}")
    lines.append(f"   课时：{req.slide_requirements.lesson_duration_min}分钟")
    lines.append("")
    
    # Special requirements
    lines.append("✨ 特殊需求")
    spec = req.special_requirements
    lines.append(f"   {'✅' if spec.cases.enabled else '❌'} 包含案例" + (f"：{spec.cases.count}个{spec.cases.case_type or ''}案例" if spec.cases.enabled else ""))
    lines.append(f"   {'✅' if spec.exercises.enabled else '❌'} 包含习题" + (f"：{spec.exercises.total_count}道练习题" if spec.exercises.enabled else ""))
    lines.append(f"   {'✅' if spec.interaction.enabled else '❌'} 互动环节" + (f"：{', '.join(spec.interaction.types) if spec.interaction.types else '常规互动'}" if spec.interaction.enabled else ""))
    lines.append(f"   {'✅' if spec.warnings.enabled else '❌'} 警示标注")
    lines.append(f"   {'✅' if spec.animations.enabled else '❌'} 动画占位")
    
    # Page distribution
    dist = req.estimated_page_distribution
    lines.append("\n📊 预估页面类型分布")
    parts = []
    if dist.cover: parts.append(f"封面({dist.cover})")
    if dist.objectives: parts.append(f"目标({dist.objectives})")
    if dist.introduction: parts.append(f"导入({dist.introduction})")
    if dist.concept_definition: parts.append(f"定义({dist.concept_definition})")
    if dist.explanation: parts.append(f"讲解({dist.explanation})")
    if dist.case_study: parts.append(f"案例({dist.case_study})")
    if dist.exercises: parts.append(f"习题({dist.exercises})")
    if dist.interaction: parts.append(f"互动({dist.interaction})")
    if dist.summary: parts.append(f"总结({dist.summary})")
    lines.append("   " + " + ".join(parts))
    
    lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return "\n".join(lines)


def generate_final_confirm_summary(req: TeachingRequest) -> str:
    """Generate final confirmation summary (shorter)."""
    return generate_display_summary(req)


# ============================================================================
# Heuristic Parser (Enhanced)
# ============================================================================

def heuristic_parse(user_text: str) -> TeachingRequest:
    """Heuristic parser for demo / LLM-offline."""
    t = user_text.strip()

    # subject
    subject_name = None
    subjects = [
        "数学", "机械", "护理", "计算机", "电工", "汽修", "语文", "英语",
        "电气", "电子", "土木", "桥梁", "医学", "药学", "农业", "林业",
        "森林", "园艺", "会计", "电商", "金融", "物流", "设计", "艺术",
        "音乐", "舞蹈", "思政", "化学", "物理", "网页", "建筑"
    ]
    for cand in subjects:
        if cand in t:
            subject_name = cand
            break

    professional_category = detect_professional_category(t, subject_name)

    # knowledge points
    kps: List[KnowledgePointDetail] = []
    invalid_kp_terms = ["ppt", "课件", "演示", "文稿", "幻灯片", "slide", "slides", "一个", "一份"]
    
    def is_valid_kp(kp: str) -> bool:
        kp_clean = kp.strip().lower()
        return len(kp_clean) >= 2 and kp_clean not in invalid_kp_terms
    
    found_kp_names = []
    quoted_pattern = r'["「『【]([^"」』】]{2,40})["」』】]'
    for m in re.findall(quoted_pattern, t):
        if is_valid_kp(m): found_kp_names.append(m)
    
    if not found_kp_names:
        keyword_pattern = r"(?:关于|主题是|知识点是?)[:：]?\s*([^，。；\n的]{2,30})"
        m = re.search(keyword_pattern, t)
        if m and is_valid_kp(m.group(1).strip()):
            found_kp_names.append(m.group(1).strip())
    
    for i, name in enumerate(found_kp_names):
        # 智能评估知识点难度
        difficulty = _assess_kp_difficulty(name, t)
        kp_type = "practice" if any(x in t for x in ["实操", "实训", "操作", "动手"]) else "theory"

        kps.append(KnowledgePointDetail(
            id=f"KP_{i+1:03d}",
            name=name,
            type=kp_type,
            difficulty_level=difficulty
        ))

    # teaching scene - 智能识别
    scene = _assess_teaching_scene(t, kps)


def _assess_teaching_scene(user_text: str, knowledge_points: List[KnowledgePointDetail]) -> str:
    """智能识别教学场景"""
    text_lower = user_text.lower()

    # 实践课关键词
    practice_keywords = ["实训", "实操", "操作", "动手", "实验", "练习", "技能", "步骤", "方法"]
    # 复习课关键词
    review_keywords = ["复习", "回顾", "总结", "巩固", "考前", "重温", "温习"]
    # 理论课关键词
    theory_keywords = ["理论", "原理", "概念", "基础", "知识", "讲解", "介绍", "定义"]

    # 检查实践关键词
    if any(kw in text_lower for kw in practice_keywords):
        return "practice"

    # 检查复习关键词
    if any(kw in text_lower for kw in review_keywords):
        return "review"

    # 检查理论关键词
    if any(kw in text_lower for kw in theory_keywords):
        return "theory"

    # 检查知识点类型
    if knowledge_points:
        if any(kp.type == "practice" for kp in knowledge_points):
            return "practice"

    # 默认返回理论课
    return "theory"

    # slide count
    target_count = None
    m = re.search(r"(\d{1,2})\s*(?:页|p|P|slides?|张)", t)
    if m: target_count = int(m.group(1))

    # duration - 更智能的默认值判断
    duration = 45  # 默认45分钟
    m = re.search(r"(\d{2,3})\s*(?:分钟|min)", t)
    if m:
        duration = int(m.group(1))
        # 如果用户指定了过长或过短的时间，进行合理调整
        if duration > 120:
            duration = 90  # 最长90分钟
        elif duration < 30:
            duration = 45  # 最短45分钟

    # Calculate minimum slides
    min_slides = calculate_min_slides(kps, "不要习题" not in t, professional_category)

    req = TeachingRequest()
    req.subject_info = SubjectInfo(subject_name=subject_name, subject_category=professional_category)
    req.knowledge_points = kps
    req.knowledge_structure = KnowledgeStructure(
        total_count=len(kps),
        relation_type="single" if len(kps) == 1 else "parallel" if len(kps) > 1 else "unknown"
    )
    req.teaching_scenario = TeachingScenarioDetail(scene_type=scene)
    req.slide_requirements = SlideRequirementsDetail(
        target_count=target_count,
        min_count=min_slides,
        max_count=min_slides + 2,
        lesson_duration_min=duration
    )
    req.special_requirements = SpecialRequirementsDetailed(
        cases=CaseRequirement(enabled="不要案例" not in t and "无案例" not in t, count=2 if "不要案例" not in t else 0),
        exercises=ExerciseRequirement(enabled="不要习题" not in t and "无习题" not in t, total_count=3 if "不要习题" not in t else 0),
        interaction=InteractionRequirement(enabled="不要互动" not in t and "无互动" not in t)
    )
    req.parsing_metadata = ParsingMetadata(
        raw_input=user_text,
        parsing_method="heuristic"
    )
    
    # Initialize distribution
    update_page_distribution(req)
    
    return req


# ============================================================================
# Validation & Questions (Enhanced for Multi-turn)
# ============================================================================

def validate_and_build_questions(req: TeachingRequest) -> Tuple[List[Question], List[str]]:
    """Return (questions, missing_keys)."""
    questions: List[Question] = []
    missing: List[str] = []
    
    stage = req.interaction_stage

    # ===== Stage: initial - Check required fields first =====
    if stage == "initial":
        if not req.subject_info.subject_name:
            missing.append("subject")
            questions.append(
                Question(
                    key="subject",
                    question="请问这是哪个专业/学科的课件？例如：机械/护理/计算机/土木…",
                    input_type="text",
                    required=True,
                )
            )
        
        if not req.knowledge_points:
            missing.append("knowledge_points")
            questions.append(
                Question(
                    key="knowledge_points",
                    question="核心知识点是什么？可输入1个或多个（用中文逗号分隔）。",
                    input_type="list",
                    required=True,
                )
            )
        
        if missing: return questions, missing
        
        kp_list = "、".join([kp.name for kp in req.knowledge_points])
        questions.append(
            Question(
                key="knowledge_points_confirm",
                question=f"已识别知识点：{kp_list}\n\n是否需要补充更多知识点？",
                input_type="select",
                options=["不需要补充", "需要补充"],
                required=True,
            )
        )
        return questions, ["confirm_kp"]

    # ===== Stage: confirm_kp - Handle additional inputs =====
    if stage == "confirm_kp":
        # 不再在这里检查页面冲突，页面冲突检查移到confirm_goals阶段
        # 直接进入配置修改询问阶段
        req.interaction_stage = "ask_config_modification"
        # 返回 ask_config_modification 阶段的问题
        questions.append(
            Question(
                key="need_config_modification",
                question="是否需要修改默认配置？\n\n系统默认配置：\n• 课时：45分钟\n• 应用案例：包含\n• 习题巩固：包含\n• 互动环节：包含",
                input_type="select",
                options=["需要修改", "不需要修改"],
                required=True
            )
        )
        return questions, ["ask_config_modification"]

    # ===== Stage: check_additional_kps - Check if user needs additional knowledge points =====
    if stage == "check_additional_kps":
        # 这个阶段不应该出现，如果出现了，直接返回空问题继续流程
        return questions, []

    # ===== Stage: add_additional_kps - Add additional knowledge points =====
    if stage == "add_additional_kps":
        questions.append(
            Question(
                key="additional_kps_input",
                question="请输入要补充的知识点：\n\n多个知识点请用逗号分隔。",
                input_type="text",
                placeholder="例如：液压泵结构, 控制阀原理, 密封技术",
                required=True
            )
        )
        return questions, ["add_additional_kps"]

    # ===== Stage: adjust_configurations - Adjust default configurations =====
    if stage == "adjust_configurations":
        questions.append(
            Question(
                key="lesson_duration_config",
                question="课时设置：\n\n请选择课时长度或选择自定义。",
                input_type="select",
                options=["30分钟", "45分钟", "60分钟", "90分钟", "120分钟", "自定义"],
                required=False
            )
        )

        questions.append(
            Question(
                key="custom_lesson_duration",
                question="自定义课时（分钟）：\n\n如果选择自定义，请输入具体的分钟数。",
                input_type="number",
                placeholder="例如：75",
                required=False
            )
        )

        questions.append(
            Question(
                key="cases_count_config",
                question="应用案例个数：\n\n请输入需要包含的应用案例数量。",
                input_type="number",
                placeholder="例如：2（0表示不包含）",
                required=False
            )
        )

        questions.append(
            Question(
                key="exercises_count_config",
                question="习题巩固道数：\n\n请输入需要包含的练习题数量。",
                input_type="number",
                placeholder="例如：5（0表示不包含）",
                required=False
            )
        )

        questions.append(
            Question(
                key="interaction_config",
                question="互动环节：\n\n是否需要在课件中包含互动环节？",
                input_type="select",
                options=["包含", "不包含"],
                required=False
            )
        )

        questions.append(
            Question(
                key="confirm_all_adjustments",
                question="确认所有调整：\n\n请确认以上配置调整无误，准备进行最终优化。",
                input_type="select",
                options=["确认，开始最终优化", "重新调整"],
                required=True
            )
        )

        return questions, ["adjust_configurations"]

    # ===== Stage: ask_config_modification - Ask if user wants to modify configurations =====
    if stage == "ask_config_modification":
        questions.append(
            Question(
                key="need_config_modification",
                question="是否需要修改默认配置？\n\n系统默认配置：\n• 课时：45分钟\n• 应用案例：包含\n• 习题巩固：包含\n• 互动环节：包含",
                input_type="select",
                options=["需要修改", "不需要修改"],
                required=True
            )
        )
        return questions, ["ask_config_modification"]

        # 检查教学场景
        scene_label = SCENE_DISPLAY_NAMES.get(req.teaching_scenario.scene_type, "未指定")
        if req.teaching_scenario.scene_type in ["theory", "practice", "review"]:
            assessment_questions.append(
                f"🎯 教学场景：{scene_label}（系统自动识别）"
            )

        # 检查知识点难度
        for kp in req.knowledge_points:
            diff_label = {"easy": "简单", "medium": "中等", "hard": "较难"}.get(kp.difficulty_level, "未知")
            assessment_questions.append(
                f"📚 {kp.name}：难度{'' if diff_label == '中等' else '评估为'}{diff_label}"
            )

        if assessment_questions:
            questions.append(
                Question(
                    key="assessments_confirm",
                    question=f"系统已进行智能评估：\n\n" + "\n".join(f"• {q}" for q in assessment_questions) + "\n\n这些评估是否准确？您可以修改或确认继续。",
                    input_type="select",
                    options=["确认评估，继续", "需要修改"],
                    required=True,
                )
            )
            return questions, ["confirm_assessments"]

        # 如果没有评估问题，直接进入默认配置确认
        questions.append(
            Question(
                key="default_config_confirm",
                question=f"默认配置确认：\n\n系统将按以下配置生成课件：\n• 课时：{req.slide_requirements.lesson_duration_min}分钟\n• 应用案例：{'包含' if req.special_requirements.cases.enabled else '不包含'}\n• 习题巩固：{'包含' if req.special_requirements.exercises.enabled else '不包含'}\n• 互动环节：{'包含' if req.special_requirements.interaction.enabled else '不包含'}\n\n这些配置是否合适？",
                input_type="select",
                options=["确认配置，继续", "需要调整配置"],
                required=True,
            )
        )
        return questions, ["confirm_defaults"]

    # ===== Stage: confirm_assessments - Allow modifications =====
    if stage == "confirm_assessments":
        questions.append(
            Question(
                key="modify_assessments",
                question="请选择需要修改的项目：",
                input_type="multi_select",
                options=[
                    "修改教学场景",
                    "修改知识点难度",
                    "都不需要修改"
                ],
                required=True,
            )
        )
        return questions, ["modify_assessments"]

    # ===== Stage: modify_assessments - Handle modifications =====
    if stage == "modify_assessments":
        # 这里会根据用户的选择生成具体的修改问题
        # 暂时跳转到目标输入阶段
        questions.append(
            Question(
                key="teaching_goals_input",
                question=f"教学目标（可选）：\n\n系统将自动生成默认目标，您也可以自定义输入：",
                input_type="text",
                placeholder="留空使用系统默认目标",
                required=False,
            )
        )
        return questions, ["confirm_goals"]

    # ===== Stage: confirm_kp - Check page count ===== (旧的逻辑，保持兼容)
    if stage == "confirm_kp":
        if check_slide_count_conflict(req):
            questions.append(
                Question(
                    key="slide_count_adjust",
                    question=f"您期望 {req.slide_requirements.target_count} 页，但根据知识点数量，系统建议至少 {req.slide_requirements.min_count} 页。\n\n请选择：",
                    input_type="select",
                    options=[f"调整为 {req.slide_requirements.min_count} 页", f"保持 {req.slide_requirements.target_count} 页"],
                    required=True,
                )
            )
            return questions, ["confirm_pages"]
        
        questions.append(
            Question(
                key="teaching_goals_input",
                question=f"教学目标（可选）：\n\n系统将自动生成默认目标，您也可以自定义输入：",
                input_type="text",
                placeholder="留空使用系统默认目标",
                required=False,
            )
        )
        return questions, ["confirm_goals"]

    # ===== Stage: confirm_pages - Handle page count selection =====
    if stage == "confirm_pages":
        # 检查是否需要显示自定义页数输入框
        needs_custom_input = req.interaction_metadata.get("needs_custom_slide_count", False)
        
        if needs_custom_input:
            # 用户选择了自定义页数，需要输入
            questions.append(
                Question(
                    key="custom_slide_count",
                    question=f"请输入目标页数：\n\n当前最小建议页数：{req.slide_requirements.min_count} 页\n\n如果输入的页数仍小于建议值，系统会在后续进行智能调整。",
                    input_type="number",
                    placeholder=f"例如：{req.slide_requirements.min_count}",
                    required=True,
                )
            )
            return questions, ["confirm_pages"]
        
        # 页面数量确认完成，继续到最终确认
        # 不再询问教学目标（已在之前阶段处理），直接进入最终确认
        summary = generate_display_summary(req)
        questions.append(
            Question(
                key="final_confirm",
                question=f"{summary}\n\n✅ 请确认以上信息无误后将进入下一步：",
                input_type="select",
                options=["确认，开始生成", "返回修改"],
                required=True,
            )
        )
        return questions, ["final_confirm"]

    # ===== Stage: confirm_defaults - Confirm or adjust default configurations =====
    if stage == "confirm_defaults":
        questions.append(
            Question(
                key="adjust_defaults",
                question="请选择需要调整的配置项目：",
                input_type="multi_select",
                options=[
                    "调整课时设置",
                    "调整案例需求",
                    "调整习题需求",
                    "调整互动需求",
                    "都不需要调整"
                ],
                required=True,
            )
        )
        return questions, ["adjust_defaults"]

    # ===== Stage: adjust_defaults - Handle configuration adjustments =====
    if stage == "adjust_defaults":
        questions.append(
            Question(
                key="teaching_goals_input",
                question=f"教学目标（可选）：\n\n系统将自动生成默认目标，您也可以自定义输入：",
                input_type="text",
                placeholder="留空使用系统默认目标",
                required=False,
            )
        )
        return questions, ["confirm_goals"]

    # ===== Stage: confirm_goals - Check page conflict before final confirmation =====
    if stage == "confirm_goals":
        # 在显示最终确认之前，先检查页面冲突
        if check_slide_count_conflict(req):
            # 检查是否有LLM推荐结果
            recommended_count = req.slide_requirements.llm_recommended_count
            # 从interaction_metadata或临时属性中获取解释
            explanation = req.interaction_metadata.get("_llm_recommendation_explanation") or getattr(req, '_llm_recommendation_explanation', None)
            
            if recommended_count and explanation:
                # 使用LLM推荐结果
                question_text = f"""⚠️ 页面数量冲突检测

您期望的页数：{req.slide_requirements.target_count} 页
系统建议的最小页数：{req.slide_requirements.min_count} 页
AI推荐页数：{recommended_count} 页

📊 推荐理由：
{explanation}

请选择处理方式："""
                
                options = [
                    f"✅ 接受推荐（调整为 {recommended_count} 页）",
                    "✏️ 自定义页数",
                    f"⚠️ 保持原页数（{req.slide_requirements.target_count} 页，后续会智能调整）"
                ]
            else:
                # 没有LLM推荐，使用简单提示
                question_text = f"您期望 {req.slide_requirements.target_count} 页，但根据知识点数量，系统建议至少 {req.slide_requirements.min_count} 页。\n\n请选择："
                options = [
                    f"调整为 {req.slide_requirements.min_count} 页",
                    f"保持 {req.slide_requirements.target_count} 页"
                ]
            
            questions.append(
                Question(
                    key="slide_count_adjust",
                    question=question_text,
                    input_type="select",
                    options=options,
                    required=True,
                    recommended_count=recommended_count,
                    explanation=explanation,
                )
            )
            # 注意：这里不直接修改interaction_stage，让apply_user_answers根据用户选择来处理
            # 但返回confirm_pages作为提示，表示下一步可能是confirm_pages
            return questions, ["confirm_pages"]
        
        # 没有页面冲突，直接显示最终确认
        summary = generate_display_summary(req)
        questions.append(
            Question(
                key="final_confirm",
                question=f"{summary}\n\n✅ 请确认以上信息无误后将进入下一步：",
                input_type="select",
                options=["确认，开始生成", "返回修改"],
                required=True,
            )
        )
        return questions, ["final_confirm"]

    # ===== Stage: supplementing_kp - Prompt for new KPs =====
    if stage == "supplementing_kp":
        questions.append(
            Question(
                key="additional_kps",
                question="请输入要补充的知识点，多个请用逗号分隔：",
                input_type="text",
                placeholder="例如：液压泵结构, 溢流阀原理",
                required=True,
            )
        )
        return questions, ["initial"]

    # ===== Stage: final_confirm - Show final confirmation =====
    if stage == "final_confirm":
        summary = generate_display_summary(req)
        questions.append(
            Question(
                key="final_confirm",
                question=f"{summary}\n\n✅ 请确认以上信息无误后将开始生成课件：",
                input_type="select",
                options=["确认，开始生成", "返回修改"],
                required=True,
            )
        )
        return questions, ["final_confirm"]
    
    if stage == "confirmed":
        return [], []

    return questions, missing

    # Default: no questions
    return questions, missing


def apply_user_answers(req: TeachingRequest, answers: Dict[str, Any]) -> TeachingRequest:
    """Merge user answers into TeachingRequest."""
    current_stage = req.interaction_stage
    
    # ===== Stage: initial → confirm_kp =====
    if current_stage == "initial":
        if "subject" in answers and answers["subject"]:
            req.subject_info.subject_name = str(answers["subject"]).strip()
            req.subject_info.subject_category = detect_professional_category(
                req.parsing_metadata.raw_input or "", req.subject_info.subject_name
            )
        
        if "knowledge_points" in answers and answers["knowledge_points"]:
            names = []
            if isinstance(answers["knowledge_points"], list):
                names = [str(x).strip() for x in answers["knowledge_points"] if str(x).strip()]
            else:
                names = [x.strip() for x in str(answers["knowledge_points"]).replace("，", ",").split(",") if x.strip()]
            
            req.knowledge_points = [
                KnowledgePointDetail(id=f"KP_{i+1:03d}", name=n) for i, n in enumerate(names)
            ]
            req.slide_requirements.min_count = calculate_min_slides(
                req.knowledge_points, req.special_requirements.exercises.enabled, req.subject_info.subject_category
            )
            req.slide_requirements.max_count = req.slide_requirements.min_count + 2
        
        if "knowledge_points_confirm" in answers:
            val = str(answers["knowledge_points_confirm"]).strip()
            # 根据用户选择决定下一步
            if val == "需要补充":
                req.interaction_stage = "add_additional_kps"
            else:
                # 不需要补充，检查页面数量冲突，然后进入配置修改阶段
                req.interaction_stage = "confirm_kp"

    # ===== Stage: confirm_kp → ask_config_modification =====
    elif current_stage == "confirm_kp":
        # 不再在这里处理页面冲突，页面冲突在confirm_goals阶段处理
        # 直接进入配置修改询问阶段
        req.interaction_stage = "ask_config_modification"

    # ===== Stage: confirm_assessments → modify_assessments =====
    elif current_stage == "confirm_assessments":
        if "modify_assessments" in answers:
            val = str(answers["modify_assessments"]).strip()
            if "都不需要" in val:
                req.interaction_stage = "supplement_and_config"
            else:
                req.interaction_stage = "modify_assessments"



    # ===== Stage: modify_assessments → confirm_defaults =====
    elif current_stage == "modify_assessments":
        # 暂时直接跳转到默认配置确认
        req.interaction_stage = "supplement_and_config"

    # ===== Stage: confirm_defaults → adjust_defaults or confirm_goals =====
    elif current_stage == "confirm_defaults":
        if "default_config_confirm" in answers:
            val = str(answers["default_config_confirm"]).strip()
            if "确认" in val:
                req.interaction_stage = "confirm_goals"
            else:
                req.interaction_stage = "adjust_defaults"

    # ===== Stage: adjust_defaults → confirm_goals =====
    elif current_stage == "adjust_defaults":
        if "adjust_defaults" in answers:
            val = str(answers["adjust_defaults"]).strip()
            if "都不需要" in val:
                req.interaction_stage = "confirm_goals"
            else:
                # 这里可以根据用户的选择生成具体的配置调整问题
                # 暂时直接跳转到目标输入
                req.interaction_stage = "confirm_goals"
        
        update_page_distribution(req)
    
    # ===== Stage: supplementing_kp → initial =====
    elif current_stage == "supplementing_kp":
        if "additional_kps" in answers:
            val = str(answers["additional_kps"]).strip()
            if val:
                new_names = [x.strip() for x in val.replace("，", ",").split(",") if x.strip()]
                existing_names = [kp.name for kp in req.knowledge_points]
                for name in new_names:
                    if name not in existing_names:
                        req.knowledge_points.append(KnowledgePointDetail(
                            id=f"KP_{len(req.knowledge_points)+1:03d}", name=name
                        ))
                req.slide_requirements.min_count = calculate_min_slides(
                    req.knowledge_points, req.special_requirements.exercises.enabled, req.subject_info.subject_category
                )
                req.slide_requirements.max_count = req.slide_requirements.min_count + 2
        req.interaction_stage = "initial"
        update_page_distribution(req)
    

    # ===== Stage: add_additional_kps → ask_config_modification =====
    elif current_stage == "add_additional_kps":
        if "additional_kps_input" in answers:
            val = str(answers["additional_kps_input"]).strip()
            if val:
                new_names = [x.strip() for x in val.replace("，", ",").split(",") if x.strip()]
                existing_names = [kp.name for kp in req.knowledge_points]
                for name in new_names:
                    if name not in existing_names:
                        req.knowledge_points.append(KnowledgePointDetail(
                            id=f"KP_{len(req.knowledge_points)+1:03d}", name=name
                        ))
                req.slide_requirements.min_count = calculate_min_slides(
                    req.knowledge_points, req.special_requirements.exercises.enabled, req.subject_info.subject_category
                )
                req.slide_requirements.max_count = req.slide_requirements.min_count + 2
                # 标记有知识点补充
                req.interaction_metadata["has_additional_kps"] = True
            req.interaction_stage = "ask_config_modification"

    # ===== Stage: ask_config_modification → adjust_configurations or confirm_goals =====
    elif current_stage == "ask_config_modification":
        if "need_config_modification" in answers:
            if answers["need_config_modification"] == "需要修改":
                req.interaction_stage = "adjust_configurations"
            else:
                # 不需要修改配置，进入confirm_goals阶段（这里会检查页面冲突）
                req.interaction_stage = "confirm_goals"

    # ===== Stage: adjust_configurations → confirm_goals =====
    elif current_stage == "adjust_configurations":
        # 处理配置调整
        if "lesson_duration_config" in answers:
            duration_choice = answers["lesson_duration_config"]
            if duration_choice == "自定义" and "custom_lesson_duration" in answers:
                try:
                    custom_duration = int(answers["custom_lesson_duration"])
                    req.slide_requirements.lesson_duration_min = max(30, min(180, custom_duration))  # 限制在30-180分钟
                except (ValueError, TypeError):
                    pass  # 使用默认值
            elif duration_choice in ["30分钟", "45分钟", "60分钟", "90分钟", "120分钟"]:
                duration_map = {
                    "30分钟": 30, "45分钟": 45, "60分钟": 60, "90分钟": 90, "120分钟": 120
                }
                req.slide_requirements.lesson_duration_min = duration_map[duration_choice]

        if "cases_count_config" in answers:
            try:
                cases_count = int(answers["cases_count_config"])
                req.special_requirements.cases = CaseRequirement(
                    enabled=cases_count > 0,
                    count=max(0, min(5, cases_count))  # 限制在0-5个
                )
            except (ValueError, TypeError):
                pass

        if "exercises_count_config" in answers:
            try:
                exercises_count = int(answers["exercises_count_config"])
                req.special_requirements.exercises = ExerciseRequirement(
                    enabled=exercises_count > 0,
                    total_count=max(0, min(10, exercises_count))  # 限制在0-10道
                )
            except (ValueError, TypeError):
                pass

        if "interaction_config" in answers:
            enabled = answers["interaction_config"] == "包含"
            req.special_requirements.interaction = InteractionRequirement(
                enabled=enabled,
                types=["提问互动", "案例分析", "小组讨论"] if enabled else []
            )

        # 标记有配置修改
        req.interaction_metadata["has_config_modification"] = True

        # 处理确认或重新调整
        if "confirm_all_adjustments" in answers:
            if answers["confirm_all_adjustments"] == "确认，开始最终优化":
                # 确认所有调整，进入confirm_goals阶段（这里会检查页面冲突）
                req.interaction_stage = "confirm_goals"
            else:
                # 重新调整，保持在 adjust_configurations 阶段，让用户重新填写配置
                req.interaction_stage = "adjust_configurations"
        else:
            # 如果没有确认选项，保持在当前阶段
            req.interaction_stage = "adjust_configurations"
    
    # ===== Stage: confirm_pages → confirm_goals =====
    elif current_stage == "confirm_pages":
        # 处理页面数量调整（从confirm_goals阶段跳转过来的）
        if "slide_count_adjust" in answers:
            val = str(answers["slide_count_adjust"]).strip()
            if "接受推荐" in val or "✅" in val:
                # 接受推荐页数
                recommended = req.slide_requirements.llm_recommended_count
                if recommended:
                    req.slide_requirements.target_count = recommended
                    req.slide_requirements.page_conflict_resolution = "accept_recommended"
                else:
                    # 如果没有推荐值，使用最小页数
                    req.slide_requirements.target_count = req.slide_requirements.min_count
                    req.slide_requirements.page_conflict_resolution = "accept_recommended"
            elif "自定义" in val or "✏️" in val:
                # 选择自定义页数，需要用户输入
                req.interaction_metadata["needs_custom_slide_count"] = True
                req.slide_requirements.page_conflict_resolution = "custom"
                # 保持在confirm_pages阶段，等待用户输入自定义页数
                return req
            elif "保持原页数" in val or "⚠️" in val:
                # 保持原页数
                req.slide_requirements.page_conflict_resolution = "keep_original"
            else:
                # 默认处理：调整为最小页数
                req.slide_requirements.target_count = req.slide_requirements.min_count
        
        # 处理自定义页数输入
        if "custom_slide_count" in answers:
            try:
                custom_count = int(answers["custom_slide_count"])
                min_count = req.slide_requirements.min_count or 0
                # 确保自定义页数不小于最小页数（但允许用户选择，后续会智能调整）
                if custom_count < min_count:
                    # 仍然接受，但记录需要后续调整
                    req.interaction_metadata["needs_smart_adjustment"] = True
                req.slide_requirements.target_count = custom_count
                req.slide_requirements.page_conflict_resolution = "custom"
            except (ValueError, TypeError):
                # 输入无效，使用最小页数
                req.slide_requirements.target_count = req.slide_requirements.min_count
        
        # 清除自定义输入标记
        req.interaction_metadata.pop("needs_custom_slide_count", None)
        
        # 更新页面分布
        update_page_distribution(req)
        
        # 页面冲突处理完成，直接进入最终确认
        req.interaction_stage = "final_confirm"
    
    # ===== Stage: confirm_goals → confirm_pages or final_confirm =====
    elif current_stage == "confirm_goals":
        # 如果用户选择了页面冲突处理，跳转到confirm_pages
        if "slide_count_adjust" in answers:
            val = str(answers["slide_count_adjust"]).strip()
            if "自定义" in val or "✏️" in val:
                # 选择自定义页数，需要用户输入
                req.interaction_metadata["needs_custom_slide_count"] = True
                req.slide_requirements.page_conflict_resolution = "custom"
                req.interaction_stage = "confirm_pages"
            else:
                # 接受推荐或保持原页数，直接处理
                if "接受推荐" in val or "✅" in val:
                    recommended = req.slide_requirements.llm_recommended_count
                    if recommended:
                        req.slide_requirements.target_count = recommended
                        req.slide_requirements.page_conflict_resolution = "accept_recommended"
                    else:
                        req.slide_requirements.target_count = req.slide_requirements.min_count
                        req.slide_requirements.page_conflict_resolution = "accept_recommended"
                elif "保持原页数" in val or "⚠️" in val:
                    req.slide_requirements.page_conflict_resolution = "keep_original"
                else:
                    # 默认：调整为最小页数
                    req.slide_requirements.target_count = req.slide_requirements.min_count
                
                # 更新页面分布
                update_page_distribution(req)
                # 继续到最终确认
                req.interaction_stage = "final_confirm"
        
        # 处理最终确认
        elif "final_confirm" in answers:
            val = str(answers["final_confirm"]).strip()
            if "确认" in val or "开始" in val:
                req.interaction_stage = "final_confirm"
            else:
                req.interaction_stage = "initial"
    
    # ===== Stage: final_confirm → confirmed =====
    elif current_stage == "final_confirm":
        if "final_confirm" in answers:
            val = str(answers["final_confirm"]).strip()
            if "确认" in val or "开始" in val:
                req.interaction_stage = "confirmed"
                # Note: confirmation_status removed in JSON Schema refactoring
            else:
                # 返回修改，回到 adjust_configurations 阶段
                req.interaction_stage = "adjust_configurations"
    
    return req


def autofill_defaults(req: TeachingRequest) -> TeachingRequest:
    """Fill missing teaching goals and requirements."""
    # Goals
    if req.teaching_objectives.auto_generated and not (req.teaching_objectives.knowledge or req.teaching_objectives.ability):
        defaults = default_goals(req.teaching_scenario.scene_type, req.subject_info.subject_name)
        req.teaching_objectives.knowledge = [defaults['knowledge']]
        req.teaching_objectives.ability = [defaults['ability']]
        req.teaching_objectives.literacy = [defaults['literacy']]
        req.teaching_objectives.auto_generated = True

    # Slide count
    if req.slide_requirements.target_count is None:
        req.slide_requirements.target_count = calculate_min_slides(
            req.knowledge_points, 
            req.special_requirements.exercises.enabled, 
            req.subject_info.subject_category
        )
    
    if req.slide_requirements.min_count is None:
        req.slide_requirements.min_count = calculate_min_slides(
            req.knowledge_points, 
            req.special_requirements.exercises.enabled, 
            req.subject_info.subject_category
        )
        req.slide_requirements.max_count = req.slide_requirements.min_count + 2

    # Special requirements defaults
    if req.special_requirements.cases.enabled and req.special_requirements.cases.count == 0:
        req.special_requirements.cases.count = 2
    if req.special_requirements.exercises.enabled and req.special_requirements.exercises.total_count == 0:
        req.special_requirements.exercises.total_count = 3
    
    # Estimated distribution
    update_page_distribution(req)

    return req
