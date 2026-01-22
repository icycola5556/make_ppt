"""
Module 3.5: 核心定义 (Schemas & Utils)
包含所有数据模型、异常类和通用无状态工具函数。
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from ...common.schemas import SlidePage

# ============================================================================
# Enums
# ============================================================================

class ImageStyle(str, Enum):
    """图片视觉风格"""
    PHOTO = "photo"          # 实拍照片
    SCHEMATIC = "schematic"  # 原理图/示意图
    DIAGRAM = "diagram"      # 流程图/框图
    ICON = "icon"            # 图标
    WARNING = "warning"      # 警示图标
    ILLUSTRATION = "illustration" # 插画

class AspectRatio(str, Enum):
    """宽高比"""
    SQUARE = "1:1"
    LANDSCAPE = "16:9"
    PORTRAIT = "9:16"
    WIDE = "21:9"
    STANDARD = "4:3"

class ColorConstraint(str, Enum):
    """颜色约束"""
    TRANSPARENT_BG = "transparent_bg"
    WHITE_BG = "white_bg"
    NO_CONSTRAINT = "no_constraint"

# ============================================================================
# Schemas
# ============================================================================

class ImageSlotRequest(BaseModel):
    """图片插槽请求 - 传递给图片生成服务"""
    
    # === 唯一标识 ===
    slot_id: str = Field(description="插槽唯一ID")
    page_index: int = Field(description="所属页面索引")

    # === 语义信息 ===
    theme: str = Field(description="主题描述")
    keywords: List[str] = Field(default_factory=list, description="关键词列表")
    context: str = Field(default="", description="上下文描述")

    # === 视觉约束 ===
    visual_style: ImageStyle = Field(default=ImageStyle.PHOTO)
    aspect_ratio: AspectRatio = Field(default=AspectRatio.STANDARD)
    color_constraint: ColorConstraint = Field(default=ColorConstraint.NO_CONSTRAINT)
    min_resolution: tuple[int, int] = Field(default=(800, 600))

    # === 布局位置 ===
    layout_position: str = Field(description="布局位置标识")
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    w: float = Field(ge=0, le=1)
    h: float = Field(ge=0, le=1)

    # === 其他 ===
    priority: int = Field(default=1, ge=1, le=5)
    fallback_query: Optional[str] = None
    
    # RAG 相关字段 (保留)
    matched_image_url: Optional[str] = None
    html_source: Optional[str] = None
    matched_score: Optional[float] = None
    caption: Optional[str] = None

    def to_rag_query(self) -> Dict[str, Any]:
        """Convert to RAG query format"""
        return {
            "query": f"{self.theme} {self.context} {' '.join(self.keywords)}",
            "filters": {
                "style": self.visual_style.value,
                "min_width": self.min_resolution[0],
                "min_height": self.min_resolution[1],
                "color_constraint": self.color_constraint.value,
            },
            "context": self.context,
            "fallback_query": self.fallback_query,
            "top_k": 3,
            "source": self.slot_id,
        }

class ImageSlotResult(BaseModel):
    """图片生成结果"""
    slot_id: str
    page_index: int
    status: str = "pending"
    prompt: str = ""
    image_path: Optional[str] = None
    error: Optional[str] = None
    generated_at: Optional[datetime] = None
    model_used: str = "qwen-image-max"
    generation_time_seconds: Optional[float] = None
    cache_hit: bool = False

class LayoutConfig(BaseModel):
    """布局模板配置"""
    layout_id: str
    display_name: str
    description: str
    
    grid_template_areas: str
    grid_template_columns: str = "1fr"
    grid_template_rows: str = "auto"
    gap: str = "2rem"
    
    image_slots: List[Dict[str, Any]] = Field(default_factory=list)
    
    suitable_slide_types: List[str] = Field(default_factory=list)
    suitable_keywords: List[str] = Field(default_factory=list)
    
    max_bullets: Optional[int] = None
    max_text_length: Optional[int] = None

class RenderResult(BaseModel):
    """渲染结果"""
    session_id: str
    html_path: str
    html_content: Optional[str] = None
    
    image_slots: List[ImageSlotRequest] = Field(default_factory=list)
    image_results: List[ImageSlotResult] = Field(default_factory=list)
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    
    total_pages: int = 0
    layouts_used: Dict[str, int] = Field(default_factory=dict)

# ============================================================================
# Stateless Utils (Moved from html_renderer.py)
# ============================================================================

def extract_bullets(page: SlidePage) -> List[str]:
    """从页面元素中提取要点列表"""
    bullets = []
    for elem in page.elements:
        if elem.type == "bullets" and isinstance(elem.content, dict):
            items = elem.content.get("items", [])
            bullets.extend([str(i) for i in items])
        elif elem.type == "text" and isinstance(elem.content, dict):
            text = elem.content.get("text", "")
            if text:
                bullets.append(str(text))
        elif elem.type == "quiz" and isinstance(elem.content, dict):
             question = elem.content.get("question", "")
             if question:
                 bullets.append(str(question))
        elif not isinstance(elem.content, dict) and elem.content:
            bullets.append(str(elem.content))
    return bullets

def calculate_text_length(page: SlidePage) -> int:
    """计算页面的总文本长度"""
    total_len = len(page.title) if page.title else 0
    bullets = extract_bullets(page)
    for bullet in bullets:
        total_len += len(bullet)
    return total_len
