from __future__ import annotations

import os
import uuid
import time
import json
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles

# 使用新的模块化导入
from .common import (
    LLMClient,
    WorkflowLogger,
    SessionStore,
    WorkflowRunRequest,
    WorkflowRunResponse,
)
from .common.security import validate_session_id
from .orchestrator import WorkflowEngine
from .common import (
    LLMClient,
    WorkflowLogger,
    SessionStore,
    WorkflowRunRequest,
    WorkflowRunResponse,
    StyleConfig,
    StyleSampleSlide,
)
from .orchestrator import WorkflowEngine
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from .modules.content import build_base_deck

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = str((BASE_DIR / "data").resolve())
FRONTEND_DIR = str((BASE_DIR.parents[0] / "frontend").resolve())
FRONTEND_DIST_DIR = str((Path(FRONTEND_DIR) / "dist").resolve())

app = FastAPI(title="PPT Outline Workflow (3.1-3.4)")

app.add_middleware(
    CORSMiddleware,
    # SECURITY WARNING: allow_origins=["*"] is unsafe for production.
    # It allows any website to make requests to your API.
    # In production, specify the exact frontend domain(s), e.g., ["https://my-ppt-app.com"]
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "OPTIONS",
    ],  # Explicitly list methods
    allow_headers=["*"],
)


# Test route - temporarily disable complex routes
# @app.post("/api/test/simple")
# async def test_simple():
#     return {"message": "Simple test works"}
#
# @app.post("/api/test/param")
# async def test_with_param(session_id: str = None):
#     return {"message": f"Param test works: {session_id}"}
#
# @app.post("/api/another/test")
# async def another_test(id: str = None):
#     return {"message": f"Another test: {id}"}


store = SessionStore(DATA_DIR)
logger = WorkflowLogger(DATA_DIR)
llm = LLMClient()
print(
    "[LLM]",
    {
        "enabled": llm.is_enabled(),
        "mode": llm.mode,
        "base_url": llm.base_url,
        "model": llm.model,
        "has_key": bool(llm.api_key),
    },
)

# 使用原版工作流引擎
engine = WorkflowEngine(store, logger, llm)
print("[WORKFLOW] Using standard WorkflowEngine")


@app.get("/api/health")
def health():
    return {"ok": True, "llm_enabled": llm.is_enabled()}


@app.post("/api/session")
def create_session():
    sid = uuid.uuid4().hex
    store.create(sid)
    logger.emit(sid, "system", "session_created", {})
    return {"session_id": sid}


@app.post("/api/workflow/run", response_model=WorkflowRunResponse)
async def run_workflow(req: WorkflowRunRequest):
    try:
        user_text = req.user_text or getattr(req, "user_input_text", None)
        state, status, questions = await engine.run(
            session_id=req.session_id,
            user_text=user_text,
            answers=req.answers or {},
            auto_fill_defaults_flag=req.auto_fill_defaults,
            stop_at=req.stop_at,
            style_name=req.style_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Try to get session_id from state if available, otherwise fallback
        sid = state.session_id if "state" in locals() and state else (req.session_id or "unknown")
        logger.emit(sid, "system", "error", {"error": str(e)})
        return WorkflowRunResponse(
            session_id=sid,
            status="error",
            stage=state.stage if "state" in locals() and state else "3.1",
            message=str(e),
            logs_preview=logger.preview(sid),
        )

    # Choose stage for response
    stage = state.stage

    if status == "need_user_input":
        # If we are asking goals only, keep stage at 3.1
        return WorkflowRunResponse(
            session_id=state.session_id,
            status="need_user_input",
            stage="3.1",
            questions=questions,
            teaching_request=state.teaching_request,
            logs_preview=logger.preview(state.session_id),
            message="需要补充信息后才能继续。",
        )

    # 根据stage生成合适的消息
    if stage == "3.2":
        message = "已生成到模块3.2：风格配置。可以继续生成大纲。"
    elif stage == "3.3":
        message = "已生成到模块3.3：PPT大纲。"
    elif stage == "3.4":
        message = "已生成到模块3.4：页面内容。"
    else:
        message = "已生成到模块3.1：意图理解。"

    return WorkflowRunResponse(
        session_id=state.session_id,
        status="ok",
        stage=stage,
        teaching_request=state.teaching_request,
        style_config=state.style_config,
        style_samples=state.style_samples,
        outline=state.outline,
        deck_content=state.deck_content,
        render_result=state.render_result,
        logs_preview=logger.preview(state.session_id),
        message=message,
    )


@app.get("/api/session/{session_id}")
def get_session(session_id: str):
    st = store.load(session_id)
    if not st:
        raise HTTPException(status_code=404, detail="session not found")
    return st.model_dump(mode="json")


@app.get("/api/logs/{session_id}", response_class=PlainTextResponse)
def get_logs(session_id: str):
    validate_session_id(session_id)
    return logger.read_all(session_id)


@app.get("/api/slide-types")
def get_slide_types():
    """返回幻灯片类型元数据，用于前端展示标签和描述
    
    直接从 slide_type.json 读取，确保与 LLM 约束使用的数据一致
    """
    from .modules.outline.core import get_slide_types as load_slide_types
    return load_slide_types()


class StyleRefineRequest(BaseModel):
    session_id: str
    feedback: str


class StyleRefineResponse(BaseModel):
    ok: bool
    style_config: Optional[StyleConfig]
    style_samples: List[StyleSampleSlide]
    warnings: List[str]
    reasoning: Optional[str] = None  # 大模型的选择理由或设计思路
    error: Optional[str] = None


@app.post("/api/workflow/style/refine", response_model=StyleRefineResponse)
async def refine_style(req: StyleRefineRequest):
    try:
        cfg, samples, warnings, reasoning = await engine.refine_style(
            req.session_id, req.feedback
        )
        return StyleRefineResponse(
            ok=True,
            style_config=cfg,
            style_samples=samples,
            warnings=warnings,
            reasoning=reasoning,
        )
    except Exception as e:
        logger.emit(req.session_id, "3.2", "refine_api_error", {"error": str(e)})
        return StyleRefineResponse(
            ok=False,
            style_config=None,
            style_samples=[],
            warnings=[],
            reasoning=None,
            error=str(e),
        )


class StyleSyncRequest(BaseModel):
    session_id: str
    style_config: StyleConfig


@app.post("/api/workflow/style/sync")
async def sync_style(req: StyleSyncRequest):
    """同步风格配置到后端（支持撤销操作）"""
    try:
        state = store.load(req.session_id)
        if not state:
            return {"ok": False, "error": "Session not found"}

        state.style_config = req.style_config
        store.save(state)
        logger.emit(req.session_id, "3.2", "style_synced", {"source": "undo"})
        return {"ok": True}
    except Exception as e:
        logger.emit(req.session_id, "3.2", "sync_error", {"error": str(e)})
        return {"ok": False, "error": str(e)}


# =============================================================================
# Phase 1: Outline Editor Endpoints (2-Stage Workflow)
# =============================================================================

# =============================================================================
# Phase 1: Outline Editor Endpoints (2-Stage Workflow)
# =============================================================================

from .common.schemas import OutlineSlide, PPTOutline, TeachingRequest


class OutlineUpdateRequest(BaseModel):
    session_id: str
    slides: List[OutlineSlide]


class OutlineUpdateResponse(BaseModel):
    ok: bool
    message: Optional[str] = None
    error: Optional[str] = None


@app.post("/api/workflow/outline/update", response_model=OutlineUpdateResponse)
async def update_outline(req: OutlineUpdateRequest):
    """
    Save user-edited outline back to session (Phase 1 - Outline Editor).

    Allows frontend to save reordered, edited, added, or deleted slides
    before proceeding to content generation.
    """
    try:
        state = store.load(req.session_id)
        if not state:
            return OutlineUpdateResponse(ok=False, error="Session not found")

        if not state.outline:
            return OutlineUpdateResponse(
                ok=False, error="No outline found in session. Run Module 3.3 first."
            )

        # Update the slides array in the existing outline
        state.outline.slides = req.slides
        store.save(state)

        logger.emit(
            req.session_id,
            "3.3",
            "outline_updated",
            {"slide_count": len(req.slides), "source": "outline_editor"},
        )

        return OutlineUpdateResponse(
            ok=True, message=f"Outline updated with {len(req.slides)} slides"
        )
    except Exception as e:
        logger.emit(req.session_id, "3.3", "outline_update_error", {"error": str(e)})
        return OutlineUpdateResponse(ok=False, error=str(e))


# =============================================================================
# Phase 6: Async Parallel Outline Generation (Structure + Expand)
# =============================================================================


class OutlineStructureRequest(BaseModel):
    session_id: str
    style_name: Optional[str] = None


class OutlineStructureResponse(BaseModel):
    ok: bool
    outline: Optional[PPTOutline]
    error: Optional[str] = None


@app.post("/api/workflow/outline/structure", response_model=OutlineStructureResponse)
async def generate_outline_structure_endpoint(req: OutlineStructureRequest):
    """Step 1: 快速生成大纲结构"""
    try:
        from .modules.outline.core import generate_outline_structure

        state = store.load(req.session_id)
        if not state or not state.teaching_request:
            return OutlineStructureResponse(
                ok=False, outline=None, error="Session or request not found"
            )

        outline = await generate_outline_structure(
            state.teaching_request, req.style_name, llm, logger, req.session_id
        )

        # Save preliminary outline to state
        state.outline = outline
        store.save(state)

        return OutlineStructureResponse(ok=True, outline=outline)
    except Exception as e:
        return OutlineStructureResponse(ok=False, outline=None, error=str(e))


class SlideExpandRequest(BaseModel):
    session_id: str
    slide_index: int  # 0-based index from slides array


class SlideExpandResponse(BaseModel):
    ok: bool
    slide: Optional[OutlineSlide]
    error: Optional[str] = None


@app.post("/api/workflow/outline/expand", response_model=SlideExpandResponse)
async def expand_slide_detail_endpoint(req: SlideExpandRequest):
    """Step 2: 并行扩展单页详情"""
    try:
        from .modules.outline.core import expand_slide_details

        state = store.load(req.session_id)
        if not state or not state.outline:
            return SlideExpandResponse(
                ok=False, slide=None, error="No outline to expand"
            )

        if not state.teaching_request:
            return SlideExpandResponse(
                ok=False, slide=None, error="No teaching request found"
            )

        slides = state.outline.slides
        if req.slide_index < 0 or req.slide_index >= len(slides):
            return SlideExpandResponse(
                ok=False, slide=None, error="Invalid slide index"
            )

        target_slide = slides[req.slide_index]

        # Build context from session
        deck_context = {
            "subject": state.teaching_request.subject,
            "scene": state.teaching_request.teaching_scene,
            "objectives": state.teaching_request.teaching_objectives.knowledge,
        }

        expanded_slide = await expand_slide_details(
            target_slide, state.teaching_request, deck_context, llm
        )

        # Update state (with lock mechanism ideally, but simple assignment here)
        # Note: In a real concurrent env, this read-modify-write on 'state' might be race-prone
        # But for this prototype, we rely on session store's simplicity or minimal collision risk
        # Since we are modifying a specific index in a list object that is already in memory...
        # Actually Python objects are passed by reference, so modifying 'target_slide' modifies 'state.outline.slides[i]'
        # We just need to save state.
        state.outline.slides[req.slide_index] = expanded_slide
        
        # 对扩展后的slide进行assets后处理（生成描述）
        if llm.is_enabled():
            from .modules.outline.core import _process_slide_assets
            processed_slide = await _process_slide_assets(
                expanded_slide,
                state.teaching_request,
                llm,
                logger,
                req.session_id
            )
            state.outline.slides[req.slide_index] = processed_slide
            expanded_slide = processed_slide
        
        store.save(state)
        return SlideExpandResponse(ok=True, slide=expanded_slide)

    except Exception as e:
        logger.emit(req.session_id, "3.3", "expand_slide_error", {"error": str(e), "slide_index": req.slide_index})
        return SlideExpandResponse(ok=False, slide=None, error=str(e))


class OutlinePostProcessRequest(BaseModel):
    session_id: str

class OutlinePostProcessResponse(BaseModel):
    ok: bool
    outline: Optional[PPTOutline] = None
    error: Optional[str] = None

@app.post("/api/workflow/outline/post-process", response_model=OutlinePostProcessResponse)
async def post_process_outline_endpoint(req: OutlinePostProcessRequest):
    """在所有slides扩展完成后，统一进行assets后处理（生成描述、补充字段）"""
    try:
        from .modules.outline.core import _post_process_outline_assets
        
        state = store.load(req.session_id)
        if not state or not state.outline:
            return OutlinePostProcessResponse(ok=False, outline=None, error="No outline found")
        
        if not state.teaching_request:
            return OutlinePostProcessResponse(ok=False, outline=None, error="No teaching request found")
        
        # 对outline进行完整的assets后处理
        processed_outline = await _post_process_outline_assets(
            state.outline,
            state.teaching_request,
            llm,
            logger,
            req.session_id
        )
        
        # 更新state
        state.outline = processed_outline
        store.save(state)
        
        logger.emit(req.session_id, "3.3", "outline_post_processed", {
            "total_slides": len(processed_outline.slides),
            "slides_with_assets": len([s for s in processed_outline.slides if s.assets])
        })
        
        return OutlinePostProcessResponse(ok=True, outline=processed_outline)
        
    except Exception as e:
        logger.emit(req.session_id, "3.3", "post_process_error", {"error": str(e)})
        return OutlinePostProcessResponse(ok=False, outline=None, error=str(e))


# =============================================================================
# Phase 2: Async Content Generation Endpoints (2-Stage Workflow)
# =============================================================================


class SlideContentGenerateRequest(BaseModel):
    session_id: str
    slide_index: int
    context: Optional[Dict[str, Any]] = None  # Additional context if needed


class SlideContent(BaseModel):
    """Generated content for a single slide."""

    script: str  # Speaker script/notes
    bullets: List[str]  # Detailed bullet points
    visual_suggestions: List[str]  # Image/diagram suggestions


class SlideContentGenerateResponse(BaseModel):
    ok: bool
    slide_index: int
    content: Optional[SlideContent] = None
    error: Optional[str] = None


@app.post("/api/workflow/slide/generate", response_model=SlideContentGenerateResponse)
async def generate_slide_content(req: SlideContentGenerateRequest):
    """
    Generate detailed content for a single slide (Phase 2 - Async Generation).

    This endpoint uses 3.3's outline output as input for 3.4's content generation.
    For exercises pages, original questions from outline are preserved.
    """
    try:
        state = store.load(req.session_id)
        if not state:
            return SlideContentGenerateResponse(
                ok=False, slide_index=req.slide_index, error="Session not found"
            )

        if not state.outline:
            return SlideContentGenerateResponse(
                ok=False, slide_index=req.slide_index, error="No outline found"
            )

        if req.slide_index < 0 or req.slide_index >= len(state.outline.slides):
            return SlideContentGenerateResponse(
                ok=False,
                slide_index=req.slide_index,
                error=f"Invalid slide index: {req.slide_index}",
            )

        slide = state.outline.slides[req.slide_index]

        # 🚨 Special handling for exercises/quiz pages
        # Preserve original questions from 3.3 outline, don't call LLM
        if slide.slide_type in ("exercises", "quiz") and slide.bullets:
            print(
                f"[DEBUG] 3.4 generate_slide {req.slide_index}: SKIPPING LLM for exercises (preserving {len(slide.bullets)} questions)"
            )

            # Return content directly from outline bullets
            content = SlideContent(
                script=f"请学生独立完成以下练习题，完成后进行讲解。",
                bullets=slide.bullets,  # Preserve original questions!
                visual_suggestions=[f"建议配图：{slide.title}相关的评分表或题目展示图"],
            )
            return SlideContentGenerateResponse(
                ok=True, slide_index=req.slide_index, content=content
            )

        # Check if LLM is enabled
        if not llm.is_enabled():
            # Return content based on outline when LLM is disabled
            mock_content = SlideContent(
                script=f"讲解{slide.title}的核心内容，确保学生理解关键概念。",
                bullets=slide.bullets
                if slide.bullets
                else [f"{slide.title}的要点1", f"{slide.title}的要点2"],
                visual_suggestions=[f"建议配图：{slide.title}相关示意图"],
            )
            return SlideContentGenerateResponse(
                ok=True, slide_index=req.slide_index, content=mock_content
            )

        # For other page types, use LLM to enhance content
        # But still preserve the outline's bullets as the source of truth
        context_info = f"""
课程主题：{state.outline.deck_title}
知识点：{", ".join(state.outline.knowledge_points)}
教学场景：{state.outline.teaching_scene}
"""

        # 🔴 Key change: Include original bullets in prompt and instruct to preserve them
        original_bullets = slide.bullets if slide.bullets else []

        # 🎯 Adaptive Density: Determine image count hint based on slide type
        slide_type_image_hints = {
            # 0 images: 纯文字页面
            "title": 0,
            "cover": 0,
            "objectives": 0,
            "agenda": 0,
            "summary": 0,
            "qa": 0,
            "reference": 0,
            # 1 image: 标准配图页面
            "concept": 1,
            "theory": 1,
            "steps": 1,
            "process": 1,
            "practice": 1,
            "case": 1,
            "warning": 1,
            "intro": 1,
            # 2 images: 对比/双主体页面
            "comparison": 2,
            "relations": 2,
            # 4 images: 阵列/工具集/作品展示
            "tools": 4,
            "gallery": 4,
            "equipment": 4,
            "grid_4": 4,
        }
        image_hint = slide_type_image_hints.get(slide.slide_type, 1)

        prompt = f"""请为以下PPT幻灯片生成内容，遵循"自适应密度"原则：

{context_info}

当前幻灯片 (第 {req.slide_index + 1}/{len(state.outline.slides)} 页)：
- 类型：{slide.slide_type}
- 标题：{slide.title}
- 原始要点：{json.dumps(original_bullets, ensure_ascii=False)}

---

## 🎯 自适应密度规则 (Adaptive Density)

### 1️⃣ 动态要点 (Dynamic Bullets)
- **优先保留原始要点**，不要改写核心内容
- 如果原始要点为空，根据页面复杂度生成 **2-4 个** 关键要点：
  - 简单页面（封面、目录、总结）：2 个精炼要点即可
  - 复杂页面（概念讲解、步骤详解）：3-4 个要点
- 每个要点 **10-20 字**，不要过长

### 2️⃣ 按需配图 (Context-Aware Images)
根据页面类型决定配图数量，**禁止超过 4 张**：

| 配图数 | 适用场景 | 页面类型示例 |
|--------|----------|-------------|
| **0** | 纯文字强化、概念定义、金句引用 | title, cover, objectives, summary, qa |
| **1** | 标准配置（左文右图） | concept, steps, case, warning |
| **2** | 对比、冲突、双主体 | comparison, relations |
| **4** | 阵列/工具集/作品展示 | tools, gallery, equipment |

当前页面类型 `{slide.slide_type}` 建议配图数：**{image_hint}**

### 3️⃣ 视觉建议格式
如果需要配图，每条建议包含：
- 图片类型（photo/diagram/icon/chart）
- 主题描述（15字以内）

---

## 📝 返回JSON格式

```json
{{
    "script": "演讲脚本（2-4句话）",
    "bullets": ["要点1", "要点2"],
    "image_count": {image_hint},
    "visual_suggestions": ["建议1", "建议2"]
}}
```

**注意**：
- `bullets` 数组长度 2-4，优先保留原始要点
- `visual_suggestions` 数组长度必须等于 `image_count`（0/1/2）
"""

        logger.emit(
            req.session_id,
            "3.4",
            "slide_generate_start",
            {
                "slide_index": req.slide_index,
                "slide_type": slide.slide_type,
                "image_hint": image_hint,
            },
        )

        # Call LLM with adaptive density constraints
        system_prompt = """你是一位专业的PPT内容设计师，专注于"少即是多"的设计理念。

## 核心原则
1. **bullets**: 优先保留原始要点，不要改写；如需新增，控制在 2-4 条
2. **视觉建议**: 严格按照 `image_count` 字段返回对应数量，绝不超过 4 张图
3. **精炼表达**: 每条要点 10-20 字，演讲脚本 2-4 句话

以JSON格式返回，数组长度可变。"""

        json_schema = """{"script": "string", "bullets": ["string"], "image_count": 0, "visual_suggestions": ["string"]}"""

        result, _meta = await llm.chat_json(
            system=system_prompt, user=prompt, json_schema_hint=json_schema
        )

        if not result:
            # Fallback: use original bullets from outline, respect image_hint
            fallback_visuals = []
            if image_hint >= 1:
                fallback_visuals.append(f"diagram: {slide.title}相关示意图")
            if image_hint >= 2:
                fallback_visuals.append(f"photo: {slide.title}对比图")

            return SlideContentGenerateResponse(
                ok=True,
                slide_index=req.slide_index,
                content=SlideContent(
                    script=f"讲解{slide.title}的核心内容。",
                    bullets=original_bullets
                    if original_bullets
                    else [f"{slide.title}的要点"],
                    visual_suggestions=fallback_visuals,
                ),
            )

        # If LLM didn't return proper bullets, use original from outline
        result_bullets = result.get("bullets", [])
        if not result_bullets or len(result_bullets) == 0:
            result_bullets = (
                original_bullets if original_bullets else [f"{slide.title}的要点"]
            )

        # 🎯 Enforce bullet limit: max 4 bullets
        if len(result_bullets) > 4:
            result_bullets = result_bullets[:4]

        # 🎯 Enforce image limit: respect image_hint, max 4
        result_visuals = result.get("visual_suggestions", [])
        actual_image_count = result.get("image_count", image_hint)
        actual_image_count = min(actual_image_count, 4)  # Never exceed 4

        # Trim or pad visual_suggestions to match image_count
        if len(result_visuals) > actual_image_count:
            result_visuals = result_visuals[:actual_image_count]

        content = SlideContent(
            script=result.get("script", ""),
            bullets=result_bullets,
            visual_suggestions=result_visuals,
        )

        logger.emit(
            req.session_id,
            "3.4",
            "slide_generate_done",
            {
                "slide_index": req.slide_index,
                "bullet_count": len(content.bullets),
                "image_count": len(content.visual_suggestions),
            },
        )

        return SlideContentGenerateResponse(
            ok=True, slide_index=req.slide_index, content=content
        )

    except Exception as e:
        logger.emit(
            req.session_id,
            "3.4",
            "slide_generate_error",
            {"slide_index": req.slide_index, "error": str(e)},
        )
        return SlideContentGenerateResponse(
            ok=False, slide_index=req.slide_index, error=str(e)
        )


@app.post("/api/workflow/render")
async def render_html_slides_api(req: dict):
    """调用 3.5 模块渲染 HTML 幻灯片"""
    try:
        session_id = req.get("session_id")
        if not session_id:
            return {"ok": False, "error": "Missing session_id"}

        state = store.load(session_id)
        if not state:
            return {"ok": False, "error": "Session not found"}

        if not state.deck_content:
            return {"ok": False, "error": "No deck_content found"}

        if not state.style_config:
            return {"ok": False, "error": "No style_config found"}

        if not state.teaching_request:
            return {"ok": False, "error": "No teaching_request found"}

        from .modules.render import render_html_slides

        # ✅ 关键修复：输出目录必须包含 session_id
        output_dir = Path(DATA_DIR) / "outputs" / session_id
        output_dir.mkdir(parents=True, exist_ok=True)

        result = await render_html_slides(
            deck_content=state.deck_content,
            style_config=state.style_config,
            teaching_request=state.teaching_request,
            session_id=session_id,
            output_dir=str(output_dir), # 现在指向 outputs/{session_id}
            llm=llm,
        )

        state.render_result = result
        store.save(state)

        logger.emit(
            session_id,
            "3.5",
            "render_complete",
            {
                "html_path": result.html_path,
                "total_pages": result.total_pages,
            },
        )

        return {
            "ok": True,
            "html_path": result.html_path,
            "total_pages": result.total_pages,
            "image_slots": [
                {
                    "slot_id": slot.slot_id,
                    "page_index": slot.page_index,
                    "theme": slot.theme,
                    "keywords": slot.keywords,
                    "visual_style": slot.visual_style.value,
                    "aspect_ratio": slot.aspect_ratio.value,
                }
                for slot in result.image_slots
            ],
            "layouts_used": result.layouts_used,
            "warnings": result.warnings,
        }
    except Exception as e:
        logger.emit(
            req.get("session_id", "unknown"), "3.5", "render_error", {"error": str(e)}
        )
        return {"ok": False, "error": str(e)}


@app.post("/api/workflow/render/with-data")
async def render_with_full_data(req: dict):
    """
    3.5 模块：使用完整的 3.1-3.4 输出数据进行渲染

    支持两种模式：
    1. 传入完整的 Mock 数据（测试模式）
    2. 传入 session_id（正常流程模式，从session读取数据）

    请求体格式：
    {
        "session_id": "xxx",  // 可选，从session读取数据
        "teaching_request": {...},  // 可选，3.1输出
        "style_config": {...},  // 可选，3.2输出
        "deck_content": {...}   // 可选，3.4输出
    }
    如果只传 session_id，则从session读取所有数据
    如果传了具体数据，则使用传入的数据（覆盖session数据）
    """
    from .modules.render import render_html_slides
    from .common.schemas import (
        TeachingRequest,
        StyleConfig,
        SlideDeckContent,
        SlidePage,
        SlideElement,
    )

    try:
        session_id = req.get("session_id") or f"mock_{int(time.time())}"

        # 确定使用的数据源
        if session_id and not req.get("teaching_request"):
            # 正常流程：从session读取
            state = store.load(session_id)
            if not state:
                return {"ok": False, "error": "Session not found"}

            teaching_request = state.teaching_request
            style_config = state.style_config
            deck_content = state.deck_content
        else:
            # 测试模式：使用传入的Mock数据
            from .modules.render.mock_data import get_mock_full_input

            if req.get("use_mock") and req.get("subject"):
                # 使用预设的Mock数据
                mock_data = get_mock_full_input(req.get("subject"))
                teaching_request = TeachingRequest(**mock_data["teaching_request"])
                style_config = StyleConfig(**mock_data["style_config"])
                deck_content = SlideDeckContent(**mock_data["deck_content"])
            else:
                # 使用传入的完整数据
                teaching_request_data = req.get(
                    "teaching_request", get_mock_full_input()["teaching_request"]
                )
                style_config_data = req.get(
                    "style_config", get_mock_full_input()["style_config"]
                )
                deck_content_data = req.get(
                    "deck_content", get_mock_full_input()["deck_content"]
                )

                teaching_request = TeachingRequest(**teaching_request_data)
                style_config = StyleConfig(**style_config_data)
                deck_content = SlideDeckContent(**deck_content_data)

        if not teaching_request:
            return {"ok": False, "error": "No teaching_request found or provided"}
        if not style_config:
            return {"ok": False, "error": "No style_config found or provided"}
        if not deck_content:
            return {"ok": False, "error": "No deck_content found or provided"}

        # 创建输出目录
        output_dir = Path(DATA_DIR) / "outputs" / session_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # 渲染HTML
        result = await render_html_slides(
            deck_content=deck_content,
            style_config=style_config,
            teaching_request=teaching_request,
            session_id=session_id,
            output_dir=str(output_dir),
            llm=llm,
        )

        # 保存到session（如果存在）
        if session_id and not session_id.startswith("mock_"):
            state = store.load(session_id)
            if state:
                state.render_result = result
                store.save(state)

        logger.emit(
            session_id,
            "3.5",
            "render_with_data_complete",
            {
                "html_path": result.html_path,
                "total_pages": result.total_pages,
                "total_image_slots": len(result.image_slots),
                "source": "session" if not req.get("use_mock") else "mock_data",
            },
        )

        return {
            "ok": True,
            "session_id": session_id,
            "html_path": result.html_path,
            "total_pages": result.total_pages,
            "image_slots": [
                {
                    "slot_id": slot.slot_id,
                    "page_index": slot.page_index,
                    "theme": slot.theme,
                    "keywords": slot.keywords,
                    "visual_style": slot.visual_style.value,
                    "aspect_ratio": slot.aspect_ratio.value,
                }
                for slot in result.image_slots
            ],
            "layouts_used": result.layouts_used,
            "warnings": result.warnings,
        }
    except Exception as e:
        logger.emit(
            req.get("session_id", "unknown"),
            "3.5",
            "render_with_data_error",
            {"error": str(e)},
        )
        return {"ok": False, "error": str(e)}


@app.post("/api/workflow/render/mock")
async def render_with_mock_data(req: dict = {}):
    """
    使用完整的 Mock 数据（3.1-3.4 输出）测试 3.5 模块渲染

    这是最完整的测试方式，直接使用预设的Mock数据进行渲染

    请求体可选参数：
    - use_mock: 是否使用Mock数据（默认true）
    - subject: 学科主题，可选 'mechanical' 或 'chemistry'（默认 'mechanical'）
    """
    from .modules.render import render_html_slides
    from .modules.render.mock_data import (
        get_mock_full_input,
        MOCK_TEACHING_REQUEST,
        MOCK_STYLE_CONFIG,
        MOCK_SLIDE_DECK_CONTENT,
        MOCK_TEACHING_REQUEST_CHEMISTRY,
        MOCK_STYLE_CONFIG_CHEMISTRY,
        MOCK_DECK_CHEMISTRY,
    )
    from .common.schemas import TeachingRequest, StyleConfig, SlideDeckContent

    try:
        session_id = f"mock_full_{int(time.time())}"

        # 根据subject选择Mock数据
        subject = req.get("subject", "mechanical")

        if subject == "chemistry":
            teaching_request = TeachingRequest(**MOCK_TEACHING_REQUEST_CHEMISTRY)
            style_config = StyleConfig(**MOCK_STYLE_CONFIG_CHEMISTRY)
            deck_content_data = MOCK_DECK_CHEMISTRY
        else:
            teaching_request = TeachingRequest(**MOCK_TEACHING_REQUEST)
            style_config = StyleConfig(**MOCK_STYLE_CONFIG)
            deck_content_data = MOCK_SLIDE_DECK_CONTENT

        deck_content = SlideDeckContent(**deck_content_data)

        # 创建输出目录
        output_dir = Path(DATA_DIR) / "outputs" / session_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # 渲染HTML
        result = await render_html_slides(
            deck_content=deck_content,
            style_config=style_config,
            teaching_request=teaching_request,
            session_id=session_id,
            output_dir=str(output_dir),
            llm=llm,
        )

        # 创建并保存 session 状态（关键：使图片生成 API 能找到该 session）
        from .common.schemas import SessionState
        mock_state = SessionState(session_id=session_id)
        mock_state.teaching_request = teaching_request
        mock_state.style_config = style_config
        mock_state.deck_content = deck_content
        mock_state.render_result = result
        store.save(mock_state)

        logger.emit(
            session_id,
            "3.5",
            "mock_render_complete",
            {
                "html_path": result.html_path,
                "total_pages": result.total_pages,
                "total_image_slots": len(result.image_slots),
                "subject": subject,
            },
        )

        return {
            "ok": True,
            "session_id": session_id,
            "html_path": result.html_path,
            "total_pages": result.total_pages,
            "image_slots": [
                {
                    "slot_id": slot.slot_id,
                    "page_index": slot.page_index,
                    "theme": slot.theme,
                    "keywords": slot.keywords,
                    "visual_style": slot.visual_style.value,
                    "aspect_ratio": slot.aspect_ratio.value,
                }
                for slot in result.image_slots
            ],
            "layouts_used": result.layouts_used,
            "warnings": result.warnings,
        }
    except Exception as e:
        import traceback

        traceback.print_exc()
        return {"ok": False, "error": str(e)}


@app.post("/api/workflow/render/mock_deprecated")
async def render_html_slides_mock_deprecated():
    """
    使用 mock 3.4 数据测试 3.5 模块渲染

    不依赖真实的 3.4 模块,直接使用模拟数据
    """
    try:
        from .common.schemas import (
            SlideDeckContent,
            SlidePage,
            SlideElement,
            StyleConfig,
            ColorConfig,
            FontConfig,
            LayoutConfig as StyleLayoutConfig,
            ImageryConfig,
            TeachingRequest,
            KnowledgePointDetail,
            TeachingScenarioDetail,
            TeachingObjectivesStructured,
            SlideRequirementsDetail,
            SpecialRequirementsDetailed,
        )
        from .modules.render import render_html_slides

        # 创建 mock 数据
        mock_deck = SlideDeckContent(
            deck_title="液压系统工作原理",
            pages=[
                # 封面页
                SlidePage(
                    index=1,
                    slide_type="title",
                    title="液压系统工作原理",
                    layout={"template": "one-column"},
                    elements=[],
                    speaker_notes="",
                ),
                # 教学目标
                SlidePage(
                    index=2,
                    slide_type="objectives",
                    title="教学目标",
                    layout={"template": "one-column"},
                    elements=[
                        SlideElement(
                            id="elem1",
                            type="bullets",
                            x=0.1,
                            y=0.2,
                            w=0.8,
                            h=0.7,
                            content={
                                "items": [
                                    "掌握液压系统的基本组成和工作原理",
                                    "能够识别液压系统的主要部件",
                                    "培养安全操作意识和规范操作习惯",
                                ]
                            },
                            style={"role": "body"},
                        ),
                    ],
                    speaker_notes="",
                ),
                # 概念讲解 (左文右图)
                SlidePage(
                    index=3,
                    slide_type="concept",
                    title="液压系统的组成",
                    layout={"template": "two-column"},
                    elements=[
                        SlideElement(
                            id="elem1",
                            type="bullets",
                            x=0.05,
                            y=0.2,
                            w=0.5,
                            h=0.7,
                            content={
                                "items": [
                                    "动力元件：液压泵,提供压力油",
                                    "执行元件：液压缸、液压马达",
                                    "控制元件：各种阀,控制流量和压力",
                                    "辅助元件：油箱、滤油器、管路等",
                                ]
                            },
                            style={"role": "body"},
                        ),
                        SlideElement(
                            id="elem2",
                            type="image",
                            x=0.6,
                            y=0.2,
                            w=0.35,
                            h=0.7,
                            content={
                                "placeholder": True,
                                "kind": "diagram",
                                "theme": "液压系统组成示意图",
                            },
                            style={"role": "visual"},
                        ),
                    ],
                    speaker_notes="",
                ),
                # 操作步骤 (左图右步骤)
                SlidePage(
                    index=4,
                    slide_type="steps",
                    title="液压系统启动步骤",
                    layout={"template": "two-column"},
                    elements=[
                        SlideElement(
                            id="elem1",
                            type="image",
                            x=0.05,
                            y=0.2,
                            w=0.4,
                            h=0.7,
                            content={
                                "placeholder": True,
                                "kind": "photo",
                                "theme": "液压系统操作面板",
                            },
                            style={"role": "visual"},
                        ),
                        SlideElement(
                            id="elem2",
                            type="bullets",
                            x=0.5,
                            y=0.2,
                            w=0.45,
                            h=0.7,
                            content={
                                "items": [
                                    "检查油箱油位,确保油量充足",
                                    "检查各连接部位,确保无泄漏",
                                    "启动液压泵,观察压力表读数",
                                    "调节溢流阀,设定系统压力",
                                    "试运行,检查系统工作是否正常",
                                ]
                            },
                            style={"role": "body"},
                        ),
                    ],
                    speaker_notes="",
                ),
                # 对比页
                SlidePage(
                    index=5,
                    slide_type="comparison",
                    title="正确操作 vs 错误操作",
                    layout={"template": "two-column"},
                    elements=[
                        SlideElement(
                            id="elem1",
                            type="image",
                            x=0.05,
                            y=0.2,
                            w=0.42,
                            h=0.6,
                            content={
                                "placeholder": True,
                                "kind": "photo",
                                "theme": "正确的液压系统操作姿势",
                            },
                            style={"role": "visual"},
                        ),
                        SlideElement(
                            id="elem2",
                            type="text",
                            x=0.05,
                            y=0.82,
                            w=0.42,
                            h=0.1,
                            content={"text": "✓ 正确操作"},
                            style={"role": "body"},
                        ),
                        SlideElement(
                            id="elem3",
                            type="image",
                            x=0.53,
                            y=0.2,
                            w=0.42,
                            h=0.6,
                            content={
                                "placeholder": True,
                                "kind": "warning",
                                "theme": "错误的液压系统操作",
                            },
                            style={"role": "visual"},
                        ),
                        SlideElement(
                            id="elem4",
                            type="text",
                            x=0.53,
                            y=0.82,
                            w=0.42,
                            h=0.1,
                            content={"text": "✗ 错误操作"},
                            style={"role": "body"},
                        ),
                    ],
                    speaker_notes="",
                ),
                # 工具展示 (四宫格)
                SlidePage(
                    index=6,
                    slide_type="tools",
                    title="常用液压工具",
                    layout={"template": "grid"},
                    elements=[
                        SlideElement(
                            id=f"elem{i}",
                            type="image",
                            x=0.05 if i % 2 == 1 else 0.53,
                            y=0.2 if i <= 2 else 0.6,
                            w=0.42,
                            h=0.35,
                            content={
                                "placeholder": True,
                                "kind": "photo",
                                "theme": ["液压扳手", "液压千斤顶", "液压钳", "压力表"][
                                    i - 1
                                ],
                            },
                            style={"role": "visual"},
                        )
                        for i in range(1, 5)
                    ],
                    speaker_notes="",
                ),
                # 总结页
                SlidePage(
                    index=7,
                    slide_type="summary",
                    title="课程总结",
                    layout={"template": "one-column"},
                    elements=[
                        SlideElement(
                            id="elem1",
                            type="bullets",
                            x=0.1,
                            y=0.2,
                            w=0.8,
                            h=0.7,
                            content={
                                "items": [
                                    "掌握了液压系统的基本组成",
                                    "学会了液压系统的启动步骤",
                                    "了解了正确与错误的操作方式",
                                    "认识了常用的液压工具",
                                ]
                            },
                            style={"role": "body"},
                        ),
                    ],
                    speaker_notes="",
                ),
            ],
        )

        mock_style = StyleConfig(
            style_name="professional",
            color=ColorConfig(
                primary="#2c3e50",
                secondary="#34495e",
                accent="#3498db",
                text="#2c3e50",
                muted="#ecf0f1",
                background="#ffffff",
                warning="#e74c3c",
            ),
            font=FontConfig(
                title_family="PingFang SC",
                heading_family="PingFang SC",
                body_family="PingFang SC",
                heading_size_base=48,
                body_size_base=24,
            ),
            layout=StyleLayoutConfig(
                width=1920,
                height=1080,
                padding=60,
            ),
            imagery=ImageryConfig(
                image_style="photo",
                icon_style="flat",
            ),
        )

        mock_request = TeachingRequest(
            teaching_scenario=TeachingScenarioDetail(
                scene_type="practice",
                scene_label="实操教学",
            ),
            professional_category="机械制造",
            knowledge_points=[
                KnowledgePointDetail(
                    id="kp1",
                    name="液压系统工作原理",
                    type="practice",
                    difficulty_level="medium",
                ),
            ],
            teaching_objectives=TeachingObjectivesStructured(
                knowledge=["掌握液压系统的基本组成和工作原理"],
                ability=["能够识别液压系统的主要部件"],
                literacy=["培养安全操作意识和规范操作习惯"],
            ),
            slide_requirements=SlideRequirementsDetail(
                target_count=7,
                min_count=5,
                max_count=10,
                lesson_duration_min=45,
            ),
            special_requirements=SpecialRequirementsDetailed(
                warnings_enabled=True,
            ),
        )

        # 调用渲染
        output_dir = Path(DATA_DIR) / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)

        session_id = f"mock_{int(time.time())}"

        result = await render_html_slides(
            deck_content=mock_deck,
            style_config=mock_style,
            teaching_request=mock_request,
            session_id=session_id,
            output_dir=str(output_dir),
        )

        logger.emit(
            session_id,
            "3.5",
            "mock_render_complete",
            {
                "html_path": result.html_path,
                "total_pages": result.total_pages,
            },
        )

        return {
            "ok": True,
            "html_path": result.html_path,
            "total_pages": result.total_pages,
            "image_slots": [
                {
                    "slot_id": slot.slot_id,
                    "page_index": slot.page_index,
                    "theme": slot.theme,
                    "keywords": slot.keywords,
                    "visual_style": slot.visual_style.value,
                    "aspect_ratio": slot.aspect_ratio.value,
                }
                for slot in result.image_slots
            ],
            "layouts_used": result.layouts_used,
            "warnings": result.warnings,
        }
    except Exception as e:
        import traceback

        traceback.print_exc()
        return {"ok": False, "error": str(e)}


# In-memory store for render status (for streaming/polling)
render_status_store: Dict[str, Dict[str, Any]] = {}


def generate_images_task(session_id: str, slots: List, output_dir: Path):
    """后台任务：生成图片并更新状态"""
    try:
        from .modules.render import ImageService
        import shutil

        # 1. 加载 Session 状态以获取上下文 (TeachingRequest, StyleConfig)
        state = store.load(session_id)
        if not state:
            print(f"[BG] Error: Session {session_id} not found")
            return
            
        if not state.teaching_request or not state.style_config:
            print(f"[BG] Error: Session {session_id} missing context")
            return

        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            print("[BG] No API Key, skipping image gen")
            return

        render_status_store[session_id] = {"images": {}}
        images_dir = output_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        # 初始化 ImageService
        filler = ImageService(api_key=api_key, cache_dir=images_dir)

        for slot in slots:
            slot_id = slot.slot_id

            # Init status
            render_status_store[session_id]["images"][slot_id] = {
                "status": "generating",
                "url": None,
            }

            print(f"[BG] Generating for {slot_id}")
            
            # 使用 ImageService 生成图片 (返回的文件名可能是随机Hash)
            try:
                # 2. 构建 Prompt
                prompt = filler.build_prompt(slot, state.teaching_request, state.style_config)
                
                # 3. 准备 slot_data (用于传递 aspect_ratio)
                slot_data = slot.model_dump() if hasattr(slot, "model_dump") else slot.__dict__

                # 4. 使用 ImageService 生成图片
                raw_image_path = filler.generate_image(prompt, slot_id, slot_data=slot_data)
            except Exception as slot_err:
                print(f"[BG] Error generating slot {slot_id}: {slot_err}")
                raw_image_path = None

            if raw_image_path:
                # ✅【关键修改】强制重命名为 slot_id.png
                # 这样 HTML 即使离线也能猜到图片路径
                ext = os.path.splitext(raw_image_path)[1]  # 获取扩展名 (如 .png)
                if not ext:
                    ext = ".png"
                
                new_filename = f"{slot_id}{ext}"
                new_image_path = images_dir / new_filename
                
                # 移动/重命名文件 (如果路径不同)
                if Path(raw_image_path).resolve() != new_image_path.resolve():
                    shutil.move(raw_image_path, new_image_path)

                # 生成相对路径 URL
                web_url = f"./images/{new_filename}"

                render_status_store[session_id]["images"][slot_id] = {
                    "status": "done",
                    "url": web_url,
                }
                print(f"[BG] Done {slot_id} -> {web_url}")
            else:
                render_status_store[session_id]["images"][slot_id] = {
                    "status": "failed",
                    "error": "Image generation returned None"
                }
                print(f"[BG] Failed {slot_id}")

    except Exception as e:
        print(f"[BG] Error: {e}")
        import traceback
        traceback.print_exc()


@app.get("/api/workflow/render/status/{session_id}")
def get_render_status(session_id: str):
    """前端轮询图片生成状态"""
    status = render_status_store.get(session_id, {})
    return {"ok": True, "images": status.get("images", {})}


@app.post("/api/workflow/render/mock_deprecated")
async def render_html_slides_mock(background_tasks: BackgroundTasks):
    """
    使用真实的 Mock 数据测试 3.5 模块 (流式渲染 + 缓存)
    """
    try:
        from .modules.render import render_html_slides
        from .common.schemas import (
            SlideDeckContent,
            SlidePage,
            SlideElement,
            StyleConfig,
            ColorConfig,
            FontConfig,
            LayoutConfig as StyleLayoutConfig,
            ImageryConfig,
            TeachingRequest,
            TeachingScenarioDetail,
            TeachingObjectivesStructured,
            SlideRequirementsDetail,
            SpecialRequirementsDetailed,
        )

        # === 1. 构建真实的 10 页 Mock 数据 (液压系统) ===
        pages = []

        # Helper to simplify element creation
        def mk_elem(etype, content, idx):
            return SlideElement(id=f"el_{idx}", type=etype, content=content)

        # Page 1: 封面
        pages.append(
            SlidePage(
                index=1,
                slide_type="title",
                title="液压系统原理与维护",
                layout={"template": "title_only"},
                elements=[],
                speaker_notes="",
            )
        )

        # Page 2: 教学目标
        pages.append(
            SlidePage(
                index=2,
                slide_type="objectives",
                title="本次课程目标",
                layout={"template": "title_bullets"},
                elements=[
                    mk_elem(
                        "bullets",
                        {
                            "items": [
                                "理解液压传动的基本工作原理 (帕斯卡定律)",
                                "掌握液压系统的核心组成部分及其功能",
                                "学会液压泵、液压缸的结构与运作方式",
                                "能够进行简单的液压系统故障排查与维护",
                            ]
                        },
                        1,
                    )
                ],
                speaker_notes="",
            )
        )

        # Page 3: 液压系统组成 (概念)
        pages.append(
            SlidePage(
                index=3,
                slide_type="concept",
                title="液压系统的五大组成部分",
                layout={"template": "title_bullets_right_img"},
                elements=[
                    mk_elem(
                        "bullets",
                        {
                            "items": [
                                "动力元件: 液压泵 (机械能 -> 液压能)",
                                "执行元件: 液压缸/马达 (液压能 -> 机械能)",
                                "控制元件: 各种阀门 (控制压力、流量、方向)",
                                "辅助元件: 油箱、滤油器、管路",
                                "工作介质: 液压油",
                            ]
                        },
                        1,
                    ),
                    mk_elem(
                        "image",
                        {
                            "kind": "diagram",
                            "theme": "液压系统五大组成全景图，包含油泵、油缸、阀门、油箱、管路，工程示意图",
                            "placeholder": True,
                        },
                        2,
                    ),
                ],
                speaker_notes="",
            )
        )

        # Page 4: 动力元件 - 液压泵 (细节)
        pages.append(
            SlidePage(
                index=4,
                slide_type="content",
                title="核心动力：液压泵",
                layout={"template": "title_bullets_right_img"},
                elements=[
                    mk_elem(
                        "bullets",
                        {
                            "items": [
                                "作用：为系统提供压力油，是心脏部件",
                                "常用类型：齿轮泵、叶片泵、柱塞泵",
                                "特点：齿轮泵结构简单但噪音大，柱塞泵压力高效率高",
                                "维护重点：防止吸空，定期更换密封件",
                            ]
                        },
                        1,
                    ),
                    mk_elem(
                        "image",
                        {
                            "kind": "photo",
                            "theme": "工业齿轮泵内部精密结构特写，金属齿轮咬合，机械剖视图，高精度渲染",
                            "placeholder": True,
                        },
                        2,
                    ),
                ],
                speaker_notes="",
            )
        )

        # Page 5: 执行元件 - 液压缸
        pages.append(
            SlidePage(
                index=5,
                slide_type="content",
                title="执行机构：液压缸",
                layout={"template": "title_bullets_right_img"},
                elements=[
                    mk_elem(
                        "bullets",
                        {
                            "items": [
                                "作用：将液压能转换为直线运动的机械能",
                                "分类：单作用式 (靠外力回程)、双作用式 (靠油压回程)",
                                "关键参数：缸径 (决定推力)、行程 (决定距离)",
                                "应用：挖掘机动臂、注塑机合模机构",
                            ]
                        },
                        1,
                    ),
                    mk_elem(
                        "image",
                        {
                            "kind": "photo",
                            "theme": "挖掘机液压缸工作特写",
                            "placeholder": True,
                        },
                        2,
                    ),
                ],
                speaker_notes="",
            )
        )

        # Page 6: 工作原理 (帕斯卡定律)
        pages.append(
            SlidePage(
                index=6,
                slide_type="concept",
                title="基本原理：帕斯卡定律",
                layout={"template": "title_bullets_right_img"},
                elements=[
                    mk_elem(
                        "bullets",
                        {
                            "items": [
                                "定义：密闭液体上的压强向各个方向传递不变",
                                "公式：F = P × A (力 = 压强 × 面积)",
                                "应用：千斤顶原理 (小力举起大重物)",
                                "优势：可以实现力的放大和远距离传递",
                            ]
                        },
                        1,
                    ),
                    mk_elem(
                        "image",
                        {
                            "kind": "diagram",
                            "theme": "帕斯卡定律千斤顶原理示意图",
                            "placeholder": True,
                        },
                        2,
                    ),
                ],
                speaker_notes="",
            )
        )

        # Page 7: 操作步骤 (启动)
        pages.append(
            SlidePage(
                index=7,
                slide_type="steps",
                title="液压系统标准启动流程",
                layout={"template": "operation_steps"},
                elements=[
                    mk_elem(
                        "image",
                        {
                            "kind": "photo",
                            "theme": "液压站控制面板操作",
                            "placeholder": True,
                        },
                        1,
                    ),
                    mk_elem(
                        "bullets",
                        {
                            "items": [
                                "检查油箱液位是否在标准刻度线以上",
                                "确认所有换向阀处于中位，卸荷启动",
                                "点动电机，检查旋转方向是否正确",
                                "空载运行 5-10 分钟，进行排气",
                                "逐步加载，观察压力表读数是否稳定",
                            ]
                        },
                        2,
                    ),
                ],
                speaker_notes="",
            )
        )

        # Page 8: 常见故障对比
        pages.append(
            SlidePage(
                index=8,
                slide_type="comparison",
                title="正常油液 vs 污染油液",
                layout={"template": "concept_comparison"},
                elements=[
                    mk_elem(
                        "image",
                        {
                            "kind": "photo",
                            "theme": "清澈透明的液压油样品",
                            "placeholder": True,
                        },
                        1,
                    ),
                    mk_elem("text", {"text": "正常油液：淡黄色、透明、无异味"}, 2),
                    mk_elem(
                        "image",
                        {
                            "kind": "photo",
                            "theme": "乳化发白的浑浊液压油",
                            "placeholder": True,
                        },
                        3,
                    ),
                    mk_elem(
                        "text", {"text": "乳化油液：呈乳白色，混入水分，需更换"}, 4
                    ),
                ],
                speaker_notes="",
            )
        )

        # Page 9: 常用维护工具
        pages.append(
            SlidePage(
                index=9,
                slide_type="tools",
                title="维修保养常用工具",
                layout={"template": "grid_4"},
                elements=[
                    mk_elem(
                        "image",
                        {
                            "kind": "photo",
                            "theme": "液压专用压力表，黑色表盘，指针指向高压区",
                        },
                        1,
                    ),
                    mk_elem(
                        "image",
                        {"kind": "photo", "theme": "工业滤芯拆卸专用扳手，金属工具"},
                        2,
                    ),
                    mk_elem(
                        "image",
                        {
                            "kind": "photo",
                            "theme": "便携式油液颗粒计数器，手持检测仪器，屏幕显示数据",
                        },
                        3,
                    ),
                    mk_elem(
                        "image",
                        {
                            "kind": "photo",
                            "theme": "工业红外测温仪，手持式，激光瞄准点",
                        },
                        4,
                    ),
                ],
                speaker_notes="",
            )
        )

        # Page 10: 总结
        pages.append(
            SlidePage(
                index=10,
                slide_type="summary",
                title="课程总结",
                layout={"template": "title_bullets"},
                elements=[
                    mk_elem(
                        "bullets",
                        {
                            "items": [
                                "液压系统通过液压油传递动力，遵循帕斯卡定律",
                                "五大组成部分各司其职，缺一不可",
                                "正确的启动和维护流程能延长系统寿命",
                                "油液清洁度是液压系统的生命线",
                            ]
                        },
                        1,
                    )
                ],
                speaker_notes="",
            )
        )

        deck = SlideDeckContent(deck_title="液压系统原理与维护", pages=pages)

        # Style Config
        style_config = StyleConfig(
            style_name="professional",
            color=ColorConfig(
                primary="#2c3e50",
                secondary="#ecf0f1",
                accent="#3498db",
                text="#2c3e50",
                muted="#95a5a6",
                background="#ffffff",
                warning="#e74c3c",
            ),
            font=FontConfig(
                title_family="Microsoft YaHei",
                body_family="Microsoft YaHei",
                title_size=40,
                body_size=24,
            ),
            layout=StyleLayoutConfig(
                density="comfortable", notes_area=True
            ),  # Corrected schema
            imagery=ImageryConfig(image_style="photorealistic", icon_style="flat"),
        )

        # Teaching Request
        teaching_req = TeachingRequest(
            teaching_scenario=TeachingScenarioDetail(
                scene_type="practice", scene_label="实操"
            ),
            subject_info={"subject_category": "engineering"},  # Mock nested input
            knowledge_points=[],
            teaching_objectives=TeachingObjectivesStructured(
                knowledge=[], ability=[], literacy=[]
            ),
            slide_requirements=SlideRequirementsDetail(target_count=10),
            special_requirements=SpecialRequirementsDetailed(),
        )
        # Manually ensure category is set if needed (but subject_info above handles it)

        # 调用渲染 (HTML立即生成)
        output_dir = Path(DATA_DIR) / "outputs"
        session_id = f"mock_{int(time.time())}"

        result = await render_html_slides(
            deck_content=deck,
            style_config=style_config,
            teaching_request=teaching_req,
            session_id=session_id,
            output_dir=str(output_dir),
        )

        # 触发后台生图
        if result.image_slots:
            background_tasks.add_task(
                generate_images_task, session_id, result.image_slots, output_dir
            )

        logger.emit(
            session_id,
            "3.5",
            "mock_render_start",
            {"html": result.html_path, "slots": len(result.image_slots)},
        )

        return {
            "ok": True,
            "html_path": result.html_path,
            "sesson_id": session_id,  # for polling
            "total_pages": result.total_pages,
            # "image_slots": ... omit detailed slots for brevity
        }

    except Exception as e:
        import traceback

        traceback.print_exc()
        return {"ok": False, "error": str(e)}


# Mount static assets (Reveal.js, etc.)
RENDER_STATIC_DIR = BASE_DIR / "app" / "modules" / "render" / "static"
if RENDER_STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(RENDER_STATIC_DIR)), name="static")

# Mount styles (CSS)
RENDER_STYLES_DIR = BASE_DIR / "app" / "modules" / "render" / "styles"
if RENDER_STYLES_DIR.exists():
    app.mount("/styles", StaticFiles(directory=str(RENDER_STYLES_DIR)), name="styles")


# Mount static data (generated outputs)
# This allows accessing /data/outputs/xxx.html
if os.path.exists(DATA_DIR):
    app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")

# Serve frontend (pure static) for easy demo
# COMMENTED OUT to fix 405 error on API routes
# The catch-all mount was intercepting API requests before they reached the API routes
# if os.path.isdir(FRONTEND_DIR):
#     dist = Path(FRONTEND_DIST_DIR)
#     directory = str(dist) if dist.exists() else FRONTEND_DIR
#     app.mount("/", StaticFiles(directory=directory, html=True), name="frontend")


# =============================================================================
# 3.5 模块图片生成 API 端点
# =============================================================================


class ImageGenerateResponse(BaseModel):
    ok: bool
    total_slots: int
    message: str
    error: Optional[str] = None


# Use APIRouter to define the route
from fastapi import APIRouter


async def trigger_image_generation(session_id: str, background_tasks: BackgroundTasks):
    """Trigger image generation for a session (runs in background)"""
    import os
    
    try:
        from .modules.render import ImageService
        
        # 1. 加载 session 状态
        state = store.load(session_id)
        if not state:
            return {"ok": False, "error": "Session not found"}
        
        if not state.render_result:
            return {"ok": False, "error": "No render_result found. Please run render first."}
        
        # 兼容性处理：如果 render_result 是 dict（因为 SessionState 中定义为 Any），则转换为对象
        if isinstance(state.render_result, dict):
            from .modules.render import RenderResult
            state.render_result = RenderResult.model_validate(state.render_result)
        
        if not state.render_result.image_slots:
            return {"ok": False, "error": "No image slots to generate"}
        
        if not state.teaching_request:
            return {"ok": False, "error": "No teaching_request found"}
        
        if not state.style_config:
            return {"ok": False, "error": "No style_config found"}
        
        # 2. 验证 API Key
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            return {"ok": False, "error": "DASHSCOPE_API_KEY not configured. Please set the environment variable."}
        
        # 3. 创建 ImageService 实例
        cache_dir = Path(DATA_DIR) / "outputs" / "images"
        cache_dir.mkdir(parents=True, exist_ok=True)
        filler = ImageService(api_key=api_key, cache_dir=str(cache_dir))
        
        total_slots = len(state.render_result.image_slots)
        
        # 3.1 立即更新状态为 pending/generating，以便前端 UI 立即响应
        from .modules.render.core import ImageSlotResult
        import time
        import shutil
        
        # 初始化全局状态存储，确保前端轮询能看到进度 (之前遗漏的关键点)
        render_status_store[session_id] = {"images": {}}

        initial_results = []
        for slot in state.render_result.image_slots:
            # 更新 SessionStore 状态
            initial_results.append(ImageSlotResult(
                slot_id=slot.slot_id,
                page_index=slot.page_index,
                status="generating",
                image_path=None,
                error=None,
            ))
            # 更新全局状态存储
            render_status_store[session_id]["images"][slot.slot_id] = {
                "status": "generating",
                "url": None,
            }

        state.render_result.image_results = initial_results
        store.save(state)
        
        # 4. 定义后台任务
        def generate_images_task():
            """后台执行图片生成"""
            try:
                results = filler.generate_for_slots_sync(
                    slots=state.render_result.image_slots,
                    teaching_request=state.teaching_request,
                    style_config=state.style_config,
                )
                
                # 确定 session 的图片目录
                # html_path 类似 "outputs/{session_id}/index.html"
                try:
                    # 解析 session 目录: backend/data/outputs/{session_id}
                    rel_html_path = state.render_result.html_path
                    if "outputs/" in rel_html_path:
                        # 提取 session_id 部分
                        # 假设路径结构 outputs/mock_xxxx/index.html
                        session_rel_dir = os.path.dirname(rel_html_path) # outputs/mock_xxxx
                        session_dir = Path(DATA_DIR) / session_rel_dir.replace("outputs/", "outputs/") # 稍微冗余但安全
                    else:
                        # Fallback
                        session_dir = Path(DATA_DIR) / "outputs" / session_id
                    
                    local_images_dir = session_dir / "images"
                    local_images_dir.mkdir(parents=True, exist_ok=True)
                except Exception as ex:
                    logger.error(f"Failed to resolve session dir: {ex}")
                    local_images_dir = None

                # 处理结果：将缓存图片复制到 session 目录并重命名 -> slot_id.png
                for res in results:
                    if res.status == "done" and res.image_path and os.path.exists(res.image_path):
                        web_url = None
                        
                        if local_images_dir:
                            try:
                                # 强制重命名为 slot_id.png
                                ext = os.path.splitext(res.image_path)[1] or ".png"
                                new_filename = f"{res.slot_id}{ext}"
                                target_path = local_images_dir / new_filename
                                
                                # 从共享缓存复制到 session 目录
                                shutil.copy2(res.image_path, target_path)
                                
                                # 生成相对路径 URL (用于 HTML 离线访问)
                                web_url = f"./images/{new_filename}"
                                
                                # 更新结果中的 path 为本地 path (或者保留缓存 path? 这里改为本地 path 更一致)
                                # res.image_path = str(target_path) 
                            except Exception as copy_err:
                                logger.error(f"Failed to copy image for {res.slot_id}: {copy_err}")
                        
                        # 更新全局状态
                        render_status_store[session_id]["images"][res.slot_id] = {
                            "status": "done",
                            "url": web_url or f"/api/files/{os.path.basename(res.image_path)}", # Fallback
                        }
                    else:
                        render_status_store[session_id]["images"][res.slot_id] = {
                            "status": "failed",
                            "error": res.error or "Unknown error"
                        }

                # 更新 session 状态
                state.render_result.image_results = results
                store.save(state)
                
                logger.emit(
                    session_id,
                    "3.5",
                    "image_generation_complete",
                    {
                        "total": total_slots,
                        "done": sum(1 for r in results if r.status == "done"),
                        "failed": sum(1 for r in results if r.status == "failed"),
                    },
                )
            except Exception as e:
                logger.emit(
                    session_id,
                    "3.5",
                    "image_generation_error",
                    {"error": str(e)},
                )
        
        # 5. 添加后台任务
        background_tasks.add_task(generate_images_task)
        
        logger.emit(
            session_id,
            "3.5",
            "image_generation_started",
            {"total_slots": total_slots},
        )
        
        return {
            "ok": True,
            "session_id": session_id,
            "total_slots": total_slots,
            "message": f"Image generation started for {total_slots} slots",
        }
        
    except Exception as e:
        logger.emit(session_id, "3.5", "image_generation_error", {"error": str(e)})
        return {"ok": False, "error": str(e)}


render_router = APIRouter()


@render_router.post("/generate/{session_id}")
async def render_generate(session_id: str, background_tasks: BackgroundTasks):
    """Generate images for a session"""
    return await trigger_image_generation(session_id, background_tasks)


# Mount the router at the correct path
app.include_router(render_router, prefix="/api/workflow/render")


# Debug route to test parameter handling
@app.post("/api/debug/generate")
async def debug_generate(session_id: str = None):
    print(f"DEBUG: debug_generate called with session_id: {session_id}")
    return {"ok": True, "session_id": session_id, "message": "Debug endpoint works"}


@app.get("/api/workflow/download/{session_id}")
async def download_project_package(session_id: str):
    """
    打包下载生成的 PPT 项目 (HTML + 资源 + 图片)
    """
    import shutil
    from fastapi.responses import FileResponse

    # 1. 定位输出目录
    output_dir = Path(DATA_DIR) / "outputs" / session_id
    if not output_dir.exists():
        raise HTTPException(status_code=404, detail="Project output not found")

    # 2. 准备临时 ZIP 路径
    temp_dir = Path(DATA_DIR) / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    zip_base_name = temp_dir / session_id  # make_archive 会自动加 .zip
    zip_path = Path(f"{zip_base_name}.zip")

    try:
        # 3. 创建 ZIP (如果已存在且较新则直接返回，这里简单起见每次都覆盖)
        shutil.make_archive(str(zip_base_name), "zip", str(output_dir))

        # 4. 返回文件
        return FileResponse(
            path=zip_path,
            filename=f"ppt_project_{session_id}.zip",
            media_type="application/zip",
        )
    except Exception as e:
        logger.emit(session_id, "export", "zip_error", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to create zip: {str(e)}")


@app.get("/api/workflow/render/status/{session_id}")
def get_image_status(session_id: str):
    """
    获取图片生成状态（供前端轮询）
    """
    try:
        state = store.load(session_id)
        if not state:
            return {"ok": False, "error": "Session not found"}

        if not state.render_result:
            return {"ok": False, "error": "No render_result found"}

        # 构建状态信息
        results = (
            state.render_result.image_results
            if state.render_result.image_results
            else []
        )

        images = {}
        done = 0
        generating = 0
        failed = 0
        total = len(state.render_result.image_slots)

        # 初始化未生成的状态
        for slot in state.render_result.image_slots:
            images[slot.slot_id] = {
                "status": "pending",
                "image_path": None,
                "error": None,
            }

        # 更新已生成的状态
        for result in results:
            images[result.slot_id] = {
                "status": result.status,
                "image_path": result.image_path,
                "error": result.error,
            }
            if result.status == "done":
                done += 1
            elif result.status == "generating":
                generating += 1
            elif result.status == "failed":
                failed += 1

        return {
            "ok": True,
            "total": total,
            "done": done,
            "generating": generating,
            "failed": failed,
            "images": images,
        }

    except Exception as e:
        logger.emit(session_id, "3.5", "status_error", {"error": str(e)})
        return {"ok": False, "error": str(e)}


@app.get("/api/workflow/render/image/{session_id}/{slot_id}")
def get_generated_image(session_id: str, slot_id: str):
    """
    获取指定插槽生成的图片
    """
    try:
        state = store.load(session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Session not found")

        if not state.render_result:
            raise HTTPException(status_code=404, detail="No render_result found")

        # 查找对应的结果
        for result in state.render_result.image_results:
            if (
                result.slot_id == slot_id
                and result.status == "done"
                and result.image_path
            ):
                # 返回文件
                from fastapi.responses import FileResponse

                return FileResponse(result.image_path)

        # 如果没找到，尝试从 image_slots 直接生成（实时生成）
        for slot in state.render_result.image_slots:
            if slot.slot_id == slot_id:
                if not state.image_filler:
                    api_key = os.getenv("DASHSCOPE_API_KEY")
                    if api_key:
                        from .modules.render import ImageService

                        state.image_filler = ImageService(
                            api_key=api_key,
                            cache_dir=f"{DATA_DIR}/{session_id}/images_cache",
                        )

                if state.image_filler and state.teaching_request and state.style_config:
                    # 同步生成
                    prompt = state.image_filler.build_prompt(
                        slot, state.teaching_request, state.style_config
                    )
                    image_path = state.image_filler.generate_image(prompt, slot_id)

                    if image_path:
                        from fastapi.responses import FileResponse

                        return FileResponse(image_path)

                break

        raise HTTPException(status_code=404, detail="Image not found or not generated")

    except HTTPException:
        raise
    except Exception as e:
        logger.emit(
            session_id, "render", "image_retrieval_error", {"slot_id": slot_id, "error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


class UpdateDeckRequest(BaseModel):
    session_id: str
    deck_content: Dict[str, Any]

@app.post("/api/workflow/deck/update")
async def update_deck_content(req: UpdateDeckRequest):
    """
    强制更新 Session 中的 deck_content
    用于 3.4 内容生成完毕后，跳转 3.5 之前的数据同步
    """
    try:
        from .common.schemas import SlideDeckContent
        
        # 1. 加载 Session
        store = SessionStore(DATA_DIR)
        state = store.load(req.session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Session not found")
            
        # 2. 验证数据结构
        # 前端传来的数据必须符合 SlideDeckContent 模型
        new_content = SlideDeckContent.model_validate(req.deck_content)
        
        # 3. 更新状态
        state.deck_content = new_content
        # 如果当前阶段还停留在 3.3，强制推进到 3.4
        if state.stage == "3.3": 
            state.stage = "3.4"
            
        # 4. 保存到磁盘
        store.save(state)
        
        return {"ok": True, "message": "Deck content updated"}
        
    except Exception as e:
        print(f"[Error] Update deck failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 2. 定义请求模型
class SlideUserContent(BaseModel):
    index: int
    script: Optional[str] = ""
    bullets: Optional[List[str]] = []

class AssembleDeckRequest(BaseModel):
    session_id: str
    contents: List[SlideUserContent]

# 3. 新增组装接口
@app.post("/api/workflow/deck/assemble")
async def assemble_deck_endpoint(req: AssembleDeckRequest):
    """
    3.4 -> 3.5 过渡专用接口：
    接收前端生成的文本内容(script/bullets)，在后端调用 Layout 引擎组装成完整的 SlideDeckContent。
    """
    try:
        # 加载 Session
        state = store.load(req.session_id)
        if not state or not state.outline:
            raise HTTPException(404, "Session or outline not found")
            
        if not state.style_config:
             raise HTTPException(400, "Style config missing. Please run Step 3.2 first.")
             
        # A. 后端生成骨架 (包含 Layout 和 Elements 坐标)
        # 这确保了数据结构符合 SlideDeckContent 的严格要求
        deck = build_base_deck(state.teaching_request, state.style_config, state.outline)
        
        # B. 填入前端传来的用户内容
        # 建立索引映射
        content_map = {c.index: c for c in req.contents}
        
        for i, page in enumerate(deck.pages):
            if i in content_map:
                user_content = content_map[i]
                
                # 1. 更新演讲备注
                page.speaker_notes = user_content.script
                
                # 2. 更新正文要点 (查找类型为 bullets 的元素)
                # 这一步将前端生成的详细 bullets 写入 PPT 元素中
                if user_content.bullets:
                    for elem in page.elements:
                        if elem.type == "bullets" and "items" in elem.content:
                            elem.content["items"] = user_content.bullets
                            break 
                        
        # C. 保存完整的 PPT 结构
        state.deck_content = deck
        state.stage = "3.4" # 标记完成
        store.save(state)
        
        return {"ok": True, "message": "Deck assembled successfully"}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.emit(req.session_id, "3.4", "assemble_error", {"error": str(e)})
        raise HTTPException(500, str(e))


@app.post("/api/workflow/render/retry/{session_id}/{slot_id}")
async def retry_slot_generation(
    session_id: str, slot_id: str, background_tasks: BackgroundTasks
):
    """重试单个插槽的图片生成"""
    try:
        state = store.load(session_id)
        if not state:
            return {"ok": False, "error": "Session not found"}

        if not state.render_result:
            return {"ok": False, "error": "No render_result found"}

        # 查找对应的 slot
        target_slot = None
        for slot in state.render_result.image_slots:
            if slot.slot_id == slot_id:
                target_slot = slot
                break

        if not target_slot:
            return {"ok": False, "error": "Slot not found"}

        # 使用 image_filler 或创建新的
        if state.image_filler:
            image_filler = state.image_filler
        else:
            api_key = os.getenv("DASHSCOPE_API_KEY")
            if not api_key:
                return {"ok": False, "error": "DASHSCOPE_API_KEY not configured"}

            from .modules.render import ImageService

            image_filler = ImageService(
                api_key=api_key, cache_dir=f"{DATA_DIR}/{session_id}/images_cache"
            )
            state.image_filler = image_filler

        # 移除旧结果（如果有）
        state.render_result.image_results = [
            r for r in state.render_result.image_results if r.slot_id != slot_id
        ]
        store.save(state)

        # 添加后台任务
        background_tasks.add_task(
            run_single_image_task,
            session_id=session_id,
            slot=target_slot,
            teaching_request=state.teaching_request,
            style_config=state.style_config,
            image_filler=image_filler,
            store=store,
        )

        return {"ok": True, "message": "Retry started"}

    except Exception as e:
        logger.emit(
            session_id, "3.5", "retry_error", {"slot_id": slot_id, "error": str(e)}
        )
        return {"ok": False, "error": str(e)}


async def run_image_generation_task(
    session_id: str,
    slots: List,
    teaching_request: Any,
    style_config: Any,
    image_filler: Any,
    store: SessionStore,
):
    """后台任务：生成所有图片"""
    try:
        # 调用 image_filler 生成图片
        results = image_filler.generate_for_slots_sync(
            slots=slots,
            teaching_request=teaching_request,
            style_config=style_config,
        )

        # 更新状态
        state = store.load(session_id)
        if state and state.render_result:
            state.render_result.image_results = results
            store.save(state)

        logger.emit(
            session_id,
            "3.5",
            "generation_complete",
            {
                "total": len(results),
                "done": sum(1 for r in results if r.status == "done"),
                "failed": sum(1 for r in results if r.status == "failed"),
            },
        )

    except Exception as e:
        logger.exception(session_id, "3.5", "generation_task_error", {"error": str(e)})


async def run_single_image_task(
    session_id: str,
    slot: Any,
    teaching_request: Any,
    style_config: Any,
    image_filler: Any,
    store: SessionStore,
):
    """后台任务：生成单个图片"""
    try:
        # 生成 prompt
        prompt = image_filler.build_prompt(slot, teaching_request, style_config)

        # 调用 API
        image_path = image_filler.generate_image(prompt, slot.slot_id)

        # 创建结果
        from .modules.render.core import ImageSlotResult
        import time
        from datetime import datetime

        result = ImageSlotResult(
            slot_id=slot.slot_id,
            page_index=slot.page_index,
            status="done" if image_path else "failed",
            prompt=prompt,
            image_path=image_path,
            error=None if image_path else "Generation failed",
            generated_at=datetime.utcnow(),
            model_used=os.getenv("DASHSCOPE_IMAGE_MODEL", "qwen-image-plus"),
            generation_time_seconds=0,
        )

        # 更新状态
        state = store.load(session_id)
        if state and state.render_result:
            # 移除旧结果
            state.render_result.image_results = [
                r
                for r in state.render_result.image_results
                if r.slot_id != slot.slot_id
            ]
            # 添加新结果
            state.render_result.image_results.append(result)
            store.save(state)

        logger.emit(
            session_id,
            "3.5",
            "slot_retry_complete",
            {
                "slot_id": slot.slot_id,
                "status": result.status,
            },
        )

    except Exception as e:
        logger.exception(
            session_id,
            "3.5",
            "slot_retry_error",
            {"slot_id": slot.slot_id, "error": str(e)},
        )
