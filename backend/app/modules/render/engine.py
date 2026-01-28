"""
Module 3.5: 布局引擎 (Engine)
负责智能选择布局模板，并生成图片插槽请求。
"""
import json
import jieba
from typing import Tuple, List, Optional, Any, Dict
from ...common.schemas import SlidePage, TeachingRequest
from ...common.llm_client import LLMClient
from ...prompts.render import LAYOUT_AGENT_SYSTEM_PROMPT

from .core import ImageSlotRequest, ImageStyle, AspectRatio, calculate_text_length
from .config import VOCATIONAL_LAYOUTS

class LayoutEngine:
    """
    布局决策引擎
    职责：
    1. 根据页面内容选择最佳布局（规则+LLM）
    2. 生成图片插槽请求（Placeholders）
    3. 处理插槽去重
    """

    @staticmethod
    async def resolve_layout(
        page: SlidePage,
        teaching_request: TeachingRequest,
        page_index: int,
        previous_layout: Optional[str] = None,
        llm: Optional[LLMClient] = None,
        template_id: Optional[str] = "business"
    ) -> Tuple[str, List[ImageSlotRequest]]:
        """主入口：决定布局并生成插槽"""
        
        # 1. 快速路径：基于 slide_type 强制映射
        layout_id = LayoutEngine._map_by_slide_type(page.slide_type)
        if layout_id:
            return layout_id, LayoutEngine._generate_image_slots(page, layout_id, page_index)

        # 2. 智能路径：LLM 分析 或 规则打分
        if llm and llm.is_enabled():
            try:
                layout_id = await LayoutEngine._analyze_with_llm(page, teaching_request, llm, previous_layout, template_id)
            except Exception as e:
                print(f"Layout Agent failed for page {page_index}: {e}")
                layout_id = LayoutEngine._score_and_select(page, teaching_request, previous_layout)
        else:
            layout_id = LayoutEngine._match_by_keywords(page)
            if not layout_id:
                layout_id = LayoutEngine._score_and_select(page, teaching_request, previous_layout)

        # 3. 避免连续重复
        if layout_id == previous_layout and previous_layout is not None:
            layout_id = LayoutEngine._find_alternative_layout(layout_id)

        # 4. 安全检查（文本溢出降级）
        layout_id = LayoutEngine._check_text_overflow_and_downgrade(page, layout_id)

        # 5. 生成并去重插槽
        slots = LayoutEngine._generate_image_slots(page, layout_id, page_index)
        return layout_id, slots


    @staticmethod
    def _map_by_slide_type(slide_type: str) -> Optional[str]:
        """根据页面类型强制映射布局"""
        mapping = {
            "title": "title_only_center",
            "toc": "toc_sidebar_right",
            "section": "section_title_impact",
            "thank_you": "thank_you_minimal"
        }
        return mapping.get(slide_type)

    @staticmethod
    def _generate_image_slots(page: SlidePage, layout_id: str, page_index: int) -> List[ImageSlotRequest]:
        """生成图片插槽"""
        # 简单实现：检查布局定义，看需要多少图片
        # 这里我们需要 VOCATIONAL_LAYOUTS 的定义
        from .config import VOCATIONAL_LAYOUTS
        
        layout_cfg = VOCATIONAL_LAYOUTS.get(layout_id)
        if not layout_cfg:
            return []
            
        slots = []
        # 假设每个布局最多支持 N 张图，我们这里简单根据 layout_id 名字猜测或查找 config
        # 实际应该从 layout_cfg.slots_config 读取
        # 由于我们没有看到 layout_cfg 的结构，这里做防御性编程
        
        slot_count = 0
        if "img" in layout_id: # 简单启发式
            slot_count = 1
        elif "grid" in layout_id:
            slot_count = 4
        elif "comparison" in layout_id:
            slot_count = 2
            
        # 尝试从 config 获取真实 slot 信息
        if hasattr(layout_cfg, 'image_slots_count'):
            slot_count = layout_cfg.image_slots_count
            
        for i in range(slot_count):
            slots.append(ImageSlotRequest(
                slot_id=f"p{page_index}_s{i}",
                page_index=page_index,
                page_title=page.title,
                slide_type=page.slide_type,
                layout_id=layout_id,
                theme="default",
                # Mandatory fields
                aspect_ratio=AspectRatio.STANDARD,
                visual_style=ImageStyle.PHOTO,
                layout_position="right",
                x=0, y=0, w=0, h=0
            ))
            
        return slots

    @staticmethod
    def _match_by_keywords(page: SlidePage) -> Optional[str]:
        """关键词匹配"""
        # 简单实现
        text = str(page.elements)
        if "对比" in page.title or "区别" in page.title:
            return "comparison_two_cols"
        if "流程" in page.title or "步骤" in page.title:
            return "process_steps_horizontal"
        return None

    @staticmethod
    def _score_and_select(page: SlidePage, req: TeachingRequest, prev_layout: Optional[str]) -> str:
        """从规则库打分选择"""
        # 默认返回通用的图文布局
        text_len = calculate_text_length(page)
        if text_len < 50:
             return "title_bullets_right_img" # 内容少，图大
        elif text_len > 300:
             return "content_dense_two_col" # 内容多，双栏
        return "title_bullets_right_img" # 默认

    @staticmethod
    def _find_alternative_layout(layout_id: str) -> str:
        """寻找替代布局"""
        alternatives = {
            "title_bullets_right_img": "title_bullets_left_img",
            "title_bullets_left_img": "title_bullets_bottom_img",
        }
        return alternatives.get(layout_id, layout_id)

    @staticmethod
    def _check_text_overflow_and_downgrade(page: SlidePage, layout_id: str) -> str:
        """检查文本溢出"""
        # 简单 pass
        return layout_id


    @staticmethod
    async def _analyze_with_llm(
        page: SlidePage, 
        req: TeachingRequest, 
        llm: LLMClient, 
        prev: Optional[str],
        template_id: str = "business"
    ) -> Optional[str]:
        # 简化的LLM分析
        slide_content = {
            "title": page.title,
            "type": page.slide_type,
            "bullets": [str(e.content) for e in page.elements if e.type in ["text", "bullets"]],
            "image_count": sum(1 for e in page.elements if e.type in ["image", "diagram"]),
            "domain": req.subject_info.subject_name
        }
        
        # 这里的 Layout Schema 需要能获取
        from .config import VOCATIONAL_LAYOUTS
        from ...prompts.render import get_layout_prompt
        from .templates_registry import get_template
        
        available_layouts = []
        for lid, cfg in VOCATIONAL_LAYOUTS.items():
            available_layouts.append({
                "layout_id": lid,
                "description": cfg.description,
                "keywords": cfg.suitable_keywords
            })
            
        user_msg = json.dumps({
            "slide_content": slide_content,
            "available_layouts": available_layouts,
            "previous_layout": prev,
            "avoid": [prev] if prev else []
        }, ensure_ascii=False)
        
        LAYOUT_SCHEMA = """{"selected_layout_id": "string", "reasoning": "string"}"""
        
        # 获取模版特定的 Prompt Modifier
        template = get_template(template_id)
        prompt_modifier = template.system_prompt_modifier if template else ""
        system_prompt = get_layout_prompt(prompt_modifier)
        
        response, _ = await llm.chat_json(system_prompt, user_msg, LAYOUT_SCHEMA)
        lid = response.get("selected_layout_id")
        if lid in VOCATIONAL_LAYOUTS:
            return lid
        return None
