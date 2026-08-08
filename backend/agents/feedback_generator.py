"""Feedback generator.

At the end of the interview, produces the final structured feedback:

* ``summary`` / ``strengths`` / ``gaps`` / ``next`` -- the only fields the
  API exposes (they match the specification exactly),
* ``score`` / ``confidence`` / ``topics_covered`` -- computed internally and
  persisted on the session but never serialised by the API layer.
"""
from __future__ import annotations

from dataclasses import dataclass

from memory.context_manager import InterviewContext
from schemas.llm import FeedbackDraft, FeedbackResult
from services.llm_service import LLMService
from services.prompt_builder import PromptBuilder
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class InternalMetrics:
    """Internally-computed metrics never exposed via the API."""

    score: int
    confidence: float
    topics_covered: list[str]


class FeedbackGenerator:
    """Single-responsibility final feedback generator (LLM-backed)."""

    def __init__(self, llm: LLMService, prompts: PromptBuilder) -> None:
        self._llm = llm
        self._prompts = prompts

    def compute_internal_metrics(self, context: InterviewContext) -> InternalMetrics:
        """Deterministic internal metrics derived from the conversation memory."""
        memory = context.memory
        raw_score = memory.average_score / 10.0  # 0..1
        coverage = min(1.0, len(memory.days_covered) / max(1, context.plan.distinct_days))
        # Coverage credit is gated by demonstrated quality: a candidate who
        # demonstrated nothing gets no coverage bonus, so a 0/10 average can
        # never produce an unexplained 30/100 — the score reflects evidence.
        score = int(round((0.7 * raw_score + 0.3 * coverage * raw_score) * 100))
        confidence = memory.estimated_confidence
        return InternalMetrics(
            score=max(0, min(100, score)),
            confidence=max(0.0, min(1.0, confidence)),
            topics_covered=memory.topics_covered,
        )

    async def generate(self, context: InterviewContext) -> FeedbackResult:
        """Ask the LLM for qualitative feedback, blending internal metrics.

        ``topics_covered`` is ALWAYS the authoritative list from the session
        memory (the same state the planner and manager use) — it is never
        reconstructed from generated text, and the LLM's own list is ignored
        so feedback can never disagree with the interview state.
        """
        internal = self.compute_internal_metrics(context)
        prompt = self._prompts.feedback_prompt(context)
        try:
            draft: FeedbackDraft = await self._llm.structured_completion(
                system_prompt=self._prompts.system_prompt(),
                user_prompt=prompt,
                schema=FeedbackDraft,
            )
        except Exception:
            # Fall back to internally-computed metrics when the LLM is
            # unavailable at wrap-up time (still fully structured).
            logger.exception("LLM feedback failed; using internal metrics only")
            return FeedbackResult(
                summary=(
                    f"The interview covered {len(internal.topics_covered)} topics "
                    f"across {len(context.memory.days_covered)} curriculum days "
                    f"with an average answer score of "
                    f"{context.memory.average_score:.1f}/10."
                ),
                strengths=[
                    t.topic
                    for t in context.memory.strong_answers
                ][:4] or ["Consistent engagement throughout the interview"],
                gaps=[m.topic for m in context.memory.mistakes][:4]
                or ["Deeper exploration of advanced topics"],
                next=[
                    "Review the curriculum days where answers were weak",
                    "Practice explaining trade-offs out loud",
                ],
                score=internal.score,
                confidence=internal.confidence,
                topics_covered=internal.topics_covered,
            )

        return FeedbackResult(
            summary=draft.summary,
            strengths=draft.strengths,
            gaps=draft.gaps,
            next=draft.next,
            score=draft.score,
            confidence=draft.confidence,
            # Authoritative interview state, never the LLM's guess.
            topics_covered=internal.topics_covered,
        )
