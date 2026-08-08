"""Question planner.

Determines *which* topic and *what* to assess next, then asks the LLM to
turn that structured intent into natural interviewer language.

The planner separates WHAT from HOW:

1. topic selection is a deterministic scoring function over the candidate's
   completed curriculum days (never over uncompleted material),
2. for the chosen day, a *learning objective* is selected deterministically
   (round-robin over the day's objectives, never reusing one on the same
   day), and a technical *concept* is derived from it,
3. the objective + concept + cognitive level + purpose + evidence bar are
   packed into a :class:`QuestionIntent`,
4. the LLM translates the intent into one natural question.

Topic score:

    score = candidate_relevance + completion_relevance + coherence
            + coverage_need + difficulty_fit
            - topic_saturation - repeated_failure_penalty

* ``candidate_relevance`` -- strong topics score higher,
* ``probe_value``       -- struggled-but-passed topics are probed mid-interview,
* ``coherence``         -- same/neighbouring module as the current topic
  (RAG path, agent path and production path emerge naturally from module
  adjacency over the candidate's own completed days),
* ``coverage_need``     -- when fewer than ``min_days`` are covered, new
  days are strongly prioritised (the 4-day requirement is enforced here,
  not left to the LLM),
* negative terms        -- per-day saturation (max 3 main questions), and a
  penalty on topics with repeated failures so the interviewer never traps
  the candidate.

Every generated question is passed through the deterministic duplicate
guard; if it is too close to anything already asked, the planner first
rotates to a different learning objective, then to a different cognitive
task, and regenerates.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import replace

from agents.difficulty_manager import DifficultyManager
from agents.duplicate_guard import is_duplicate
from memory.context_manager import InterviewContext
from models.candidate_profile import CandidateProfile
from models.enums import Difficulty, QuestionType
from models.plan import InterviewPlan, PlannedQuestion
from models.question_intent import QuestionIntent
from retrieval.curriculum_retriever import CurriculumRetriever
from schemas.llm import QuestionDraft
from services.llm_service import LLMService
from services.prompt_builder import PromptBuilder
from utils.concepts import (
    cognitive_label,
    concept_from_objective,
    expected_evidence_for_type,
    purpose_for_type,
)
from utils.logging import get_logger

logger = get_logger(__name__)

#: Soft limit on main questions per single curriculum day.  Two mains per
#: day keep the interview in the 4-6 day / 8-10 question band: a strong
#: candidate gets a deeper second question on a day (synthesis), while the
#: planner still moves on to fresh topics once a day is fully used.
MAX_MAIN_PER_DAY = 2
#: Question types weighted towards later, harder cognitive levels.
_EARLY_TYPES = (
    QuestionType.DEFINITION,
    QuestionType.CONCEPTUAL,
    QuestionType.SCENARIO,
    QuestionType.REASONING,
)
_LATE_TYPES = (
    QuestionType.ARCHITECTURE,
    QuestionType.TRADEOFFS,
    QuestionType.DESIGN,
    QuestionType.PRODUCTION,
    QuestionType.DEBUGGING,
    QuestionType.DEPLOYMENT,
)


class QuestionPlanner:
    """Determines the next topic dynamically and generates question text."""

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
        """Validate curriculum availability and initialise the plan."""
        if not self._retriever.available:
            from utils.errors import CurriculumUnavailableError

            raise CurriculumUnavailableError(
                "curriculum.json is unavailable — cannot plan the interview. "
                "Place the dataset in the configured data directory."
            )
        return InterviewPlan()

    # ------------------------------------------------------------------ public

    async def generate_next_question(
        self,
        context: InterviewContext,
        profile: CandidateProfile,
        plan: InterviewPlan,
        index: int,
    ) -> PlannedQuestion:
        """Pick the best next topic and generate a non-duplicate question."""
        day_index, topic = self._determine_next_topic(profile, plan)
        difficulty = self._difficulty_for(profile, plan, index, topic)
        question_type = self._next_type(profile, plan, index, day_index, topic)
        curriculum = self._retriever.ground_context(day_index)
        previous_texts, previous_types, previous_topics = self._history(plan, context)

        day_obj = self._retriever.get_day(day_index)
        objective, concept = self._select_objective(day_index, plan)
        previous_index = plan.questions[-1].day_index if plan.questions else None
        previous_topic = plan.questions[-1].topic if plan.questions else ""

        intent = QuestionIntent(
            curriculum_day=day_obj.day_number if day_obj else day_index + 1,
            topic=topic,
            module=day_obj.module if day_obj else "",
            learning_objective=objective,
            concept=concept,
            cognitive_level=cognitive_label(question_type),
            purpose=purpose_for_type(question_type),
            expected_evidence=expected_evidence_for_type(question_type),
            difficulty=difficulty.value,
            relationship=self._relationship(previous_index, day_index),
            candidate_signal=self._signal_for(profile, topic),
        )

        draft, objective, concept, used_intent = await self._generate_with_dedup(
            context,
            plan,
            index,
            day_index,
            topic,
            question_type,
            difficulty,
            curriculum,
            previous_texts,
            previous_types,
            previous_topics,
            intent,
            previous_topic,
        )

        day_title = (
            f"Day {day_obj.day_number} — {day_obj.title}"
            if day_obj
            else f"Day {day_index + 1}"
        )
        # The topic/objective/concept are structured engine state; the LLM's
        # free-text topic field is never used for state (per the spec, state
        # must not be parsed from generated text).  When the duplicate guard
        # rotated to a different objective/type, we store the *final* intent
        # so the recorded state always matches the question actually asked.
        return PlannedQuestion(
            day_index=day_index,
            day_title=day_title,
            topic=topic,
            question_type=question_type,
            difficulty=difficulty,
            question=draft.question,
            intent=used_intent.purpose,
            learning_objective=objective,
            concept=concept,
            expected_evidence=list(used_intent.expected_evidence),
        )

    # ------------------------------------------------------------------ topic choice

    def _determine_next_topic(
        self, profile: CandidateProfile, plan: InterviewPlan
    ) -> tuple[int, str]:
        """Score every completed curriculum day and return the best (index, topic)."""
        completed = set(profile.completed_days)
        excluded = set(plan.days_covered)
        day_counts = Counter(q.day_index for q in plan.questions)
        covered = set(plan.days_covered)
        need_new_day = len(covered) < self._min_days
        q_index = len(plan.questions)

        current_index = plan.questions[-1].day_index if plan.questions else None

        candidates: list[tuple[float, int, str]] = []
        for index in range(self._retriever.day_count):
            day = self._retriever.get_day(index)
            if day is None:
                continue
            day_number = day.day_number
            # Only interview about material the candidate completed.
            if day_number not in completed:
                continue
            if day_counts[index] >= MAX_MAIN_PER_DAY:
                continue  # topic saturation

            topic = day.primary_topic
            assessment = plan.assessment.get_topic(topic)
            if assessment.consecutive_failures >= 2 or assessment.bare_claims >= 2:
                # Repeated failure or repeated bare claims -> move on, never
                # trap the candidate on the same topic.
                continue

            score = 0.0

            # Candidate relevance.
            if topic in profile.strong_topics:
                score += 8.0
            # Struggled-but-passed topics: probe mid-interview, not early.
            if topic in profile.weak_topics:
                score += 6.0 if q_index >= 4 else -2.0

            # Completion + coverage need (enforces the 4-day requirement).
            if need_new_day and index not in covered:
                score += 7.0
            elif index in covered:
                score += 2.0  # allow deepening but less attractive

            # Coherence: stay on the current module, then neighbours.  Once
            # the 4-day minimum is met, *deepening* the current topic/area
            # outranks hopping to a new strong topic far away, so the
            # interview collects depth instead of day-count.
            if current_index is not None and index == current_index:
                score += 6.0 if not need_new_day else 3.0
            elif current_index is not None:
                if self._retriever.are_adjacent_days(current_index, index):
                    score += 4.0
                elif (
                    self._retriever.module_for_day(current_index)
                    == self._retriever.module_for_day(index)
                ):
                    score += 5.0
                elif not need_new_day and day.module_number:
                    current_module = self._retriever.module_for_day(current_index)
                    if current_module and abs(current_module.number - day.module_number) > 1:
                        score -= 2.0  # far-away module: only if it is a strong pull

            # Difficulty fit: senior candidates benefit from later modules.
            if profile.baseline_difficulty in (Difficulty.ADVANCED,) and day.module_number >= 6:
                score += 2.0
            if profile.baseline_difficulty in (Difficulty.EASY,) and day.module_number <= 3:
                score += 2.0

            # Saturation penalty.
            if day_counts[index]:
                score -= 3.0 * day_counts[index]

            candidates.append((score, index, topic))

        # Fallback 1: any completed day still within the per-day cap.  This
        # may re-pick days already marked weak/failed — but only when the
        # primary loop found nothing, i.e. every completed day is either at
        # its 2-main cap or was exhausted (repeated failures / bare claims).
        # Re-picking is intentional: the 8-main minimum must still be
        # reachable for candidates who completed few days and struggled on
        # all of them.  In the common case the interviewer never circles
        # back: failure-excluded days are skipped by the primary loop, and
        # the evidence-based early finish ends the interview at 8 mains
        # before this fallback is ever reached.
        if not candidates:
            for index in range(self._retriever.day_count):
                day = self._retriever.get_day(index)
                if day is None or day.day_number not in completed:
                    continue
                if day_counts[index] < MAX_MAIN_PER_DAY:
                    candidates.append((0.0, index, day.primary_topic))

        # Fallback 2 (theoretical): any day, preferring uncovered ones.
        if not candidates:
            for index in range(self._retriever.day_count):
                day = self._retriever.get_day(index)
                if day is None:
                    continue
                bonus = 0.0 if index in covered else 5.0
                candidates.append((bonus, index, day.primary_topic))

        if not candidates:
            return 0, "General Concepts"

        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1], candidates[0][2]

    # ------------------------------------------------------------------ objective choice

    def _select_objective(
        self,
        day_index: int,
        plan: InterviewPlan,
        *,
        exclude: set[str] | None = None,
    ) -> tuple[str, str]:
        """Pick the next learning objective for a day (never reusing one).

        Returns ``(objective, concept)``.  When the day has no explicit
        objectives, the day's own title is used as the objective (its
        wording, not invented).
        """
        day = self._retriever.get_day(day_index)
        objectives = list(day.objectives) if day and day.objectives else []
        if not objectives:
            label = day.title if day else f"Day {day_index + 1}"
            return label, label

        used = [
            q.learning_objective
            for q in plan.questions
            if q.day_index == day_index and q.learning_objective
        ]
        blocked = set(used) | set(exclude or ())
        available = [objective for objective in objectives if objective not in blocked]
        if available:
            objective = available[0]
        else:
            # All objectives used (unlikely given the per-day cap): rotate
            # to the least-recently-used one.
            counter = Counter(used)
            objective = min(
                objectives, key=lambda o: (counter.get(o, 0), objectives.index(o))
            )
        return objective, concept_from_objective(objective)

    def _relationship(self, previous_index: int | None, next_index: int) -> str:
        """Short human description of how two days connect (for the prompt)."""
        if previous_index is None:
            return "the opening question of the interview"
        if previous_index == next_index:
            return "continuing on the same curriculum day"
        previous_module = self._retriever.module_for_day(previous_index)
        next_module = self._retriever.module_for_day(next_index)
        if previous_module and next_module:
            if previous_module.number == next_module.number:
                return f"the same module ({next_module.title})"
            if abs(previous_module.number - next_module.number) <= 1:
                return "a neighbouring module in the same area"
        return "a new curriculum area"

    def _signal_for(self, profile: CandidateProfile, topic: str) -> str:
        """Which candidate-profile signal explains this topic choice."""
        if topic in profile.strong_topics:
            return "strong topic per profile — expect a solid baseline"
        if topic in profile.weak_topics:
            return "struggled-but-passed topic per profile — probe carefully"
        if topic in profile.failed_topics:
            return "previously failed topic — establish the baseline first"
        return "completed curriculum day — normal coverage"

    # ------------------------------------------------------------------ difficulty

    def _difficulty_for(
        self,
        profile: CandidateProfile,
        plan: InterviewPlan,
        index: int,
        topic: str,
    ) -> Difficulty:
        baseline = profile.baseline_difficulty
        difficulty = self._difficulty.question_difficulty(
            baseline, index, self._total_questions
        )
        assessment = plan.assessment.get_topic(topic)
        if assessment.consecutive_failures > 0 or assessment.confidence == "low":
            difficulty = Difficulty.from_rank(difficulty.rank - 1)
        elif assessment.confidence == "high":
            difficulty = Difficulty.from_rank(difficulty.rank + 1)
        return difficulty

    # ------------------------------------------------------------------ type choice

    def _next_type(
        self,
        profile: CandidateProfile,
        plan: InterviewPlan,
        index: int,
        day_index: int,
        topic: str,
    ) -> QuestionType:
        """Pick the least-used question type, never repeating the previous one.

        Earlier in the interview (or for weaker candidates) conceptual
        types are preferred; later, architecture / production / trade-off
        types dominate (the cognitive ladder).
        """
        used: Counter = Counter(q.question_type for q in plan.questions)
        previous = plan.questions[-1].question_type if plan.questions else None

        # Prefer a fresh type on this topic.
        topic_types = {
            q.question_type for q in plan.questions if q.day_index == day_index
        }

        # Weight the phase-appropriate cognitive level first, then variety.
        phase_rank: dict[QuestionType, int] = {}
        if index < 3:
            # Discovery phase: concept / definition / scenario / reasoning.
            phase_rank = {t: (0 if t in _EARLY_TYPES else 1) for t in QuestionType}
        elif index >= self._min_questions or profile.baseline_difficulty == Difficulty.ADVANCED:
            # Synthesis phase (or a senior candidate): architecture,
            # trade-offs, design, production, deployment, debugging.
            phase_rank = {t: (0 if t in _LATE_TYPES else 1) for t in QuestionType}
        else:
            phase_rank = {t: 0 for t in QuestionType}

        # Deterministic: least-used first, phase preference, stable order.
        pool = sorted(
            QuestionType, key=lambda t: (used[t], phase_rank.get(t, 0), t.value)
        )

        for candidate in pool:
            if candidate == previous:
                continue
            if candidate in topic_types and len(topic_types) < len(pool):
                continue  # avoid repeating a type on the same day
            return candidate
        return pool[0]

    # ------------------------------------------------------------------ generation

    async def _generate_with_dedup(
        self,
        context: InterviewContext,
        plan: InterviewPlan,
        index: int,
        day_index: int,
        topic: str,
        question_type: QuestionType,
        difficulty: Difficulty,
        curriculum: str,
        previous_texts: list[str],
        previous_types: list[QuestionType | None],
        previous_topics: list[str],
        intent: QuestionIntent,
        previous_topic: str,
    ) -> tuple[QuestionDraft, str, str, QuestionIntent]:
        """Generate a question grounded in ``intent``, regenerating when the
        guard flags a duplicate.  Retry order: different learning objective,
        then a different cognitive task.

        Returns ``(draft, objective, concept, used_intent)`` so the caller
        always records the objective/concept the question *actually* targets
        (the structured state must never diverge from the question text).
        """

        async def _call(
            _intent: QuestionIntent, _type: QuestionType
        ) -> QuestionDraft:
            prompt = self._prompts.question_prompt(
                context,
                intent=_intent,
                question_type=_type.value,
                difficulty=difficulty.value,
                curriculum=curriculum,
                previous_topic=previous_topic,
            )
            return await self._llm.structured_completion(
                system_prompt=self._prompts.system_prompt(),
                user_prompt=prompt,
                schema=QuestionDraft,
            )

        def _duplicate(_draft: QuestionDraft) -> bool:
            return is_duplicate(
                _draft.question,
                previous_texts,
                candidate_type=question_type,
                previous_types=previous_types,
                candidate_topic=topic,
                previous_topics=previous_topics,
            )

        objective = intent.learning_objective
        concept = intent.concept
        used_intent = intent

        draft = await _call(intent, question_type)
        if not _duplicate(draft):
            return draft, objective, concept, used_intent

        # Retry 1: a different learning objective on the same day.
        logger.info(
            "Duplicate guard: regenerating question %d (type %s, topic %s)",
            index + 1,
            question_type.value,
            topic,
        )
        objective2, concept2 = self._select_objective(
            day_index, plan, exclude={intent.learning_objective}
        )
        if objective2 != intent.learning_objective:
            intent2 = replace(
                intent, learning_objective=objective2, concept=concept2
            )
            draft = await _call(intent2, question_type)
            if not _duplicate(draft):
                return draft, objective2, concept2, intent2

        # Retry 2: a different cognitive task.  The intent is rebuilt for
        # the alternate type so the prompt never mixes "question type X"
        # with "purpose of type Y" (consistent evidence bar).
        alternate_type = self._alternate_type(question_type)
        intent_alt = replace(
            used_intent,
            cognitive_level=cognitive_label(alternate_type),
            purpose=purpose_for_type(alternate_type),
            expected_evidence=expected_evidence_for_type(alternate_type),
        )
        draft = await _call(intent_alt, alternate_type)
        # If the retry still duplicates, keep it (rare last resort: the LLM
        # prompt, objective rotation and type rotation already failed).
        return draft, intent_alt.learning_objective, intent_alt.concept, intent_alt

    def _alternate_type(self, current: QuestionType) -> QuestionType:
        if current in _LATE_TYPES:
            return QuestionType.SCENARIO
        return QuestionType.REASONING

    @staticmethod
    def _history(
        plan: InterviewPlan, context: InterviewContext
    ) -> tuple[list[str], list[QuestionType | None], list[str]]:
        """All previously asked questions (main + follow-ups) + their type/topic."""
        texts: list[str] = []
        types: list[QuestionType | None] = []
        topics: list[str] = []
        for question in plan.questions:
            texts.append(question.question)
            types.append(question.question_type)
            topics.append(question.topic)
        for turn in context.memory.all_turns:
            if turn.is_follow_up:
                texts.append(turn.question)
                types.append(None)
                topics.append(turn.topic)
        return texts, types, topics
