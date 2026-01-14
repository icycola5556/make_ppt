from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Optional

from .schemas import SessionState


class SessionStore:
    """A tiny session store.

    Demo implementation: persist SessionState to JSON files.
    In production you can replace it with Redis/MySQL.
    """

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.sessions_dir = os.path.join(data_dir, "sessions")
        os.makedirs(self.sessions_dir, exist_ok=True)

    def _path(self, session_id: str) -> str:
        return os.path.join(self.sessions_dir, f"{session_id}.json")

    def _history_path(self, session_id: str) -> str:
        # Optional: keep an append-only history for debugging, one JSON object per line.
        return os.path.join(self.sessions_dir, f"{session_id}.jsonl")

    @staticmethod
    def _iso_utc(ts: float) -> str:
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    @staticmethod
    def _iso_local(ts: float) -> str:
        return datetime.fromtimestamp(ts, tz=timezone.utc).astimezone().isoformat(timespec="seconds")

    def create(self, session_id: str) -> SessionState:
        now = time.time()
        state = SessionState(
            session_id=session_id,
            created_at=self._iso_utc(now),
            updated_at=self._iso_utc(now),
        )
        self.save(state)
        return state

    def load(self, session_id: str) -> Optional[SessionState]:
        path = self._path(session_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return SessionState.model_validate(data)

    def save(self, state: SessionState) -> None:
        # Keep timestamps for easier debugging and reproducibility.
        now = time.time()
        if state.created_at is None:
            state.created_at = self._iso_utc(now)
        state.updated_at = self._iso_utc(now)

        path = self._path(state.session_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state.model_dump(mode="json"), f, ensure_ascii=False, indent=2)

        # Append a snapshot record (jsonl) so we can quickly inspect the evolution of a session.
        hist_path = self._history_path(state.session_id)
        record = {
            "ts": now,
            "ts_utc": self._iso_utc(now),
            "ts_local": self._iso_local(now),
            "session_id": state.session_id,
            "stage": state.stage,
            "state": state.model_dump(mode="json"),
        }
        with open(hist_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
