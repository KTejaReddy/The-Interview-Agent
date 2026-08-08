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

import re
from pathlib import Path

from config import Settings
from memory.context_manager import InterviewContext
from models.question_intent import QuestionIntent
from utils.logging import get_logger

logger = get_logger(__name__)

#: Phrases that never belong in an interviewer reaction, whichever path
#: generated it.  Used to validate the LLM's reaction and fall back to the
#: deterministic pools instead of letting a canned phrase through.
_BANNED_REACTION = (
    "glad to hear it",
    "let's make sure we're on the same page",
    "no problem — let's ground this differently",
    "let's try a simpler angle",
    "what's the core job",
    "core job of",
    "you mentioned",
    "earlier you said",
    "based on your previous",
    "according to your previous",
    "let's move on",
    "let me reframe",
    "let's make it concrete",
    "that's okay",
    "can you give me an example",
    "now let's discuss",
    "let's transition to",
)

#: Trailing dangling connectors the LLM sometimes leaves on a reaction
#: ("...embeddings, but") before the engine appends the question.  Stripped
#: so the assembled line never reads "...but What problem does X?".
_DANGLING_CONNECTOR = re.compile(
    r"[,;:\s]*(but|and|so|also|though|although|while|however|yet)$",
    re.IGNORECASE,
)

#: Every template file we expect to find in the prompts directory.
_TEMPLATES = (
    "human_interviewer",
    "interviewer_system",
    "generate_question",
    "evaluate_answer",
    "generate_follow_up",
    "generate_feedback",
    "security_check",
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

    def human_interviewer_prompt(self) -> str:
        """The dedicated human-interviewer behavioral block
        (``prompts/human_interviewer.md``): how the interviewer listens,
        remembers, reacts and decides what to say next.  This is the single
        authoritative home for interviewer persona/behavior — the per-task
        templates only carry their own mechanics, and the engine contract in
        ``interviewer_system`` only carries security + plumbing."""
        return self._templates["human_interviewer"]

    def system_prompt(self) -> str:
        """Composed system prompt for conversation-facing generation
        (questions and follow-ups): the dedicated human-interviewer block
        plus the compact engine contract and security rules."""
        return (
            f"{self._templates['human_interviewer']}\n\n"
            f"{self._templates['interviewer_system']}"
        )

    def assessment_system_prompt(self) -> str:
        """Lean system prompt for internal assessment calls (answer
        evaluation, final feedback): the engine contract + security rules.

        The full human-interviewer block stays on the conversation-facing
        generation calls, where it shapes what the candidate hears.  The
        internal calls only produce structured verdicts/feedback — their
        task templates already carry the judgment rules — so paying the
        full persona there would add ~3.6K tokens per call for no gain."""
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
    def _previous_questions(context: InterviewContext, limit: int = 6) -> str:
        """Recent question texts (rolling window).  The deterministic
        duplicate guard keeps its own full history, so the prompt only needs
        the recent ones — older questions add tokens without adding
        dedup power."""
        questions = [turn.question for turn in context.memory.all_turns]
        recent = questions[-limit:] if limit > 0 else questions
        return "\n".join(f"- {question}" for question in recent) or "none yet"

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
            conversation_so_far=context.transcript_excerpt,
            consecutive_weak=context.memory.consecutive_weak,
            interviewer_state=self._interviewer_state(context),
        )

    @staticmethod
    def _interviewer_state(context: InterviewContext) -> str:
        """Structured interviewer state for the question prompt: the
        emotional state, firmness level and last-answer assessment.  The
        LLM calibrates its reaction from this — it never quotes it to the
        candidate."""
        mem = context.memory
        last = mem.last()
        notes = last.notes.strip() if last and last.notes else "none"
        return (
            f"- Emotion: {mem.interviewer_emotion}\n"
            f"- Firmness: {mem.firmness}/3 (0 calm, 1 concerned, 2 direct, 3 firm)\n"
            f"- Last answer verdict: {last.verdict.value if last else 'none yet'}\n"
            f"- Last answer notes: {notes}\n"
            f"- Candidate recovered from an earlier struggle: "
            f"{'yes' if mem.recovered else 'no'}"
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
            conversation_so_far=context.transcript_excerpt,
            notable_earlier_statements=context.notable_earlier_statements,
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
            consecutive_weak=context.memory.consecutive_weak,
            previous_questions="\n".join(
                f"- {q}" for q in previous_questions[-6:]
            )
            or "none yet",
        )

    def security_check_prompt(self, message: str) -> str:
        """Prompt for a guard model classifying one untrusted message."""
        return self._templates["security_check"].format(message=message or "—")

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
            # Feedback runs ONCE at the end and must reason over the whole
            # interview, so it always gets the full transcript — the rolling
            # window only applies to per-turn prompts.
            transcript=context.memory.format_transcript(),
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

    # --- conversational bridge between main questions ---------------------
    #
    # The deterministic bridge owns ALL spoken transitions: a short reaction
    # to the previous answer (keyed by its verdict) plus a rotated transition
    # into the next topic.  The LLM is instructed to ask only the pure
    # question, so transitions are consistent, varied and never doubled.
    # Wording lives in messages.md rotation pools; this method only composes.

    def _pool(self, name: str) -> list[str]:
        """Rotation-pool entries: non-empty lines of a messages.md section.

        Comment lines ("# ...") are skipped defensively so a stray comment
        between sections can never leak into the interviewer's reply.
        """
        raw = self._messages.get(name, "")
        return [
            line.strip()
            for line in raw.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]

    def _reaction_for(
        self,
        verdict: str | None,
        index: int,
        *,
        consecutive_weak: int = 0,
        recovered: bool = False,
    ) -> str:
        """Short human reaction to the previous answer, rotated by turn and
        escalated by the interview's emotional trajectory.

        * a good answer on a topic the candidate previously struggled with
          gets an explicit *recovery* acknowledgment ("Much better — "),
        * repeated weak answers make the tone progressively firmer (mild →
          direct → firm), exactly like a human interviewer who has tried a
          concept a couple of ways and is about to move on,
        * repeated bare claims ("I know") get a firmer, more skeptical
          reaction instead of the same neutral "Alright — " every time.
        """
        if verdict is None:
            return ""
        verdict = verdict.lower()
        if recovered and verdict in ("good", "excellent"):
            pool = self._pool("reaction_recovery")
        elif verdict in ("good", "excellent"):
            pool = self._pool("reaction_good")
        elif verdict == "weak":
            if consecutive_weak >= 3:
                pool = self._pool("reaction_weak3")
            elif consecutive_weak >= 2:
                pool = self._pool("reaction_weak2")
            else:
                pool = self._pool("reaction_weak")
        elif verdict == "wrong":
            pool = self._pool("reaction_wrong")
        elif verdict == "unclear":
            if consecutive_weak >= 2:
                pool = self._pool("reaction_claim2")
            else:
                pool = self._pool("reaction_claim")
        else:
            return ""
        if not pool:
            return ""
        # Every third bridge has no reaction at all (human rhythm).
        if index % 3 == 2:
            return ""
        return pool[index % len(pool)]

    def _transition_for(self, related: bool, same_topic: bool, index: int) -> str:
        """A rotated spoken transition into the next topic.

        Entries are literal lines from messages.md — never formatted, so a
        stray brace in a pool can never break the reply."""
        if same_topic:
            pool = self._pool("transition_same")
        elif related:
            pool = self._pool("transition_related")
        else:
            pool = self._pool("transition_new")
        if not pool:
            return ""
        # Every fourth bridge asks the next question directly (no transition).
        if index % 4 == 3:
            return ""
        return pool[index % len(pool)]

    def reaction_or_fallback(
        self,
        reaction: str,
        *,
        topic: str,
        index: int,
        last_verdict: str | None = None,
        consecutive_weak: int = 0,
        recovered: bool = False,
    ) -> str:
        """Validate the LLM's content-aware reaction; fall back to the
        deterministic pool reaction when it is empty, canned, oversized or
        leaks curriculum metadata.  The pools remain a safety net, never the
        primary reaction mechanism."""
        reaction = (reaction or "").strip()
        low = reaction.lower()
        invalid = (
            len(reaction) > 160
            or any(phrase in low for phrase in _BANNED_REACTION)
            or bool(re.search(r"\bday \d+\b", low))
            or (topic and topic.lower() in low)
        )
        if not reaction or invalid:
            return self._reaction_for(
                last_verdict,
                index,
                consecutive_weak=consecutive_weak,
                recovered=recovered,
            )
        reaction = _DANGLING_CONNECTOR.sub("", reaction).strip()
        if not reaction:
            return self._reaction_for(
                last_verdict,
                index,
                consecutive_weak=consecutive_weak,
                recovered=recovered,
            )
        # The engine appends the question right after the reaction; a
        # reaction that does not end in punctuation would glue the two
        # together ("Let's shift gears What problem does...").  Normalize
        # to a complete short sentence.
        if reaction[-1] not in ".!?\u2014:\u2026":
            reaction += "."
        return reaction

    def next_question_bridge(
        self,
        question: str,
        previous_topic: str = "",
        next_topic: str = "",
        *,
        index: int = 0,
        last_verdict: str | None = None,
        related: bool = False,
        same_topic: bool = False,
        consecutive_weak: int = 0,
        recovered: bool = False,
    ) -> str:
        reaction = self._reaction_for(
            last_verdict,
            index,
            consecutive_weak=consecutive_weak,
            recovered=recovered,
        )
        transition = self._transition_for(related, same_topic, index)
        parts = [part for part in (reaction, transition) if part]
        if parts and not reaction and transition:
            # No reaction: the transition opens the sentence -> capitalise it.
            parts[0] = transition[0].upper() + transition[1:]
        prefix = (" ".join(parts) + " ") if parts else ""
        return f"{prefix}{question}"

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
            content = raw[start:end].strip()
            # Drop full-line comments ("# ...") that sit above the next
            # header — the section parser would otherwise glue them onto
            # this section and leak them into the interviewer's reply.
            content = "\n".join(
                line for line in content.splitlines()
                if not line.lstrip().startswith("#")
            ).strip()
            sections[name] = content
        return sections
