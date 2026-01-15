"""
Module 3.5: 智能排版与动态渲染引擎
"""

from .schemas import (
    ImageSlotRequest,
    RenderResult,
    LayoutConfig,
    ImageStyle,
    AspectRatio,
    ColorConstraint,
)
from .html_renderer import render_html_slides
from .layout_configs import VOCATIONAL_LAYOUTS

__all__ = [
    "ImageSlotRequest",
    "RenderResult",
    "LayoutConfig",
    "ImageStyle",
    "AspectRatio",
    "ColorConstraint",
    "render_html_slides",
    "VOCATIONAL_LAYOUTS",
]
