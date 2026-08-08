"""Conversation memory.

Stores every question, answer and evaluation for the entire session and
derives aggregate signals: topics covered, days covered, mistakes, strong
answers and a running question counter.  Nothing is pruned until the
session itself expires, so the memory is complete from START to DONE.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from models.enums import Difficulty, FollowUpStrategy, QuestionType, Verdict


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class TurnRecord:
    """One conversational exchange between interviewer and candidate."""

    turn: int
    question: str
    topic: str
    day_index: int
    question_type: QuestionType
    difficulty: Difficulty
    answer: str
    score: int = 0
    verdict: Verdict = Verdict.UNCLEAR
    follow_up: FollowUpStrategy = FollowUpStrategy.NEXT_TOPIC
    notes: str = ""
    is_follow_up: bool = False
    timestamp: datetime = field(default_factory=_now)

    def to_dict(self) -> dict:
        return {
            "turn": self.turn,
            "question": self.question,
            "topic": self.topic,
            "day_index": self.day_index,
            "question_type": self.question_type.value,
            "difficulty": self.difficulty.value,
            "answer": self.answer,
            "score": self.score,
            "verdict": self.verdict.value,
            "follow_up": self.follow_up.value,
            "is_follow_up": self.is_follow_up,
        }


class ConversationMemory:
    """Complete, session-scoped record of the interview."""

    def __init__(self, max_history_turns: int = 12) -> None:
        self._turns: list[TurnRecord] = []
        self._max_history_turns = max_history_turns
        #: Curriculum concepts the candidate brought up themselves (used to
        #: reference their own words later in the interview).
        self.mentions: list[str] = []
        #: Contradictions the evaluator noticed between the candidate's
        #: earlier statements and a later answer (surfaced in prompts and
        #: feedback so the interviewer can gently call them out).
        self.contradictions: list[str] = []

    def add_mentions(self, concepts: list[str]) -> None:
        """Record curriculum concepts the candidate mentioned in an answer."""
        for concept in concepts:
            if concept not in self.mentions:
                self.mentions.append(concept)

    def add_contradiction(self, statement: str) -> None:
        """Record a contradiction between two of the candidate's answers."""
        if statement not in self.contradictions:
            self.contradictions.append(statement)

    # --- writers ---------------------------------------------------------

    def add_turn(
        self,
        question: str,
        topic: str,
        day_index: int,
        question_type: QuestionType,
        difficulty: Difficulty,
        answer: str,
        score: int,
        verdict: Verdict,
        follow_up: FollowUpStrategy,
        notes: str = "",
        is_follow_up: bool = False,
    ) -> TurnRecord:
        record = TurnRecord(
            turn=len(self._turns) + 1,
            question=question,
            topic=topic,
            day_index=day_index,
            question_type=question_type,
            difficulty=difficulty,
            answer=answer,
            score=score,
            verdict=verdict,
            follow_up=follow_up,
            notes=notes,
            is_follow_up=is_follow_up,
        )
        self._turns.append(record)
        return record

    # --- readers ---------------------------------------------------------

    @property
    def all_turns(self) -> list[TurnRecord]:
        return list(self._turns)

    @property
    def count(self) -> int:
        return len(self._turns)

    def recent_turns(self, limit: int | None = None) -> list[TurnRecord]:
        """Most recent turns; ``limit=None`` returns the complete history so
        prompts can reason over the ENTIRE conversation (the interviewer
        must never forget an earlier claim or mistake)."""
        if limit is None:
            return list(self._turns)
        return self._turns[-limit:]

    def last(self) -> TurnRecord | None:
        return self._turns[-1] if self._turns else None

    @property
    def topics_covered(self) -> list[str]:
        return list(dict.fromkeys(turn.topic for turn in self._turns))

    def question_count_on_topic(self, topic: str) -> int:
        """Total questions (main + follow-ups) asked on a topic."""
        return sum(1 for turn in self._turns if turn.topic == topic)

    @property
    def days_covered(self) -> list[int]:
        return list(dict.fromkeys(turn.day_index for turn in self._turns))

    @property
    def mistakes(self) -> list[TurnRecord]:
        return [
            turn for turn in self._turns
            if turn.verdict in (Verdict.WRONG, Verdict.WEAK)
        ]

    @property
    def strong_answers(self) -> list[TurnRecord]:
        return [
            turn for turn in self._turns
            if turn.verdict in (Verdict.GOOD, Verdict.EXCELLENT)
        ]

    @property
    def consecutive_weak(self) -> int:
        """Trailing streak of non-substantive answers (weak / bare-claim
        verdicts).  Drives the interviewer's escalating firmness: the more
        consecutive struggles, the more direct the tone — exactly like a
        human interviewer becoming gradually firmer."""
        streak = 0
        for turn in reversed(self._turns):
            if turn.verdict in (Verdict.WEAK, Verdict.UNCLEAR):
                streak += 1
            else:
                break
        return streak

    @property
    def firmness(self) -> int:
        """Interviewer firmness 0 (calm) .. 3 (firm), derived from the
        conversation — never a fixed template.  Repeated struggles make the
        interviewer gradually more direct; a demonstrated answer resets it."""
        streak = self.consecutive_weak
        if streak >= 3:
            return 3
        if streak >= 2:
            return 2
        if streak >= 1:
            return 1
        return 0

    @property
    def recovered(self) -> bool:
        """True when the last answer was strong but an earlier answer on the
        same topic was weak / wrong / a bare claim — the candidate improved,
        and the interviewer should recognize the recovery."""
        last = self.last()
        if last is None or last.verdict not in (Verdict.GOOD, Verdict.EXCELLENT):
            return False
        return any(
            turn.topic == last.topic
            and turn.verdict in (Verdict.WEAK, Verdict.WRONG, Verdict.UNCLEAR)
            for turn in self._turns[:-1]
        )

    @property
    def interviewer_emotion(self) -> str:
        """Subtle internal emotional state derived from the conversation
        (never shown to the candidate).  Calibrates the interviewer's tone:
        impressed by sustained strength, concerned by wrong answers,
        gradually firmer under repeated non-answers, relieved on recovery."""
        last = self.last()
        if last is None:
            return "neutral"
        if self.recovered:
            return "relieved"
        if last.verdict in (Verdict.GOOD, Verdict.EXCELLENT):
            return "impressed" if last.score >= 9 else "encouraging"
        if last.verdict == Verdict.WRONG:
            return "concerned"
        if last.verdict == Verdict.UNCLEAR:
            # Repeated "I know" without evidence: neutral -> skeptical -> firm.
            if self.consecutive_weak >= 3:
                return "firm"
            if self.consecutive_weak >= 2:
                return "skeptical"
            return "neutral"
        # Verdict.WEAK
        if self.consecutive_weak >= 3:
            return "firm"
        if self.consecutive_weak >= 2:
            return "mildly_frustrated"
        return "concerned"

    @property
    def average_score(self) -> float:
        if not self._turns:
            return 0.0
        return sum(turn.score for turn in self._turns) / len(self._turns)

    @property
    def estimated_confidence(self) -> float:
        """0..1 derived from answer scores (10-point scale)."""
        return max(0.0, min(1.0, self.average_score / 10.0))

    def format_transcript(self, limit: int | None = None) -> str:
        """Compact interview log used to ground feedback generation and give
        every prompt full conversational awareness.  ``limit=None`` includes
        every turn of the interview."""
        lines: list[str] = []
        for turn in self.recent_turns(limit):
            lines.append(
                f"[Q{turn.turn}{' (follow-up)' if turn.is_follow_up else ''} | "
                f"{turn.difficulty.value} | {turn.question_type.value}] {turn.topic}"
            )
            lines.append(f"  Interviewer: {turn.question}")
            lines.append(f"  Candidate:   {turn.answer}")
            lines.append(
                f"  Evaluated:   score={turn.score}/10 verdict={turn.verdict.value}"
            )
        return "\n".join(lines)
