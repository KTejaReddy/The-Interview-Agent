"""Prompt builder.

Loads every prompt template from ``backend/prompts/*.md`` once and exposes
methods that fill them with concrete context.  No service contains prompt
text inline; all wording lives in the template files.
"""
from __future__ import annotations

from pathlib import Path

from config import Settings
from memory.context_manager import InterviewContext
from retrieval.curriculum_retriever import CurriculumRetriever
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

    # --- user prompts -----------------------------------------------------

    def question_prompt(
        self,
        context: InterviewContext,
        *,
        topic: str,
        question_type: str,
        difficulty: str,
        curriculum: str,
    ) -> str:
        return self._templates["generate_question"].format(
            candidate_summary=context.candidate.summary,
            strong_topics=", ".join(context.candidate.strong_topics) or "none",
            weak_topics=", ".join(context.candidate.weak_topics) or "none",
            knowledge_gaps=", ".join(context.candidate.knowledge_gaps) or "none",
            curriculum_context=curriculum,
            topic=topic,
            question_type=question_type,
            difficulty=difficulty,
            question_number=context.current_question_index + 1,
            total_questions=context.plan.size,
            topics_covered=", ".join(context.memory.topics_covered) or "none yet",
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
        answer: str,
    ) -> str:
        return self._templates["evaluate_answer"].format(
            question=question,
            topic=topic,
            question_type=question_type,
            difficulty=difficulty,
            intent=intent or "—",
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
        answer: str,
        verdict: str,
        score: int,
        strategy: str,
        notes: str,
        curriculum: str,
        difficulty: str,
    ) -> str:
        return self._templates["generate_follow_up"].format(
            question=question,
            topic=topic,
            answer=answer or "—",
            verdict=verdict,
            score=score,
            strategy=strategy,
            notes=notes or "—",
            curriculum_context=curriculum,
            difficulty=difficulty,
        )

    def feedback_prompt(self, context: InterviewContext) -> str:
        return self._templates["generate_feedback"].format(
            transcript=context.transcript_excerpt,
            candidate_summary=context.candidate.summary,
            aggregate_summary=context.aggregate_summary,
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

    def next_question_bridge(self, question: str) -> str:
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
