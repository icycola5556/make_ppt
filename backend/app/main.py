from __future__ import annotations

import os
import uuid
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles

# 使用新的模块化导入
from .common import LLMClient, WorkflowLogger, SessionStore, WorkflowRunRequest, WorkflowRunResponse
from .orchestrator import WorkflowEngine
from .common import (
    LLMClient, WorkflowLogger, SessionStore, 
    WorkflowRunRequest, WorkflowRunResponse,
    StyleConfig, StyleSampleSlide
)
from .orchestrator import WorkflowEngine
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = str((BASE_DIR / "data").resolve())
FRONTEND_DIR = str((BASE_DIR.parents[0] / "frontend").resolve())
FRONTEND_DIST_DIR = str((Path(FRONTEND_DIR) / "dist").resolve())

app = FastAPI(title="PPT Outline Workflow (3.1-3.4)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = SessionStore(DATA_DIR)
logger = WorkflowLogger(DATA_DIR)
llm = LLMClient()
print("[LLM]", {
    "enabled": llm.is_enabled(),
    "mode": llm.mode,
    "base_url": llm.base_url,
    "model": llm.model,
    "has_key": bool(llm.api_key),
})

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
        logger.emit(req.session_id, "system", "error", {"error": str(e)})
        return WorkflowRunResponse(
            session_id=req.session_id,
            status="error",
            stage=state.stage if "state" in locals() and state else "3.1",
            message=str(e),
            logs_preview=logger.preview(req.session_id),
        )

    # Choose stage for response
    stage = state.stage

    if status == "need_user_input":
        # If we are asking goals only, keep stage at 3.1
        return WorkflowRunResponse(
            session_id=req.session_id,
            status="need_user_input",
            stage="3.1",
            questions=questions,
            teaching_request=state.teaching_request,
            logs_preview=logger.preview(req.session_id),
            message="需要补充信息后才能继续。",
        )

    return WorkflowRunResponse(
        session_id=req.session_id,
        status="ok",
        stage=stage,
        teaching_request=state.teaching_request,
        style_config=state.style_config,
        style_samples=state.style_samples,
        outline=state.outline,
        deck_content=state.deck_content,
        logs_preview=logger.preview(req.session_id),
        message="已生成到模块3.4：页面内容。" if stage == "3.4" else "已生成到模块3.3：PPT大纲。",
    )


@app.get("/api/session/{session_id}")
def get_session(session_id: str):
    st = store.load(session_id)
    if not st:
        raise HTTPException(status_code=404, detail="session not found")
    return st.model_dump(mode="json")


@app.get("/api/logs/{session_id}", response_class=PlainTextResponse)
def get_logs(session_id: str):
    return logger.read_all(session_id)



class StyleRefineRequest(BaseModel):
    session_id: str
    feedback: str

class StyleRefineResponse(BaseModel):
    ok: bool
    style_config: Optional[StyleConfig]
    style_samples: List[StyleSampleSlide]
    warnings: List[str]
    error: Optional[str] = None

@app.post("/api/workflow/style/refine", response_model=StyleRefineResponse)
async def refine_style(req: StyleRefineRequest):
    try:
        cfg, samples, warnings = await engine.refine_style(req.session_id, req.feedback)
        return StyleRefineResponse(
            ok=True,
            style_config=cfg,
            style_samples=samples,
            warnings=warnings
        )
    except Exception as e:
        logger.emit(req.session_id, "3.2", "refine_api_error", {"error": str(e)})
        return StyleRefineResponse(
            ok=False,
            style_config=None,
            style_samples=[],
            warnings=[],
            error=str(e)
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


@app.post("/api/workflow/render")
def render_html_slides_api(req: dict):
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
        
        from .modules.render import render_html_slides
        
        output_dir = Path(DATA_DIR) / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        result = render_html_slides(
            deck_content=state.deck_content,
            style_config=state.style_config,
            teaching_request=state.teaching_request,
            session_id=session_id,
            output_dir=str(output_dir),
        )
        
        state.render_result = result
        store.save(state)
        
        logger.emit(session_id, "3.5", "render_complete", {
            "html_path": result.html_path,
            "total_pages": result.total_pages,
        })
        
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
        logger.emit(req.get("session_id", "unknown"), "3.5", "render_error", {"error": str(e)})
        return {"ok": False, "error": str(e)}


@app.post("/api/workflow/render-mock-deprecated")
def render_html_slides_mock_deprecated():
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
                            x=0.1, y=0.2, w=0.8, h=0.7,
                            content={"items": [
                                "掌握液压系统的基本组成和工作原理",
                                "能够识别液压系统的主要部件",
                                "培养安全操作意识和规范操作习惯",
                            ]},
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
                            x=0.05, y=0.2, w=0.5, h=0.7,
                            content={"items": [
                                "动力元件：液压泵,提供压力油",
                                "执行元件：液压缸、液压马达",
                                "控制元件：各种阀,控制流量和压力",
                                "辅助元件：油箱、滤油器、管路等",
                            ]},
                            style={"role": "body"},
                        ),
                        SlideElement(
                            id="elem2",
                            type="image",
                            x=0.6, y=0.2, w=0.35, h=0.7,
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
                            x=0.05, y=0.2, w=0.4, h=0.7,
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
                            x=0.5, y=0.2, w=0.45, h=0.7,
                            content={"items": [
                                "检查油箱油位,确保油量充足",
                                "检查各连接部位,确保无泄漏",
                                "启动液压泵,观察压力表读数",
                                "调节溢流阀,设定系统压力",
                                "试运行,检查系统工作是否正常",
                            ]},
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
                            x=0.05, y=0.2, w=0.42, h=0.6,
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
                            x=0.05, y=0.82, w=0.42, h=0.1,
                            content={"text": "✓ 正确操作"},
                            style={"role": "body"},
                        ),
                        SlideElement(
                            id="elem3",
                            type="image",
                            x=0.53, y=0.2, w=0.42, h=0.6,
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
                            x=0.53, y=0.82, w=0.42, h=0.1,
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
                                "theme": ["液压扳手", "液压千斤顶", "液压钳", "压力表"][i-1],
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
                            x=0.1, y=0.2, w=0.8, h=0.7,
                            content={"items": [
                                "掌握了液压系统的基本组成",
                                "学会了液压系统的启动步骤",
                                "了解了正确与错误的操作方式",
                                "认识了常用的液压工具",
                            ]},
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
        
        result = render_html_slides(
            deck_content=mock_deck,
            style_config=mock_style,
            teaching_request=mock_request,
            session_id=session_id,
            output_dir=str(output_dir),
        )
        
        logger.emit(session_id, "3.5", "mock_render_complete", {
            "html_path": result.html_path,
            "total_pages": result.total_pages,
        })
        
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
        from .modules.render.image_generator import generate_image
        
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            print("[BG] No API Key, skipping image gen")
            return
            
        render_status_store[session_id] = {"images": {}}
        images_dir = output_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        
        for slot in slots:
            slot_id = slot.slot_id
            
            # Init status
            render_status_store[session_id]["images"][slot_id] = {
                "status": "generating",
                "url": None
            }
            
            prompt = f"{slot.theme}, {', '.join(slot.keywords)}, photorealistic, high quality, 4k"
            if getattr(slot, 'visual_style', None):
                 prompt += f", {slot.visual_style} style"
            
            # 使用 Hash 缓存的生成器
            filename = f"{session_id}_{slot_id}.png"
            # 注意: image_generator 内部现在使用 hash 做文件名，但我们可以把 session 相关文件名 copy 过去或者直接用 hash 名
            # 为了简单，直接用 image_generator 返回的路径
            
            print(f"[BG] Generating for {slot_id}: {prompt}")
            image_abs_path = generate_image(prompt, str(images_dir), api_key)
            
            if image_abs_path:
                # 获取相对路径 (相对于 HTML)
                # image_abs_path 是绝对路径，我们需要 /data/outputs/images/xxx.png 或者 ./images/xxx.png
                # HTML 也是在 output_dir 下，所以 ./images/文件名
                rel_name = os.path.basename(image_abs_path)
                web_url = f"./images/{rel_name}"
                
                render_status_store[session_id]["images"][slot_id] = {
                    "status": "done",
                    "url": web_url
                }
                print(f"[BG] Done {slot_id} -> {web_url}")
            else:
                render_status_store[session_id]["images"][slot_id] = {
                    "status": "error"
                }

    except Exception as e:
        print(f"[BG] Error: {e}")


@app.get("/api/workflow/render/status/{session_id}")
def get_render_status(session_id: str):
    """前端轮询图片生成状态"""
    status = render_status_store.get(session_id, {})
    return {"ok": True, "images": status.get("images", {})}


@app.post("/api/workflow/render-mock")
def render_html_slides_mock(background_tasks: BackgroundTasks):
    """
    使用真实的 Mock 数据测试 3.5 模块 (流式渲染 + 缓存)
    """
    try:
        from .modules.render import render_html_slides
        from .common.schemas import (
            SlideDeckContent, SlidePage, SlideElement, StyleConfig, ColorConfig,
            FontConfig, LayoutConfig as StyleLayoutConfig, ImageryConfig,
            TeachingRequest, TeachingScenarioDetail, TeachingObjectivesStructured,
            SlideRequirementsDetail, SpecialRequirementsDetailed
        )
        
        # === 1. 构建真实的 10 页 Mock 数据 (液压系统) ===
        pages = []
        
        # Helper to simplify element creation
        def mk_elem(etype, content, idx):
            return SlideElement(id=f"el_{idx}", type=etype, content=content)

        # Page 1: 封面
        pages.append(SlidePage(
            index=1, slide_type="title", title="液压系统原理与维护",
            layout={"template": "title_only"}, 
            elements=[], 
            speaker_notes=""
        ))
        
        # Page 2: 教学目标
        pages.append(SlidePage(
            index=2, slide_type="objectives", title="本次课程目标",
            layout={"template": "title_bullets"},
            elements=[mk_elem("bullets", {"items": [
                "理解液压传动的基本工作原理 (帕斯卡定律)",
                "掌握液压系统的核心组成部分及其功能",
                "学会液压泵、液压缸的结构与运作方式",
                "能够进行简单的液压系统故障排查与维护"
            ]}, 1)], 
            speaker_notes=""
        ))
        
        # Page 3: 液压系统组成 (概念)
        pages.append(SlidePage(
            index=3, slide_type="concept", title="液压系统的五大组成部分",
            layout={"template": "title_bullets_right_img"},
            elements=[
                mk_elem("bullets", {"items": [
                    "动力元件: 液压泵 (机械能 -> 液压能)",
                    "执行元件: 液压缸/马达 (液压能 -> 机械能)",
                    "控制元件: 各种阀门 (控制压力、流量、方向)",
                    "辅助元件: 油箱、滤油器、管路",
                    "工作介质: 液压油"
                ]}, 1),
                mk_elem("image", {"kind": "diagram", "theme": "液压系统五大组成全景图，包含油泵、油缸、阀门、油箱、管路，工程示意图", "placeholder": True}, 2)
            ], speaker_notes=""
        ))
        
        # Page 4: 动力元件 - 液压泵 (细节)
        pages.append(SlidePage(
            index=4, slide_type="content", title="核心动力：液压泵",
            layout={"template": "title_bullets_right_img"},
            elements=[
                mk_elem("bullets", {"items": [
                    "作用：为系统提供压力油，是心脏部件",
                    "常用类型：齿轮泵、叶片泵、柱塞泵",
                    "特点：齿轮泵结构简单但噪音大，柱塞泵压力高效率高",
                    "维护重点：防止吸空，定期更换密封件"
                ]}, 1),
                mk_elem("image", {"kind": "photo", "theme": "工业齿轮泵内部精密结构特写，金属齿轮咬合，机械剖视图，高精度渲染", "placeholder": True}, 2)
            ], speaker_notes=""
        ))
        
        # Page 5: 执行元件 - 液压缸
        pages.append(SlidePage(
            index=5, slide_type="content", title="执行机构：液压缸",
            layout={"template": "title_bullets_right_img"},
            elements=[
                mk_elem("bullets", {"items": [
                    "作用：将液压能转换为直线运动的机械能",
                    "分类：单作用式 (靠外力回程)、双作用式 (靠油压回程)",
                    "关键参数：缸径 (决定推力)、行程 (决定距离)",
                    "应用：挖掘机动臂、注塑机合模机构"
                ]}, 1),
                mk_elem("image", {"kind": "photo", "theme": "挖掘机液压缸工作特写", "placeholder": True}, 2)
            ], speaker_notes=""
        ))
        
        # Page 6: 工作原理 (帕斯卡定律)
        pages.append(SlidePage(
            index=6, slide_type="concept", title="基本原理：帕斯卡定律",
            layout={"template": "title_bullets_right_img"},
            elements=[
                mk_elem("bullets", {"items": [
                    "定义：密闭液体上的压强向各个方向传递不变",
                    "公式：F = P × A (力 = 压强 × 面积)",
                    "应用：千斤顶原理 (小力举起大重物)",
                    "优势：可以实现力的放大和远距离传递"
                ]}, 1),
                mk_elem("image", {"kind": "diagram", "theme": "帕斯卡定律千斤顶原理示意图", "placeholder": True}, 2)
            ], speaker_notes=""
        ))

        # Page 7: 操作步骤 (启动)
        pages.append(SlidePage(
            index=7, slide_type="steps", title="液压系统标准启动流程",
            layout={"template": "operation_steps"},
            elements=[
                mk_elem("image", {"kind": "photo", "theme": "液压站控制面板操作", "placeholder": True}, 1),
                mk_elem("bullets", {"items": [
                    "检查油箱液位是否在标准刻度线以上",
                    "确认所有换向阀处于中位，卸荷启动",
                    "点动电机，检查旋转方向是否正确",
                    "空载运行 5-10 分钟，进行排气",
                    "逐步加载，观察压力表读数是否稳定"
                ]}, 2)
            ], speaker_notes=""
        ))

        # Page 8: 常见故障对比
        pages.append(SlidePage(
            index=8, slide_type="comparison", title="正常油液 vs 污染油液",
            layout={"template": "concept_comparison"},
            elements=[
                mk_elem("image", {"kind": "photo", "theme": "清澈透明的液压油样品", "placeholder": True}, 1),
                mk_elem("text", {"text": "正常油液：淡黄色、透明、无异味"}, 2),
                mk_elem("image", {"kind": "photo", "theme": "乳化发白的浑浊液压油", "placeholder": True}, 3),
                mk_elem("text", {"text": "乳化油液：呈乳白色，混入水分，需更换"}, 4)
            ], speaker_notes=""
        ))
        
        # Page 9: 常用维护工具
        pages.append(SlidePage(
            index=9, slide_type="tools", title="维修保养常用工具",
            layout={"template": "grid_4"},
            elements=[
                mk_elem("image", {"kind": "photo", "theme": "液压专用压力表，黑色表盘，指针指向高压区"}, 1),
                mk_elem("image", {"kind": "photo", "theme": "工业滤芯拆卸专用扳手，金属工具"}, 2),
                mk_elem("image", {"kind": "photo", "theme": "便携式油液颗粒计数器，手持检测仪器，屏幕显示数据"}, 3),
                mk_elem("image", {"kind": "photo", "theme": "工业红外测温仪，手持式，激光瞄准点"}, 4)
            ], speaker_notes=""
        ))
        
        # Page 10: 总结
        pages.append(SlidePage(
            index=10, slide_type="summary", title="课程总结",
            layout={"template": "title_bullets"},
            elements=[mk_elem("bullets", {"items": [
                "液压系统通过液压油传递动力，遵循帕斯卡定律",
                "五大组成部分各司其职，缺一不可",
                "正确的启动和维护流程能延长系统寿命",
                "油液清洁度是液压系统的生命线"
            ]}, 1)], speaker_notes=""
        ))

        deck = SlideDeckContent(deck_title="液压系统原理与维护", pages=pages)

        # Style Config
        style_config = StyleConfig(
            style_name="professional",
            color=ColorConfig(primary="#2c3e50", secondary="#ecf0f1", accent="#3498db", text="#2c3e50", muted="#95a5a6", background="#ffffff", warning="#e74c3c"),
            font=FontConfig(title_family="Microsoft YaHei", body_family="Microsoft YaHei", title_size=40, body_size=24),
            layout=StyleLayoutConfig(density="comfortable", notes_area=True), # Corrected schema
            imagery=ImageryConfig(image_style="photorealistic", icon_style="flat")
        )

        # Teaching Request
        teaching_req = TeachingRequest(
            teaching_scenario=TeachingScenarioDetail(scene_type="practice", scene_label="实操"),
            subject_info={"subject_category": "engineering"}, # Mock nested input
            knowledge_points=[], 
            teaching_objectives=TeachingObjectivesStructured(knowledge=[], ability=[], literacy=[]),
            slide_requirements=SlideRequirementsDetail(target_count=10),
            special_requirements=SpecialRequirementsDetailed()
        )
        # Manually ensure category is set if needed (but subject_info above handles it)
        
        
        # 调用渲染 (HTML立即生成)
        output_dir = Path(DATA_DIR) / "outputs"
        session_id = f"mock_{int(time.time())}"
        
        result = render_html_slides(
            deck_content=deck,
            style_config=style_config,
            teaching_request=teaching_req,
            session_id=session_id,
            output_dir=str(output_dir),
        )
        
        # 触发后台生图
        if result.image_slots:
            background_tasks.add_task(generate_images_task, session_id, result.image_slots, output_dir)
        
        logger.emit(session_id, "3.5", "mock_render_start", {"html": result.html_path, "slots": len(result.image_slots)})
        
        return {
            "ok": True,
            "html_path": result.html_path,
            "sesson_id": session_id, # for polling
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
if os.path.isdir(FRONTEND_DIR):
    dist = Path(FRONTEND_DIST_DIR)
    directory = str(dist) if dist.exists() else FRONTEND_DIR
    app.mount("/", StaticFiles(directory=directory, html=True), name="frontend")
