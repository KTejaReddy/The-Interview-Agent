"""Security guard for untrusted candidate messages.

Two layers:

1. **Deterministic** — :mod:`utils.input_guard` runs on every message at
   zero cost (it already sanitises input before the engine sees it).
2. **Model guards** — when a message shows soft signals of an override /
   extraction / jailbreak attempt (or the deterministic layer already
   fired), the *light* prompt-guard model (22M) classifies it; a
   ``suspicious`` light verdict is escalated to the *strong* guard (86M),
   and key/system-prompt extraction attempts additionally go through the
   *safeguard* model (20B).  Guard models only classify — they never
   generate interviewer language.

Normal technical answers skip the guard models entirely (zero extra LLM
calls on the happy path).  A confirmed attempt is answered with a short,
in-persona deflection and the interview does NOT advance: the candidate is
still expected to answer the current question.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from utils.input_guard import input_guard
from utils.logging import get_logger

logger = get_logger(__name__)

#: Soft signals that justify running the (cheap) light guard model.  Normal
#: technical answers about prompts/APIs are deliberately NOT all escalated —
#: the light guard only runs when there is some hint of an attempt.
_SOFT_SIGNALS = re.compile(
    r"\b(instructions|prompt|system|override|ignore|reveal|expose|"
    r"secret|key|jailbreak|developer mode|do anything now)\b",
    re.I,
)

#: Phrases that make an attempt an *extraction* attempt (API key / system
#: prompt), warranting the safeguard model as an extra validation layer.
_EXTRACTION = re.compile(
    r"(api\s*key|system\s+prompt|environment\s+variables|secret|reveal)",
    re.I,
)

#: Short, in-character deflections.  Rotated deterministically; the
#: interviewer stays in role and never engages with the injection.
_DEFLECTIONS = (
    "I'm here to run your technical interview — let's get back to the question.",
    "We'll keep this to the interview. Can you answer the question?",
    "Let's stay on the technical question at hand.",
)


@dataclass
class ScreenResult:
    """Outcome of screening one candidate message."""

    flagged: bool
    models_used: list[str] = field(default_factory=list)
    reason: str = ""


class SecurityGuard:
    """Two-layer candidate-message screening (deterministic + model guards)."""

    def __init__(self, llm, prompts) -> None:
        self._llm = llm
        self._prompts = prompts
        self._deflections_used = 0

    # ------------------------------------------------------------------ public

    async def screen(self, message: str) -> ScreenResult:
        """Classify a candidate message.

        Zero guard-model calls for normal messages.  Deterministically
        flagged messages are confirmed by the guards; soft-signal messages
        get a light-guard pass first.  If the guard models themselves are
        unavailable the deterministic verdict stands (fail-safe toward the
        deterministic layer, which already runs on every message).
        """
        if not message or not message.strip():
            return ScreenResult(flagged=False)

        deterministic = input_guard.is_suspicious(message)
        if not deterministic and not _SOFT_SIGNALS.search(message):
            return ScreenResult(flagged=False)

        reason = "deterministic pattern" if deterministic else "soft signal"
        models_used: list[str] = []
        try:
            # If we already have a deterministic hit, go straight to the
            # confirm path (light -> strong -> safeguard when extracting).
            if deterministic:
                return await self._confirm(
                    message, reason=reason, models_used=models_used
                )

            light = await self._classify(message, task="guard_light")
            models_used.append(self._last_guard_model())
            if light.flag == "suspicious":
                return await self._confirm(
                    message,
                    reason=f"{reason} -> light guard flagged",
                    models_used=models_used,
                )
            return ScreenResult(flagged=False, models_used=models_used)
        except Exception as exc:  # guard failure must never break the interview
            logger.warning("Guard screening failed (%s) — using deterministic verdict", exc)
            return ScreenResult(flagged=deterministic, models_used=models_used)

    def deflection(self) -> str:
        """A short in-character reply for a confirmed injection attempt.
        Rotates so consecutive deflections read differently."""
        text = _DEFLECTIONS[self._deflections_used % len(_DEFLECTIONS)]
        self._deflections_used += 1
        return text

    # ------------------------------------------------------------------ internals

    def _last_guard_model(self) -> str:
        """Model the guard just used (recorded by the LLM service)."""
        return getattr(self._llm, "_last_guard_model", "") or "guard"

    async def _confirm(
        self, message: str, *, reason: str, models_used: list[str]
    ) -> ScreenResult:
        """Escalation path: light guard -> strong guard -> safeguard."""
        light = await self._classify(message, task="guard_light")
        models_used.append(self._last_guard_model())
        if light.flag != "suspicious":
            return ScreenResult(flagged=False, models_used=models_used)

        strong = await self._classify(message, task="guard_strong")
        models_used.append(self._last_guard_model())
        if strong.flag != "suspicious":
            return ScreenResult(flagged=False, models_used=models_used)

        if _EXTRACTION.search(message):
            try:
                safeguard = await self._classify(message, task="safeguard")
                models_used.append(self._last_guard_model())
                if safeguard.flag != "suspicious":
                    return ScreenResult(
                        flagged=False, models_used=models_used
                    )
            except Exception as exc:
                logger.warning("Safeguard model unavailable (%s)", exc)

        logger.warning(
            "Injection attempt confirmed (guards=%s) — deflecting",
            models_used,
        )
        return ScreenResult(
            flagged=True, models_used=models_used, reason=reason
        )

    async def _classify(self, message: str, *, task: str):
        prompt = self._prompts.security_check_prompt(message)
        return await self._llm.classify(task=task, user_prompt=prompt)
