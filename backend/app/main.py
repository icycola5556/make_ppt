from __future__ import annotations

import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
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
from typing import List, Optional
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
        session_id=req.session_id,
        status="ok",
        stage=stage,
        teaching_request=state.teaching_request,
        style_config=state.style_config,
        style_samples=state.style_samples,
        outline=state.outline,
        deck_content=state.deck_content,
        logs_preview=logger.preview(req.session_id),
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
    return logger.read_all(session_id)



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
        cfg, samples, warnings, reasoning = await engine.refine_style(req.session_id, req.feedback)
        return StyleRefineResponse(
            ok=True,
            style_config=cfg,
            style_samples=samples,
            warnings=warnings,
            reasoning=reasoning
        )
    except Exception as e:
        logger.emit(req.session_id, "3.2", "refine_api_error", {"error": str(e)})
        return StyleRefineResponse(
            ok=False,
            style_config=None,
            style_samples=[],
            warnings=[],
            reasoning=None,
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


@app.get("/api/slide-types")
def get_slide_types():
    """获取所有可用的slide_type定义"""
    from .modules.outline.core import get_slide_types as get_types
    return get_types()


# Serve frontend (pure static) for easy demo
if os.path.isdir(FRONTEND_DIR):
    dist = Path(FRONTEND_DIST_DIR)
    directory = str(dist) if dist.exists() else FRONTEND_DIR
    app.mount("/", StaticFiles(directory=directory, html=True), name="frontend")
