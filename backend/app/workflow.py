from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from .intent import apply_user_answers, autofill_defaults, heuristic_parse, validate_and_build_questions, detect_professional_category, calculate_min_slides, generate_display_summary, update_page_distribution
from .llm import LLMClient
from .logger import WorkflowLogger
from .outline import generate_outline
from .schemas import PPTOutline, SessionState, SlideDeckContent, StyleConfig, StyleSampleSlide, TeachingRequest
from .style import build_style_samples, choose_style
from .content import build_base_deck, refine_with_llm, validate_deck
from .tools import ToolExecutor


# Enhanced system prompt with Few-Shot examples and tool usage guidance
INTENT_SYSTEM_PROMPT = """你是高职教学课件意图理解助手。请从教师的自然语言需求中精准抽取结构化信息。

## 核心任务
从教师的自然语言输入中提取结构化教学需求，确保准确理解教学意图和专业背景。

## 分析原则
1. **内容驱动的理解**：让教学内容本身指导需求分析，而不是套用固定模板
2. **专业领域验证**：遇到不熟悉的知识点必须通过工具搜索验证
3. **合理预估**：基于搜索结果和教学经验进行合理参数预估
4. **用户体验优先**：提供清晰的确认机制，避免误解用户需求

## 工具使用策略
- **主动搜索场景**：
  - 遇到任何不确定的专业术语或知识点名称
  - 需要了解知识点的教学标准或行业应用
  - 查找相关的教学案例或实践指导
  - 验证专业分类是否符合高职教学规范

- **智能搜索技巧**：
  - 组合关键词：知识点名称 + "高职" + "教学" + "职业教育"
  - 优先中文搜索，确保符合本土教学场景
  - 关注最新标准和行业发展趋势

## 处理流程示例
输入："机械专业液压传动原理的理论课，10页PPT"

1. 识别专业领域：机械工程类
2. 搜索验证："液压传动原理 高职教学 机械专业"
3. 提取结构化信息：理论课件、10页要求、机械专业背景
4. 补充默认配置：案例展示、练习题等

## 设计哲学
- **精准提取**：宁可少提取也要确保准确，避免过度推测
- **保守扩展**：在没有外部信息时，不要过度拆分知识点
- **用户优先**：严格按照用户输入的知识点数量，不要擅自增加
- **智能评估**：基于专业知识对知识点难度和教学场景进行合理评估
- **渐进完善**：通过多轮对话完善需求，而不是一次性穷举
- **专业适配**：根据不同专业特点调整默认参数和建议
- **教学导向**：始终以提升教学效果为最终目标

## 输出要求
- 严格JSON格式，无额外解释文字
- 确保数据完整性和逻辑一致性
- 提供充分的上下文信息便于后续优化"""

INTENT_SCHEMA_HINT = """{
  "subject_info": {
    "subject_name": "string",
    "subject_category": "engineering|medical|agriculture|arts|business|science|civil|transportation|tourism|food|textile|resources|water|media|public-security|public-service|sports|unknown",
    "sub_field": "string or null"
  },
  "knowledge_points": [
    {
      "id": "string",
      "name": "string",
      "type": "theory|practice|mixed",
      "difficulty_level": "easy|medium|hard"
    }
  ],
  "teaching_scenario": {
    "scene_type": "theory|practice|review|unknown",
    "scene_label": "string"
  },
  "teaching_objectives": {
    "knowledge": ["string"],
    "ability": ["string"],
    "literacy": ["string"]
  },
  "slide_requirements": {
    "target_count": number,
    "lesson_duration_min": number
  },
  "special_requirements": {
    "cases": {"enabled": boolean, "count": number},
    "exercises": {"enabled": boolean, "total_count": number},
    "interaction": {"enabled": boolean, "types": ["string"]}
  }
}"""

STYLE_SYSTEM_PROMPT = """你是PPT风格设计助手。你将基于教学场景输出风格配置JSON。
只输出JSON对象，不要解释。"""

STYLE_SCHEMA_HINT = """{
  "style_name": "string",
  "color": {"primary": "#RRGGBB", "secondary": "#RRGGBB", "accent": "#RRGGBB", "text": "#RRGGBB", "background": "#RRGGBB", "warning": "#RRGGBB"},
  "font": {"title_family": "string", "body_family": "string", "title_size": 34, "body_size": 22, "line_height": 1.2},
  "layout": {"density": "compact|comfortable", "notes_area": true, "alignment": "left|center"},
  "imagery": {"image_style": "string", "icon_style": "string", "chart_preference": ["string"]}
}"""

OUTLINE_SYSTEM_PROMPT = """你是高职课程PPT大纲优化助手，专注于创建高质量的教学演示文稿结构。

## 设计哲学
- **内容驱动的选择**：让每页的内容目的决定标题和要点设计，而不是套用固定格式
- **教学逻辑递进**：确保页面间的逻辑流畅，符合学生的认知规律
- **实用性优先**：避免华而不实的表达，追求清晰实用的教学内容
- **受众适配**：针对高职学生的特点优化语言和内容深度

## 优化原则
1. **标题优化**：
   - 使用具体、明确的标题，避免抽象的概念
   - 体现教学重点和学生关心的内容
   - 符合高职教学的实用导向

2. **要点提炼**：
   - 每页3-5个要点，控制信息密度
   - 使用学生熟悉的语言和表达方式
   - 突出关键概念和操作步骤
   - 体现教学的递进关系

3. **结构保持**：
   - 维持原始slide数量和类型
   - 基于slide_type优化内容表达
   - 确保逻辑连贯性和教学完整性

## 教学内容特点
- **实践导向**：强调实用技能和操作能力
- **案例结合**：融入实际工作场景和案例
- **层次清晰**：从基础概念到应用实践的递进
- **互动性强**：便于教师讲解和学生理解

只输出JSON对象，不要解释。"""


class WorkflowEngine:
    def __init__(self, store, logger: WorkflowLogger, llm: LLMClient):
        self.store = store
        self.logger = logger
        self.llm = llm
        self.tool_executor = ToolExecutor()

    async def _parse_intent(self, session_id: str, user_text: str, use_tools: bool = True,
                           tone: Optional[str] = None, verbosity: Optional[str] = None,
                           instructions: Optional[str] = None, streaming: bool = False) -> TeachingRequest:
        """解析用户意图，支持工具调用（如联网搜索）
        
        Args:
            session_id: 会话ID
            user_text: 用户输入文本
            use_tools: 是否启用工具调用（默认True）
        """
        # Try LLM first
        if self.llm.is_enabled():
            try:
                # 如果启用工具调用，使用chat_with_tools方法
                if use_tools:
                    tools = self.tool_executor.get_tool_definitions()

                    # 构建用户提示，支持额外参数
                    user_prompt_parts = [f"## 用户输入\n{user_text}"]

                    # 添加指令参数
                    if instructions:
                        user_prompt_parts.append(f"## 特殊指令\n{instructions}")

                    # 添加语气参数
                    if tone:
                        user_prompt_parts.append(f"## 分析风格\n{tone}")

                    # 添加详细程度参数
                    if verbosity:
                        user_prompt_parts.append(f"## 详细程度\n{verbosity}")

                    user_prompt_parts.append("""
## 分析任务
请基于用户输入提取完整的教学需求信息，并对未明确的部分进行智能评估：

1. **核心要素识别**：
   - 教学科目和专业领域
   - 主要知识点和教学内容（严格按照用户输入的数量）
   - 教学场景类型（理论/实践/复习）- 如果未明确，通过内容分析自动判断
   - 课件页数和时间要求

2. **智能评估**：
   - **知识点难度评估**：基于知识点名称复杂度、专业领域特点进行评估
     * easy：基础概念、简单定义
     * medium：原理讲解、基本应用（默认）
     * hard：复杂计算、高级应用
   - **教学场景自动识别**：通过关键词和上下文判断
     * "理论"、"原理"、"概念" → theory
     * "实训"、"操作"、"动手"、"步骤" → practice
     * "复习"、"回顾"、"总结" → review

3. **专业验证**：
   - 对不熟悉的知识点使用web_search工具进行验证
   - 确认专业分类和教学标准
   - 了解相关教学案例和应用场景

4. **合理补充**：
   - 根据专业特点预估合适的教学目标
   - 提供合理的案例和练习题建议
   - 考虑教学页面的逻辑分布

5. **默认配置提示**：
   - 识别用户未明确指定的配置项
   - 准备默认配置说明，用于前端展示
   - 突出可调整的配置项，让用户了解可以修改的内容

## 输出格式
请返回符合以下JSON schema的结构化数据：
""")
                    user_prompt_parts.append(INTENT_SCHEMA_HINT)
                    user_prompt_parts.append("""
## 注意事项
- 优先使用工具验证专业信息
- 如果工具调用失败，请基于用户输入进行保守的结构化提取
- 不要擅自拆分或扩展用户未提及的知识点
- 保持数据准确性和教学实用性
- 默认课时为45分钟，除非用户明确指定
- 为后续模块提供充分的结构化信息""")

                    user_prompt = "\n".join(user_prompt_parts)
                    
                    self.logger.emit(session_id, "3.1", "llm_prompt", {
                        "system": INTENT_SYSTEM_PROMPT, 
                        "user": user_prompt, 
                        "schema_hint": INTENT_SCHEMA_HINT,
                        "tools_enabled": True,
                        "tools": tools,
                        "parameters": {
                            "tone": tone,
                            "verbosity": verbosity,
                            "instructions": instructions
                        }
                    })
                    
                    try:
                        response, meta, tool_calls = await self.llm.chat_with_tools(
                            system=INTENT_SYSTEM_PROMPT,
                            user=user_prompt,
                            tools=tools,
                            tool_executor=self.tool_executor,
                            max_iterations=5,
                            thinking=None,  # 工具调用时不使用thinking参数，避免API兼容性问题
                        )
                    except Exception as tool_error:
                        # 工具调用失败，记录错误并尝试不使用工具的降级方案
                        self.logger.emit(session_id, "3.1", "tool_call_failed", {
                            "error": str(tool_error),
                            "fallback": "disabling_tools"
                        })
                        # 降级到不使用工具的方案
                        parsed, meta = await self.llm.chat_json(INTENT_SYSTEM_PROMPT, user_text, INTENT_SCHEMA_HINT)
                        tool_calls = []
                        self.logger.emit(session_id, "3.1", "llm_response", meta)
                        req = TeachingRequest.model_validate({"**parsed": parsed})
                        req.parsing_metadata.raw_input = user_text
                        req.parsing_metadata.parsing_method = "llm_extraction_fallback"
                        update_page_distribution(req)
                        return req

                    # 记录工具调用历史
                    if tool_calls:
                        self.logger.emit(session_id, "3.1", "tool_calls", {
                            "tool_calls": tool_calls,
                            "successful_calls": len([tc for tc in tool_calls if tc.get("success", False)]),
                            "failed_calls": len([tc for tc in tool_calls if not tc.get("success", True)])
                        })
                    
                    # 解析最终响应（应该是JSON格式）
                    # 增强的JSON解析策略
                    parsed = None
                    try:
                        if isinstance(response, dict):
                            # 如果已经是字典，直接使用
                            parsed = response
                        elif isinstance(response, str):
                            # 如果是字符串，尝试解析JSON
                            try:
                                parsed = json.loads(response.strip())
                            except json.JSONDecodeError:
                                # 尝试提取JSON部分 - 多策略匹配
                                json_patterns = [
                                    r'```json\s*\n(.*?)\n\s*```',  # ```json ... ``` 代码块
                                    r'```\s*\n(\{.*?\})\s*\n```',  # ``` ... ``` 通用代码块
                                    r'(\{[^{}]*\{[^{}]*\}[^{}]*\})',  # 包含嵌套对象的JSON
                                    r'(\{[^{}]*\})',  # 简单JSON对象
                                    r'\{.*\}',  # 最后的回退匹配
                                ]

                                for pattern in json_patterns:
                                    json_match = re.search(pattern, response, re.DOTALL)
                                    if json_match:
                                        json_text = json_match.group(1) if json_match.groups() else json_match.group()
                                        try:
                                            parsed = json.loads(json_text.strip())
                                            break
                                        except json.JSONDecodeError:
                                            continue

                                if parsed is None:
                                    # 如果仍然无法解析，记录详细错误信息
                                    self.logger.emit(session_id, "3.1", "json_parse_error", {
                                        "response_preview": response[:500],
                                        "response_length": len(response),
                                        "tool_calls_count": len(tool_calls),
                                        "attempted_patterns": len(json_patterns)
                                    })
                                    raise ValueError(f"无法从响应中提取有效的JSON。响应预览: {response[:200]}")
                        else:
                            raise ValueError(f"意外的响应类型: {type(response)} - 期望dict或str，得到{type(response)}")
                    except Exception as parse_error:
                        # 解析失败时的详细错误记录
                        self.logger.emit(session_id, "3.1", "response_parse_failed", {
                            "error": str(parse_error),
                            "response_type": type(response).__name__,
                            "response_preview": str(response)[:300] if response else None,
                            "tool_calls_count": len(tool_calls)
                        })
                        raise parse_error

                    # 后处理修正常见错误
                    try:
                        parsed = self._post_process_llm_response(parsed, user_text, tool_calls)
                        self.logger.emit(session_id, "3.1", "post_process_success", {
                            "corrections_applied": True
                        })
                    except Exception as post_process_error:
                        self.logger.emit(session_id, "3.1", "post_process_error", {
                            "error": str(post_process_error)
                        })
                    
                    self.logger.emit(session_id, "3.1", "llm_response", {
                        **meta,
                        "tool_calls_count": len(tool_calls),
                    })
                    
                    req = TeachingRequest.model_validate({
                        **parsed,
                    })
                    req.parsing_metadata.raw_input = user_text
                    req.parsing_metadata.parsing_method = "llm_extraction_with_tools"
                    update_page_distribution(req)
                    return req
                else:
                    # 不使用工具调用，使用原来的chat_json方法
                    self.logger.emit(session_id, "3.1", "llm_prompt", {
                        "system": INTENT_SYSTEM_PROMPT, 
                        "user": user_text, 
                        "schema_hint": INTENT_SCHEMA_HINT,
                        "tools_enabled": False,
                        "parameters": {
                            "tone": tone,
                            "verbosity": verbosity,
                            "instructions": instructions
                        }
                    })
                    parsed, meta = await self.llm.chat_json(INTENT_SYSTEM_PROMPT, user_text, INTENT_SCHEMA_HINT)
                    self.logger.emit(session_id, "3.1", "llm_response", meta)
                    req = TeachingRequest.model_validate({
                        **parsed,
                    })
                    req.parsing_metadata.raw_input = user_text
                    req.parsing_metadata.parsing_method = "llm_extraction"
                    update_page_distribution(req)
                    return req
            except Exception as e:
                self._handle_workflow_error(session_id, "3.1", e, {"parsing_method": "llm_extraction"})

        # Fallback heuristic
        req = heuristic_parse(user_text)
        update_page_distribution(req)
        self.logger.emit(session_id, "3.1", "heuristic_parse", req.model_dump(mode="json"))
        return req

    async def _design_style(self, session_id: str, req: TeachingRequest) -> Tuple[StyleConfig, List[StyleSampleSlide]]:
        # Start from deterministic templates
        cfg = choose_style(req)
        samples = build_style_samples(req, cfg)
        self.logger.emit(session_id, "3.2", "style_base", {"style_config": cfg.model_dump(mode="json"), "style_samples": [s.model_dump(mode="json") for s in samples]})

        # Optionally refine with LLM
        if self.llm.is_enabled():
            try:
                user_msg = json.dumps({"teaching_request": req.model_dump(mode="json"), "style_config": cfg.model_dump(mode="json")}, ensure_ascii=False)
                self.logger.emit(session_id, "3.2", "llm_prompt", {"system": STYLE_SYSTEM_PROMPT, "user": user_msg, "schema_hint": STYLE_SCHEMA_HINT})
                parsed, meta = await self.llm.chat_json(STYLE_SYSTEM_PROMPT, user_msg, STYLE_SCHEMA_HINT)
                self.logger.emit(session_id, "3.2", "llm_response", meta)
                cfg2 = StyleConfig.model_validate(parsed)
                return cfg2, samples
            except Exception as e:
                self._handle_workflow_error(session_id, "3.2", e, {"style_config": cfg.model_dump(mode="json")})

        return cfg, samples

    async def _generate_outline(self, session_id: str, req: TeachingRequest, style: StyleConfig) -> PPTOutline:
        outline = generate_outline(req, style_name=style.style_name)
        self.logger.emit(session_id, "3.3", "outline_base", outline.model_dump(mode="json"))

        if self.llm.is_enabled():
            try:
                schema_hint = outline.model_json_schema()
                user_msg = json.dumps(outline.model_dump(mode="json"), ensure_ascii=False)
                self.logger.emit(session_id, "3.3", "llm_prompt", {"system": OUTLINE_SYSTEM_PROMPT, "user": user_msg, "schema_hint": schema_hint})
                parsed, meta = await self.llm.chat_json(OUTLINE_SYSTEM_PROMPT, user_msg, json.dumps(schema_hint, ensure_ascii=False))
                self.logger.emit(session_id, "3.3", "llm_response", meta)
                optimized = PPTOutline.model_validate(parsed)
                return optimized
            except Exception as e:
                self._handle_workflow_error(session_id, "3.3", e, {"outline_available": True})

        return outline

    def _post_process_llm_response(self, parsed: Optional[Dict[str, Any]], user_text: str, tool_calls: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """后处理LLM响应，修正常见错误"""
        if parsed is None:
            return parsed

        modifications = []

        # 1. 智能修正学科名称
        subject_info = parsed.get("subject_info", {})
        subject_name = subject_info.get("subject_name", "")
        knowledge_points = parsed.get("knowledge_points", [])

        # 检查是否需要修正学科名称
        if subject_name and knowledge_points:
            kp_names = [kp.get("name", "") for kp in knowledge_points if kp.get("name")]
            # 如果学科名称出现在知识点中，说明分类错误
            if subject_name in kp_names or len(subject_name) > 10:  # 知识点通常不会这么短
                # 从用户输入中提取学科
                subject_patterns = [
                    r'([机械电气建筑焊接护理医学计算机数学物理化学会计金融物流等]+)专业',
                    r'([机械电气建筑焊接护理医学计算机数学物理化学会计金融物流等]+)课',
                    r'([机械电气建筑焊接护理医学计算机数学物理化学会计金融物流等]+)课程'
                ]

                for pattern in subject_patterns:
                    match = re.search(pattern, user_text)
                    if match:
                        new_subject = match.group(1)
                        subject_info["subject_name"] = new_subject
                        modifications.append(f"修正学科名称：{subject_name} → {new_subject}")
                        break

        # 2. 控制知识点数量和质量，智能评估难度
        if len(knowledge_points) > 5:
            # 保留最重要的前3个
            knowledge_points = knowledge_points[:3]
            parsed["knowledge_points"] = knowledge_points
            modifications.append(f"限制知识点数量至3个（原{len(knowledge_points)}个）")
        elif len(knowledge_points) == 0:
            # 如果没有知识点，从用户输入中提取
            quoted_kp = re.findall(r'[""「『【]([^"」』】]{2,20})["」』】]', user_text)
            if quoted_kp:
                parsed["knowledge_points"] = [{
                    "id": "KP_001",
                    "name": quoted_kp[0],
                    "type": "theory",
                    "difficulty_level": "medium"
                }]
                modifications.append(f"从用户输入提取知识点：{quoted_kp[0]}")

        # 智能评估知识点难度
        for kp in knowledge_points:
            if not kp.get("difficulty_level") or kp.get("difficulty_level") not in ["easy", "medium", "hard"]:
                assessed_difficulty = self._assess_knowledge_point_difficulty(kp.get("name", ""), user_text)
                if assessed_difficulty != kp.get("difficulty_level"):
                    kp["difficulty_level"] = assessed_difficulty
                    modifications.append(f"评估知识点'{kp['name']}'难度为：{assessed_difficulty}")

        # 3. 智能识别教学场景
        teaching_scenario = parsed.get("teaching_scenario", {})
        if not teaching_scenario.get("scene_type") or teaching_scenario.get("scene_type") == "unknown":
            assessed_scene = self._assess_teaching_scenario(user_text, knowledge_points)
            if assessed_scene != teaching_scenario.get("scene_type"):
                teaching_scenario["scene_type"] = assessed_scene
                modifications.append(f"自动识别教学场景为：{assessed_scene}")

        # 3. 修正默认参数
        slide_req = parsed.get("slide_requirements", {})
        duration = slide_req.get("lesson_duration_min", 45)
        if duration > 90 or duration < 30:
            slide_req["lesson_duration_min"] = 45
            modifications.append(f"修正课时：{duration}分钟 → 45分钟")

        # 4. 确保数据完整性
        if not subject_info.get("subject_name"):
            subject_info["subject_name"] = "待补充"

        if not subject_info.get("subject_category"):
            subject_info["subject_category"] = "unknown"

        # 5. 添加修改记录
        if modifications:
            parsed["_post_process_modifications"] = modifications

        return parsed

    def _assess_knowledge_point_difficulty(self, kp_name: str, user_text: str) -> str:
        """智能评估知识点难度"""
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

    def _assess_teaching_scenario(self, user_text: str, knowledge_points: List[Dict[str, Any]]) -> str:
        """智能识别教学场景"""
        text_lower = user_text.lower()

        # 实践课关键词
        practice_keywords = ["实训", "实操", "操作", "动手", "实验", "练习", "技能", "步骤", "方法"]
        # 复习课关键词
        review_keywords = ["复习", "回顾", "总结", "巩固", "考前", "重温", "温习"]

        # 检查实践关键词
        if any(kw in text_lower for kw in practice_keywords):
            return "practice"

        # 检查复习关键词
        if any(kw in text_lower for kw in review_keywords):
            return "review"

        # 检查知识点类型
        if knowledge_points:
            kp_types = [kp.get("type", "") for kp in knowledge_points]
            if "practice" in kp_types:
                return "practice"

        # 检查理论关键词（理论课是默认）
        theory_keywords = ["理论", "原理", "概念", "基础", "知识", "讲解", "介绍"]
        if any(kw in text_lower for kw in theory_keywords):
            return "theory"

        # 默认返回理论课
        return "theory"

    def _should_reoptimize_with_llm(self, answers: Dict[str, Any], original_request: Dict[str, Any]) -> bool:
        """判断是否需要重新调用LLM进行优化"""
        # 检查是否提供了重要的补充信息
        important_keys = [
            "subject",           # 新增学科
            "knowledge_points",  # 新增知识点
            "additional_kps",    # 补充知识点
            "teaching_goals_input", # 自定义教学目标
            "modify_assessments" # 修改评估结果
        ]

        return any(key in answers for key in important_keys)

    async def _reoptimize_with_llm(self, session_id: str, current_request: TeachingRequest, user_answers: Dict[str, Any]) -> TeachingRequest:
        """基于用户补充信息，重新调用LLM进行智能优化"""

        # 构建重新优化的prompt
        reoptimize_system_prompt = """你是高职教学课件意图理解优化助手。你将根据用户补充的新信息，对当前的教学需求进行智能调整和优化。

## 优化任务
基于用户的最新补充信息，对教学需求进行以下优化：
1. **信息整合**：将新补充的信息与原有信息进行有机整合
2. **智能调整**：根据新信息调整知识点难度、教学场景等评估结果
3. **合理完善**：补充缺失的合理默认值
4. **逻辑优化**：确保整体教学逻辑的合理性和连贯性

## 调整原则
- 尊重用户明确提供的信息，不擅自推翻
- 对模糊或缺失信息进行合理推测和补充
- 保持教学内容的专业性和实用性
- 确保调整结果符合高职教学规律

只输出JSON对象，不要解释。"""

        reoptimize_schema = """{
  "optimizations": [
    {
      "field": "string",
      "original_value": "any",
      "new_value": "any",
      "reason": "string"
    }
  ],
  "recommendations": ["string"],
  "confidence_score": "number"
}"""

        # 构建用户消息
        user_message = {
            "original_request": current_request.model_dump(),
            "user_answers": user_answers,
            "optimization_context": "用户补充了新的教学需求信息，请进行智能调整"
        }

        try:
            self.logger.emit(session_id, "3.1", "reoptimize_prompt", {
                "system": reoptimize_system_prompt,
                "user": json.dumps(user_message, ensure_ascii=False),
                "schema": reoptimize_schema
            })

            parsed, meta = await self.llm.chat_json(
                reoptimize_system_prompt,
                json.dumps(user_message, ensure_ascii=False),
                reoptimize_schema
            )

            self.logger.emit(session_id, "3.1", "reoptimize_response", meta)

            # 应用优化建议
            return self._apply_optimizations(current_request, parsed)

        except Exception as e:
            self.logger.emit(session_id, "3.1", "reoptimize_llm_error", {"error": str(e)})
            # 如果优化失败，返回原请求
            return current_request

    def _apply_optimizations(self, request: TeachingRequest, optimizations: Dict[str, Any]) -> TeachingRequest:
        """应用LLM的优化建议"""
        if not optimizations.get("optimizations"):
            return request

        # 应用每个优化建议
        for opt in optimizations["optimizations"]:
            field = opt.get("field")
            new_value = opt.get("new_value")

            try:
                if field == "knowledge_points.difficulty_level":
                    # 更新知识点难度
                    for kp in request.knowledge_points:
                        if kp.name in str(new_value):
                            kp.difficulty_level = new_value.get("difficulty_level", kp.difficulty_level)
                elif field == "teaching_scenario.scene_type":
                    # 更新教学场景
                    request.teaching_scenario.scene_type = new_value
                elif field == "teaching_objectives.knowledge":
                    # 更新教学目标
                    request.teaching_objectives.knowledge = new_value
                    request.teaching_objectives.auto_generated = False
                # 可以继续添加其他字段的优化逻辑

            except Exception as e:
                self.logger.emit("optimization", "apply_error", {
                    "field": field,
                    "error": str(e)
                })

        return request

    async def _final_intent_optimization(self, session_id: str, current_request: TeachingRequest) -> Optional[TeachingRequest]:
        """基于用户完整输入进行最终的意图理解优化"""

        # 构建最终优化的prompt
        final_optimization_prompt = """你是高职教学课件意图理解最终优化助手。你将根据用户的完整输入（包括所有补充信息和配置调整），进行全面的意图理解和结构化优化。

## 优化任务
基于用户的所有输入信息，进行完整的教学需求优化：
1. **整合所有信息**：将初始输入、补充知识点、配置调整等所有信息进行有机整合
2. **完整评估**：对所有要素进行全面评估，包括难度、场景、目标等
3. **优化结构**：确保整体教学逻辑合理，内容结构完整
4. **完善细节**：补充所有必要的默认值和推测信息

## 优化原则
- 基于完整上下文进行判断，不要局限于单次输入
- 确保教学内容的系统性和连贯性
- 充分考虑高职教学的特点和规律
- 提供完整、可直接使用的教学需求结构

只输出JSON对象，不要解释。"""

        final_schema = """{
  "optimized_request": {
    "subject_info": {"subject_name": "string", "subject_category": "string", "sub_field": "string"},
    "knowledge_points": [{"id": "string", "name": "string", "type": "string", "difficulty_level": "string"}],
    "teaching_scenario": {"scene_type": "string", "scene_label": "string"},
    "teaching_objectives": {"knowledge": ["string"], "ability": ["string"], "literacy": ["string"]},
    "slide_requirements": {"target_count": "number", "min_count": "number", "max_count": "number", "lesson_duration_min": "number"},
    "special_requirements": {
      "cases": {"enabled": "boolean", "count": "number"},
      "exercises": {"enabled": "boolean", "total_count": "number"},
      "interaction": {"enabled": "boolean", "types": ["string"]}
    }
  },
  "optimization_summary": "string",
  "confidence_score": "number"
}"""

        # 构建完整的上下文信息
        context_data = {
            "original_user_input": current_request.parsing_metadata.raw_input,
            "current_request": current_request.model_dump(),
            "all_user_interactions": getattr(current_request, 'interaction_history', []),
            "final_optimization": True
        }

        try:
            self.logger.emit(session_id, "3.1", "final_optimization_prompt", {
                "system": final_optimization_prompt,
                "user": json.dumps(context_data, ensure_ascii=False),
                "schema": final_schema
            })

            parsed, meta = await self.llm.chat_json(
                final_optimization_prompt,
                json.dumps(context_data, ensure_ascii=False),
                final_schema
            )

            self.logger.emit(session_id, "3.1", "final_optimization_response", meta)

            # 应用最终优化结果
            if parsed and "optimized_request" in parsed:
                from .schemas import TeachingRequest
                optimized_request = TeachingRequest.model_validate(parsed["optimized_request"])
                # 保持原有的元数据
                optimized_request.parsing_metadata = current_request.parsing_metadata
                optimized_request.interaction_stage = "confirmed"
                # Note: confirmation_status removed in JSON Schema refactoring

                return optimized_request

        except Exception as e:
            self.logger.emit(session_id, "3.1", "final_optimization_llm_error", {"error": str(e)})

        return None

    def _handle_workflow_error(self, session_id: str, stage: str, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """统一的错误处理和日志记录"""
        error_info = {
            "stage": stage,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        self.logger.emit(session_id, f"{stage}_error", error_info)

        # 对于关键错误，可以设置降级策略
        if stage == "3.1" and isinstance(error, (json.JSONDecodeError, ValueError)):
            # 意图理解失败时的降级处理
            error_info["fallback_strategy"] = "use_heuristic_parser"
        elif stage in ["3.2", "3.3", "3.4"]:
            # 后续阶段失败时的降级处理
            error_info["fallback_strategy"] = "use_base_implementation"

    async def run(self, session_id: str, user_text: Optional[str], answers: Optional[Dict[str, Any]], auto_fill_defaults_flag: bool, stop_at: Optional[str] = None,
                 intent_params: Optional[Dict[str, Any]] = None) -> Tuple[SessionState, str, List[Any]]:
        """Run the workflow until it either completes or needs user input.

        Args:
            stop_at: If set to "3.1", "3.2", "3.3", or "3.4", stop after that module.

        Returns: (state, status, questions)
          status: "ok" | "need_user_input"
        """

        state = self.store.load(session_id) or self.store.create(session_id)

        # --- Stage 3.1 ---
        if state.teaching_request is None:
            if not user_text:
                raise ValueError("user_text is required for the first run")
            req = await self._parse_intent(
                session_id, user_text,
                tone=intent_params.get("tone") if intent_params else None,
                verbosity=intent_params.get("verbosity") if intent_params else None,
                instructions=intent_params.get("instructions") if intent_params else None
            )
            # Generate human-readable summary
            req.display_summary = generate_display_summary(req)
            state.teaching_request = req
            state.stage = "3.1"
            self.store.save(state)

        # Apply user answers if present
        if answers:
            self.logger.emit(session_id, "3.1", "user_answers", answers)
            original_request = state.teaching_request.model_dump()
            state.teaching_request = apply_user_answers(state.teaching_request, answers)

            # 如果用户提供了新的信息，重新调用LLM进行智能调整
            if self.llm.is_enabled() and self._should_reoptimize_with_llm(answers, original_request):
                try:
                    state.teaching_request = await self._reoptimize_with_llm(session_id, state.teaching_request, answers)
                    self.logger.emit(session_id, "3.1", "reoptimized_with_llm", {
                        "answers_provided": answers,
                        "optimizations_applied": True
                    })
                except Exception as e:
                    self.logger.emit(session_id, "3.1", "reoptimize_error", {"error": str(e)})
                    # 如果重新优化失败，继续使用原有逻辑

            # Regenerate display summary after updates
            state.teaching_request.display_summary = generate_display_summary(state.teaching_request)
            self.store.save(state)


        # Validate and get questions based on interaction_stage
        questions, missing = validate_and_build_questions(state.teaching_request)

        # If there are questions to ask, return for user input
        if questions:
            # Update display summary before returning
            state.teaching_request.display_summary = generate_display_summary(state.teaching_request)
            self.store.save(state)
            return state, "need_user_input", questions
        
        # Check if user has confirmed (interaction_stage == "confirmed")
        if state.teaching_request.interaction_stage != "confirmed":
            # Not yet confirmed, keep asking questions
            return state, "need_user_input", questions

        # User confirmed, autofill defaults if needed
        if auto_fill_defaults_flag:
            state.teaching_request = autofill_defaults(state.teaching_request)

            # 检查是否有补充信息，如果有则进行最终意图理解优化
            has_additional_info = (
                getattr(state.teaching_request, 'interaction_metadata', {}).get("has_additional_kps", False) or
                getattr(state.teaching_request, 'interaction_metadata', {}).get("has_config_modification", False)
            )

            if has_additional_info and self.llm.is_enabled():
                try:
                    final_optimized = await self._final_intent_optimization(session_id, state.teaching_request)
                    if final_optimized:
                        state.teaching_request = final_optimized
                        self.logger.emit(session_id, "3.1", "final_optimization_completed", {
                            "complete_request": True,
                            "has_additional_info": True
                        })
                except Exception as e:
                    self.logger.emit(session_id, "3.1", "final_optimization_error", {"error": str(e)})
                    # 如果最终优化失败，继续使用当前结果

            state.teaching_request.display_summary = generate_display_summary(state.teaching_request)
            self.logger.emit(session_id, "3.1", "autofill_defaults", state.teaching_request.model_dump(mode="json"))
            self.store.save(state)

        # Check if we should stop at 3.1
        if stop_at == "3.1":
            return state, "ok", []

        # --- Stage 3.2 ---
        if state.style_config is None:
            cfg, samples = await self._design_style(session_id, state.teaching_request)
            state.style_config = cfg
            state.style_samples = samples
            state.stage = "3.2"
            self.store.save(state)

        # Check if we should stop at 3.2
        if stop_at == "3.2":
            return state, "ok", []

        # --- Stage 3.3 ---
        if state.outline is None:
            outline = await self._generate_outline(session_id, state.teaching_request, state.style_config)
            state.outline = outline
            state.stage = "3.3"
            self.store.save(state)

        # Check if we should stop at 3.3
        if stop_at == "3.3":
            return state, "ok", []

        # --- Stage 3.4 ---
        if state.deck_content is None:
            base = build_base_deck(state.teaching_request, state.style_config, state.outline)
            deck = await refine_with_llm(session_id, self.llm, self.logger, state.teaching_request, state.style_config, state.outline, base)
            ok, errs = validate_deck(state.outline, deck)
            if not ok:
                self.logger.emit(session_id, "3.4", "validate_failed", {"errors": errs})
                deck = base
            else:
                self.logger.emit(session_id, "3.4", "validate_ok", {"pages": len(deck.pages)})
            state.deck_content = deck
            state.stage = "3.4"
            self.store.save(state)

        return state, "ok", []

