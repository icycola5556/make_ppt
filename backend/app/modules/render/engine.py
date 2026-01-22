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
        llm: Optional[LLMClient] = None
    ) -> Tuple[str, List[ImageSlotRequest]]:
        """主入口：决定布局并生成插槽"""
        
        # 1. 快速路径：基于 slide_type 强制映射
        layout_id = LayoutEngine._map_by_slide_type(page.slide_type)
        if layout_id:
            return layout_id, LayoutEngine._generate_image_slots(page, layout_id, page_index)

        # 2. 智能路径：LLM 分析 或 规则打分
        if llm and llm.is_enabled():
            try:
                layout_id = await LayoutEngine._analyze_with_llm(page, teaching_request, llm, previous_layout)
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
    def _generate_image_slots(page: SlidePage, layout_id: str, page_index: int) -> List[ImageSlotRequest]:
        """生成并去重图片插槽"""
        layout_config = VOCATIONAL_LAYOUTS.get(layout_id)
        if not layout_config or not layout_config.image_slots:
            return []

        # 1. 生成原始插槽
        slots = []
        for i, slot_def in enumerate(layout_config.image_slots):
            theme = LayoutEngine._extract_theme_from_page(page, slot_def)
            keywords = LayoutEngine._extract_keywords(page.title, theme)
            context = LayoutEngine._build_context(page)
            vis_style = LayoutEngine._infer_visual_style(page.slide_type, slot_def)
            
            slot = ImageSlotRequest(
                slot_id=f"page{page_index}_slot{i}",
                page_index=page_index,
                theme=theme,
                keywords=keywords,
                context=context,
                visual_style=vis_style,
                aspect_ratio=AspectRatio(slot_def.get("aspect_ratio", "4:3")),
                layout_position=slot_def["position"],
                x=slot_def["x"],
                y=slot_def["y"],
                w=slot_def["w"],
                h=slot_def["h"],
                priority=slot_def.get("priority", 1),
            )
            slots.append(slot)

        # 2. 去重逻辑 (防止四宫格生成重复图片)
        seen_prompts = set()
        fallback_bullets = []
        for elem in page.elements:
            if elem.type == "bullets" and isinstance(elem.content, dict):
                items = elem.content.get("items", [])
                fallback_bullets.extend([str(i) for i in items])
        
        for i, slot in enumerate(slots):
            current_prompt = slot.context or slot.theme or (page.title if page.title else "")
            
            is_duplicate = current_prompt in seen_prompts
            is_default_title = current_prompt == page.title
            
            if (is_duplicate or is_default_title) and i < len(fallback_bullets):
                # 使用要点生成独特Prompt
                bullet_text = fallback_bullets[i]
                clean_bullet = bullet_text[:50].replace("\n", " ")
                
                new_prompt = f"{page.title} 特写: {clean_bullet}"
                slot.context = new_prompt
                slot.theme = f"{page.title} - {clean_bullet[:15]}..."
                slot.keywords = [page.title, "特写", clean_bullet[:5]]
                
                seen_prompts.add(new_prompt)
            else:
                seen_prompts.add(current_prompt)
                
        return slots

    # === Helper Methods (Originally from placeholder_generator.py & layout_engine.py) ===

    @staticmethod
    def _extract_theme_from_page(page: SlidePage, slot_def: dict) -> str:
        for elem in page.elements:
            if elem.type in ["image", "diagram", "chart"]:
                if isinstance(elem.content, dict) and elem.content.get("placeholder"):
                    return elem.content.get("theme", page.title)
        return page.title

    @staticmethod
    def _extract_keywords(title: str, theme: str) -> List[str]:
        text = f"{title} {theme}"
        words = jieba.cut(text, cut_all=False)
        stopwords = {"的", "是", "和", "与", "或", "在", "了", "有", "为", "以", "及", "等", "中"}
        keywords = [w for w in words if len(w) > 1 and w not in stopwords]
        return list(set(keywords))[:5]

    @staticmethod
    def _build_context(page: SlidePage) -> str:
        parts = [page.title]
        for elem in page.elements:
            if elem.type == "bullets" and isinstance(elem.content, dict):
                items = elem.content.get("items", [])
                parts.extend(items[:3])
        return " | ".join(parts)

    @staticmethod
    def _infer_visual_style(slide_type: str, slot_def: dict) -> ImageStyle:
        if "default_style" in slot_def:
            return ImageStyle(slot_def["default_style"])
        STYLE_MAP = {
            "concept": ImageStyle.SCHEMATIC,
            "steps": ImageStyle.DIAGRAM,
            "warning": ImageStyle.WARNING,
            "cover": ImageStyle.ILLUSTRATION,
            "title": ImageStyle.ILLUSTRATION,
        }
        return STYLE_MAP.get(slide_type, ImageStyle.PHOTO)

    @staticmethod
    def _map_by_slide_type(slide_type: str) -> Optional[str]:
        TYPE_LAYOUT_MAP = {
            "title": "title_only",
            "cover": "title_only",
            "bridge": "title_only",
            "objectives": "title_bullets",
            "summary": "title_bullets",
            "agenda": "title_bullets",
        }
        return TYPE_LAYOUT_MAP.get(slide_type)

    @staticmethod
    def _match_by_keywords(page: SlidePage) -> Optional[str]:
        title_text = page.title.lower() if page.title else ""
        content_text = " ".join([str(e.content) for e in page.elements]).lower()
        full_text = f"{title_text} {content_text}"
        
        KEYWORD_PATTERNS = {
            "operation_steps": ["步骤", "操作", "流程", "方法", "怎么做", "如何", "实训"],
            "concept_comparison": ["对比", "区别", "正确", "错误", "vs", "比较", "优缺点"],
            "grid_4": ["工具", "设备", "部件", "类型", "分类"],
        }
        for lid, kws in KEYWORD_PATTERNS.items():
            if any(k in full_text for k in kws):
                return lid
        return None

    @staticmethod
    def _find_alternative_layout(current: str) -> str:
        ALTERNATIVES = {
            "title_bullets_right_img": ["center_visual", "split_vertical", "operation_steps"],
            "operation_steps": ["timeline_horizontal", "title_bullets_right_img", "split_vertical"],
            "concept_comparison": ["table_comparison", "grid_4", "center_visual"],
            "grid_4": ["concept_comparison", "center_visual", "split_vertical"],
            "title_bullets": ["title_bullets_right_img", "table_comparison", "center_visual"],
            "table_comparison": ["concept_comparison", "title_bullets", "grid_4"],
            "timeline_horizontal": ["operation_steps", "title_bullets", "split_vertical"],
            "center_visual": ["title_bullets_right_img", "split_vertical", "operation_steps"],
            "split_vertical": ["center_visual", "title_bullets_right_img", "operation_steps"],
        }
        candidates = ALTERNATIVES.get(current, ["title_bullets_right_img"])
        # 简单返回第一个存在的
        for alt in candidates:
            if alt in VOCATIONAL_LAYOUTS:
                return alt
        return "title_bullets"

    @staticmethod
    def _check_text_overflow_and_downgrade(page: SlidePage, layout_id: Optional[str]) -> str:
        if not layout_id: return "title_bullets"
        config = VOCATIONAL_LAYOUTS.get(layout_id)
        if not config: return "title_bullets"

        # 1. 标题长度
        if len(page.title or "") > 45 and layout_id != "title_only":
            return "title_bullets"

        # 2. 总字数
        text_len = calculate_text_length(page)
        max_len = {
            "title_bullets_right_img": 450,
            "operation_steps": 300,
            "concept_comparison": 250,
            "grid_4": 200,
            "split_vertical": 500,
            "center_visual": 200,
        }.get(layout_id, 500)

        if text_len > max_len + 50:
            return "title_bullets"
        return layout_id

    @staticmethod
    def _score_and_select(page: SlidePage, req: TeachingRequest, previous_layout: Optional[str] = None) -> str:
        # 简化版打分逻辑
        text_len = calculate_text_length(page)
        has_bullets = any(e.type == "bullets" for e in page.elements)
        bullet_count = sum(len(e.content.get("items", [])) for e in page.elements if e.type == "bullets")
        image_count = sum(1 for e in page.elements if e.type in ["image", "diagram", "chart"])
        
        scores = {lid: 0 for lid in VOCATIONAL_LAYOUTS.keys()}
        
        # 场景加分
        if req.teaching_scene == "practice":
            scores["operation_steps"] += 50
            scores["timeline_horizontal"] += 30
        elif req.teaching_scene == "theory":
            scores["title_bullets_right_img"] += 30
            scores["table_comparison"] += 25
            
        # 图片数量规则
        if image_count == 1:
            if text_len < 120:
                scores["center_visual"] += 80
                scores["title_bullets_right_img"] += 40
            elif text_len > 400:
                scores["split_vertical"] += 100
                scores["title_bullets"] += 60
                scores["title_bullets_right_img"] -= 50
            else:
                scores["title_bullets_right_img"] += 60
        elif image_count >= 4:
            scores["grid_4"] += 100
        elif image_count >= 2:
            scores["concept_comparison"] += 60
            
        # 历史惩罚
        if previous_layout and previous_layout in scores:
            scores[previous_layout] -= 80
            
        return max(scores, key=scores.get)

    @staticmethod
    async def _analyze_with_llm(page: SlidePage, req: TeachingRequest, llm: LLMClient, prev: Optional[str]) -> Optional[str]:
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
        
        response, _ = await llm.chat_json(LAYOUT_AGENT_SYSTEM_PROMPT, user_msg, LAYOUT_SCHEMA)
        lid = response.get("selected_layout_id")
        if lid in VOCATIONAL_LAYOUTS:
            return lid
        return None
