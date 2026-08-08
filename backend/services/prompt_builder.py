"""Prompt builder.

Loads every prompt template from ``backend/prompts/*.md`` once and exposes
methods that fill them with concrete context.  No service contains prompt
text inline; all wording lives in the template files.

The question prompt receives a structured :class:`QuestionIntent` — the
learning objective, derived concept, purpose and evidence bar — so the LLM
translates *what we want to assess* into natural interviewer language
instead of substituting a topic title into a template.
"""
from __future__ import annotations

from pathlib import Path

from config import Settings
from memory.context_manager import InterviewContext
from models.question_intent import QuestionIntent
from utils.logging import get_logger

logger = get_logger(__name__)

#: Every template file we expect to find in the prompts directory.
_TEMPLATES = (
    "interviewer_system",
    "generate_question",
    "evaluate_answer",
    "generate_follow_up",
    "generate_feedback",
    "messages",
)


class PromptBuilder:
    """Holds loaded templates and produces final prompt strings."""

    def __init__(self, settings: Settings) -> None:
        prompts_dir = Path(__file__).resolve().parent.parent / "prompts"
        self._templates: dict[str, str] = {}
        for name in _TEMPLATES:
            path = prompts_dir / f"{name}.md"
            try:
                self._templates[name] = path.read_text(encoding="utf-8")
            except OSError as exc:  # pragma: no cover - should not happen
                logger.error("Failed to load prompt template %s: %s", path, exc)
                self._templates[name] = ""
        self._messages = self._parse_messages()

    # --- system -----------------------------------------------------------

    def system_prompt(self) -> str:
        return self._templates["interviewer_system"]

    # --- shared context ---------------------------------------------------

    @staticmethod
    def _assessment_summary(context: InterviewContext) -> str:
        """Per-topic evidence collected so far (never profile guesses)."""
        lines: list[str] = []
        for topic, state in context.plan.assessment.topics.items():
            if not state.assessed:
                continue
            lines.append(
                f"- {topic}: confidence={state.confidence}, "
                f"failures={state.consecutive_failures}, "
                f"scores {state.worst_score}-{state.best_score}/10"
            )
        return "\n".join(lines) if lines else "No evidence collected yet."

    @staticmethod
    def _last_answer(context: InterviewContext) -> str:
        last = context.memory.last()
        return last.answer if last else "none yet"

    @staticmethod
    def _previous_questions(context: InterviewContext) -> str:
        questions = [turn.question for turn in context.memory.all_turns]
        return "\n".join(f"- {question}" for question in questions) or "none yet"

    # --- user prompts -----------------------------------------------------

    def question_prompt(
        self,
        context: InterviewContext,
        *,
        intent: QuestionIntent,
        question_type: str,
        difficulty: str,
        curriculum: str,
        previous_topic: str,
    ) -> str:
        return self._templates["generate_question"].format(
            candidate_summary=context.candidate.summary,
            strong_topics=", ".join(context.candidate.strong_topics) or "none",
            weak_topics=", ".join(context.candidate.weak_topics) or "none",
            knowledge_gaps=", ".join(context.candidate.knowledge_gaps) or "none",
            assessment_summary=self._assessment_summary(context),
            previous_answer=self._last_answer(context),
            previous_questions=self._previous_questions(context),
            curriculum_context=curriculum,
            day_number=intent.curriculum_day,
            day_title=intent.topic,
            module=intent.module or "—",
            learning_objective=intent.learning_objective or "—",
            concept=intent.concept or "—",
            question_type=question_type,
            cognitive_level=intent.cognitive_level or "—",
            purpose=intent.purpose or "—",
            expected_evidence=", ".join(intent.expected_evidence) or "—",
            difficulty=difficulty,
            question_number=context.current_question_index + 1,
            total_questions=max(context.plan.size, 8),
            topics_covered=", ".join(context.memory.topics_covered) or "none yet",
            previous_topic=previous_topic or "none",
            relationship=intent.relationship or "—",
            candidate_signal=intent.candidate_signal or "—",
            candidate_mentions=context.candidate_mentions,
        )

    def evaluate_prompt(
        self,
        context: InterviewContext,
        *,
        question: str,
        topic: str,
        question_type: str,
        difficulty: str,
        intent: str,
        learning_objective: str,
        concept: str,
        answer: str,
    ) -> str:
        return self._templates["evaluate_answer"].format(
            question=question,
            topic=topic,
            question_type=question_type,
            difficulty=difficulty,
            intent=intent or "—",
            learning_objective=learning_objective or "—",
            concept=concept or "—",
            answer=answer or "—",
            candidate_summary=context.candidate.summary,
            aggregate_summary=context.aggregate_summary,
        )

    def follow_up_prompt(
        self,
        context: InterviewContext,
        *,
        question: str,
        topic: str,
        learning_objective: str,
        concept: str,
        expected_evidence: list[str],
        day_title: str,
        module: str,
        answer: str,
        verdict: str,
        score: int,
        strategy: str,
        notes: str,
        curriculum: str,
        difficulty: str,
        follow_up_count: int,
        previous_questions: list[str],
    ) -> str:
        return self._templates["generate_follow_up"].format(
            question=question,
            topic=topic,
            day_title=day_title,
            module=module or "—",
            learning_objective=learning_objective or "—",
            concept=concept or "—",
            expected_evidence=", ".join(expected_evidence) or "—",
            answer=answer or "—",
            verdict=verdict,
            score=score,
            strategy=strategy,
            notes=notes or "—",
            curriculum_context=curriculum,
            difficulty=difficulty,
            follow_up_count=follow_up_count,
            previous_questions="\n".join(
                f"- {q}" for q in previous_questions
            )
            or "none yet",
        )

    def feedback_prompt(self, context: InterviewContext) -> str:
        # Evidence-based assessment state: per-topic verdicts and scores
        # from the actual interview (never invented).  EVERY touched topic
        # is listed — including topics where the candidate produced no
        # evidence — so feedback can never again report "0 topics" while
        # the transcript clearly covered several.
        assessment_lines = []
        for topic, state in context.plan.assessment.topics.items():
            if not state.touched:
                continue
            evidence = "; ".join(state.evidence) or "no explicit evidence"
            confidence = (
                state.confidence
                if state.assessed
                else "insufficient_evidence"
            )
            status = state.knowledge_status
            assessment_lines.append(
                f"- {topic}: knowledge_status={status}, confidence={confidence}, "
                f"failures={state.consecutive_failures}, "
                f"bare_claims={state.bare_claims}, "
                f"score range {state.worst_score}-{state.best_score}/10 | {evidence}"
            )
        assessment_str = (
            "\n".join(assessment_lines)
            if assessment_lines
            else "No topic could be confidently assessed."
        )

        # Topics from the profile that were NOT tested: the feedback must not
        # claim knowledge (or lack of it) about untested material.
        not_tested = (
            context.candidate.failed_topics + context.candidate.knowledge_gaps
        )
        not_tested_str = ", ".join(not_tested) if not_tested else "none"

        return self._templates["generate_feedback"].format(
            transcript=context.transcript_excerpt,
            candidate_summary=context.candidate.summary,
            aggregate_summary=context.aggregate_summary,
            assessment_state=assessment_str,
            not_tested=not_tested_str,
        )

    # --- deterministic messages (no LLM) ----------------------------------

    def intro_message(self, name: str) -> str:
        first_name = name.split()[0] if name else "there"
        return self._messages["intro"].format(
            name=name or "there", first_name=first_name
        )

    def first_question_bridge(self, name: str, question: str) -> str:
        first_name = name.split()[0] if name else "there"
        return self._messages["first_question_bridge"].format(
            first_name=first_name, question=question
        )

    def next_question_bridge(self, question: str, previous_topic: str = "", next_topic: str = "") -> str:
        return self._messages["next_question_bridge"].format(question=question)

    def final_question_message(self) -> str:
        return self._messages["final_question"]

    def wrap_up_message(self, name: str) -> str:
        return self._messages["wrap_up"].format(name=name or "there")

    def _parse_messages(self) -> dict[str, str]:
        """Split messages.md into per-section templates before formatting."""
        import re

        sections: dict[str, str] = {}
        pattern = re.compile(r"^\[(\w+)\]\s*$", re.MULTILINE)
        raw = self._templates["messages"]
        matches = list(pattern.finditer(raw))
        for index, match in enumerate(matches):
            name = match.group(1)
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(raw)
            sections[name] = raw[start:end].strip()
        return sections
