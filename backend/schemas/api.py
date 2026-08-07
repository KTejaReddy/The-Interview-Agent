"""API contract.

These classes are the single source of truth for every payload exchanged
over HTTP.  If ``technical-spec.md`` (once provided) defines a different
field name, adjust it here and nowhere else.

Endpoints
---------
* ``POST /api/interview``          -- drive the conversation turn by turn
* ``GET  /api/interview/{id}``     -- resume / inspect a session
* ``GET  /api/candidates``         -- list candidates from candidate.json
* ``GET  /api/health``             -- service & dataset status
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class InterviewRequest(BaseModel):
    """Body of ``POST /api/interview``.

    On the first message of a session omit ``sessionId``; the server creates
    a session for the given ``candidateId`` and returns the new id.
    """

    candidateId: str = Field(
        ..., min_length=1, description="Candidate id inside candidate.json"
    )
    message: str = Field(
        ..., min_length=1, description="Candidate's latest message"
    )
    sessionId: Optional[str] = Field(
        default=None, description="Existing session id (omit to start fresh)"
    )

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("message must not be blank")
        return stripped


class FeedbackPayload(BaseModel):
    """Final structured feedback — exactly the fields required by the spec."""

    summary: str
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    next: list[str] = Field(default_factory=list)


class InterviewResponse(BaseModel):
    """Body of every successful ``POST /api/interview`` response."""

    sessionId: str
    state: str
    message: str
    questionNumber: int = 0
    totalQuestions: int = 0
    currentDay: Optional[str] = None
    currentTopic: Optional[str] = None
    interviewComplete: bool = False
    feedback: Optional[FeedbackPayload] = None


class CandidateSummary(BaseModel):
    """Lightweight candidate descriptor for the landing page."""

    id: str
    name: str = ""
    role: str = ""


class SessionSnapshot(BaseModel):
    """Full state snapshot returned by ``GET /api/interview/{id}``."""

    sessionId: str
    candidateId: str
    state: str
    questionNumber: int
    totalQuestions: int
    interviewComplete: bool
    messages: list[dict[str, Any]] = Field(default_factory=list)
    feedback: Optional[FeedbackPayload] = None


class HealthResponse(BaseModel):
    """Service health and dataset status."""

    status: str
    app: str
    curriculumDays: int = 0
    candidates: int = 0
    specLoaded: bool = False
    llmConfigured: bool = False
    mockMode: bool = False
    datasetsError: Optional[str] = None


class ErrorResponse(BaseModel):
    """Uniform error envelope for non-2xx responses."""

    detail: dict[str, Any]
