# common - 公共模块
# 包含共享数据结构、LLM客户端、日志、存储等基础设施
#
# 注意：当前处于迁移过渡期，同时保留原始文件位置的兼容性
# 完成迁移后，将直接从 common/ 目录导入

# 暂时从原始位置导入以保持兼容性
from ..schemas import (
    TeachingRequest,
    StyleConfig,
    StyleSampleSlide,
    PPTOutline,
    OutlineSlide,
    SlideDeckContent,
    SlidePage,
    SlideElement,
    Question,
)
from ..llm import LLMClient
from ..logger import WorkflowLogger
from ..store import SessionStore
from ..tools import ToolExecutor

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
    # 基础设施
    "LLMClient",
    "WorkflowLogger",
    "SessionStore",
    "ToolExecutor",
]
