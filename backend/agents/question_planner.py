"""Question planner.

Builds the interview plan *before* any question is asked:

* at least ``min_questions`` questions (default 8),
* spread across at least ``min_days`` curriculum days (default 4),
* difficulty ramps easy -> medium -> advanced (offset by the candidate's
  baseline difficulty),
* question styles rotate through the ten mixed types without repeating the
  same style twice in a row.

The plan skeleton (days, topics, types, difficulty) is computed locally and
instantly.  Only the actual question *text* is generated with the LLM, on
demand, when the question is about to be asked — this keeps per-turn
latency low while the plan is still fully determined in advance.

Topic selection is biased toward the candidate's weak topics and knowledge
gaps (they get covered with accessible questions) while strong topics get
harder, probing questions.
"""
from __future__ import annotations

import random

from agents.difficulty_manager import DifficultyManager
from memory.context_manager import InterviewContext
from models.candidate_profile import CandidateProfile
from models.enums import Difficulty, QuestionType
from models.plan import InterviewPlan, PlannedQuestion
from retrieval.curriculum_retriever import CurriculumRetriever
from schemas.llm import QuestionDraft
from services.llm_service import LLMService
from services.prompt_builder import PromptBuilder
from utils.logging import get_logger

logger = get_logger(__name__)

_ALL_QUESTION_TYPES = list(QuestionType)


class QuestionPlanner:
    """Determines the full plan skeleton and generates question text."""

    def __init__(
        self,
        llm: LLMService,
        prompts: PromptBuilder,
        retriever: CurriculumRetriever,
        *,
        min_questions: int = 8,
        min_days: int = 4,
        total_questions: int = 12,
        difficulty_manager: DifficultyManager | None = None,
    ) -> None:
        self._llm = llm
        self._prompts = prompts
        self._retriever = retriever
        self._min_questions = min_questions
        self._min_days = min_days
        self._total_questions = total_questions
        self._difficulty = difficulty_manager or DifficultyManager()

    def build_plan(self, profile: CandidateProfile) -> InterviewPlan:
        """Deterministic plan skeleton. Never touches the LLM."""
        if not self._retriever.available:
            from utils.errors import CurriculumUnavailableError

            raise CurriculumUnavailableError(
                "curriculum.json is unavailable — cannot plan the interview. "
                "Place the dataset in the configured data directory."
            )

        total = max(self._min_questions, self._total_questions)
        day_count = max(self._min_days, min(self._retriever.day_count, total))

        day_indices = self._select_days(profile, day_count)
        assignments = self._assign_topics(profile, day_indices, total)

        plan = InterviewPlan()
        baseline = profile.baseline_difficulty
        previous_type: QuestionType | None = None
        type_pool = _ALL_QUESTION_TYPES[:]
        random.shuffle(type_pool)

        for index, (day_index, topic) in enumerate(assignments):
            question_type = self._next_type(type_pool, previous_type, index)
            previous_type = question_type

            # Progressive easy -> medium -> advanced ramp, offset by the
            # candidate's baseline (delegated to the Difficulty Manager).
            difficulty = self._difficulty.question_difficulty(
                baseline, index, total
            )

            day = self._retriever.get_day(day_index)
            plan.questions.append(
                PlannedQuestion(
                    day_index=day_index,
                    day_title=day.title if day else f"Day {day_index + 1}",
                    topic=topic,
                    question_type=question_type,
                    difficulty=difficulty,
                    question="",   # filled on demand by generate_question_text
                )
            )
            plan.days_covered.append(day_index)

        logger.info(
            "Interview plan skeleton ready: %d questions across %d days for %s",
            plan.size,
            plan.distinct_days,
            profile.candidate_id,
        )
        return plan

    async def generate_question_text(
        self,
        context: InterviewContext,
        entry: PlannedQuestion,
        index: int,
        total: int,
        curriculum: str,
    ) -> QuestionDraft:
        """Generate the natural-language question for one plan entry."""
        prompt = self._prompts.question_prompt(
            context,
            topic=entry.topic,
            question_type=entry.question_type.value,
            difficulty=entry.difficulty.value,
            curriculum=curriculum,
        )
        draft = await self._llm.structured_completion(
            system_prompt=self._prompts.system_prompt(),
            user_prompt=prompt,
            schema=QuestionDraft,
        )
        entry.question = draft.question
        entry.intent = entry.intent or draft.intent
        if draft.topic and draft.topic != entry.topic:
            entry.topic = draft.topic
        return draft

    # ------------------------------------------------------------------ steps

    def _select_days(self, profile: CandidateProfile, day_count: int) -> list[int]:
        """Pick days, prioritising those matching weak/gap topics."""
        all_days = list(range(self._retriever.day_count))
        if not all_days:
            return []
        random.shuffle(all_days)

        weak_matches: list[int] = []
        for topic in profile.weak_topics + profile.knowledge_gaps:
            day = self._retriever.find_day_for_topic(topic)
            if day is not None and day not in weak_matches:
                weak_matches.append(day)

        selected: list[int] = []
        for day in weak_matches:
            if len(selected) < day_count:
                selected.append(day)
        for day in all_days:
            if len(selected) >= day_count:
                break
            if day not in selected:
                selected.append(day)
        return selected

    def _assign_topics(
        self,
        profile: CandidateProfile,
        day_indices: list[int],
        total: int,
    ) -> list[tuple[int, str]]:
        """Round-robin day -> topic assignment with weak-topic priority."""
        assignments: list[tuple[int, str]] = []
        per_day: dict[int, list[str]] = {}

        for day_index in day_indices:
            day = self._retriever.get_day(day_index)
            topics = list(day.topics) if day else []
            if not topics:
                topics = [day.title if day else f"Day {day_index + 1}"]

            def sort_key(topic: str) -> tuple[int, str]:
                weak = topic in profile.weak_topics or topic in profile.knowledge_gaps
                strong = topic in profile.strong_topics
                priority = 0 if weak else (2 if strong else 1)
                return (priority, topic)

            topics.sort(key=sort_key)
            per_day[day_index] = topics

        cursor = 0
        for index in range(total):
            day_index = day_indices[index % len(day_indices)]
            topics = per_day[day_index]
            topic = topics[cursor % len(topics)]
            cursor += 1
            assignments.append((day_index, topic))
        return assignments

    @staticmethod
    def _next_type(
        pool: list[QuestionType], previous: QuestionType | None, index: int
    ) -> QuestionType:
        """Rotate styles, never repeating the previous type."""
        if index % len(pool) == 0:
            random.shuffle(pool)
        for candidate in pool:
            if candidate != previous:
                return candidate
        return pool[0]
