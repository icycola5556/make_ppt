"""
3.3 PPT大纲生成 - LLM智能规划

使用LLM进行智能规划生成PPT大纲
"""
from __future__ import annotations

import json
from typing import Any, Optional

from ...common.schemas import PPTOutline, TeachingRequest
from .core import generate_outline
from .adjustment import adjust_outline_to_target_count


# LLM智能规划系统提示词
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
        outline = adjust_outline_to_target_count(outline, req.slide_requirements.target_count)
        
        return outline
        
    except Exception as e:
        # LLM调用失败，降级到确定性生成
        logger.emit(session_id, "3.3", "llm_planning_error", {
            "error": str(e),
            "fallback_to_deterministic": True,
        })
        return generate_outline(req, style_name)
