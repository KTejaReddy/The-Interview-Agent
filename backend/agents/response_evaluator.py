"""Response evaluator.

Rates the candidate's answer on a 0-10 scale, assigns a verdict and decides
the interviewer's next move (deeper / simplify / recovery / probe / move on).
The decision feeds both the follow-up generator and the state machine.
"""
from __future__ import annotations

from dataclasses import dataclass

from memory.context_manager import InterviewContext
from models.enums import Difficulty, FollowUpStrategy, Verdict
from models.plan import PlannedQuestion
from schemas.llm import EvaluationDraft
from services.llm_service import LLMService
from services.prompt_builder import PromptBuilder

_VERDICT_MAP = {
    "excellent": Verdict.EXCELLENT,
    "good": Verdict.GOOD,
    "weak": Verdict.WEAK,
    "wrong": Verdict.WRONG,
    "unclear": Verdict.UNCLEAR,
}

_STRATEGY_MAP = {
    "deeper": FollowUpStrategy.DEEPER,
    "simplify": FollowUpStrategy.SIMPLIFY,
    "recovery": FollowUpStrategy.RECOVERY,
    "probe": FollowUpStrategy.PROBE,
    "next_topic": FollowUpStrategy.NEXT_TOPIC,
}


@dataclass
class EvaluationResult:
    """Outcome of evaluating one answer."""

    score: int
    verdict: Verdict
    strategy: FollowUpStrategy
    mastered_topic: bool
    notes: str

    @property
    def wants_follow_up(self) -> bool:
        """True when the interviewer should stay on the topic."""
        return self.strategy in {
            FollowUpStrategy.DEEPER,
            FollowUpStrategy.SIMPLIFY,
            FollowUpStrategy.RECOVERY,
            FollowUpStrategy.PROBE,
        }


class ResponseEvaluator:
    """Single-responsibility evaluator (LLM-backed)."""

    def __init__(self, llm: LLMService, prompts: PromptBuilder) -> None:
        self._llm = llm
        self._prompts = prompts

    async def evaluate(
        self,
        context: InterviewContext,
        question: PlannedQuestion,
        answer: str,
    ) -> EvaluationResult:
        prompt = self._prompts.evaluate_prompt(
            context,
            question=question.question,
            topic=question.topic,
            question_type=question.question_type.value,
            difficulty=question.difficulty.value,
            intent=question.intent,
            answer=answer,
        )
        draft: EvaluationDraft = await self._llm.structured_completion(
            system_prompt=self._prompts.system_prompt(),
            user_prompt=prompt,
            schema=EvaluationDraft,
        )
        return EvaluationResult(
            score=draft.score,
            verdict=_VERDICT_MAP.get(draft.verdict, Verdict.UNCLEAR),
            strategy=_STRATEGY_MAP.get(draft.follow_up, FollowUpStrategy.NEXT_TOPIC),
            mastered_topic=draft.mastered_topic,
            notes=draft.notes,
        )
