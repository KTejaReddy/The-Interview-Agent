"""Session manager.

In-memory store for interview sessions (no database).  Provides creation,
lookup, update and TTL-based expiry.  All operations are safe for use with
FastAPI's async handlers via a single asyncio lock.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from config import Settings
from models.session import InterviewSession
from utils.errors import SessionExpiredError, SessionNotFoundError
from utils.logging import get_logger

logger = get_logger(__name__)


class SessionManager:
    """Thread-safe in-memory session repository."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._sessions: dict[str, InterviewSession] = {}
        self._lock = asyncio.Lock()

    @staticmethod
    def new_session_id() -> str:
        return str(uuid.uuid4())

    async def create(self, session: InterviewSession) -> InterviewSession:
        async with self._lock:
            self._sessions[session.session_id] = session
        logger.debug("Session created: %s", session.session_id)
        return session

    async def get(self, session_id: str) -> InterviewSession:
        async with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(
                f"No session with id '{session_id}'. Start a new interview "
                "by calling POST /api/interview without a sessionId."
            )
        if self._is_expired(session):
            async with self._lock:
                self._sessions.pop(session_id, None)
            raise SessionExpiredError(
                f"Session '{session_id}' has expired after "
                f"{self._settings.session_ttl_seconds}s of inactivity."
            )
        return session

    async def update(self, session: InterviewSession) -> InterviewSession:
        session.touch()
        async with self._lock:
            self._sessions[session.session_id] = session
        return session

    async def delete(self, session_id: str) -> None:
        async with self._lock:
            self._sessions.pop(session_id, None)

    async def sweep_expired(self) -> int:
        """Remove expired sessions; returns how many were dropped."""
        now = datetime.now(timezone.utc)
        async with self._lock:
            expired = [
                sid
                for sid, session in self._sessions.items()
                if (now - session.updated_at).total_seconds()
                > self._settings.session_ttl_seconds
            ]
            for sid in expired:
                self._sessions.pop(sid, None)
        if expired:
            logger.info("Swept %d expired session(s)", len(expired))
        return len(expired)

    async def size(self) -> int:
        async with self._lock:
            return len(self._sessions)

    def _is_expired(self, session: InterviewSession) -> bool:
        now = datetime.now(timezone.utc)
        return (
            now - session.updated_at
        ).total_seconds() > self._settings.session_ttl_seconds
