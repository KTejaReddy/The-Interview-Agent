"""Tests for the in-memory session manager."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from config import settings
from models.candidate_profile import CandidateProfile
from models.session import InterviewSession
from services.session_manager import SessionManager
from utils.errors import SessionExpiredError, SessionNotFoundError


def _make_session(session_id: str) -> InterviewSession:
    return InterviewSession(
        session_id=session_id,
        candidate_id="candidate-1",
        profile=CandidateProfile(candidate_id="candidate-1"),
    )


@pytest.mark.asyncio
async def test_create_and_get() -> None:
    manager = SessionManager(settings)
    session = _make_session("s-1")
    await manager.create(session)

    fetched = await manager.get("s-1")
    assert fetched.session_id == "s-1"
    assert (await manager.size()) == 1


@pytest.mark.asyncio
async def test_get_missing_raises_404() -> None:
    manager = SessionManager(settings)
    with pytest.raises(SessionNotFoundError):
        await manager.get("missing")


@pytest.mark.asyncio
async def test_expired_session_raises() -> None:
    manager = SessionManager(settings)
    session = _make_session("s-old")
    session.updated_at = datetime.now(timezone.utc) - timedelta(
        seconds=settings.session_ttl_seconds + 10
    )
    await manager.create(session)

    with pytest.raises(SessionExpiredError):
        await manager.get("s-old")


@pytest.mark.asyncio
async def test_sweep_removes_expired() -> None:
    manager = SessionManager(settings)
    fresh = _make_session("s-fresh")
    stale = _make_session("s-stale")
    stale.updated_at = datetime.now(timezone.utc) - timedelta(
        seconds=settings.session_ttl_seconds + 10
    )
    await manager.create(fresh)
    await manager.create(stale)

    removed = await manager.sweep_expired()
    assert removed == 1
    with pytest.raises(SessionNotFoundError):
        await manager.get("s-stale")
    assert await manager.get("s-fresh")
