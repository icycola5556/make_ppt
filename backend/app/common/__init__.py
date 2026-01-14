# common - 公共模块
# 包含共享数据结构、LLM客户端、日志、存储等基础设施

from .schemas import (
    # 核心数据结构
    TeachingRequest,
    StyleConfig,
    StyleSampleSlide,
    PPTOutline,
    OutlineSlide,
    SlideDeckContent,
    SlidePage,
    SlideElement,
    Question,
    SessionState,
    # API 请求/响应
    WorkflowRunRequest,
    WorkflowRunResponse,
    # 子模型
    SubjectInfo,
    KnowledgePointDetail,
    KnowledgeStructure,
    TeachingScenarioDetail,
    TeachingObjectivesStructured,
    SlideRequirementsDetail,
    SpecialRequirementsDetailed,
    PageDistribution,
    ParsingMetadata,
    CaseRequirement,
    ExerciseRequirement,
    InteractionRequirement,
    WarningRequirement,
    # 类型别名
    TeachingScene,
    ProfessionalCategory,
)
from .llm_client import LLMClient
from .logger import WorkflowLogger
from .store import SessionStore
from .tools import ToolExecutor
from .standards import default_goals

__all__ = [
    # 数据结构
    "TeachingRequest",
    "StyleConfig",
    "StyleSampleSlide",
    "PPTOutline",
    "OutlineSlide",
    "SlideDeckContent",
    "SlidePage",
    "SlideElement",
    "Question",
    "SessionState",
    "WorkflowRunRequest",
    "WorkflowRunResponse",
    # 子模型
    "SubjectInfo",
    "KnowledgePointDetail",
    "KnowledgeStructure",
    "TeachingScenarioDetail",
    "TeachingObjectivesStructured",
    "SlideRequirementsDetail",
    "SpecialRequirementsDetailed",
    "PageDistribution",
    "ParsingMetadata",
    "CaseRequirement",
    "ExerciseRequirement",
    "InteractionRequirement",
    "WarningRequirement",
    # 类型别名
    "TeachingScene",
    "ProfessionalCategory",
    # 基础设施
    "LLMClient",
    "WorkflowLogger",
    "SessionStore",
    "ToolExecutor",
    "default_goals",
]
