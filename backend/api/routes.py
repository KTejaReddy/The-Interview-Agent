"""API routes.

* ``POST /api/interview``  -- main conversational endpoint (spec contract)
* ``GET  /api/interview/{session_id}`` -- resume / inspect a session
* ``GET  /api/candidates`` -- candidates from candidates.json
* ``GET  /api/health``     -- service & dataset status

POST /api/interview
-------------------
Accepts two request shapes, exactly per ``technical-spec.md``:

* START (first request): ``{"sessionId": "...", "candidate": {...}}`` — the
  client supplies the session id and the full candidate object.  A
  ``candidateId`` shorthand is also accepted for the bundled frontend.
* TURN (every later request): ``{"sessionId": "...", "message": "..."}``.

Responses always carry the spec fields ``reply`` and ``done``.  When the
request advertises ``Accept: text/event-stream`` the same payload is
delivered as a single SSE ``reply`` event (preceded by ``phase`` events),
keeping the streaming capability while preserving the structured
architecture.
"""
from __future__ import annotations

import json
from typing import Annotated, Any, AsyncIterator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from agents.interview_manager import InterviewManager
from config import settings as app_settings
from schemas.api import (
    CandidateSummary,
    HealthResponse,
    InterviewRequest,
    InterviewResponse,
    SessionSnapshot,
)
from services.session_manager import SessionManager
from utils.context import current_session
from utils.errors import (
    AppError,
    DatasetUnavailableError,
    MalformedRequestError,
    SessionCandidateMismatchError,
)
from utils.input_guard import input_guard
from utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["interview"])

_SSE_MEDIA = "text/event-stream"


def _services(request: Request) -> dict:
    return request.app.state.services


def _sse(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload)}\n\n"


def _extract_candidate_id(candidate: dict[str, Any]) -> str:
    """Pull the candidate id from the client-supplied candidate object."""
    member = candidate.get("member") if isinstance(candidate.get("member"), dict) else {}
    for source in (member, candidate):
        for key in ("id", "candidateId", "candidate_id"):
            value = source.get(key)
            if value not in (None, ""):
                return str(value)
    return ""


def _resolve_start(services: dict, payload: InterviewRequest) -> str:
    """Determine the authoritative candidate id for a start request."""
    candidate_loader = services["candidate_loader"]
    candidate_id = (payload.candidateId or "").strip()
    if payload.candidate:
        candidate_id = candidate_id or _extract_candidate_id(payload.candidate)
    if not candidate_id:
        raise MalformedRequestError(
            "A start request must include 'candidate' (with an id) or 'candidateId'."
        )
    # Validate the candidate exists in the authoritative dataset.  The
    # interview always profiles the dataset's record, never a client copy.
    try:
        candidate_loader.get(candidate_id)
    except AppError:
        raise
    return candidate_id


async def _run_turn(services: dict, payload: InterviewRequest) -> InterviewResponse:
    """Execute one conversational turn and return the spec-shaped response."""
    manager: InterviewManager = services["manager"]
    sessions: SessionManager = services["sessions"]

    # --- START ------------------------------------------------------------
    if payload.is_start() or (payload.candidateId and not payload.sessionId):
        candidate_id = _resolve_start(services, payload)
        session_id = (payload.sessionId or "").strip() or sessions.new_session_id()
        existing = None
        try:
            existing = await sessions.get(session_id)
        except AppError:
            existing = None
        if existing is not None:
            raise MalformedRequestError(
                f"A session with id '{session_id}' already exists. "
                "Use a fresh sessionId to start a new interview."
            )
        # Sanitise the opening message (usually a greeting) before dispatch.
        message = input_guard.sanitize(payload.message or "") or "Hello!"
        session = await manager.start_session(
            candidate_id, first_message=message, session_id=session_id
        )
        current_session.set(session)
        result = await manager.handle_message(session, message)
        return InterviewResponse(**result.to_api())

    # --- TURN -------------------------------------------------------------
    if payload.is_turn():
        if not (payload.sessionId or "").strip():
            raise MalformedRequestError("sessionId is required to continue an interview.")
        sessions: SessionManager = services["sessions"]
        session = await sessions.get(payload.sessionId.strip())
        if payload.candidateId:
            if session.candidate_id != payload.candidateId.strip():
                raise SessionCandidateMismatchError(
                    "candidateId does not match the session's candidate",
                    detail={
                        "sessionCandidate": session.candidate_id,
                        "requestedCandidate": payload.candidateId,
                    },
                )
        message = input_guard.sanitize(payload.message or "")
        if not message:
            raise MalformedRequestError("message must not be blank.")
        current_session.set(session)
        result = await manager.handle_message(session, message)
        return InterviewResponse(**result.to_api())

    raise MalformedRequestError(
        "Request must include either 'candidate'/'candidateId' (to start) "
        "or 'sessionId' + 'message' (to continue)."
    )


@router.post("/interview", response_model=InterviewResponse)
async def post_interview(payload: InterviewRequest, request: Request):
    """Drive the interview one turn at a time (spec contract)."""
    services = _services(request)

    wants_stream = (request.headers.get("accept") or "").find(_SSE_MEDIA) != -1
    if wants_stream:

        async def event_stream() -> AsyncIterator[str]:
            try:
                yield _sse({"type": "phase", "phase": "thinking"})
                response = await _run_turn(services, payload)
                yield _sse({"type": "reply", "payload": response.model_dump(exclude_none=True)})
            except AppError as exc:
                yield _sse(
                    {
                        "type": "error",
                        "error": {"code": exc.code, "message": exc.message},
                    }
                )

        return StreamingResponse(
            event_stream(),
            media_type=_SSE_MEDIA,
            headers={
                "Cache-Control": "no-cache, no-transform",
                "X-Accel-Buffering": "no",
            },
        )

    response = await _run_turn(services, payload)
    return response


@router.get("/interview/{session_id}", response_model=SessionSnapshot)
async def get_session(session_id: str, request: Request) -> SessionSnapshot:
    """Return the full snapshot of a session (for resume / inspection)."""
    services = _services(request)
    sessions: SessionManager = services["sessions"]
    session = await sessions.get(session_id)
    # The snapshot reports ACTUAL interviewer questions (mains + follow-ups
    # + the one just asked), matching the live turn responses — a follow-up
    # is also a question, so the count never understates the conversation.
    question_number = session.memory.count + 1
    return SessionSnapshot(
        sessionId=session.session_id,
        candidateId=session.candidate_id,
        state=session.state.value,
        questionNumber=question_number,
        totalQuestions=max(question_number, app_settings.min_questions),
        interviewComplete=session.completed,
        messages=list(session.transcript),
        feedback=session.feedback.to_api_payload() if session.feedback else None,
    )


@router.get("/candidates", response_model=list[CandidateSummary])
async def list_candidates(request: Request) -> list[CandidateSummary]:
    """List every candidate inside candidates.json (read-only)."""
    services = _services(request)
    loader = services["candidate_loader"]
    summaries = loader.summaries()
    if not loader.is_available:
        raise DatasetUnavailableError(
            loader.error or "candidate dataset unavailable",
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
        ("candidates.json", loader.is_available),
        ("technical-spec.md", spec.is_available),
    ):
        if not available:
            datasets_error = datasets_error or (
                f"{name} is missing or malformed in the configured data directory"
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
