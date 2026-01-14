"""LangGraph版本的PPT生成工作流

这个文件包含完整的LangGraph实现，将原有的WorkflowEngine重构为基于LangGraph的状态机。
保留了所有功能和日志输出，提供了更好的可观察性和扩展性。

主要特性：
- 每个阶段都是独立的节点
- 使用条件边控制复杂流程（用户交互、多阶段处理）
- 保留完整的日志记录
- 保持API兼容性
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict
import json
from datetime import datetime

from .intent import apply_user_answers, autofill_defaults, heuristic_parse, validate_and_build_questions, generate_display_summary
from .llm import LLMClient
from .logger import WorkflowLogger
from .schemas import PPTOutline, SessionState, StyleConfig, StyleSampleSlide, TeachingRequest
from .store import SessionStore
from .style import build_style_samples, choose_style
from .content import build_base_deck, refine_with_llm, validate_deck
from .tools import ToolExecutor


class GraphState(TypedDict, total=False):
    """LangGraph状态定义"""
    # 输入参数
    session_id: str
    user_text: Optional[str]
    answers: Optional[Dict[str, Any]]
    auto_fill_defaults: bool
    stop_at: Optional[str]

    # 工作流状态
    stage: str
    status: str  # "ok" | "need_user_input"
    questions: List[Dict[str, Any]]

    # 核心数据
    teaching_request: Optional[TeachingRequest]
    style_config: Optional[StyleConfig]
    style_samples: Optional[List[StyleSampleSlide]]
    outline: Optional[PPTOutline]
    deck_content: Optional[Any]

    # 内部组件（在初始化时设置）
    _store: Optional[SessionStore]
    _logger: Optional[WorkflowLogger]
    _llm: Optional[LLMClient]
    _tool_executor: Optional[ToolExecutor]


class LangGraphWorkflowEngine:
    """基于LangGraph的PPT生成工作流引擎

    这个类完全替代了原来的WorkflowEngine，但保持API兼容性。
    内部使用LangGraph管理复杂的多阶段流程和条件分支。
    """

    def __init__(self, store: SessionStore, logger: WorkflowLogger, llm: LLMClient):
        self.store = store
        self.logger = logger
        self.llm = llm
        self.tool_executor = ToolExecutor()

        # 构建LangGraph
        self.graph = self._build_graph()

    def _build_graph(self):
        """构建LangGraph工作流图"""
        from langgraph.graph import StateGraph, END

        graph = StateGraph(GraphState)

        # 添加节点
        graph.add_node("initialize", self._node_initialize)
        graph.add_node("parse_intent", self._node_parse_intent)
        graph.add_node("validate_and_interact", self._node_validate_and_interact)
        graph.add_node("design_style", self._node_design_style)
        graph.add_node("generate_outline", self._node_generate_outline)
        graph.add_node("generate_content", self._node_generate_content)
        graph.add_node("finalize", self._node_finalize)

        # 设置入口点
        graph.set_entry_point("initialize")

        # 定义流程边
        graph.add_edge("initialize", "parse_intent")
        graph.add_edge("parse_intent", "validate_and_interact")

        # 条件边：根据验证结果决定下一步
        def route_after_validate(state: GraphState) -> str:
            if state.get("status") == "need_user_input":
                return END  # 等待用户输入
            return "design_style"

        graph.add_conditional_edges(
            "validate_and_interact",
            route_after_validate,
            {
                END: END,  # 等待用户输入
                "design_style": "design_style"
            }
        )

        # 继续流程
        graph.add_edge("design_style", "generate_outline")
        graph.add_edge("generate_outline", "generate_content")
        graph.add_edge("generate_content", "finalize")
        graph.add_edge("finalize", END)

        return graph.compile()

    async def run(
        self,
        session_id: str,
        user_text: Optional[str] = None,
        answers: Optional[Dict[str, Any]] = None,
        auto_fill_defaults: bool = False,
        stop_at: Optional[str] = None
    ) -> tuple[SessionState, str, List[Dict[str, Any]]]:
        """运行工作流（保持与原API兼容）

        Args:
            session_id: 会话ID
            user_text: 用户输入文本
            answers: 用户回答
            auto_fill_defaults: 是否自动填充默认值
            stop_at: 在指定阶段停止（用于测试）

        Returns:
            (state, status, questions)
        """

        # 准备初始状态
        initial_state: GraphState = {
            "session_id": session_id,
            "user_text": user_text,
            "answers": answers,
            "auto_fill_defaults": auto_fill_defaults,
            "stop_at": stop_at,
            "status": "ok",
            "questions": [],
            "_store": self.store,
            "_logger": self.logger,
            "_llm": self.llm,
            "_tool_executor": self.tool_executor,
        }

        # 运行LangGraph
        try:
            final_state = await self.graph.ainvoke(initial_state)

            # 从最终状态提取结果
            state = final_state.get("_session_state")
            status = final_state.get("status", "ok")
            questions = final_state.get("questions", [])

            return state, status, questions

        except Exception as e:
            # 出错时记录日志并返回错误状态
            self.logger.emit(session_id, "system", "error", {"error": str(e)})
            # 返回空的会话状态
            state = self.store.load(session_id) or self.store.create(session_id)
            return state, "error", []

    # ==================== LangGraph节点函数 ====================

    async def _node_initialize(self, state: GraphState) -> GraphState:
        """初始化节点"""
        session_id = state["session_id"]

        # 加载或创建会话状态
        session_state = state.get("_store").load(session_id) or state.get("_store").create(session_id)

        # 将会话状态数据合并到graph state
        state.update({
            "stage": session_state.stage,
            "teaching_request": session_state.teaching_request,
            "style_config": session_state.style_config,
            "style_samples": session_state.style_samples,
            "outline": session_state.outline,
            "deck_content": session_state.deck_content,
            "_session_state": session_state,
        })

        return state

    async def _node_parse_intent(self, state: GraphState) -> GraphState:
        """意图理解节点（3.1阶段）"""
        session_id = state["session_id"]
        logger = state["_logger"]
        llm = state["_llm"]
        tool_executor = state["_tool_executor"]

        # 如果已有teaching_request，跳过解析
        if state.get("teaching_request"):
            return state

        user_text = state.get("user_text")
        if not user_text:
            raise ValueError("user_text is required for intent parsing")

        # 创建临时WorkflowEngine来复用现有逻辑
        temp_engine = type('TempEngine', (), {
            'llm': llm,
            'logger': logger,
            'tool_executor': tool_executor,
            '_parse_intent': None
        })()

        # 直接调用workflow.py中的_parse_intent方法
        from .workflow import WorkflowEngine
        temp_engine.__class__ = WorkflowEngine

        try:
            req = await temp_engine._parse_intent(session_id, user_text, use_tools=True)

            # 生成显示摘要
            req.display_summary = generate_display_summary(req)

            state["teaching_request"] = req
            state["stage"] = "3.1"
            state["_session_state"].teaching_request = req
            state["_session_state"].stage = "3.1"
            state["_store"].save(state["_session_state"])

        except Exception as e:
            logger.emit(session_id, "3.1", "error", {"error": str(e)})
            # 降级到启发式解析
            req = heuristic_parse(user_text)
            req.display_summary = generate_display_summary(req)
            req.parsing_metadata.parsing_method = "heuristic_fallback"

            state["teaching_request"] = req
            state["stage"] = "3.1"
            state["_session_state"].teaching_request = req
            state["_session_state"].stage = "3.1"
            state["_store"].save(state["_session_state"])

        return state

    async def _node_validate_and_interact(self, state: GraphState) -> GraphState:
        """验证和交互节点（处理用户确认流程）"""
        session_id = state["session_id"]
        logger = state["_logger"]
        answers = state.get("answers")

        req = state["teaching_request"]

        # 应用用户回答（如果有）
        if answers:
            logger.emit(session_id, "3.1", "user_answers", answers)
            req = apply_user_answers(req, answers)
            req.display_summary = generate_display_summary(req)
            state["teaching_request"] = req
            state["_session_state"].teaching_request = req
            state["_store"].save(state["_session_state"])

        # 验证并生成问题
        questions, missing = validate_and_build_questions(req)

        if questions:
            state["status"] = "need_user_input"
            state["questions"] = [q.model_dump() for q in questions]
            return state

        # 如果没有问题，检查是否需要确认
        if req.interaction_stage != "confirmed":
            # 自动填充默认值（如果启用）
            if state.get("auto_fill_defaults", False):
                req = autofill_defaults(req)
                req.display_summary = generate_display_summary(req)
                req.interaction_stage = "confirmed"
                # Note: confirmation_status removed in JSON Schema refactoring

                state["teaching_request"] = req
                state["_session_state"].teaching_request = req
                logger.emit(session_id, "3.1", "autofill_defaults", req.model_dump(mode="json"))
                state["_store"].save(state["_session_state"])

        return state

    async def _node_design_style(self, state: GraphState) -> GraphState:
        """风格设计节点（3.2阶段）"""
        session_id = state["session_id"]
        logger = state["_logger"]
        llm = state["_llm"]

        # 如果已有style_config，跳过
        if state.get("style_config"):
            return state

        req = state["teaching_request"]

        # 创建临时引擎复用逻辑
        temp_engine = type('TempEngine', (), {
            'llm': llm,
            'logger': logger,
            '_design_style': None
        })()
        from .workflow import WorkflowEngine
        temp_engine.__class__ = WorkflowEngine

        try:
            cfg, samples = await temp_engine._design_style(session_id, req)

            state["style_config"] = cfg
            state["style_samples"] = samples
            state["stage"] = "3.2"
            state["_session_state"].style_config = cfg
            state["_session_state"].style_samples = samples
            state["_session_state"].stage = "3.2"
            state["_store"].save(state["_session_state"])

        except Exception as e:
            logger.emit(session_id, "3.2", "error", {"error": str(e)})
            # 使用默认风格
            cfg = choose_style(req)
            samples = build_style_samples(req, cfg)

            state["style_config"] = cfg
            state["style_samples"] = samples
            state["stage"] = "3.2"
            state["_session_state"].style_config = cfg
            state["_session_state"].style_samples = samples
            state["_session_state"].stage = "3.2"
            state["_store"].save(state["_session_state"])

        return state

    async def _node_generate_outline(self, state: GraphState) -> GraphState:
        """大纲生成节点（3.3阶段）"""
        session_id = state["session_id"]
        logger = state["_logger"]
        llm = state["_llm"]

        # 如果已有outline，跳过
        if state.get("outline"):
            return state

        req = state["teaching_request"]
        style = state["style_config"]

        # 创建临时引擎复用逻辑
        temp_engine = type('TempEngine', (), {
            'llm': llm,
            'logger': logger,
            '_generate_outline': None
        })()
        from .workflow import WorkflowEngine
        temp_engine.__class__ = WorkflowEngine

        try:
            outline = await temp_engine._generate_outline(session_id, req, style)

            state["outline"] = outline
            state["stage"] = "3.3"
            state["_session_state"].outline = outline
            state["_session_state"].stage = "3.3"
            state["_store"].save(state["_session_state"])

        except Exception as e:
            logger.emit(session_id, "3.3", "error", {"error": str(e)})
            # 使用基础大纲生成
            from .outline import generate_outline
            outline = generate_outline(req, style_name=style.style_name)

            state["outline"] = outline
            state["stage"] = "3.3"
            state["_session_state"].outline = outline
            state["_session_state"].stage = "3.3"
            state["_store"].save(state["_session_state"])

        return state

    async def _node_generate_content(self, state: GraphState) -> GraphState:
        """内容生成节点（3.4阶段）"""
        session_id = state["session_id"]
        logger = state["_logger"]
        llm = state["_llm"]

        # 检查是否需要停止在3.3
        if state.get("stop_at") == "3.3":
            return state

        # 如果已有deck_content，跳过
        if state.get("deck_content"):
            return state

        req = state["teaching_request"]
        style = state["style_config"]
        outline = state["outline"]

        try:
            # 生成基础内容
            base = build_base_deck(req, style, outline)
            # 使用LLM优化内容
            deck = await refine_with_llm(session_id, llm, logger, req, style, outline, base)

            # 验证内容
            ok, errs = validate_deck(outline, deck)
            if not ok:
                logger.emit(session_id, "3.4", "validate_failed", {"errors": errs})
                deck = base

            state["deck_content"] = deck
            state["stage"] = "3.4"
            state["_session_state"].deck_content = deck
            state["_session_state"].stage = "3.4"
            state["_store"].save(state["_session_state"])

        except Exception as e:
            logger.emit(session_id, "3.4", "error", {"error": str(e)})
            # 使用基础内容
            base = build_base_deck(req, style, outline)
            state["deck_content"] = base
            state["stage"] = "3.4"
            state["_session_state"].deck_content = base
            state["_session_state"].stage = "3.4"
            state["_store"].save(state["_session_state"])

        return state

    async def _node_finalize(self, state: GraphState) -> GraphState:
        """最终化节点"""
        # 可以在这里添加最终的清理或统计工作
        return state


# ==================== 兼容性函数 ====================

def build_graph():
    """构建LangGraph图（兼容原有接口）"""
    # 这个函数主要用于演示，现在LangGraphWorkflowEngine内部管理图
    pass


# ==================== 使用示例 ====================

async def run_langgraph_workflow(
    session_id: str,
    user_text: Optional[str] = None,
    answers: Optional[Dict[str, Any]] = None,
    auto_fill_defaults: bool = False,
    stop_at: Optional[str] = None
):
    """使用LangGraph运行工作流的示例函数

    这个函数展示了如何使用新的LangGraphWorkflowEngine
    """
    # 这里需要外部提供store, logger, llm实例
    # 在实际使用中，这些应该从依赖注入或全局配置获取

    # 示例（实际使用时需要正确的依赖注入）：
    # store = SessionStore("data")
    # logger = WorkflowLogger("data")
    # llm = LLMClient()
    #
    # engine = LangGraphWorkflowEngine(store, logger, llm)
    # state, status, questions = await engine.run(
    #     session_id, user_text, answers, auto_fill_defaults, stop_at
    # )
    #
    # return state, status, questions

    raise NotImplementedError("此函数需要正确的依赖注入配置")