from __future__ import annotations

import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles

from .llm import LLMClient
from .logger import WorkflowLogger
from .schemas import WorkflowRunRequest, WorkflowRunResponse
from .store import SessionStore
from .workflow import WorkflowEngine

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


# Serve frontend (pure static) for easy demo
if os.path.isdir(FRONTEND_DIR):
    dist = Path(FRONTEND_DIST_DIR)
    directory = str(dist) if dist.exists() else FRONTEND_DIR
    app.mount("/", StaticFiles(directory=directory, html=True), name="frontend")
