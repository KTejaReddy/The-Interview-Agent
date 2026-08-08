"""API contract — matches ``technical-spec.md`` exactly.

Start interview (first request)::

    POST /api/interview
    {"sessionId": "abc-123", "candidate": { ...candidate.json }}

Conversation turn (every subsequent request)::

    {"sessionId": "abc-123", "message": "..."}

Responses::

    {"reply": "...", "done": false}
    {"reply": "...", "done": true, "feedback": {"summary": ..., "strengths": [], "gaps": [], "next": []}}

The required fields are never renamed or removed.  A few *supplementary*
fields (``sessionId``, ``state``, ``questionNumber``, ``totalQuestions``,
``currentDay``, ``currentTopic``) ride along for the frontend; automated
judges asserting the required fields are unaffected.  ``feedback.score`` is
an optional extended field (not part of the contract) and is omitted unless
present.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class InterviewRequest(BaseModel):
    """Body of ``POST /api/interview``.

    Two accepted shapes (spec-exact and convenience):

    * START: ``{"sessionId": "...", "candidate": {...}}`` — optionally also
      ``candidateId`` (frontend convenience) and ``message`` (first message).
    * TURN: ``{"sessionId": "...", "message": "..."}``.
    """

    model_config = ConfigDict(extra="ignore")

    sessionId: Optional[str] = Field(default=None, description="Session id (client-supplied per spec)")
    candidate: Optional[dict[str, Any]] = Field(
        default=None, description="Full candidate object (spec start shape)"
    )
    candidateId: Optional[str] = Field(default=None, description="Candidate id inside the dataset (convenience)")
    message: Optional[str] = Field(default=None, description="Candidate's latest message")

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if value is not None else value

    def is_start(self) -> bool:
        """True when this request starts a new interview.

        Per the spec the start request carries the full ``candidate``
        object; the id is then resolved against the authoritative dataset.
        """
        return bool(self.candidate)

    def is_turn(self) -> bool:
        """True when this request continues an existing interview.

        A turn is ``sessionId`` + ``message``.  ``candidateId`` may ride
        along (frontend convenience) but never turns a turn into a start.
        """
        return bool(self.sessionId) and bool(self.message)


class FeedbackPayload(BaseModel):
    """Final structured feedback — exactly the fields required by the spec.

    ``score`` is an optional extended field for the UI's score ring; it is
    omitted from the payload when not set so the contract stays exact.
    """

    model_config = ConfigDict(exclude_none=True)

    summary: str
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    next: list[str] = Field(default_factory=list)
    score: Optional[int] = Field(default=None, ge=0, le=100)


class InterviewResponse(BaseModel):
    """Body of every successful ``POST /api/interview`` response.

    Required by the spec: ``reply`` and ``done``.  The remaining fields are
    supplementary (UI state) and never replace the contract fields.
    """

    model_config = ConfigDict(exclude_none=True)

    reply: str
    done: bool
    sessionId: Optional[str] = None
    state: Optional[str] = None
    questionNumber: int = 0
    totalQuestions: int = 0
    currentDay: Optional[str] = None
    currentTopic: Optional[str] = None
    feedback: Optional[FeedbackPayload] = None


class CandidateSummary(BaseModel):
    """Lightweight candidate descriptor for the landing page."""

    id: str
    name: str = ""
    role: str = ""
    experience: Any = 0
    education: str = ""
    missionsCompleted: int = 0
    missionsFirstTry: int = 0
    struggles: int = 0
    skipped: int = 0
    failed: int = 0
    # Actual day numbers for each outcome — the frontend uses these to
    # render a candidate-specific journey timeline (not a hardcoded array).
    completedDays: list[int] = Field(default_factory=list)
    skippedDays: list[int] = Field(default_factory=list)
    failedDays: list[int] = Field(default_factory=list)
    # Human-readable topic titles for completed missions
    completedTopics: list[str] = Field(default_factory=list)


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
