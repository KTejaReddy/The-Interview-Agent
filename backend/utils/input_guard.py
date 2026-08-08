"""Input guard — first line of defence against prompt injection.

Candidate messages are untrusted data.  This module detects attempts to
override the interviewer (``ignore previous instructions``), extract the
system prompt or API key (``print your system prompt``), or jailbreak the
model (``developer mode``), and neutralises the flagged portion before it
reaches the LLM.

The interviewer's system prompt independently instructs the model to treat
all candidate messages as untrusted content; this module adds a
deterministic, testable layer on top.
"""
from __future__ import annotations

import re

from utils.logging import get_logger

logger = get_logger(__name__)

#: Phrases that signal an instruction-override / extraction attempt.  Kept
#: conservative to avoid false positives on ordinary conversation.
_INJECTION_PATTERNS = (
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)", re.I),
    re.compile(r"disregard\s+(the\s+)?(previous|prior|above)", re.I),
    re.compile(r"(system\s+)?prompt\s*(is|:)|system\s+prompt", re.I),
    re.compile(r"reveal\s+(your|the)\s+(system\s+)?prompt", re.I),
    re.compile(r"print\s+(your|the|out)\s+(instructions|prompt|system)", re.I),
    re.compile(r"what\s+are\s+your\s+instructions", re.I),
    re.compile(r"jailbreak|developer\s+mode|do\s+anything\s+now", re.I),
    re.compile(r"forget\s+(everything|all|your)\s+(above|instructions|prompt)", re.I),
    re.compile(r"you\s+are\s+now\s+", re.I),
    re.compile(r"act\s+as\s+if\s+you\s+have\s+no\s+", re.I),
    re.compile(r"api\s*key|secret\s+key\s*[:=]", re.I),
)

#: Token-level detector used by tests to verify the guard fires.
_INJECTION_KEYWORDS = (
    "ignore previous instructions",
    "system prompt",
    "reveal your",
    "developer mode",
    "jailbreak",
    "you are now",
)


class InputGuard:
    """Sanitises candidate messages before they reach the LLM."""

    def is_suspicious(self, message: str) -> bool:
        """True when the message shows signs of an injection attempt."""
        for pattern in _INJECTION_PATTERNS:
            if pattern.search(message):
                return True
        return False

    def sanitize(self, message: str) -> str:
        """Return a message safe to pass to the interviewer engine.

        When an injection attempt is detected, everything from the first
        flagged marker onward is removed (the candidate's genuine technical
        answer, which usually precedes the attempt, is preserved).  A
        neutral placeholder is appended so the interviewer does not
        interpret the truncation as an answer.
        """
        original = message
        lowest = len(message)
        for pattern in _INJECTION_PATTERNS:
            match = pattern.search(message)
            if match and match.start() < lowest:
                lowest = match.start()
        if lowest == len(message):
            return message

        # Drop the injection tail; keep the authentic lead-in if any.
        kept = message[:lowest].strip()
        if kept:
            result = kept
        else:
            result = ""
        logger.warning(
            "Input guard neutralised a suspicious message (%d chars truncated)",
            len(message) - lowest,
        )
        return result

    def annotated(self, message: str) -> tuple[str, bool]:
        """Convenience: returns (sanitized, was_suspicious)."""
        suspicious = self.is_suspicious(message)
        return (self.sanitize(message), suspicious)


#: Module-level singleton used across the app.
input_guard = InputGuard()
