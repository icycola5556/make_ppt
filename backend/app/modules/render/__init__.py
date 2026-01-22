"""
Module 3.5: 智能排版与动态渲染引擎
"""

from .schemas import (
    ImageSlotRequest,
    ImageSlotResult,
    RenderResult,
    LayoutConfig,
    ImageStyle,
    AspectRatio,
    ColorConstraint,
)
from .html_renderer import render_html_slides
from .layout_configs import VOCATIONAL_LAYOUTS
from .image_filler import ImageFiller

__all__ = [
    "ImageSlotRequest",
    "ImageSlotResult",
    "RenderResult",
    "LayoutConfig",
    "ImageStyle",
    "AspectRatio",
    "ColorConstraint",
    "render_html_slides",
    "VOCATIONAL_LAYOUTS",
    "ImageFiller",
]
