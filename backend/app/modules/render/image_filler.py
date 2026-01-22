"""
Module 3.5: 图片填充器

基于 3.1-3.4 模块的上下文，调用百炼 API 生成教学配图。
核心功能：
1. 综合 TeachingRequest、StyleConfig、ImageSlotRequest 组装提示词
2. 调用 qwen-image-max 模型生成图片
3. MD5 缓存管理
4. 后台任务管理
"""

import asyncio
import hashlib
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
from dashscope import ImageSynthesis
from pydantic import BaseModel, Field
from http import HTTPStatus

from ...common.schemas import TeachingRequest, StyleConfig
from .schemas import ImageSlotRequest, AspectRatio, ImageStyle

logger = logging.getLogger(__name__)


class ImageSlotResult(BaseModel):
    """图片生成结果"""

    slot_id: str = Field(description="插槽ID")
    page_index: int = Field(description="页面索引")
    status: str = Field(
        default="pending", description="状态: pending/generating/done/failed/skipped"
    )
    prompt: str = Field(default="", description="使用的提示词")
    image_path: Optional[str] = Field(default=None, description="生成的图片路径")
    error: Optional[str] = Field(default=None, description="错误信息")
    generated_at: Optional[datetime] = Field(default=None, description="生成时间")

    model_used: str = Field(default="qwen-image-max", description="使用的模型")
    generation_time_seconds: Optional[float] = Field(
        default=None, description="生成耗时"
    )
    cache_hit: bool = Field(default=False, description="是否命中缓存")


class ImageFiller:
    """
    图片填充器 - 3.5模块核心

    职责：
    1. 综合 3.1-3.4 上下文组装提示词
    2. 调用百炼 API 生成图片
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
        """
        初始化图片填充器

        Args:
            api_key: 百炼 API Key
            cache_dir: 图片缓存目录
        """
        self.api_key = api_key
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"ImageFiller initialized with cache_dir: {self.cache_dir}")

    def build_prompt(
        self,
        slot: ImageSlotRequest,
        teaching_request: TeachingRequest,
        style_config: StyleConfig,
    ) -> str:
        """
        综合 3.1-3.4 上下文组装完整提示词

        输入来源：
        - 3.1 TeachingRequest.subject_info（学科专业风格）
        - 3.2 StyleConfig（颜色+风格配置）
        - 3.5 ImageSlotRequest（插槽主题+关键词）
        - 3.4 page.elements[].content（已有prompt/描述）

        优先级：
        1. 页面元素中的 existing_prompt（3.4最高优先级）
        2. 插槽的theme（3.5）
        3. 学科专业风格（3.1）
        4. PPT整体风格配置（3.2）
        """
        prompt_parts = []

        # 优先级1：如果插槽的context包含完整的已有prompt，直接使用
        if slot.context and len(slot.context) > 30:
            base_prompt = slot.context
        else:
            # 优先级2：插槽的主题（基础）
            prompt_parts.append(f"主题：{slot.theme}")

            # 优先级3：学科专业风格（3.1 TeachingRequest）
            subject_name = teaching_request.subject_info.subject_name
            subject_style = self.SUBJECT_STYLE_MAP.get(subject_name, {})

            if subject_style:
                prompt_parts.append(subject_style.get("style_hint", ""))

                # 如果插槽没有指定aspect_ratio，从学科映射获取
                if slot.aspect_ratio.value == "4:3":
                    aspect = subject_style.get("aspect_ratio", "4:3")
                    if aspect != "4:3":
                        slot.aspect_ratio = AspectRatio(aspect)

            # 添加学科关键词
            prompt_parts.append(f"专业领域：{subject_name}")

            # 优先级4：风格配置（3.2 StyleConfig）
            style_name = style_config.style_name

            if style_name in self.STYLE_NAME_MAP:
                style_info = self.STYLE_NAME_MAP[style_name]
                prompt_parts.append(f"配色风格：{style_info['color_style']}")
                prompt_parts.append(f"视觉风格：{style_info['visual_style']}")
            else:
                # 通用风格配置
                if style_config.color:
                    if style_config.color.primary:
                        prompt_parts.append(f"主色调：{style_config.color.primary}色系")
                    if style_config.color.accent:
                        prompt_parts.append(f"强调色：{style_config.color.accent}色系")

            # 优先级5：插槽的关键词
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

            # 组装
            base_prompt = "，".join([p for p in prompt_parts if p])

        # 根据aspect_ratio添加构图要求
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

    def _get_size_for_aspect_ratio(self, aspect_ratio: str) -> str:
        """将aspect_ratio转换为DashScope尺寸"""
        size_map = {
            "16:9": "1280*720",
            "9:16": "720*1280",
            "4:3": "1024*768",
            "3:4": "768*1024",
            "1:1": "1024*1024",
            "21:9": "1440*616",
        }
        return size_map.get(aspect_ratio, "1024*768")

    def generate_image(self, prompt: str, slot_id: str) -> Optional[str]:
        """
        调用百炼API生成图片

        流程：
        1. MD5缓存检查
        2. 调用API（qwen-image-plus）
        3. 下载图片
        4. 保存到缓存

        Args:
            prompt: 图片生成提示词
            slot_id: 插槽ID（用于日志）

        Returns:
            图片路径，如果失败返回None
        """
        # 🔍 增强日志：记录启动状态
        logger.info(f"[IMG_GEN_START] slot={slot_id}, api_key={'SET' if self.api_key else 'MISSING'}")
        logger.info(f"[IMG_GEN_START] cache_dir={self.cache_dir}, exists={self.cache_dir.exists()}")
        
        if not self.api_key:
            logger.error(f"[IMG_GEN_FATAL] No API key configured for slot {slot_id}")
            return None
        
        # 1. MD5缓存检查
        prompt_hash = hashlib.md5(prompt.encode("utf-8")).hexdigest()
        cache_path = self.cache_dir / f"{prompt_hash}.png"
        logger.info(f"[IMG_GEN] cache_path={cache_path}")

        if cache_path.exists():
            logger.info(f"[CACHE HIT] Image for slot {slot_id} at {cache_path}")
            return str(cache_path)

        # 2. 调用API
        logger.info(f"[CACHE MISS] Generating image for slot {slot_id}")
        logger.info(f"[IMG_GEN] Prompt ({len(prompt)} chars): {prompt[:150]}...")

        try:
            size = self._get_size_for_aspect_ratio("4:3")
            logger.info(f"[IMG_GEN] Calling DashScope API: model=qwen-image-plus, size={size}")
            
            response = ImageSynthesis.call(
                api_key=self.api_key,
                model="qwen-image-plus",
                prompt=prompt,
                n=1,
                size=size,
            )
            
            # 🔍 增强日志：记录 API 响应
            logger.info(f"[IMG_GEN_API] status_code={response.status_code}, code={response.code}")
            logger.info(f"[IMG_GEN_API] message={response.message}")

            if response.status_code == HTTPStatus.OK:
                # API 返回的 output 是对象，需要使用属性访问
                if response.output:
                    logger.info(f"[IMG_GEN_API] output.task_status={getattr(response.output, 'task_status', 'N/A')}")
                    
                if response.output and response.output.results:
                    image_url = response.output.results[0].url
                    logger.info(f"[IMG_GEN_API] Got image URL: {image_url[:80]}...")

                    if not image_url:
                        logger.error(f"[IMG_GEN_ERROR] No image URL in response for slot {slot_id}")
                        return None

                    # 3. 下载图片
                    logger.info(f"[IMG_GEN] Downloading image...")
                    img_response = requests.get(image_url, timeout=60)
                    img_response.raise_for_status()
                    logger.info(f"[IMG_GEN] Downloaded {len(img_response.content)} bytes")

                    # 4. 保存到缓存
                    with open(cache_path, "wb") as f:
                        f.write(img_response.content)

                    logger.info(f"[IMG_GEN_SUCCESS] Image saved to {cache_path}")
                    return str(cache_path)
                else:
                    logger.error(f"[IMG_GEN_ERROR] No results in DashScope response for slot {slot_id}")
                    logger.error(f"[IMG_GEN_ERROR] output={response.output}")
            else:
                logger.error(
                    f"[IMG_GEN_ERROR] API error for slot {slot_id}: "
                    f"code={response.code}, message={response.message}"
                )

        except Exception as e:
            logger.exception(f"[IMG_GEN_FATAL] Failed to generate image for slot {slot_id}: {e}")

        return None

    async def generate_for_slots(
        self,
        slots: List[ImageSlotRequest],
        teaching_request: TeachingRequest,
        style_config: StyleConfig,
    ) -> List[ImageSlotResult]:
        """
        为多个插槽生成图片

        流程：
        1. 遍历所有slots
        2. 为每个slot生成prompt
        3. 调用generate_image
        4. 返回结果列表

        Args:
            slots: 图片插槽列表
            teaching_request: 教学需求（3.1输出）
            style_config: 风格配置（3.2输出）

        Returns:
            图片生成结果列表
        """
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

                # 调用API生成图片（在线程池中执行避免阻塞）
                image_path = await asyncio.to_thread(
                    self.generate_image, prompt=prompt, slot_id=slot.slot_id
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
                logger.exception(f"Failed to generate image for slot {slot.slot_id}")

            results.append(result)

        return results

    def generate_for_slots_sync(
        self,
        slots: List[ImageSlotRequest],
        teaching_request: TeachingRequest,
        style_config: StyleConfig,
        max_workers: int = 3,  # 并行工作线程数
    ) -> List[ImageSlotResult]:
        """
        并行同步版本：使用 ThreadPoolExecutor 并行生成图片
        用于后台任务等不能使用async的场景
        
        Args:
            max_workers: 最大并行工作线程数（默认3，避免API限流）
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def generate_single(slot: ImageSlotRequest) -> ImageSlotResult:
            """生成单张图片的任务"""
            start_time = time.time()
            result = ImageSlotResult(
                slot_id=slot.slot_id,
                page_index=slot.page_index,
                status="generating",
                prompt="",
            )
            
            try:
                prompt = self.build_prompt(slot, teaching_request, style_config)
                result.prompt = prompt
                
                logger.info(f"[PARALLEL] Starting generation for slot {slot.slot_id}")
                image_path = self.generate_image(prompt, slot.slot_id)
                
                if image_path:
                    result.status = "done"
                    result.image_path = image_path
                    result.generated_at = datetime.utcnow()
                    result.generation_time_seconds = time.time() - start_time
                    result.cache_hit = False
                    logger.info(f"[PARALLEL] Completed slot {slot.slot_id} in {result.generation_time_seconds:.1f}s")
                else:
                    result.status = "failed"
                    result.error = "Image generation failed"
            except Exception as e:
                result.status = "failed"
                result.error = str(e)
                logger.exception(f"Failed to generate image for slot {slot.slot_id}")
            
            return result
        
        results = []
        logger.info(f"[PARALLEL] Starting parallel generation for {len(slots)} slots with {max_workers} workers")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_slot = {executor.submit(generate_single, slot): slot for slot in slots}
            
            # 收集结果（按完成顺序）
            for future in as_completed(future_to_slot):
                result = future.result()
                results.append(result)
        
        # 按 page_index 排序结果
        results.sort(key=lambda r: (r.page_index, r.slot_id))
        
        logger.info(f"[PARALLEL] Completed all {len(results)} slots")
        return results

    def get_cache_stats(self) -> dict:
        """获取缓存统计信息"""
        cache_files = list(self.cache_dir.glob("*.png"))
        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            "total_images": len(cache_files),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "cache_dir": str(self.cache_dir),
        }

    def clear_cache(self, older_than_days: int = 7) -> int:
        """
        清理旧缓存

        Args:
            older_than_days: 清理多少天前的缓存

        Returns:
            清理的文件数量
        """
        import time as time_module

        cutoff = time_module.time() - (older_than_days * 24 * 60 * 60)
        removed = 0

        for cache_file in self.cache_dir.glob("*.png"):
            if cache_file.stat().st_mtime < cutoff:
                cache_file.unlink()
                removed += 1

        logger.info(f"Cleared {removed} cache files older than {older_than_days} days")
        return removed
