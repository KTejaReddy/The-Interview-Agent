"""Request-scoped context variables.

Provides a thread-safe / async-safe way to access the active session
without passing it deeply through every service method signature.
"""
from __future__ import annotations

import contextvars
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from models.session import InterviewSession

current_session: contextvars.ContextVar[Optional["InterviewSession"]] = contextvars.ContextVar(
    "current_session", default=None
)
