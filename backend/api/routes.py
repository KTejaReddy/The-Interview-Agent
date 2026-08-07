"""API routes.

* ``POST /api/interview``  -- main conversational endpoint
* ``GET  /api/interview/{session_id}`` -- resume / inspect a session
* ``GET  /api/candidates`` -- candidates from candidate.json
* ``GET  /api/health``     -- service & dataset status
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from agents.interview_manager import InterviewManager
from schemas.api import (
    CandidateSummary,
    HealthResponse,
    InterviewRequest,
    InterviewResponse,
    SessionSnapshot,
)
from services.session_manager import SessionManager
from utils.context import current_session
from utils.errors import DatasetUnavailableError, SessionCandidateMismatchError
from utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["interview"])


def _services(request: Request) -> dict:
    return request.app.state.services


@router.post("/interview", response_model=InterviewResponse)
async def post_interview(
    payload: InterviewRequest, request: Request
) -> InterviewResponse:
    """Drive the interview one turn at a time.

    Omit ``sessionId`` to start a fresh interview for ``candidateId``;
    include it to continue the existing session.
    """
    services = _services(request)
    manager: InterviewManager = services["manager"]
    sessions: SessionManager = services["sessions"]

    if not payload.sessionId:
        session = await manager.start_session(payload.candidateId, payload.message)
    else:
        session = await sessions.get(payload.sessionId)
        if session.candidate_id != payload.candidateId:
            raise SessionCandidateMismatchError(
                "candidateId does not match the session's candidate",
                detail={
                    "sessionCandidate": session.candidate_id,
                    "requestedCandidate": payload.candidateId,
                },
            )

    current_session.set(session)
    result = await manager.handle_message(session, payload.message)
    return InterviewResponse(**result.to_api())


@router.get("/interview/{session_id}", response_model=SessionSnapshot)
async def get_session(session_id: str, request: Request) -> SessionSnapshot:
    """Return the full snapshot of a session (for resume / inspection)."""
    services = _services(request)
    manager: InterviewManager = services["manager"]
    sessions: SessionManager = services["sessions"]
    session = await sessions.get(session_id)
    return SessionSnapshot(
        sessionId=session.session_id,
        candidateId=session.candidate_id,
        state=session.state.value,
        questionNumber=session.current_question_index + 1,
        totalQuestions=session.plan.size,
        interviewComplete=session.completed,
        messages=list(session.transcript),
        feedback=session.feedback.to_api_payload() if session.feedback else None,
    )


@router.get("/candidates", response_model=list[CandidateSummary])
async def list_candidates(request: Request) -> list[CandidateSummary]:
    """List every candidate inside candidate.json (read-only)."""
    services = _services(request)
    loader = services["candidate_loader"]
    summaries = loader.summaries()
    if not loader.is_available:
        raise DatasetUnavailableError(
            loader.error or "candidate.json unavailable",
            detail={"path": str(loader.path)},
        )
    return [CandidateSummary(**summary) for summary in summaries]


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    """Service health, dataset status and LLM configuration status."""
    services = _services(request)
    settings = services["settings"]
    curriculum = services["curriculum_retriever"]
    loader = services["candidate_loader"]
    spec = services["spec_loader"]
    llm = services["llm"]

    datasets_error = None
    for name, available in (
        ("curriculum.json", curriculum.available),
        ("candidate.json", loader.is_available),
        ("technical-spec.md", spec.is_available),
    ):
        if not available:
            datasets_error = datasets_error or (
                f"{name} is missing or malformed in {settings.data_dir}"
            )

    return HealthResponse(
        status="ok" if not datasets_error else "degraded",
        app=settings.app_name,
        curriculumDays=curriculum.day_count,
        candidates=len(loader.all()),
        specLoaded=spec.is_available,
        llmConfigured=llm.configured,
        mockMode=settings.llm_mock_mode,
        datasetsError=datasets_error,
    )
