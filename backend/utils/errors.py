"""Domain exceptions for the interview engine.

Each exception carries an HTTP status code so API layer can translate it
into a proper error response without scattering business logic in routes.
"""
from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base class for all application-level errors."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str, *, detail: Any | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
        }
        if self.detail is not None:
            payload["detail"] = self.detail
        return payload


class CandidateNotFoundError(AppError):
    """The requested candidate does not exist in candidate.json."""

    status_code = 404
    code = "candidate_not_found"


class SessionNotFoundError(AppError):
    """The sessionId does not map to any live interview session."""

    status_code = 404
    code = "session_not_found"


class SessionExpiredError(AppError):
    """The sessionId exists but its TTL has elapsed."""

    status_code = 410
    code = "session_expired"


class DatasetUnavailableError(AppError):
    """Required dataset files are missing or malformed."""

    status_code = 503
    code = "datasets_unavailable"


class CurriculumUnavailableError(DatasetUnavailableError):
    """curriculum.json could not be loaded."""

    code = "curriculum_unavailable"


class LLMNotConfiguredError(AppError):
    """No LLM provider is configured (no API key, mock mode disabled)."""

    status_code = 503
    code = "llm_not_configured"


class LLMError(AppError):
    """The LLM provider returned an error or malformed output."""

    status_code = 502
    code = "llm_error"


class InvalidStateTransitionError(AppError):
    """An illegal state-machine transition was attempted."""

    status_code = 409
    code = "invalid_state_transition"


class SessionCandidateMismatchError(AppError):
    """The request's candidateId does not match the session's candidate."""

    status_code = 409
    code = "session_candidate_mismatch"


class MalformedRequestError(AppError):
    """The request payload failed validation."""

    status_code = 400
    code = "malformed_request"
