"""Follow-up generator.

Every answer influences the next question.  When the evaluator decides the
interviewer should stay on the topic, this agent produces a follow-up that
is adapted to the answer:

* good answer   -> deeper question,
* weak answer   -> simplified sub-question,
* wrong answer  -> recovery / scaffolding question,
* unclear       -> clarification probe.

The generated follow-up is grounded in the same curriculum day and never
leaps to a new topic.
"""
from __future__ import annotations

from dataclasses import dataclass

from agents.difficulty_manager import DifficultyManager
from memory.context_manager import InterviewContext
from models.enums import Difficulty, FollowUpStrategy, Verdict
from models.plan import PlannedQuestion
from retrieval.curriculum_retriever import CurriculumRetriever
from schemas.llm import FollowUpDraft
from services.llm_service import LLMService
from services.prompt_builder import PromptBuilder


@dataclass
class FollowUpResult:
    """The generated follow-up question."""

    question: str
    intent: str
    difficulty: Difficulty


class FollowUpGenerator:
    """Single-responsibility follow-up generator (LLM-backed)."""

    def __init__(
        self,
        llm: LLMService,
        prompts: PromptBuilder,
        retriever: CurriculumRetriever,
        difficulty_manager: DifficultyManager | None = None,
    ) -> None:
        self._llm = llm
        self._prompts = prompts
        self._retriever = retriever
        self._difficulty = difficulty_manager or DifficultyManager()

    async def generate(
        self,
        context: InterviewContext,
        question: PlannedQuestion,
        answer: str,
        verdict: Verdict,
        score: int,
        strategy: FollowUpStrategy,
        notes: str,
    ) -> FollowUpResult:
        curriculum = self._retriever.ground_context(question.day_index)
        difficulty = self._difficulty.follow_up_difficulty(strategy)
        prompt = self._prompts.follow_up_prompt(
            context,
            question=question.question,
            topic=question.topic,
            answer=answer,
            verdict=verdict.value,
            score=score,
            strategy=strategy.value,
            notes=notes,
            curriculum=curriculum,
            difficulty=difficulty.value,
        )
        draft: FollowUpDraft = await self._llm.structured_completion(
            system_prompt=self._prompts.system_prompt(),
            user_prompt=prompt,
            schema=FollowUpDraft,
        )
        return FollowUpResult(
            question=draft.question,
            intent=draft.intent,
            difficulty=Difficulty(draft.difficulty),
        )
