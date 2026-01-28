from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List
from .security import validate_session_id


@dataclass
class LogEvent:
    ts: float
    ts_utc: str
    ts_local: str
    session_id: str
    stage: str
    kind: str
    payload: Dict[str, Any]


def _iso_utc(ts: float) -> str:
    # ISO 8601 UTC timestamp, e.g. 2026-01-07T09:12:34Z
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _iso_local(ts: float) -> str:
    # ISO 8601 local timestamp with offset, e.g. 2026-01-07T01:12:34-08:00
    return datetime.fromtimestamp(ts, tz=timezone.utc).astimezone().isoformat(timespec="seconds")


def _log_path(data_dir: str, session_id: str) -> str:
    # Security: Validate session_id to prevent path traversal
    try:
        validate_session_id(session_id)
    except ValueError:
        # Fallback for invalid session_id to prevent crash, but ensure safety
        # In practice, this should be caught earlier
        session_id = "invalid_session"
        
    return os.path.join(data_dir, "logs", f"{session_id}.jsonl")


class WorkflowLogger:
    """Write per-session JSONL logs.

    We log:
    - module input/output
    - LLM prompt/response (redact keys)
    - user answers
    - validation results

    This directly addresses the user's requirement: every step's I/O and
    LLM adjustments must be recorded as logs.
    """

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        os.makedirs(os.path.join(self.data_dir, "logs"), exist_ok=True)

    def emit(self, session_id: str, stage: str, kind: str, payload: Dict[str, Any]) -> None:
        ts = time.time()
        evt = LogEvent(
            ts=ts,
            ts_utc=_iso_utc(ts),
            ts_local=_iso_local(ts),
            session_id=session_id,
            stage=stage,
            kind=kind,
            payload=payload,
        )
        path = _log_path(self.data_dir, session_id)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(evt.__dict__, ensure_ascii=False) + "\n")

    def preview(self, session_id: str, limit: int = 30) -> List[Dict[str, Any]]:
        path = _log_path(self.data_dir, session_id)
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()[-limit:]
        out: List[Dict[str, Any]] = []
        for ln in lines:
            try:
                out.append(json.loads(ln))
            except Exception:
                continue
        return out

    def read_all(self, session_id: str) -> str:
        path = _log_path(self.data_dir, session_id)
        if not os.path.exists(path):
            return ""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
