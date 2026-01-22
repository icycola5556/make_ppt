"""
Module 3.5: Render 模块入口
"""
from .core import RenderResult, ImageSlotRequest, ImageSlotResult
from .renderer import HTMLRenderer
from .services import ImageService

# 为了保持向后兼容，或者提供便捷函数
# 我们可以简单包装一下 HTMLRenderer.render
async def render_html_slides(*args, **kwargs):
    return await HTMLRenderer.render(*args, **kwargs)

# 导出为了类型提示
__all__ = [
    "render_html_slides",
    "HTMLRenderer",
    "ImageService",
    "RenderResult",
    "ImageSlotRequest",
    "ImageSlotResult",
]
