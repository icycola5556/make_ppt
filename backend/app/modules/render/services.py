"""
Module 3.5: 图片生成服务 (Services)
负责调用 DashScope API 生成图片，管理缓存和重试逻辑。
"""
import asyncio
import hashlib
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from http import HTTPStatus

import requests
from dashscope import ImageSynthesis

# Imports from common
from ...common.schemas import TeachingRequest, StyleConfig

# Imports from local core
from .core import ImageSlotRequest, ImageSlotResult, AspectRatio, ImageStyle

logger = logging.getLogger(__name__)

class ImageService:
    """
    图片生成服务
    职责：
    1. 综合上下文组装提示词
    2. 调用百炼 API (qwen-image-plus)
    3. 管理 MD5 缓存
    """

    SUBJECT_STYLE_MAP = {
        "机械": {
            "style_hint": "技术原理图风格，线条清晰，标注规范，符合机械制图标准",
            "aspect_ratio": "4:3",
        },
        "电气": {
            "style_hint": "电路图风格，元件符号符合国家标准，连接线清晰",
            "aspect_ratio": "16:9",
        },
        "电子": {
            "style_hint": "电子电路风格，原理图布局合理，标注完整",
            "aspect_ratio": "16:9",
        },
        "化学": {
            "style_hint": "化学方程式示意图，化学符号清晰准确，反应条件标注明确",
            "aspect_ratio": "4:3",
        },
        "生物": {
            "style_hint": "生物学插画风格，细胞器结构准确，颜色区分明显",
            "aspect_ratio": "4:3",
        },
        "物理": {
            "style_hint": "物理原理图风格，力学/电磁学/光学图示规范",
            "aspect_ratio": "16:9",
        },
        "建筑": {
            "style_hint": "建筑效果渲染图风格，专业建筑设计效果图",
            "aspect_ratio": "16:9",
        },
        "土木": {
            "style_hint": "土木工程图风格，施工图/结构图规范制图",
            "aspect_ratio": "16:9",
        },
        "医学": {
            "style_hint": "医学解剖图风格，结构准确，专业标注，符合医学教学标准",
            "aspect_ratio": "4:3",
        },
        "计算机": {
            "style_hint": "技术架构图/流程图风格，UML或系统设计图规范",
            "aspect_ratio": "16:9",
        },
        "数学": {
            "style_hint": "数学几何图形风格，图形准确，标注清晰，适合教学演示",
            "aspect_ratio": "4:3",
        },
        "会计": {
            "style_hint": "财务报表/流程图风格，数据清晰，表格规范，专业财务风格",
            "aspect_ratio": "16:9",
        },
        "物流": {
            "style_hint": "物流流程图/示意图风格，流程清晰，节点明确",
            "aspect_ratio": "16:9",
        },
    }

    STYLE_NAME_MAP = {
        "theory_clean": {
            "color_style": "简洁专业的配色，白色或浅灰色背景",
            "visual_style": "教学课件插图风格",
        },
        "practice_steps": {
            "color_style": "实训操作配色，对比明显，步骤区分清晰",
            "visual_style": "操作演示图风格，包含步骤编号和说明",
        },
        "review_mindmap": {
            "color_style": "知识图谱配色，层次分明，重点突出",
            "visual_style": "思维导图风格，结构化展示",
        },
    }

    def __init__(self, api_key: str, cache_dir: str = "outputs/images_cache"):
        self.api_key = api_key
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"ImageService initialized with cache_dir: {self.cache_dir}")

    def build_prompt(
        self,
        slot: ImageSlotRequest,
        teaching_request: TeachingRequest,
        style_config: StyleConfig,
    ) -> str:
        prompt_parts = []

        # 优先级1：如果插槽的context包含完整的已有prompt，直接使用
        if slot.context and len(slot.context) > 30:
            base_prompt = slot.context
        else:
            # 优先级2：插槽的主题
            prompt_parts.append(f"主题：{slot.theme}")

            # 优先级3：学科专业风格
            subject_name = teaching_request.subject_info.subject_name
            subject_style = self.SUBJECT_STYLE_MAP.get(subject_name, {})

            if subject_style:
                prompt_parts.append(subject_style.get("style_hint", ""))
                # 如果插槽没有指定aspect_ratio，从学科映射获取
                if slot.aspect_ratio.value == "4:3":
                    aspect = subject_style.get("aspect_ratio", "4:3")
                    if aspect != "4:3":
                        slot.aspect_ratio = AspectRatio(aspect)

            prompt_parts.append(f"专业领域：{subject_name}")

            # 优先级4：风格配置
            style_name = style_config.style_name
            if style_name in self.STYLE_NAME_MAP:
                style_info = self.STYLE_NAME_MAP[style_name]
                prompt_parts.append(f"配色风格：{style_info['color_style']}")
                prompt_parts.append(f"视觉风格：{style_info['visual_style']}")
            else:
                if style_config.color:
                    if style_config.color.primary:
                        prompt_parts.append(f"主色调：{style_config.color.primary}色系")
                    if style_config.color.accent:
                        prompt_parts.append(f"强调色：{style_config.color.accent}色系")

            # 优先级5：插槽关键词
            if slot.keywords:
                prompt_parts.append(f"关键元素：{', '.join(slot.keywords[:5])}")

            # 优先级6：visual_style特定指令
            visual_style_hints = {
                "photo": "真实摄影风格，高清晰度，专业布光",
                "schematic": "技术原理图风格，标注规范，线条清晰，专业的工程图纸风格",
                "diagram": "流程图/框图风格，结构清晰，层次分明，矢量图形风格",
                "icon": "图标风格，简洁现代，扁平化设计",
                "warning": "警示图标风格，醒目标识，安全标准配色",
                "illustration": "教学插画风格，色彩鲜明，风格统一，易于理解",
            }
            hint = visual_style_hints.get(slot.visual_style.value, "专业配图风格")
            prompt_parts.append(hint)

            # 优先级7：通用质量要求
            prompt_parts.append("高清细节，专业品质，无水印，适合教学使用")

            base_prompt = "，".join([p for p in prompt_parts if p])

        # 构图要求
        aspect_prompts = {
            "16:9": "横向宽屏构图，全景展示，适合对比说明",
            "9:16": "纵向构图，单主角展示",
            "4:3": "标准教材配图构图，信息量适中",
            "1:1": "正方形构图，适合网格布局",
            "21:9": "超宽横向构图，适合时间线或流程展示",
        }
        aspect_hint = aspect_prompts.get(slot.aspect_ratio.value, "")
        if aspect_hint:
            base_prompt = f"{base_prompt}，{aspect_hint}"

        return base_prompt

    def _map_ratio_to_size(self, aspect_ratio: str) -> str:
        """根据长宽比映射到 DashScope 支持的分辨率"""
        if aspect_ratio in ["16:9", "4:3"]:
            return "1280*720"
        elif aspect_ratio in ["9:16", "3:4"]:
            return "720*1280"
        else:
            return "1024*1024"

    def generate_image(self, prompt: str, slot_id: str, slot_data: Dict = None) -> Optional[str]:
        """同步生成单张图片"""
        logger.info(f"[IMG_GEN_START] slot={slot_id}, api_key={'SET' if self.api_key else 'MISSING'}")
        
        if not self.api_key:
            logger.error(f"[IMG_GEN_FATAL] No API key configured for slot {slot_id}")
            return None
        
        # 1. MD5缓存检查
        prompt_hash = hashlib.md5(prompt.encode("utf-8")).hexdigest()
        cache_path = self.cache_dir / f"{prompt_hash}.png"
        
        if cache_path.exists():
            logger.info(f"[CACHE HIT] Image for slot {slot_id} at {cache_path}")
            return str(cache_path)

        # 2. 调用API
        logger.info(f"[CACHE MISS] Generating image for slot {slot_id}")
        
        try:
            aspect_ratio = "4:3"
            if slot_data and "aspect_ratio" in slot_data:
                ar = slot_data["aspect_ratio"]
                if hasattr(ar, "value"):
                    aspect_ratio = ar.value
                else:
                    aspect_ratio = str(ar)
            
            size = self._map_ratio_to_size(aspect_ratio)
            logger.info(f"[IMG_GEN] Calling DashScope: size={size}, ratio={aspect_ratio}")
            
            response = ImageSynthesis.call(
                api_key=self.api_key,
                model="qwen-image-plus",
                prompt=prompt,
                n=1,
                size=size,
            )

            if response.status_code == HTTPStatus.OK:
                if response.output and response.output.results:
                    image_url = response.output.results[0].url
                    
                    if not image_url:
                        return None

                    # 3. 下载图片
                    img_response = requests.get(image_url, timeout=60)
                    img_response.raise_for_status()
                    
                    # 4. 保存到缓存
                    with open(cache_path, "wb") as f:
                        f.write(img_response.content)

                    logger.info(f"[IMG_GEN_SUCCESS] Image saved to {cache_path}")
                    return str(cache_path)
            else:
                logger.error(f"[IMG_GEN_ERROR] API error: {response.code} {response.message}")

        except Exception as e:
            logger.exception(f"[IMG_GEN_FATAL] Error for slot {slot_id}: {e}")

        return None

    async def generate_for_slots(
        self,
        slots: List[ImageSlotRequest],
        teaching_request: TeachingRequest,
        style_config: StyleConfig,
    ) -> List[ImageSlotResult]:
        """批量生成图片 (Async)"""
        results = []
        for slot in slots:
            start_time = time.time()
            result = ImageSlotResult(
                slot_id=slot.slot_id,
                page_index=slot.page_index,
                status="generating",
                prompt="",
            )

            try:
                # 生成prompt
                prompt = self.build_prompt(slot, teaching_request, style_config)
                result.prompt = prompt

                # 准备 slot_data
                slot_data = slot.model_dump() if hasattr(slot, "model_dump") else slot.__dict__
                
                # 在线程池中执行同步生成
                image_path = await asyncio.to_thread(
                    self.generate_image, 
                    prompt=prompt, 
                    slot_id=slot.slot_id,
                    slot_data=slot_data
                )

                if image_path:
                    result.status = "done"
                    result.image_path = image_path
                    result.generated_at = datetime.utcnow()
                    result.generation_time_seconds = time.time() - start_time
                    result.cache_hit = False
                else:
                    result.status = "failed"
                    result.error = "Image generation failed"

            except Exception as e:
                result.status = "failed"
                result.error = str(e)
                logger.exception(f"Failed to generate slot {slot.slot_id}")

            results.append(result)
        return results

    def generate_for_slots_sync(
        self,
        slots: List[ImageSlotRequest],
        teaching_request: TeachingRequest,
        style_config: StyleConfig,
    ) -> List[ImageSlotResult]:
        """批量生成图片 (Sync version for background tasks)"""
        results = []
        for slot in slots:
            start_time = time.time()
            result = ImageSlotResult(
                slot_id=slot.slot_id,
                page_index=slot.page_index,
                status="generating",
                prompt="",
            )

            try:
                # 生成prompt
                prompt = self.build_prompt(slot, teaching_request, style_config)
                result.prompt = prompt

                # 准备 slot_data
                slot_data = slot.model_dump() if hasattr(slot, "model_dump") else slot.__dict__
                
                # 直接同步执行
                image_path = self.generate_image(
                    prompt=prompt, 
                    slot_id=slot.slot_id,
                    slot_data=slot_data
                )

                if image_path:
                    result.status = "done"
                    result.image_path = image_path
                    result.generated_at = datetime.utcnow()
                    result.generation_time_seconds = time.time() - start_time
                    result.cache_hit = False
                else:
                    result.status = "failed"
                    result.error = "Image generation failed"

            except Exception as e:
                result.status = "failed"
                result.error = str(e)
                logger.exception(f"Failed to generate slot {slot.slot_id}")

            results.append(result)
        return results

    def clear_cache(self, older_than_days: int = 7) -> int:
        """清理过期缓存"""
        cutoff = time.time() - (older_than_days * 24 * 60 * 60)
        removed = 0
        for cache_file in self.cache_dir.glob("*.png"):
            if cache_file.stat().st_mtime < cutoff:
                cache_file.unlink()
                removed += 1
        return removed
