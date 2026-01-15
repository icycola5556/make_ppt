"""
Module 3.5: 智能排版与动态渲染引擎 - 数据模型定义
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ============================================================================
# 图片风格枚举
# ============================================================================

class ImageStyle(str, Enum):
    """图片视觉风格"""
    PHOTO = "photo"              # 实拍照片
    SCHEMATIC = "schematic"      # 原理图/示意图
    DIAGRAM = "diagram"          # 流程图/框图
    ICON = "icon"                # 图标
    WARNING = "warning"          # 警示图标
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
    TRANSPARENT_BG = "transparent_bg"  # 透明背景
    WHITE_BG = "white_bg"              # 白色背景
    NO_CONSTRAINT = "no_constraint"    # 无约束


# ============================================================================
# 图片插槽请求 (传递给 3.6 RAG 模块)
# ============================================================================

class ImageSlotRequest(BaseModel):
    """图片插槽请求 - 传递给 3.6 RAG 模块"""
    
    # === 唯一标识 ===
    slot_id: str = Field(description="插槽唯一ID")
    page_index: int = Field(description="所属页面索引")
    
    # === 语义信息 (核心!) ===
    theme: str = Field(description="主题描述,如'液压系统原理图'")
    keywords: List[str] = Field(default_factory=list, description="关键词列表")
    context: str = Field(default="", description="上下文描述(来自页面标题和内容)")
    
    # === 视觉约束 ===
    visual_style: ImageStyle = Field(default=ImageStyle.PHOTO, description="期望的图片风格")
    aspect_ratio: AspectRatio = Field(default=AspectRatio.STANDARD, description="期望宽高比")
    color_constraint: ColorConstraint = Field(default=ColorConstraint.NO_CONSTRAINT, description="颜色约束")
    min_resolution: tuple[int, int] = Field(default=(800, 600), description="最小分辨率(宽,高)")
    
    # === 布局位置 ===
    layout_position: str = Field(description="在布局中的位置,如'right_half'")
    x: float = Field(ge=0, le=1, description="归一化 x 坐标")
    y: float = Field(ge=0, le=1, description="归一化 y 坐标")
    w: float = Field(ge=0, le=1, description="归一化宽度")
    h: float = Field(ge=0, le=1, description="归一化高度")
    
    # === 优先级和备选 ===
    priority: int = Field(default=1, ge=1, le=5, description="匹配优先级(1最高)")
    fallback_query: Optional[str] = Field(default=None, description="备用查询(英文)")
    
    # === 3.6 模块填充字段 ===
    matched_image_url: Optional[str] = Field(default=None, description="匹配到的图片URL")
    matched_score: Optional[float] = Field(default=None, description="匹配置信度")
    caption: Optional[str] = Field(default=None, description="图注")
    
    def to_rag_query(self) -> dict:
        """生成 RAG 查询参数"""
        return {
            "query": f"{self.theme} {' '.join(self.keywords)}",
            "filters": {
                "style": self.visual_style.value,
                "min_width": self.min_resolution[0],
                "min_height": self.min_resolution[1],
                "color_constraint": self.color_constraint.value,
            },
            "context": self.context,
            "top_k": 3,
            "fallback_query": self.fallback_query,
        }


# ============================================================================
# 布局配置
# ============================================================================

class LayoutConfig(BaseModel):
    """布局模板配置"""
    
    layout_id: str = Field(description="布局唯一标识")
    display_name: str = Field(description="显示名称")
    description: str = Field(description="布局说明")
    
    # === CSS Grid 定义 ===
    grid_template_areas: str = Field(description="CSS grid-template-areas")
    grid_template_columns: str = Field(default="1fr", description="列定义")
    grid_template_rows: str = Field(default="auto", description="行定义")
    gap: str = Field(default="2rem", description="间距")
    
    # === 图片插槽配置 ===
    image_slots: List[Dict[str, Any]] = Field(default_factory=list, description="图片插槽位置定义")
    
    # === 适用场景 ===
    suitable_slide_types: List[str] = Field(default_factory=list, description="适用的 slide_type")
    suitable_keywords: List[str] = Field(default_factory=list, description="适用的关键词")
    
    # === 约束条件 ===
    max_bullets: Optional[int] = Field(default=None, description="最大要点数")
    max_text_length: Optional[int] = Field(default=None, description="最大文本长度")


# ============================================================================
# 渲染结果
# ============================================================================

class RenderResult(BaseModel):
    """3.5 模块渲染结果"""
    
    session_id: str
    html_path: str = Field(description="生成的 HTML 文件路径")
    html_content: Optional[str] = Field(default=None, description="HTML 内容(可选)")
    
    # === 给 3.6 模块的数据 ===
    image_slots: List[ImageSlotRequest] = Field(default_factory=list, description="图片插槽列表")
    
    # === 元数据 ===
    metadata: Dict[str, Any] = Field(default_factory=dict, description="渲染元数据")
    warnings: List[str] = Field(default_factory=list, description="警告信息")
    
    # 统计信息
    total_pages: int = 0
    layouts_used: Dict[str, int] = Field(default_factory=dict, description="使用的布局统计")
