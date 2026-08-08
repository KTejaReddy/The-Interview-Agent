"""Response evaluator.

Rates the candidate's answer on a 0-10 scale, assigns a verdict and decides
the interviewer's next move (deeper / verify / simplify / recovery / probe /
move on).

Deterministic rules run *alongside* the LLM verdict so behaviour is
predictable where it matters most:

* an "I don't know" style answer always lands in the weak/simplify branch,
  regardless of what the model says,
* a *bare knowledge claim* ("I know", "yes", "I understand" with no
  substance) is never treated as demonstrated competence: it is marked
  ``VERIFY`` so the interviewer asks for evidence with a concrete scenario,
* failure ladder on the same topic: first struggle -> one simpler,
  *different* diagnostic question (``simplify``, or ``recovery`` when the
  answer contained a misconception); second struggle -> the topic is marked
  weak and the interviewer moves on (``next_topic``), never trapping the
  candidate,
* every answer updates the per-topic assessment (confidence, counters,
  best/worst score) that drives planning and final feedback.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from memory.context_manager import InterviewContext
from models.enums import Difficulty, FollowUpStrategy, Verdict
from models.plan import PlannedQuestion
from schemas.llm import EvaluationDraft
from services.llm_service import LLMService
from services.prompt_builder import PromptBuilder
from utils.answer_signals import (
    detects_claim_without_evidence,
    detects_greeting,
    detects_idk,
)
from utils.logging import get_logger

logger = get_logger(__name__)

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
    "verify": FollowUpStrategy.VERIFY,
    "probe": FollowUpStrategy.PROBE,
    "next_topic": FollowUpStrategy.NEXT_TOPIC,
}

#: Repeated failures on the same topic before the interviewer moves on.
#: First -> SIMPLIFY (a *different*, easier diagnostic; or RECOVERY when
#: the answer was a recognizable misconception), second -> NEXT_TOPIC
#: (mark weak, never trap).  A real interviewer does not spend 5-6
#: questions on one concept the candidate cannot answer.
_MAX_CONSECUTIVE_FAILURES = 2

#: Regexes that hint at a non-answer even when worded unusually (defensive,
#: complements the stricter detectors in ``utils.answer_signals``).
_WEAK_ANSWER_PATTERNS = (
    re.compile(r"^(?:well|hmm|um|uh|ok|okay|so)[,.\s]*$", re.I),
    re.compile(r"^\s*$"),
)


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
            FollowUpStrategy.VERIFY,
            FollowUpStrategy.PROBE,
        }


class ResponseEvaluator:
    """Single-responsibility evaluator (LLM-backed + deterministic rules)."""

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
            learning_objective=question.learning_objective,
            concept=question.concept,
            answer=answer,
        )
        draft: EvaluationDraft = await self._llm.structured_completion(
            system_prompt=self._prompts.system_prompt(),
            user_prompt=prompt,
            schema=EvaluationDraft,
        )

        verdict = _VERDICT_MAP.get(draft.verdict, Verdict.UNCLEAR)
        strategy = _STRATEGY_MAP.get(draft.follow_up, FollowUpStrategy.NEXT_TOPIC)
        score = draft.score
        notes = draft.notes or ""
        mastered = draft.mastered_topic

        # --- deterministic signal overrides -------------------------------
        # These are the hard rules: surface phrases never decide competence.
        claim = False
        contradiction = False
        if detects_idk(answer):
            score = min(score, 3)
            verdict = Verdict.WEAK if verdict not in (Verdict.WRONG,) else Verdict.WRONG
            strategy = (
                FollowUpStrategy.SIMPLIFY
                if verdict == Verdict.WEAK
                else FollowUpStrategy.RECOVERY
            )
            mastered = False
            notes = "The candidate did not provide a substantive answer."
        elif detects_greeting(answer):
            # "hello" / "okay" / "hmm": a non-answer, not a claim.  One
            # short, simpler recovery question is enough.
            score = min(score, 3)
            verdict = Verdict.WEAK
            strategy = FollowUpStrategy.SIMPLIFY
            mastered = False
            notes = "The candidate gave a greeting/non-answer — ask the same assessment more simply."
        elif detects_claim_without_evidence(answer):
            # "I know" / "yes" / "I understand" without content: not evidence.
            # Probe with a concrete scenario instead of rewarding the claim.
            score = min(score, 5)
            verdict = Verdict.UNCLEAR
            strategy = FollowUpStrategy.VERIFY
            mastered = False
            claim = True
            notes = (
                "The candidate asserted knowledge without demonstrating it — "
                "verify with a concrete scenario from the learning objective."
            )
        elif draft.contradiction_detected:
            # The answer contradicts an earlier statement of the candidate's
            # (the LLM compared it against the full transcript).  Gently
            # point out the discrepancy instead of scoring it as plain
            # competence or failure: the next turn probes which they meant.
            contradiction = True
            strategy = FollowUpStrategy.PROBE
            notes = (
                draft.notes
                or "The candidate contradicted an earlier statement in the interview."
            )
            context.memory.add_contradiction(f"{question.topic}: {notes}")
        elif any(pattern.match(answer) for pattern in _WEAK_ANSWER_PATTERNS):
            score = min(score, 3)
            verdict = Verdict.WEAK
            strategy = FollowUpStrategy.SIMPLIFY
            mastered = False
            notes = "The candidate gave no substantive answer."

        # --- update the per-topic assessment -------------------------------
        topic_assessment = context.plan.assessment.get_topic(question.topic)
        topic_assessment.questions_asked += 1
        topic_assessment.best_score = max(topic_assessment.best_score, score)
        topic_assessment.worst_score = min(topic_assessment.worst_score, score)
        topic_assessment.evidence.append(
            f"{'follow-up' if context.is_follow_up else 'main'}: score {score}/10 "
            f"({verdict.value}){' [bare claim]' if claim else ''}"
        )

        if claim:
            # Repeated bare claims never become evidence.  After two
            # consecutive claims with no substance, stop probing this topic
            # (insufficient evidence) and move on — never trap the candidate.
            topic_assessment.bare_claims += 1
            if topic_assessment.bare_claims >= 2:
                strategy = FollowUpStrategy.NEXT_TOPIC
                notes = (
                    "The candidate repeatedly asserted knowledge without "
                    "demonstrating it — mark insufficient evidence and move on."
                )

        if verdict in (Verdict.WRONG, Verdict.WEAK):
            # Failure ladder (max two attempts per weak concept): first
            # struggle -> a different, simpler diagnostic (or a scaffolding
            # probe for a wrong answer); second struggle -> mark the topic
            # weak and move on.  Never trap the candidate on one concept.
            topic_assessment.consecutive_failures += 1
            failures = topic_assessment.consecutive_failures
            if failures >= _MAX_CONSECUTIVE_FAILURES:
                topic_assessment.confidence = "low"
                strategy = FollowUpStrategy.NEXT_TOPIC
            elif verdict == Verdict.WRONG:
                # Misconception: probe it once with a concrete diagnostic.
                strategy = FollowUpStrategy.RECOVERY
            else:
                # First struggle: a *different*, simpler diagnostic question.
                strategy = FollowUpStrategy.SIMPLIFY
        elif verdict in (Verdict.GOOD, Verdict.EXCELLENT):
            # Demonstrated evidence clears both failure and bare-claim marks:
            # a strong answer between two claims means the second claim is not
            # a fresh reason to abandon the topic.
            topic_assessment.consecutive_failures = 0
            topic_assessment.bare_claims = 0
            if mastered or verdict == Verdict.EXCELLENT:
                topic_assessment.confidence = "high"
            else:
                topic_assessment.confidence = "medium"
                if topic_assessment.best_score >= 8:
                    topic_assessment.confidence = "high"
        # Verdict.UNCLEAR (bare claim): no confidence change; the claim is
        # neither a mistake nor evidence.

        # A contradiction always stays a gentle call-out (the failure ladder
        # or claim logic above must never turn it into a silent move-on).
        if contradiction:
            strategy = FollowUpStrategy.PROBE

        return EvaluationResult(
            score=score,
            verdict=verdict,
            strategy=strategy,
            mastered_topic=mastered,
            notes=notes,
        )
