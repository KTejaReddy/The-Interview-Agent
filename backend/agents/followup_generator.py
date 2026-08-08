"""Follow-up generator.

Every answer influences the next question.  When the evaluator decides the
interviewer should stay on the topic, this agent produces a follow-up that
is adapted to the answer:

* good answer     -> deeper question,
* bare claim      -> verify: ask for evidence with a concrete scenario,
* weak answer     -> a *different*, simpler diagnostic question,
* wrong answer    -> recovery / scaffolding question,
* unclear         -> clarification probe.

Follow-ups are grounded in the exact learning objective and concept of the
question just asked (never in the day title), and are checked against every
earlier question by the deterministic duplicate guard — a follow-up must add
a new dimension, not re-ask the same thing.
"""
from __future__ import annotations

from dataclasses import dataclass

from agents.difficulty_manager import DifficultyManager
from agents.duplicate_guard import is_duplicate
from memory.context_manager import InterviewContext
from models.enums import Difficulty, FollowUpStrategy, Verdict
from models.plan import PlannedQuestion
from retrieval.curriculum_retriever import CurriculumRetriever
from schemas.llm import FollowUpDraft
from services.llm_service import LLMService
from services.prompt_builder import PromptBuilder
from utils.concepts import action_phrase_from_objective
from utils.logging import get_logger

logger = get_logger(__name__)

#: Deterministic follow-up templates used only when the LLM keeps producing
#: semantic duplicates.  They are *evidence-form-safe*: explanation-style
#: templates use the ``how …`` concept, activity-style templates use the
#: gerund action phrase ("creating a /chat API endpoint…"), so a template
#: can never produce "How does how to build X fit…?".  They are keyed by
#: strategy so a simplify never turns into a deep probe, and they rotate so
#: repeated probing of the same topic still asks genuinely different
#: questions instead of a fixed main→example→mistake bundle.
# The openers are short and vary per rotation so interviews never repeat
# the same stock phrase ("Glad to hear it…", "No problem — let's ground this
# differently…" are banned).
_FALLBACK_DEEPER = (
    lambda a: f"Suppose {a} had to be production-ready next month — what's the "
    f"first thing you'd verify?",
    lambda a: f"What trade-offs would you weigh around {a} in a real system?",
    lambda a: f"Where does {a} sit in the architecture, and what would you "
    f"monitor in production?",
)
_FALLBACK_SIMPLIFY = (
    lambda a: f"Let's try a simpler angle: in one sentence, what's the core job "
    f"of {a}?",
    lambda a: f"Okay, let's come at it from the basics: when would you reach "
    f"for {a}?",
)
_FALLBACK_RECOVERY = (
    lambda c: f"Let's step back: how would you explain {c} to a junior "
    f"teammate?",
    lambda a: f"Suppose your team asked you to handle {a} from scratch — what's "
    f"your very first step?",
)
_FALLBACK_VERIFY = (
    lambda c: f"Alright, let's test that: walk me through {c} with a quick "
    f"example.",
    lambda a: f"Good — let's see it in action: how would you approach {a} step "
    f"by step?",
)
_FALLBACK_PROBE = (
    lambda c: f"Could you expand on how {c} works in practice?",
    lambda c: f"Tell me more about the practical side of {c}.",
)


_FALLBACK_BY_STRATEGY: dict[FollowUpStrategy, tuple] = {
    FollowUpStrategy.DEEPER: _FALLBACK_DEEPER,
    FollowUpStrategy.SIMPLIFY: _FALLBACK_SIMPLIFY,
    FollowUpStrategy.RECOVERY: _FALLBACK_RECOVERY,
    FollowUpStrategy.VERIFY: _FALLBACK_VERIFY,
    FollowUpStrategy.PROBE: _FALLBACK_PROBE,
}


def _fallback_question(
    question: PlannedQuestion, strategy: FollowUpStrategy, question_count: int
) -> str:
    """A guaranteed-fresh deterministic follow-up for the question, grounded
    in the curriculum's own wording and safe for both phrase forms.

    Activity-style templates (deeper / probe / simplify) take the gerund
    action phrase ("creating a /chat API endpoint…"), explanation-style
    ones (recovery / verify) take the "how …" concept — so a template can
    never produce "How does how to build X fit…?" nor "the core job of how
    to create X".
    """
    concept = question.concept or question.learning_objective or question.topic
    action = (
        action_phrase_from_objective(question.learning_objective)
        if question.learning_objective
        else concept
    )
    templates = _FALLBACK_BY_STRATEGY.get(strategy, _FALLBACK_DEEPER)
    template = templates[question_count % len(templates)]
    if strategy in (
        FollowUpStrategy.DEEPER,
        FollowUpStrategy.PROBE,
        FollowUpStrategy.SIMPLIFY,
    ):
        return template(action)
    return template(concept)


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
        day = self._retriever.get_day(question.day_index)
        difficulty = self._difficulty.follow_up_difficulty(strategy)
        # Parallel lists of question text / topic so the duplicate guard can
        # apply its same-topic similarity rules (follow-ups carry no explicit
        # question-type metadata, so topic overlap is what catches template
        # repeats like two consecutive production-scenario probes).
        previous_texts = [q.question for q in context.plan.questions]
        previous_topics = [q.topic for q in context.plan.questions]
        follow_up_turns = [
            turn for turn in context.memory.all_turns if turn.is_follow_up
        ]
        previous_texts += [turn.question for turn in follow_up_turns]
        previous_topics += [turn.topic for turn in follow_up_turns]

        follow_up_count = context.plan.assessment.get_topic(
            question.topic
        ).follow_ups
        prompt = self._prompts.follow_up_prompt(
            context,
            question=question.question,
            topic=question.topic,
            learning_objective=question.learning_objective,
            concept=question.concept,
            expected_evidence=question.expected_evidence,
            day_title=question.day_title,
            module=day.module if day else "",
            answer=answer,
            verdict=verdict.value,
            score=score,
            strategy=strategy.value,
            notes=notes,
            curriculum=curriculum,
            difficulty=difficulty.value,
            follow_up_count=follow_up_count,
            previous_questions=previous_texts,
        )
        draft: FollowUpDraft = await self._llm.structured_completion(
            system_prompt=self._prompts.system_prompt(),
            user_prompt=prompt,
            schema=FollowUpDraft,
        )

        # Deterministic duplicate check: a follow-up must add a dimension.
        if is_duplicate(
            draft.question,
            previous_texts,
            candidate_topic=question.topic,
            previous_topics=previous_topics,
        ):
            logger.info(
                "Duplicate guard: regenerating follow-up (topic %s, strategy %s)",
                question.topic,
                strategy.value,
            )
            prompt = prompt + (
                "\n\nANTI-DUPLICATION: Your previous follow-up was too similar "
                "to an earlier question. Ask something genuinely new — a "
                "concrete scenario, an edge case, or a design consequence of "
                "what the candidate just said."
            )
            draft = await self._llm.structured_completion(
                system_prompt=self._prompts.system_prompt(),
                user_prompt=prompt,
                schema=FollowUpDraft,
            )
            # If the retry still collides (e.g. a deterministic provider),
            # fall back to a strategy-aware template that is guaranteed to
            # differ from anything asked before on this topic.
            if is_duplicate(
                draft.question,
                previous_texts,
                candidate_topic=question.topic,
                previous_topics=previous_topics,
            ):
                logger.info(
                    "Duplicate guard: using deterministic fallback follow-up "
                    "(%s, %s)",
                    question.topic,
                    strategy.value,
                )
                count = context.memory.question_count_on_topic(question.topic)
                fallback = _fallback_question(question, strategy, count)
                return FollowUpResult(
                    question=fallback,
                    intent="Recover depth with a fresh angle on the concept.",
                    difficulty=difficulty,
                )

        return FollowUpResult(
            question=draft.question,
            intent=draft.intent,
            difficulty=Difficulty(draft.difficulty),
        )
